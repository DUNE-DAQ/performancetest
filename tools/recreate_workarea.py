#!/usr/bin/env python
"""
Created on: 11/11/2024 14:15

Author: Shyam Bhuller

Description: Re-create a workarea provided the software and configuration information from a given performance report. 
"""

import os
import argparse
import subprocess

import files
import utils

from rich import print

def setup_commands(path : str, spack_version : str, release_type : str, release_name : str) -> str:
    """ Set of commands to create the dunedaq workarea.

    Args:
        path (str): Directory to make workarea in.
        spack_version (str): Version of spack to get buidtools from.
        release_type (str): Type of release i.e. candidate, nightly etc.
        release_name (str): Name of release.

    Returns:
        str: Bash commands which runs the buildtools.
    """
    cmd = f"cd {path};"
    cmd += f"source /cvmfs/dunedaq.opensciencegrid.org/setup_dunedaq.sh;"
    cmd += f"setup_dbt {spack_version};"
    cmd += f"dbt-create -b {release_type} {release_name} RECREATED_{release_name};"
    return f'bash -c "{cmd}"'


def clone(repo : str, sha : str) -> str:
    """ Set of commands to clone a git compliant repo and checkout a specific commit.
        repo will be in a detatched HEAD state.

    Args:
        repo (str): repo url; can be ssh, https or any other type.
        sha (str): short commit hash.

    Returns:
        str: Bash commands.
    """
    dire = repo.split("/")[-1].split(".")[0]
    cmd = f"git clone {repo};"
    cmd += f"cd {dire};"
    cmd += f"git checkout {sha}"
    return cmd


def main(args : argparse.Namespace):

    test_args = files.load_json(args.file)
    info = files.load_json(utils.search_data_file("workarea_info.json", test_args["data_path"])[0])

    work_dir = args.path + f'RECREATED_{info["release"]["release"]}'

    # check if the workarea was already made
    if os.path.exists(work_dir):
        raise Exception(f"workarea has already been recreated in {work_dir}")

    # make daq workarea
    cmd = setup_commands(args.path, info["release"]["dbt_version"], info["release"]["release_type"], info["release"]["release"])
    subprocess.run(cmd, env = {}, shell = True)

    # commit local repos
    with utils.chdir(f'{work_dir}/sourcecode/'):
        for k, v in info["local_commit"].items():
            subprocess.run("pwd", env = {}, shell = True)
            subprocess.run(clone(f"https://github.com/DUNE-DAQ/{k}.git", v[1]), shell = True)

    # add ehn1-daqconfigs if applicable
    if info["configuration"] is not None:
        if "ehn1-daqconfigs" in info["configuration"]:
            os.makedirs(f"{work_dir}/work/", exist_ok = True)
            with utils.chdir(f"{work_dir}/work/"):
                subprocess.run(clone("ssh://git@gitlab.cern.ch:7999/dune-daq/online/ehn1-daqconfigs.git", info["configuration"]["ehn1-daqconfigs"][1]), shell = True)

    print(f"workarea created at: {work_dir}")
    print(f'make sure you run (in a brand new terminal) "cd {work_dir}; source env.sh; dbt-build; dbt-workarea-env" to finish making the workarea.')
    return


if __name__ == "__main__":
    parser = utils.ApplicationArguments("Re-create a workarea provided the software and configuration information from a given performance report.")
    parser.add_argument("-p", "--path", dest = "path", type = str, help = "dunedaq working directory.", required = True)

    args = parser.create()

    print(args)
    main(args)
