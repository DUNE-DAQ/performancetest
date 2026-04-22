#!/usr/bin/env python
"""
Created on: 05/12/2024 12:17

Author: Shyam Bhuller

Description: Create a cpu pinning file for a readout server.

#! Can get the server name from the template pinning file.
#! Pinning file needs to figure out the thread names somehow...
#! rte-worker threads are predefined in the OKS configuration, must read them in.

#! quick way is to pass the script a template pinning file with thread names (and rte-worker-threads), script then assigns the core numbers appropriately
#! correct way is to read in OKS file, somehow infer names from the configuration (unclear how) and create json file.

"""
import argparse
import copy
import json
import os

import files, cpu_topology

from collections import ChainMap

from rich import print, rule

def core_list_to_str(cores : list[int]) -> str:
    """ Convert a list of cores to a string format for the json file.

    Args:
        cores (list[int]): List of cores.

    Returns:
        str: Core list string.
    """
    #! for now, just use join, but can try to condense it later on.
    return ",".join(str(c) for c in cores)


def get_resource_allocation(template_file : str) -> ChainMap:
    with open(template_file, "r") as f:
        template = json.load(f)

    if "resource_allocation" in template:
        cpu_resource_allocation = ChainMap(*template["resource_allocation"])
    else:
        print("Warning: no resource allocation found in the pinning template, using the default")
        cpu_resource_allocation = ChainMap(*[dict(i) for i in cpu_resource_allocation_default.maps])

    tmp = []
    for i in cpu_resource_allocation.maps:
        tmp.append({k : getattr(args, k) if cpu_resource_allocation[k] is None else cpu_resource_allocation[k] for k in i})
    cpu_resource_allocation = ChainMap(*tmp)
    print(f"{cpu_resource_allocation=}")

    return cpu_resource_allocation


def assign_cores(core_map : cpu_topology.CoreMap, cores : list[cpu_topology.Element], max_cores : int) -> list[int]:
    """ Assign processing units to a thread. Used for cache aware pinning.

    Args:
        core_map (CoreMap): CPU map of server.
        cores (list[Element]): List of cores to assign processing units from.
        max_cores (int): Maximum number of procssing units to assign to a thread.

    Returns:
        list[int]: assigned processing units
    """
    pus = []
    while len(pus) < (2 * max_cores):
        if len(cores) == 0:
            raise Exception("Ran out of cores to assign!")
        next_core = cpu_topology.ElementList(cores, core_map).first
        pus.extend([c.id for c in next_core.children])
    return pus


def fill_pinning_map(pinning : dict, cpu_alloc : ChainMap, core_map : cpu_topology.CoreMap) -> dict:
    """ Assign processing units to threads. Is L3 cache aware. Thread names are prioritized by order in the dictionary.

    Args:
        pinning (dict): Pinning dictionary.
        cpu_alloc (ChainMap): cpu reosurce allocation map.
        core_map (CoreMap): CPU map of server.

    Returns:
        dict: Filled pinning map.
    """
    # First exclude the first core (first two processing units) in each numa region
    for n in core_map.numa.elements:
        core_map.core.get_id(min([c.id for c in n.get_type("Core")]))

    isolated_cores = cpu_topology.get_isolated_cores()
    pu_list = {numa_region.id : [i.id for i in numa_region.get_type("PU")] for numa_region in core_map.numa.elements} # keep a snapshot of the numa/pu assignment

    pinning_dict = {k : {"threads" : {}} for k in pinning}
    for app in pinning:
        print(app)
        parents = []
        for thread_group in pinning[app]["thread_group"]:
            for numa_region in core_map.numa.elements: # get the numa region, but do not remove it from the map yet
                if numa_region.id == thread_group["numa"]: break

            rte_cores = []
            for i in isolated_cores:
                if i in pu_list[numa_region.id]:
                    rte_cores.append(i)
                    if i in [j.id for j in numa_region.get_type("PU")]:
                        core_map.pu.get_id(i) # remove the rte pus
            n_rte = len(rte_cores)
            if n_rte == 0:
                print(f"Warning: no isolated cores were found for server {args.readout_server}! Cannot assign rte worker threads.")

            # count the total number of cores requested to be assigned to this application, and check it is sensible
            alloc_rte = cpu_alloc["rte"] if "rte" in cpu_alloc else 0
            total_requested_processing_units = (n_rte * alloc_rte) + sum([2 * v for k, v in cpu_alloc.items() if k != "rte"])
            print(f"{total_requested_processing_units=}")

            processing_units_available = len(numa_region.get_type("PU"))
            if total_requested_processing_units > processing_units_available:
                raise Exception(f"number of processing units required {total_requested_processing_units} exceeds the number available {processing_units_available}")

            # calculate the number of caches to assign for each thread group, and check this can also be fulfilled.
            requested_caches_map = []

            caches = numa_region.get_type("Cache")
            available_caches = len(caches)
            len_caches = [len(i.children) for i in caches]
            caches = sorted(caches, key=lambda c: len_caches[caches.index(c)], reverse = True) # sort cache domains to assign the caches with the highest core count first.
            caches = {c.id : c for c in caches}
            # print(caches)

            for i in cpu_alloc.maps: # over each set of caches, compute the required cores and assign the required number of caches to do so.
                requried_cores = 0
                for v in i.values():
                    requried_cores += v

                n_cache = 0
                found_caches = []
                found_cores = 0
                for cid in list(caches.keys()):
                    if found_cores >= requried_cores:
                        break
                    else:
                        found_caches.append(caches[cid])
                        found_cores += len(caches[cid].get_type("Core"))
                        del caches[cid]
                        n_cache += 1
                requested_caches_map.append(found_caches)

            # print(cpu_alloc.maps)
            # print(requested_caches_map)
            # print([len(i) for i in requested_caches_map])
            # print(requested_cores_in_caches_map)

            n_cache = sum([len(i) for i in requested_caches_map])
            if n_cache > available_caches:
                raise Exception(f"number of cache domains required ({n_cache}) exceeded the number available ({available_caches})")

            if n_rte > 0:
                # Now find the cache corresponding to the rte workers, and assign the rte worker threads
                rte_cache = None

                for pu in rte_cores:
                    for c in caches.values():
                        if pu in [i.id for i in c.get_type("PU")]:
                            if rte_cache is None:
                                rte_cache = c
                    # before assigning the other cores, assign rtes first as these are provided by the configuration
                    pinning_dict[app]["threads"][f"rte-worker-{pu}"] = str(pu)
                if rte_cache in caches:
                    caches.pop(rte_cache.id)
                    # caches.remove(rte_cache)


            # collect the cores for each cache needed in each thread group
            groups = []
            for n, m in zip(requested_caches_map, cpu_alloc.maps):
                g = []
                for cache in n:
                    g.extend(cache.children)
                    if cache.id in caches: caches.pop(cache.id)
                groups.append(g)
            # print(groups)

            # assign the remaining cores
            ccps = None
            for t in thread_group["threads"]:
                if "rte-worker" in t: # this assignment happens before, as lcores are defined by the configuration
                    continue

                # infer the thread type
                if ("cleanup" in t) or ("consumer" in t) or ("periodic" in t):
                    prefix = "ccp"
                else:
                    prefix = t.split("-")[0]

                # find the core group this thread type is within
                cg = [g for g, m in zip(groups, cpu_alloc.maps) if prefix in m]
                if len(cg) > 1:
                    raise Exception("cannot have the same thread type in different cache groups.")
                elif len(cg) == 0:
                    raise Exception(f"do not know how to assign cores to thread {t}")
                cg = cg[0]

                if prefix == "ccp": # cleanup, consumer and periodic threads are unique because they are all assigned the same cores
                    if ccps is None:
                        ccps = assign_cores(core_map, cg, cpu_alloc["ccp"])
                    pinning_dict[app]["threads"][t] = core_list_to_str(ccps)
                else:
                    pus = assign_cores(core_map, cg, cpu_alloc[prefix])
                    pinning_dict[app]["threads"][t] = core_list_to_str(pus)
            parents.extend(ccps)
        pinning_dict[app]["parent"] = core_list_to_str(parents)
    return {"daq_application" : pinning_dict}

def main(args = argparse.Namespace):
    cm = cpu_topology.CoreMap(cpu_topology.get_and_create_llc_domain_map(args.readout_server))
    print(rule.Rule("CPU map"))
    cm.print()

    has_multiple_caches = len(cm.numa.elements[0].children) > 1

    pus_numa = [[p.id for p in n.get_type("PU")] for n in cm.numa.elements]

    cpu_resource_allocation = get_resource_allocation(args.template)

    if not has_multiple_caches and len(cpu_resource_allocation.maps) > 1:
        print("hardware does not have multiple cache boundaries, cache regions will be merged into one")
    if has_multiple_caches and len(cpu_resource_allocation.maps) == 1:
        print('Warning: CPU has multiple cache boundaries, but only one cache region was requested. Consider using the default resource allocation (remove "resource_allocation" from the template), or define multiple cache regions')

    # ! this should be inferred from the oks config
    pinning_template = files.read_json(args.template)["daq_application"]
    print(pinning_template)

    # pinnig while running
    pinning = fill_pinning_map(pinning_template, cpu_resource_allocation, cm)
    print(rule.Rule("CPU pinning running"))
    print(pinning)

    # pinning during conf

    print(pinning_template)

    pinning_conf = copy.deepcopy(pinning)
    for app in pinning_conf["daq_application"]:
        numa_cores = []
        for tg in pinning_template[app]["thread_group"]:
            numa_cores.extend(pus_numa[tg["numa"]])
        pinning_conf["daq_application"][app]["parent"] = core_list_to_str(numa_cores)
    print(rule.Rule("CPU pinning all"))
    print(pinning_conf)

    print(rule.Rule("remaining CPUs in CPU map"))
    cm.print()

    for p, n in zip([pinning, pinning_conf],["cpupin-all-running.json", "cpupin-all.json"]):
        if os.path.isfile(n):
            # file exists, append/update
            pin_file = files.read_json(n)
            for k, v in p["daq_application"].items():
                pin_file["daq_application"][k] = v
            files.write_json(n, pin_file)
        else:
            files.write_json(n, p)
        
        print(f"pinning has been written to {n}")
    return

if __name__ == "__main__":
    cpu_resource_allocation_default = ChainMap(*[
        {
            "rawproc" : 8,
            "rte" : 1
        },
        {
            "recording" : 3,
        },
        {
            "tpproc" : 1,
            "ccp" : 3,
        }
    ])

    parser = argparse.ArgumentParser("Generate a pinning file for a readout machine.")
    parser.add_argument("-t", "--template", type = str, help = "pinning file template. must be a json file.", required = True)
    parser.add_argument("-r", "--readout_server", type = str, help = "hostname for the machine, if not provided the current machine hostname is used.", required = True)

    for k, v in cpu_resource_allocation_default.items():
        if k == "ccp":
            name = "consumer, cleanup or periodic"
        else:
            name = k
        parser.add_argument(f"--{k}", dest = k, type = int, default = None, help = f"number of cores to assign to a {name} thread. Set to {cpu_resource_allocation_default[k]} by default.")

    args = parser.parse_args()

    print(args)
    main(args)