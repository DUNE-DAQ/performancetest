"""
Created on: 12/10/2024 18:42

Author: Shyam Bhuller

Description: Module to handle file input/output.
"""
import pathlib
import json
import tables

import pandas as pd


def write_dict_hdf5(dictionary : dict, file : str):
    """ Write dictionary to a HDF5 file.

    Args:
        dictionary (dict): dictionary to save
        file (str): file
    """
    with pd.HDFStore(file) as hdf:
        for k, v in dictionary.items():
            try:
                hdf.put(k, v)
            except Exception as e:
                print(f"cannot write {k} to file: {e}")
                pass
    return


def read_hdf5(file : str | pathlib.Path) -> pd.DataFrame | dict[pd.DataFrame]:
    """ Reads a HDF5 file and unpacks the contents into pandas dataframes.

    Args:
        file (str): file path.

    Returns:
        pd.DataFrame : if hdf5 file only has 1 key
        dict : if hdf5 file contains more than 1 key
    """
    keys = []
    with tables.open_file(pathlib.Path(file), driver = "H5FD_CORE") as hdf5file:
        for i in hdf5file.root:
            keys.append(i._v_pathname[1:])
            if type(i) == tables.group.Group:
                for j in hdf5file.root[i._v_pathname[1:]]:
                    if type(j) == tables.group.Group:
                        keys.append(j._v_pathname[1:])

    data = {}
    if len(keys) == 1:
        return pd.read_hdf(file)
    else:
        for k in keys:
            try:
                data[k] = pd.read_hdf(file, key = k)
            except:
                print(f"could not open {k}")
                pass
    return data


def load_json(file : str | pathlib.Path) -> dict:
    """Open json file as dictionary.

    Args:
        file (str | pathlib.Path): json file to open.

    Returns:
        dict: loaded file.
    """
    with pathlib.Path(file).open("r") as f:
        return json.load(f)


def save_json(file : str | pathlib.Path, data : dict):
    """Save dictionary to json file.

    Args:
        file (str | pathlib.Path): path to save dictonary to.
        data (dict): dictionary to save.
    """
    with pathlib.Path(file).with_suffix(".json").open("w") as f:
        json.dump(data, f, indent = 4)
