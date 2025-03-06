"""
Created on: 13/11/2024 11:23

Author: Shyam Bhuller (University of Oxford)

Description: Functions to help perform shell script actions, directory management and some common commands.
"""

import contextlib
import pathlib
import os
import re
import subprocess

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


def run(cmd : str, new_env : bool = False, capture : bool = False, host : str = None) -> subprocess.CompletedProcess:
    """ Run a bash command.

    Args:
        cmd (str): Bash command.
        env (bool, optional): Whether to run the command without the enviromnent variables. Defaults to False.
        capture (bool, optional): Capture output of command to a string. Defaults to False.
        host (str, optional): if provided, runs command on a specified remote host.

    Returns:
        subprocess.CompletedProcess: _description_
    """
    if host:
        cmd = f"ssh {os.environ['USER']}@{host} {cmd}"    
    pipe = subprocess.PIPE if capture is True else None
    out = subprocess.run(cmd, env = {} if new_env is True else None, shell = True, stdout = pipe, stderr = pipe)
    if out.stderr:
        print(f"Error running '{cmd}': {out.stderr}")
    return out


def parse_output(output: subprocess.CompletedProcess, separator : str = None) -> list | dict:
    """ Get output from run and apply some simple formatting.

    Args:
        output (subprocess.CompletedProcess): Subprocess output.
        separator (str, optional): String separator to split key-value pairs. Defaults to None.

    Returns:
        list | dict: _description_
    """
    output_lines = str(output.stdout)[2:].split("\\n")

    if separator:
        parsed = {}
        for i in output_lines:
            info = i.split(separator)
            if len(info) > 1:
                parsed[info[0]] = info[1].replace("  ", "")

        return parsed
    else:
        return output_lines


def search_data_file(s : str, path : str | pathlib.Path) -> list[pathlib.Path]:
    """ Search for terms in the names of files in a directory. Acts recursively.

    Args:
        s (str): Search term.
        path (str | pathlib.Path): Directory to search in.

    Returns:
        list[pathlib.Path]: list of matches for the search term.
    """
    matches = []
    for p in pathlib.Path(path).glob("**/*"):
        if re.search(s, p.name): matches.append(p)
        # if s in p.name: matches.append(p)
    return matches


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
