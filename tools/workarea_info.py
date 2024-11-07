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

printout = False

def verbprint(i : any):
    """ controlled printout.

    Args:
        i (any): item to print.
    """
    if printout is True: print(i)
    return


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


def get_repo_info(repo : str) -> list[str]:
    """ Get the branch name and commit for a github directory.

    Args:
        repo (str): Path to github repo.

    Returns:
        list: branch name, short commit hash.
    """
    with chdir(repo):
        result = subprocess.Popen("echo -n \"$(git rev-parse --abbrev-ref HEAD),$( git rev-parse --short HEAD )\"", shell = True, stdout = subprocess.PIPE)

        return result.communicate()[0].decode().split(",")


def check_repos(dire : str) -> dict[list]:
    """ Check the branch and commit hash of a github repo.

    Args:
        dire (str): Sourcecode directory.

    Returns:
        dict[list]: repos and their branch name and commit hash.
    """
    repo_info = {}

    for repo in filter(os.path.isdir, [os.path.join(dire, i) for i in os.listdir(dire)]):
        repo_info[repo.split("/")[-1]] = get_repo_info(repo)

    return repo_info


def check_configs(dire : str) -> tabulate.JupyterHTMLStr | None:
    """ Check workarea for ehn1-configurations, and return information about the repo.

    Args:
        dire (str): dunedaq directory.

    Returns:
        tabulate.JupyterHTMLStr | None: HTML table of repo info.
    """
    ehn1_daqconf_path = utils.search_data_file("ehn1-daqconfigs", dire)

    if len(ehn1_daqconf_path) > 0:
        info = get_repo_info(ehn1_daqconf_path[0]) # should only have one
        html_table = make_repo_table({"ehn1-daqconfigs" : info})
        return html_table
    else:
        verbprint("no ehn1-daqconfig area was found.")
        return


def make_repo_table(repos : dict) -> tabulate.JupyterHTMLStr:
    """ Compile information form github repos into a table

    Args:
        repos (dict): Dictionary where key is repo name and value is output from get_repo_info.

    Returns:
        tabulate.JupyterHTMLStr: HTML table of repo infos.
    """
    table_headers = ["repo", "branch name", "commit"]
    tab_info = [[k,] + v for k,v in repos.items()]
    table = tabulate.tabulate(tab_info, tablefmt = "html", headers = table_headers)
    verbprint(tabulate.tabulate(tab_info, tablefmt = "fancy", headers = table_headers))
    return table


def get_info(path : str) -> dict[str]:
    """ get information about a dunedaq repository and return html formatted tables.

    Args:
        path (str): dunedaq directory

    Returns:
        dict[str]: html tables of the information.
    """

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
    for src, t in zip([env_vars["DUNE_DAQ_RELEASE_SOURCE"], path + "/sourcecode/"], ["release", "local"]):
        repos = check_repos(src)
        verbprint(f"{t} repositories:")
        html_tables[t] = make_repo_table(repos)

    html_tables["configuration"] = check_configs(path)

    return html_tables


def main(args):
    global printout
    printout = True
    get_info(args.path)
    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Create a performance report with one command.")

    parser.add_argument(dest = "path", type = str, help = "dunedaq working directory.")

    args = parser.parse_args()

    print(args)
    main(args)