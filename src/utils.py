"""
Created on: 12/10/2024 22:57

Author: Shyam Bhuller

Description: general utility functions.
"""
from datetime import datetime as dt

import numpy as np
import pandas as pd

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


def create_filename(test_args : dict, test_num : int) -> str:
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
        str(test_args["socket_num"][test_num]),
        test_args["data_type"],
        test_args["test_name"][test_num]
        ])
