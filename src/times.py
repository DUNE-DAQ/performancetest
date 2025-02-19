"""
Created on: 29/11/2024 13:53

Authors: Shyam Bhuller (University of Oxford), Matthew Man (University of Toronto), Danaisis Vargas Oliva (University of Toronto)

Description: Module to handle functions to do with maniputating times.
"""
from collections import namedtuple
from datetime import datetime as dt

import pandas as pd
import numpy as np

time_range = namedtuple("time_range", ["start", "end"])


def month2num(month : str) -> int:
    """ Convert a Month in text to number.
        Matthew Man (University of Toronto), Danaisis Vargas Oliva (University of Toronto)

    Args:
        month (str): Month in text form.

    Returns:
        int: Month number.
    """
    months = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
    return months[month] if month in months else print('Warning: invalid month')


def get_unix_timestamp(time : str) -> int:
    """ Convert date time into unix timestamp.
        Matthew Man (University of Toronto), Danaisis Vargas Oliva (University of Toronto)

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


def dt_to_unix_array(times : np.array) -> pd.Series:
    """ Convert an array of times from numpy into unix time in units of seconds.
        Authors: Shyam Bhuller (University of Oxford), Matthew Man (University of Toronto), Danaisis Vargas Oliva (University of Toronto)

    Args:
        times (np.array): Times, should be timezone compliant.

    Returns:
        pd.Series: Pandas series of times
    """
    s = pd.to_datetime(pd.Series(times).str.replace("T", " ").str.replace("Z", " "))
    return (s - pd.Timestamp("1970-01-01")) // pd.Timedelta('1s')


def relative_time(df : pd.DataFrame) -> pd.Series:
    """ Convert absolute time from the performance metric into relative time.
        Authors: Shyam Bhuller (University of Oxford)

    Args:
        df (pd.DataFrame): Performance metric.

    Returns:
        pd.Series: Relative time.
    """
    time = df.index.astype(int)
    return time - time[0]


def parse_time_range(times : time_range) -> time_range:
    """ Take a time range from a configuration and correctly format it.
        Authors: Shyam Bhuller (University of Oxford), Matthew Man (University of Toronto), Danaisis Vargas Oliva (University of Toronto)

    Args:
        times (time_range): times from a configuration.

    Raises:
        Exception: type of start and end time (relative or absolute) are not the same.

    Returns:
        time_range: formatted time range.
    """
    if type(times.start) != type(times.end):
        raise Exception("Time start and time end must be the same type")
    fmt_times = time_range(*[get_unix_timestamp(i) if (type(i) == str) else i for i in times])
    return fmt_times


def slice_time_range(data : dict[pd.DataFrame], times : time_range) -> dict[pd.DataFrame]:
    """ Slice perfomance metric Dataframes using a time range.
        Authors: Shyam Bhuller (University of Oxford), Matthew Man (University of Toronto), Danaisis Vargas Oliva (University of Toronto)

    Args:
        data (dict[pd.DataFrame]): performance metric data.
        times (time_range): time range to slice in. Allowed input:
        [0, x] # first x seconds
        [0, -1] # whole time range
        [x, -1] # from x to end time
        [x, y] # from x to y in seconds

    Raises:
        Exception: requested time range is out of bounds of the data.

    Returns:
        dict[pd.DataFrame]: performance metric Dataframes in the specified time range.
    """    
    fmt_times = parse_time_range(times)
    for k, df in data.items():
        if len(df.index) < 2: continue
        rt = relative_time(df)

        is_unix_timestamp = (min(df.index) - fmt_times.start) < 31_556_926 # timestamps one year out will be just intrepeted as relative time in seconds
        is_valid_range = (max(df.index) - min(df.index)) > (fmt_times.end - fmt_times.start) # should work even if end time is -1

        if is_unix_timestamp:
            mask = (df.index >= fmt_times.start) & (df.index <= fmt_times.end)
        else:
            if is_valid_range:
                end_time = max(rt) if fmt_times.end == -1 else fmt_times.end
                mask = (rt >= fmt_times.start) & (rt <= end_time)
            else:
                raise Exception(f"requested {fmt_times} is out of bounds {time_range(start=min(rt), end=max(rt))}")
        data[k] = df[mask]
    return data

