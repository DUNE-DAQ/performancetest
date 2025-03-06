#!/usr/bin/env python
"""
Created on: 06/02/2025 13:49

Author: Shyam Bhuller

Description: Get the Last Level Cache (LLC) domain for the physical processing units.
"""
import argparse
import xml.etree.ElementTree as ET

import shell, utils

from rich import print

def search_elem_type(elem : ET.ElementTree | ET.Element, type : str) -> callable:
    """ Search for elements by type.

    Args:
        elem (ET.ElementTree | ET.Element): xml element.
        type (str): Value of type to find.

    Returns:
        callable[ET.Element]: Generator of elements.
    """
    return utils.xml_search_elem(elem, "type", type)


def create_cache_map(parent : ET.Element) -> dict:
    """ Create a dictionary of processing units per core and L3 cache domain.

    Args:
        parent (ET.Element): Parent element, either a group or package as defined in lstopo.

    Returns:
        dict: Dictionary of L3 caches, cores and processing units.
    """
    caches = {}
    for cache in utils.xml_search_elem(parent, "type", "L3Cache"): # get the L3 cache domains in the parent element
        c = int(cache.attrib["gp_index"])
        caches[c] = {}
        for core in search_elem_type(cache, "Core"): # cores in each cache
            co = int(core.attrib["os_index"])
            caches[c][co] = [int(pu.attrib["os_index"]) for pu in search_elem_type(core, "PU")] # processing units in each core
    return caches


def create_llc_domain_map(server : str) -> dict:
    """ Parse output of lstopo and create a dictionary of the CPU topology.
        #? Extend to also include PCIe map?
    Args:
        server (str): Server to map.

    Returns:
        dict: CPU map.
    """
    output = shell.run("lstopo -p --of xml", capture = True, host = server).stdout

    tree = ET.ElementTree(ET.fromstring(output))

    socket = {}
    for package in search_elem_type(tree, "Package"): # package = socket
        has_groups = len(list(search_elem_type(package, "Group"))) != 0 # check if the socket has groups, if so there are multiple cache domains and the topology is different (so differnet logic is needed to build the map)


        s = int(package.attrib["os_index"])
        socket[s] = {}
        for numa in search_elem_type(package, "NUMANode"): # get numa regions in each socket
            n = int(numa.attrib["os_index"])
            socket[s][n] = {}

            if not has_groups: # if there are no groups, there is a single cache domain
                socket[s][n] = create_cache_map(package)

        if has_groups:
            for group in search_elem_type(package, "Group"):
                for numa in search_elem_type(group, "NUMANode"):
                    n = int(numa.attrib["os_index"])

                socket[s][n] = create_cache_map(group)

    return socket


def main(args : argparse.Namespace):
    domain_map = create_llc_domain_map(args.server)
    print(domain_map)
    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Get CPU topology of a computer including NUMA and L3 cache domains.")
    parser.add_argument("server", type = str)
    args = parser.parse_args()
    print(args)
    main(args)
