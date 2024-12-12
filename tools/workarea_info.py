#!/usr/bin/env python3
"""
Created on: 06/11/2024 11:57

Author: Shyam Bhuller (University of Oxford)

Description: Information about the workarea used to perform the test.
"""

import argparse
import os

import tabulate
import yaml

import files, shell, utils

from rich import print

printout = False

def verbprint(i : any):
    """ controlled printout.

    Args:
        i (any): item to print.
    """
    if printout is True: print(i)
    return


def get_repo_info(repo : str) -> list[str]:
    """ Get the branch name and commit for a github directory.

    Args:
        repo (str): Path to github repo.

    Returns:
        list: branch name, short commit hash.
    """
    with shell.chdir(repo):
        result = shell.run("echo -n \"$(git rev-parse --abbrev-ref HEAD),$( git rev-parse --short HEAD )\"", capture = True)
        return result.stdout.decode().split(",")


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


def check_configs(dire : str, out : str) -> dict | None:
    """ Check workarea for ehn1-configurations, and return information about the repo.

    Args:
        dire (str): dunedaq directory.

    Returns:
        tabulate.JupyterHTMLStr | None: HTML table of repo info.
    """
    ehn1_daqconf_path = shell.search_data_file("ehn1-daqconfigs", dire)

    if len(ehn1_daqconf_path) > 0:
        info = get_repo_info(ehn1_daqconf_path[0]) # should only have one

        # clone ehn1 repo in tmp and copy the pinning files to the output path.
        with shell.chdir("/tmp/"):
            shell.run(shell.clone("ssh://git@gitlab.cern.ch:7999/dune-daq/online/ehn1-daqconfigs.git", info[1]))
            shell.run(f"cp ehn1-daqconfigs/hw/cpupin-all* {out}")
            shell.run(f"rm -rf ehn1-daqconfigs/")

        return {"ehn1-daqconfigs" : info}
    else:
        verbprint("no ehn1-daqconfig area was found.")
        return


def make_release_table(release_info : dict) -> tabulate.JupyterHTMLStr:
    """ Compile release information into a table.

    Args:
        release_info (dict): Release information from the yaml file. 

    Returns:
        tabulate.JupyterHTMLStr: HTML table of the information.
    """
    verbprint(tabulate.tabulate(release_info.items(), tablefmt = "fancy"))
    return tabulate.tabulate(release_info.items(), tablefmt = "html")


def make_repo_table(repos : dict) -> tabulate.JupyterHTMLStr:
    """ Compile information from github repos into a table

    Args:
        repos (dict): Dictionary where key is repo name and value is output from get_repo_info.

    Returns:
        tabulate.JupyterHTMLStr: HTML table of repo infos.
    """
    table_headers = ["repo", "branch name", "commit"]
    tab_info = [[k,] + v for k,v in repos.items()]
    verbprint(tabulate.tabulate(tab_info, tablefmt = "fancy", headers = table_headers))
    return tabulate.tabulate(tab_info, tablefmt = "html", headers = table_headers)


def get_info(path : str, out : str) -> dict[str]:
    """ Get information about a dunedaq repository and return html formatted tables.

    Args:
        path (str): dunedaq directory.
        out (str): Output directory for info.

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
    file = shell.search_data_file(env_vars["SPACK_RELEASE"] + ".yaml", release_dir)[0]

    verbprint("release information:")
    info = yaml.safe_load(file.open())

    release_info = {k : v for k,v in info.items() if k in ["release", "type", "base_release"]}
    release_info["release_type"] = env_vars["SPACK_RELEASES_DIR"].split("/")[-1]
    release_info["dbt_version"] = env_vars["DBT_ROOT_WHEN_CREATED"].split("/")[-1]

    if release_info["release_type"] == "candidates":
        release_info["release_type"] = "candidate"

    make_release_table(release_info)

    workarea_info = {"release" : release_info}

    # get the local and remote repos
    for src, t in zip([env_vars["DUNE_DAQ_RELEASE_SOURCE"], path + "/sourcecode/"], ["release", "local"]):
        repos = check_repos(src)
        workarea_info[t+"_commit"] = repos
        verbprint(f"{t} repositories:")
        make_repo_table(repos)

    workarea_info["configuration"] = check_configs(path, out = out)

    files.save_json(out + "workarea_info.json", workarea_info)

    return


def main(args : argparse.Namespace):
    global printout
    printout = True

    test_args = files.load_json(args.file)
    path = args.path

    if (path is None) and (test_args["workarea"] is None):
        print("configuration has no workarea and it was not supplied in the commandline, exiting.")
        exit()
    elif (path is None):
        path = test_args["workarea"]
    else:
        pass

    get_info(path, test_args["data_path"])
    return


if __name__ == "__main__":

    parser = utils.ApplicationArguments("Create a performance report with one command.")
    parser.add_argument("-p", "--path", type=str, required = False, help="dunedaq working directory.")

    args = parser.create()

    print(args)
    main(args)