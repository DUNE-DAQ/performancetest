#!/usr/bin/env python
"""
Created on: 16/04/2025 14:11

Author: Shyam Bhuller

Description: Readout CPU affinity using OKS configurations to infer thread names.
"""
import argparse
import os

from collections import ChainMap

import conffwk
import resources, files

import numpy as np

from rich import print


def create_thread_names(ids : list, threads : list[str], app_info : dict) -> list[str]:
    """ Create the thread names based on information found from the OKS config.

    Args:
        ids (list): Source IDs.
        threads (list[str]): Threads to create for the provided source IDs.
        app_info (dict): Application information.

    Returns:
        list[str]: Created thread names.
    """
    names = []
    for n in threads:
        initial_prefix = app_info["prefix"][n]
        if n in ["link", "tp"]:
            initial_prefix += "0-" # not sure why the 0 is added to the raw and tp procs... 
        all_thread_names = [initial_prefix + str(d) for d in ids]
        new_prefix = os.path.commonprefix(all_thread_names)
        diff = np.unique([len(t.replace(new_prefix, "")) for t in all_thread_names])
        if new_prefix != initial_prefix: # try some regex to simplify pinning file
            for n in diff:
                names.append(new_prefix + "".join(["."]*n))
        else: # dont know how to handle the regex in this case.
            names.extend(all_thread_names)
    return names


def main(args : argparse.Namespace):
    print(args.oks_session)
    db = conffwk.Configuration('oksconflibs:' + args.oks_session)

    segments = db.get_dals(class_name = "Segment")
    for tpc_segment in segments:
        if tpc_segment.id == "tpc-segment":
            break

    """
        thread names can be found by searching for thead_name_prefix (can we do this in the python?)
        for raw processors, a thread is made per detector stream. Detector streams are found under the HermesDataSenders under apa1-connections.

        recording thread name is hardcoded, one per detector stream.
        cleanup, consumer and periodic thread names are hardcoded, one per detector stream.
        
        tp proc thread name found under TPDataProcessors in the DataHandlerConfs for the repsective numa.
        number of tp proc threads should be equal to the number of tp handlers, found under tp_source_ids in the readout application.
        also need to make cleanup, consumer and periodic threads for the tp handlers.
    """
    app_info = {}
    for s in tpc_segment.segments:
        for apps in s.applications:
            info = {}
            if apps.className() == "ReadoutApplication":
                host = apps.runs_on.runs_on.id # get the host of the readout application
                for i in apps.contains:
                    if i.className() == "DetectorToDaqConnection":
                        for j in i.contains:
                            if j.className() == "DPDKReceiver": # get dpdk receiver
                                lcores = j.configuration.used_lcores # get lcores and numa number to associate to this readout application
                                if len(lcores) != 1:
                                    raise Exception(f"Expected 1 lcore for the DPDK reciever, found {len(lcores)}")
                                numa = lcores[0].numa_id
                                lcores = lcores[0].cpu_cores
                            
                            if j.className() == "ResourceSetAND":
                                detstream_source_id = []
                                for ds in j.contains:
                                    detstream_source_id.extend([d.source_id for d in ds.contains]) # get detector stream source IDs
                prefix = {"recording" : "recording-", "cleanup" : "cleanup-", "consumer" : "consumer-", "periodic" : "periodic-"} # thread name prefixes that must be inferred (not exposed in the oks configuration)
                for k, h in zip(["link", "tp"], [apps.link_handler, apps.tp_handler]): # get the thread prefix names that can be inferred
                    if not h:
                        print(f"Warning, no {k} handler found for ReadoutApplication {apps.id}")
                        print(h)
                        prefix[k] = None
                    else:
                        prefix[k] = h.data_processor.thread_names_prefix
                tp_source_ids = [t.sid for t in apps.tp_source_ids] # get the TP source IDs

                info["host"] = host
                info["numa"] = numa
                info["lcores"] = lcores
                info["tp_source_ids"] = tp_source_ids
                info["detstream_source_ids"] = detstream_source_id
                info["prefix"] = prefix
                app_info[apps.id] = info

    print(app_info)

    unique_hosts = np.unique([app_info[i]["host"] for i in app_info])
    pinning_info = {str(k) : {} for k in unique_hosts}

    cpu_maps = {}
    for i in app_info:
        host = app_info[i]["host"]
        if host not in cpu_maps:
            cpu_maps[host] = resources.CoreMap(resources.create_llc_domain_map(host))

        pinning_info[host][i] = {"numa" : app_info[i]["numa"]}
        link_handler_thread_names = create_thread_names(app_info[i]["detstream_source_ids"], ["link", "cleanup", "consumer", "periodic", "recording"], app_info[i])
        if app_info[i]["prefix"]["tp"]:
            tp_handler_thread_names = create_thread_names(app_info[i]["tp_source_ids"], ["tp", "cleanup", "consumer", "periodic"], app_info[i])
        else:
            tp_handler_thread_names = []
        rte_thread_names = [f"rte-worker-{l}" for l in app_info[i]["lcores"]]

        pinning_info[host][i]["threads"] = [*link_handler_thread_names, *tp_handler_thread_names, *rte_thread_names]

    print(pinning_info)
    print(cpu_maps)

    resource_allocation = files.read_json(args.template)
    for h, m in resource_allocation.items():
        resource_allocation[h] = ChainMap(*m)
    print(resource_allocation)

    for i in unique_hosts:
        print(f"validating resource allocation for host {i}")
        if i not in resource_allocation:
            raise Exception(f"resource allocation template for {i} was not provided in {args.template}")
        resources.validate_cpu_resource_map(cpu_maps[i], resource_allocation[i])
    print("done!")

    pinning = []
    pinning_conf = []
    for k, v in pinning_info.items():
        print(f"creating pinning for readout applications on host {k}")
        pin_run, pin_conf = resources.create_cpu_pinning(v, cpu_maps[k], resource_allocation[k])
        pinning.append(pin_run["daq_application"])
        pinning_conf.append(pin_conf["daq_application"])

    pinning = {"daq_application" : {k : v for d in pinning for k, v in d.items()}}
    pinning_conf = {"daq_application" : {k : v for d in pinning_conf for k, v in d.items()}}

    for p, n in zip([pinning, pinning_conf],["cpupin-all-running.json", "cpupin-all.json"]):
        files.write_json(n, p)
        print(f"pinning has been written to {n}")
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Readout CPU affinity using OKS configurations to infer thread names.")
    parser.add_argument("-t", "--template", type = str, help = "pinning file template. must be a json file.", required = True)
    parser.add_argument("-o", "--oks_session", type = str, help = "OKS session file.", required = True)

    args = parser.parse_args()

    print(args)
    main(args)