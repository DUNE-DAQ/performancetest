"""
Created on: 12/10/2024 22:57

Author: Shyam Bhuller

Description: general utility functions.
"""
import argparse
import os
import re

import requests
import pathlib

class ApplicationArguments(argparse.ArgumentParser):
    """ Class for managing application arguments for the performance report tools.
        Inherits from application.ArgumentParser and modifies class to reduce boilerplate when defining application args.
    """
    def __init__(self, description : str) -> None:
        super().__init__(description =description)
        # add arguments all applications should require
        self.add_argument("-f", "--file", type = pathlib.Path, help = "json file which contains the details of the test.", required = True)


    def create(self) -> argparse.Namespace:
        """ Parse the arguments and check provided arguments make sense.

        Raises:
            Exception: Incorrect value for configuration file passed. 

        Returns:
            argparse.Namespace: Parsed arguments.
        """
        args = self.parse_args()

        if args.file.suffix != ".json":
            raise Exception("not a json file")

        print(args)

        return args


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


def is_collection(x : any) -> bool:
    """ Check if object is iterable but not a string.

    Args:
        x (any): Object.

    Returns:
        bool: True if iterable and not string, False otherwise.
    """
    return (type(x) != str) and hasattr(x, "__iter__")


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


def dunedaq_major_version(version : str) -> int:
    """ Get the major version of the dunedaq verison.

    Args:
        version (str): version string (format is vX.Y.Z).

    Returns:
        int: version number
    """
    return int(version.split(".")[0][-1])


def search_dict(d : dict[str], regex : str) -> dict[str]:
    """ Search for string keys in a dictionary using regex.

    Args:
        d (dict[str]): Dictionary, keys must be string type
        regex (str): regular expresison.

    Returns:
        dict[str]: Dictionary with the found items.
    """
    filtered_dict = {}
    for k, v in d.items():
        if re.search(regex, k):
            filtered_dict[k] = v
    return filtered_dict


def add_to_dict(dictionary : dict, item : list, key : any):
    """ Add an item to another item in a dictionary. The item must be an object that suports the addition operator.

    Args:
        dictionary (dict): Dictionary, original is modified.
        item (list): Item to add.
        key (any): Item to add to.
    """ 
    if key not in dictionary:
        dictionary[key] = item
    else:
        dictionary[key] = dictionary[key] + item
    return
