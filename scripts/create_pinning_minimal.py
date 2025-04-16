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

import resources, files

from collections import ChainMap

from rich import print, rule


def get_resource_allocation(template_file : str) -> ChainMap:
    template = files.read_json(template_file)

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


def main(args = argparse.Namespace):
    cm = resources.CoreMap(resources.create_llc_domain_map(args.readout_server))
    print(rule.Rule("CPU map"))
    cm.print()

    cpu_resource_allocation = get_resource_allocation(args.template)

    resources.validate_cpu_resource_map(cm, cpu_resource_allocation)

    # ! this should be inferred from the oks config
    pinning = files.read_json(args.template)["daq_application"]
    print(pinning)

    pinning, pinning_conf = resources.create_cpu_pinning(pinning, cm, cpu_resource_allocation)

    for p, n in zip([pinning, pinning_conf],["cpupin-all-running.json", "cpupin-all.json"]):
        files.write_json(n, p)
        print(f"pinning has been written to {n}")
    return

if __name__ == "__main__":
    cpu_resource_allocation_default = ChainMap(*[
        {
            "rawproc" : 16,
            "rte" : 1
        },
        {
            "recording" : 6,
        },
        {
            "tpproc" : 2,
            "ccp" : 6,
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