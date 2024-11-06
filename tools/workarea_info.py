#!/usr/bin/env python3
"""
Created on: 06/11/2024 11:57

Author: Shyam Bhuller

Description: Information about the workarea used to perform the test.
"""

import argparse
import contextlib
import os
import subprocess

import tabulate
import yaml

import utils

from rich import print

@contextlib.contextmanager
def chdir(dire : str):
    """ Switch directories, then back to cwd.

    Args:
        dire (str): Temporary cwd.
    """
    cwd = os.getcwd()
    try:
        os.chdir(dire)
        yield
    finally:
        os.chdir(cwd)


def check_repos(dire : str) -> dict[list]:
    """ Check the branch and commit hash of a github repo.

    Args:
        dire (str): Sourcecode directory.

    Returns:
        dict[list]: repos and their branch name and commit hash.
    """
    repo_info = {}

    for repo in filter(os.path.isdir, [os.path.join(dire, i) for i in os.listdir(dire)]):
        with chdir(repo):
            result = subprocess.Popen("echo -n \"$( git rev-parse --abbrev-ref HEAD ),$( git rev-parse --short HEAD )\"", shell = True, stdout = subprocess.PIPE)

            repo_info[repo.split("/")[-1]] = result.communicate()[0].decode().split(",")

    return repo_info


def get_info(path : str, printout : bool) -> dict[str]:
    """ get information about a dunedaq repository and return html formatted tables.

    Args:
        path (str): dunedaq directory
        printout (bool): printout the information.

    Returns:
        dict[str]: html tables of the information.
    """
    def verbprint(i : any):
        if printout is True: print(i)
        return

    # check this is valid dunedaq directory
    ls = os.listdir(path)
    if "dbt-workarea-constants.sh" not in ls:
        raise Exception(f"{path} is not a valid dunedaq directory.")
    
    # get the workarea constants
    with open(path + "/dbt-workarea-constants.sh") as f:
        lines = f.readlines()

    env_vars = {}
    for l in lines:
        if "export" not in l: continue
        var = l.split("export ")[1].split("\n")[0].split("=")
        env_vars[var[0]] = var[1].replace('"', '')
    release_dir = env_vars["SPACK_RELEASES_DIR"] + "/" + env_vars["SPACK_RELEASE"]

    verbprint(env_vars)

    # get the release information from the yaml file in spack
    file = utils.search_data_file(env_vars["SPACK_RELEASE"] + ".yaml", release_dir)[0]

    info = yaml.safe_load(file.open())

    verbprint("release information:")
    release_info = {k : v for k,v in info.items() if k in ["release", "type", "base_release"]}
    html_table_info = tabulate.tabulate(release_info.items(), tablefmt = "html")
    verbprint(tabulate.tabulate(release_info.items(), tablefmt = "fancy"))

    html_tables = {"release_info" : html_table_info}

    # get the local and remote repos
    table_headers = ["repo", "branch name", "commit"]

    for src, t in zip([env_vars["DUNE_DAQ_RELEASE_SOURCE"], path + "/sourcecode/"], ["release", "local"]):
        repos = check_repos(src)
        verbprint(f"{t} repositories:")
        tab_info = [[k,] + v for k,v in repos.items()]
        html_tables["t"] = tabulate.tabulate(tab_info, tablefmt = "html", headers = table_headers)
        verbprint(tabulate.tabulate(tab_info, tablefmt = "fancy", headers = table_headers))
    return html_tables


def main(args):
    get_info(args.path, True)
    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Create a performance report with one command.")

    parser.add_argument(dest = "path", type = str, help = "dunedaq working directory.")

    args = parser.parse_args()

    print(args)
    main(args)