"""
Created on: 12/10/2024 22:57

Author: Shyam Bhuller

Description: general utility functions.
"""
import argparse
import os

from datetime import datetime as dt

import numpy as np
import pandas as pd

import requests
import pathlib


def make_plot_dir(args : dict):
    make_outdir = False
    if "plot_path" in args:
        if args["plot_path"] is None:
            make_outdir = True
    else:
        make_outdir = True

    if make_outdir:
        out_dir = str(test_path(args)) + "/plots/"
        print(out_dir)
        os.makedirs(out_dir, exist_ok = True)
    else:
        out_dir = args["plot_path"]

    return out_dir


def test_path(test_args : dict) -> pathlib.Path:
    path = f"perftest-run{test_args['run_number']}-{test_args['dunedaq_version'].replace('.', '_')}-{test_args['host'].replace('-', '')}-{test_args['test_name']}"

    path = pathlib.Path(test_args["out_path"] + "/" + path + "/")
    os.makedirs(path, exist_ok = True)
    print(f"created output directory: {path}")
    return path


def transfer(url : str, files : dict[pathlib.Path]):    
    for k, v in files.items():
        response = requests.put(url + k, files = {k : pathlib.Path(v).open("rb")})
    return response


def make_public_link(fp : pathlib.Path | str) -> str:
    """ Create cernbox link for file using the public url and file path (only works if the file path has been uploaded).

    Args:
        fp (pathlib.Path | str): file path in cernbox

    Returns:
        str: url
    """
    # cernbox_url_pdf = "https://cernbox.cern.ch/pdf-viewer/public/gEl6XmzXbW8OffB/"
    cernbox_url = "https://cernbox.cern.ch/files/link/public/ceg2IUASsNrHSvn/"
    return cernbox_url + fp


def dt_to_unix_array(times : np.array) -> pd.Series:
    """ Convert an array of times from numpy into unix time in units of seconds.

    Args:
        times (np.array): Times, should be timezone compliant.

    Returns:
        pd.Series: Pandas series of times
    """
    s = pd.to_datetime(pd.Series(times).str.replace("T", " ").str.replace("Z", " "))
    return (s - pd.Timestamp("1970-01-01")) // pd.Timedelta('1s')


def is_collection(x : any) -> bool:
    """ Check if object is iterable but not a string.

    Args:
        x (any): Object.

    Returns:
        bool: True if iterable and not string, False otherwise.
    """
    return (type(x) != str) and hasattr(x, "__iter__")


def get_unix_timestamp(time : str) -> int:
    """ Convert date time into unix timestamp.

    Args:
        time (str): Time in yyyy/mm/dd hh/mm/ss.

    Raises:
        ValueError: Time is not in the correct format.

    Returns:
        int: Unix time.
    """
    formats = ['%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S']
    for fmt in formats:
        try:
            timestamp = dt.strptime(time, fmt).timestamp()
            return int(timestamp * 1000) if '.' in time else int(timestamp)
        except ValueError:
            pass
    raise ValueError(f'Invalid time format: {time}')


def create_filename(test_args : dict) -> str:
    """Create filename based on the test report information.

    Args:
        test_args (dict): test report information.
        test_num (int): test number/index.

    Returns:
        str: filename.
    """
    return "-".join([
        test_args["dunedaq_version"].replace(".", "_"),
        test_args["host"].replace("-", ""),
        str(test_args["socket_num"]),
        test_args["data_source"],
        test_args["test_name"]
        ])


def search_data_file(s : str, path : str | pathlib.Path) -> pathlib.Path | list[pathlib.Path]:
    matches = []
    for p in pathlib.Path(path).glob("**/*"):
        if s in p.name: matches.append(p)
    return matches


def create_app_args(description : str) -> argparse.Namespace:
    """ Boiler plate code for application arguments.

    Args:
        description (str): description of the application.

    Raises:
        Exception: incorrect file type passed as the config.

    Returns:
        argparse.Namespace: parsed arguments.
    """
    parser = argparse.ArgumentParser(description)

    parser.add_argument("-f", "--file", type = pathlib.Path, help = "json file which contains the details of the test.", required = True)

    args = parser.parse_args()

    if args.file.suffix != ".json":
        raise Exception("not a json file")

    print(args)

    return args


def dunedaq_major_version(version : str) -> int:
    """ Get the major version of the dunedaq verison.

    Args:
        version (str): version string (format is vX.Y.Z).

    Returns:
        int: version number
    """
    return int(version.split(".")[0][-1])
