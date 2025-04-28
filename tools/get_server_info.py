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
    cmd = "lshw -xml"
    if shell.is_sudo(test_args["host"]):
        cmd = "sudo " + cmd
    else:
        print("Warning: user does not have sudo permissions, lshw output will be limited.")
    lshw_out = shell.run(cmd, capture = True, host = test_args['host'])

    if lshw_out.returncode > 0:
        print("could not get lshw output. See above for reason.")
        exit()

    tree = ET.ElementTree(ET.fromstring(lshw_out.stdout))
    out_path = f"{test_args['data_path']}lshw_{test_args['host']}.xml"

    print(f"file saved to: {out_path}")
    files.write_xml(tree, out_path)
    return


def main(args : argparse.Namespace):
    test_args = files.read_config(args.file)
    server_info(test_args)
    return


if __name__ == "__main__":
    args = utils.ApplicationArguments("Analyse performance metrics.").create()
    main(args)