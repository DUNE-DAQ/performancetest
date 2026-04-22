#!/usr/bin/env python
"""
Created on: 06/02/2025 13:49

Author: Shyam Bhuller

Description: Get the Last Level Cache (LLC) domain for the physical processing units.
"""
import argparse
import cpu_topology
from rich import print

def main(args : argparse.Namespace):
    domain_map = cpu_topology.get_and_create_llc_domain_map(args.server)
    print(domain_map)
    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Get CPU topology of a computer including NUMA and L3 cache domains.")
    parser.add_argument("server", type = str)
    args = parser.parse_args()
    print(args)
    main(args)
