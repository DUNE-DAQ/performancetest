#!/usr/bin/env python
"""
Created on: 03/03/2025 13:36

Author: Shyam Bhuller

Description: Get information about a server and store it for a given test.
"""

import argparse
import multiprocessing

import xml.etree.ElementTree as ET

import files, utils, shell

from rich import print

def run(host : str, data_path : str):
    """ Run lshw on the host machine, capture the output as an xml tree and save the output.

    Args:
        host (str): Host name.
        data_path (str): Output data path.
    """
    lshw_out = shell.run("sudo lshw -xml", capture = True, host = host)

    if lshw_out.returncode > 0:
        print("could not get lshw output. See above for reason.")
        exit()

    tree = ET.ElementTree(ET.fromstring(lshw_out.stdout))
    out_path = f"{data_path}lshw_{host}.xml"

    print(f"file saved to: {out_path}")
    files.write_xml(tree, out_path)
    return


def server_info(test_args : dict):
    args = [[test_args["host"][i], test_args["data_path"]] for i in range(len(test_args["host"]))]
    pool = multiprocessing.Pool(len(test_args["host"]))
    result = pool.starmap_async(run, args)
    result.get()
    return


def main(args : argparse.Namespace):
    test_args = files.read_config(args.file)
    server_info(test_args)
    return


if __name__ == "__main__":
    args = utils.ApplicationArguments("Analyse performance metrics.").create()
    main(args)