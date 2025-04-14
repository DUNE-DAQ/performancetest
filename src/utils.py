"""
Created on: 12/10/2024 22:57

Authors: Shyam Bhuller (University of Oxford), Matthew Man (University of Toronto), Danaisis Vargas Oliva (University of Toronto)

Description: general utility functions.
"""
import argparse
import os
import re
import time

import xml.etree.ElementTree as ET

import pathlib

def timer(func):
    """ Decorator which times a function.

    Args:
        func (function): function to time
    """
    def wrapper_function(*args, **kwargs) -> object:
        """ Times funcions, returns outputs
        Returns:
            any: func output
        """
        s = time.time()
        out = func(*args,  **kwargs)
        print(f'{func.__name__!r} executed in {(time.time()-s):.4f}s')
        return out
    return wrapper_function


class ApplicationArguments(argparse.ArgumentParser):
    """ Class for managing application arguments for the performance report tools.
        Inherits from application.ArgumentParser and modifies class to reduce boilerplate when defining application args.
        Authors: Shyam Bhuller (University of Oxford)

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


def make_plot_dir(args : dict) -> str:
    """ Make directory to keep performance report plots in.
        Authors: Shyam Bhuller (University of Oxford), Matthew Man (University of Toronto), Danaisis Vargas Oliva (University of Toronto)

    Args:
        args (dict): performance test config.

    Returns:
        str: name of created plot path.
    """
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
    """ Create outpput test directory path.
        Authors: Shyam Bhuller (University of Oxford), Matthew Man (University of Toronto), Danaisis Vargas Oliva (University of Toronto)

    Args:
        test_args (dict): performance test configuration.

    Returns:
        pathlib.Path: created directory.
    """
    path = f"perftest-run{test_args['run_number']}-{test_args['dunedaq_version'].replace('.', '_')}-{test_args['test_name']}"

    path = pathlib.Path(test_args["out_path"] + "/" + path + "/")
    os.makedirs(path, exist_ok = True)
    print(f"created output directory: {path}")
    return path


def make_public_link(fp : pathlib.Path | str) -> str:
    """ Create cernbox link for file using the public url and file path (only works if the file path has been uploaded).
        Authors: Shyam Bhuller (University of Oxford)

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
        Authors: Shyam Bhuller (University of Oxford)

    Args:
        x (any): Object.

    Returns:
        bool: True if iterable and not string, False otherwise.
    """
    return (type(x) != str) and hasattr(x, "__iter__")


def create_filename(test_args : dict) -> str:
    """ Create filename based on the test report information.
        Authors: Shyam Bhuller (University of Oxford), Matthew Man (University of Toronto), Danaisis Vargas Oliva (University of Toronto)

    Args:
        test_args (dict): test report information.
        test_num (int): test number/index.

    Returns:
        str: filename.
    """
    return "-".join([
        test_args["dunedaq_version"].replace(".", "_"),
        test_args["data_source"],
        test_args["test_name"]
        ])


def dunedaq_major_version(version : str) -> int:
    """ Get the major version of the dunedaq verison.
        Authors: Shyam Bhuller (University of Oxford)

    Args:
        version (str): version string (format is vX.Y.Z).

    Returns:
        int: version number
    """
    try:
        return int(version.split(".")[0][-1])
    except:
        raise Exception(f"Not a valid run number : {version}")


def search_dict(d : dict[str], regex : str) -> dict[str]:
    """ Search for string keys in a dictionary using regex.
        Authors: Shyam Bhuller (University of Oxford)

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
        Authors: Shyam Bhuller (University of Oxford)

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


def xml_match_attrib(elem : ET.Element, attrib : str, value : str) -> bool:
    """ Returns True if a value of an attribute in an xml Element matches the target value.

    Args:
        elem (ET.Element): xml Element.
        attrib (str): attribute name.
        value (str): target value.

    Returns:
        bool: whether there was a match.
    """
    if value:
        return (attrib in elem.attrib) and (elem.attrib[attrib] == value)


def xml_search_elem(elem : ET.ElementTree | ET.Element, attrib : str, value : str) -> ET.Element:
    """ Search an xml Element by attribute value and yield the found Element.

    Args:
        elem (ET.ElementTree | ET.Element): 
        attrib (str): attribute to compare.
        value (str): value of attribute to match.

    Yields:
        Iterator[ET.Element]: Element with the found attribute value.
    """
    for obj in elem.iter():
        if xml_match_attrib(obj, attrib, value):
            yield obj
    return


def xml_search_elem_name(elem : ET.ElementTree | ET.Element, name : str) -> ET.Element:
    """ Search an xml Element by name and yield the found Element.

    Args:
        elem (ET.ElementTree | ET.Element): elements.
        name (str): name of the Elements to match.

    Yields:
        Iterator[ET.Element]: Element with the found attribute value.
    """
    for obj in elem.iter():
        if obj.tag == name:
            yield obj
    return


def xml_search_elem_name_single(elem : ET.ElementTree | ET.Element, name : str) -> ET.Element | None:
    """ Search for a single Element by name. If multiple elements found it returns the first.

    Args:
        elem (ET.ElementTree | ET.Element): elements.
        name (str): name of the Elements to match.

    Returns:
        ET.Element: first found Element.
    """
    return next(xml_search_elem_name(elem, name), None)
