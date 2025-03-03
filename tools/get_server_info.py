#!/usr/bin/env python
"""
Created on: 03/03/2025 13:36

Author: Shyam Bhuller

Description: Get information about a server and store it for a given test.
"""

import argparse
import os

import xml.etree.ElementTree as ET

import files, utils, shell

from rich import print

def server_info(test_args : dict):
    lshw_out = shell.run(f"ssh {os.environ['USER']}@{test_args['host']} sudo lshw -xml", capture = True)

    if lshw_out.returncode > 0:
        print("could not get lshw output. See above for reason.")
        exit()

    tree = ET.ElementTree(ET.fromstring(lshw_out.stdout))
    out_path = f"{test_args['data_path']}lshw_{test_args['host']}.xml"

    print(f"file saved to: {out_path}")
    files.write_xml(tree, out_path)
    return


def main(args : argparse.Namespace):
    test_args = files.read_json(args.file)
    server_info(test_args)
    return


if __name__ == "__main__":
    args = utils.ApplicationArguments("Analyse performance metrics.").create()
    main(args)