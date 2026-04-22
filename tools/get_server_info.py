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

def xml_to_file(data_path : str, host : str, cmd_name : str, xmlstring : str):
    """ Write xml data to file.

    Args:
        data_path (str): Output data path.
        host (str): Host name.
        cmd_name (str): Command name, used as file prefix.
        xmlstring (str): xml data to write.
    """
    tree = ET.ElementTree(ET.fromstring(xmlstring))
    out_path = f"{data_path}{cmd_name}_{host}.xml"

    print(f"file saved to: {out_path}")
    files.write_xml(tree, out_path)
    return


def run_cmd(cmd : str, host : str, require_sudo : bool) -> str:
    """ Run commad and capture stdout.

    Args:
        cmd (str): Command to run.
        host (str): Host to run command on.
        require_sudo (bool): Command requires sudo to run properly.

    Returns:
        str: command stdout.
    """
    if require_sudo and shell.is_sudo(host):
        cmd = "sudo " + cmd
    else:
        print("Note: user does not have sudo permissions, lshw output will be limited.")
    cmd_out = shell.run(cmd, capture = True, host = host)

    if cmd_out.returncode > 0:
        print("Could not get hardware info output. See above for reason.")
        exit()
    return cmd_out.stdout


def run(host : str, data_path : str):
    """ Run lshw on the host machine, capture the output as an xml tree and save the output.

    Args:
        host (str): Host name.
        data_path (str): Output data path.
    """
    cmds = {
        "lshw" : "lshw -xml",
        "lstopo": "lstopo -p --of xml"
    }
    for name, cmd in cmds.items():
        cmd_out = run_cmd(cmd, host, True)
        xml_to_file(data_path, host, name, cmd_out)
    return


def server_info(test_args : dict):
    args = [[test_args["host"][i], test_args["data_path"]] for i in range(len(test_args["host"]))]
    pool = multiprocessing.Pool(min(len(test_args["host"]), multiprocessing.cpu_count() - 1))
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