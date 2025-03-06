#!/usr/bin/env python
"""
Created on: 03/03/2025 16:33

Author: Shyam Bhuller

Description: Get a map of the physical GPCIe slot number to the pcie address and numa number of the installed PCIe devices.
"""

import argparse

import shell
from rich import print

def main(args : argparse.Namespace):
    dmi = shell.parse_output(shell.run('sudo dmidecode -t slot | grep -e Designation -e "Bus Address" -e "Current Usage"', host = args.host, capture = True))

    pcie_map = {}

    for i in range(0, len(dmi)-1, 3):
        slot = dmi[i].split(": ")[-1]
        addr = dmi[i + 2].split(": ")[-1]
        usage = dmi[i + 1].split(": ")[-1]
        pcie_map[addr] = f"{slot}|{usage}"


    lspci = shell.parse_output(shell.run('lspci -D', host = args.host, capture = True))

    lspci_numa = shell.parse_output(shell.run('lspci -vv -m | grep -Ew "Device:|NUMANode:"', host = args.host, capture = True))

    addr_numa = {}
    for i in range(0, len(lspci_numa)-1, 3):
        addr = lspci_numa[i].split("\\t")[-1]
        numa = lspci_numa[i+2].split("\\t")[-1]
        addr_numa[f"0000:{addr}"] = numa

    pcie_map_dev = {}

    for a in pcie_map:
        dev = None
        for i in lspci:
            if a in i:
                dev = i
                break
        pcie_map_dev[pcie_map[a]] = {"deivce:" : dev, "NUMA:" : addr_numa.get(a)}

    print(pcie_map_dev)
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Get a map of the physical GPCIe slot number to the pcie address and numa number of the installed PCIe devices.")
    parser.add_argument("-s", "--server", dest = "host", default = None, type = str)
    args = parser.parse_args()
    print(args)
    main(args)