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


def dt_to_unix_array(times : np.array, timedelta : str = "0.1s") -> pd.Series:
    """ Convert an array of times from numpy into unix time in units of seconds.
        Authors: Shyam Bhuller (University of Oxford), Matthew Man (University of Toronto), Danaisis Vargas Oliva (University of Toronto)

    Args:
        times (np.array): Times, should be timezone compliant.

    Returns:
        pd.Series: Pandas series of times
    """
    # s = pd.Series(times).str.replace("T", " ").str.replace("Z", "")
    # mask = s.str.contains(r'\.')
    # s[mask] = pd.to_datetime(s[mask], format="%Y-%m-%d %H:%M:%S.%f")
    # s[~mask] = pd.to_datetime(s[~mask], format="%Y-%m-%d %H:%M:%S")
    # s = pd.Series(s, dtype="datetime64[ns]")

    s = pd.to_datetime(pd.Series(times).str.replace("T", " ").str.replace("Z", " "), format = "mixed")
    # print(s)



    # result = any(['.' in s for s in times])
    # # result = np.char.find(times, '.') >= 0
    # if result is True:
    #     fmt = "%Y-%m-%d %H:%M:%S.%f "
    # else:
    #     fmt = "%Y-%m-%d %H:%M:%S "

    # s = pd.to_datetime(pd.Series(times).str.replace("T", " ").str.replace("Z", " "), format = fmt)

    # try:
    #   s = pd.to_datetime(pd.Series(list(times)).str.replace("T", " ").str.replace("Z", " "))
    # except:
      # s = pd.to_datetime(pd.Series(times).str.replace("T", " ").str.replace("Z", " "), format = "mixed")
    #   print(pd.to_datetime("2026-04-01 15:08:57.2 "))
    #   exit(1)

    return (s - pd.Timestamp("1970-01-01")) // pd.Timedelta(timedelta)


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


def parse_time_range(times : time_range) -> tuple[time_range, bool]:
    """ Take a time range from a configuration and correctly format it.
        Authors: Shyam Bhuller (University of Oxford), Matthew Man (University of Toronto), Danaisis Vargas Oliva (University of Toronto)

    Args:
        times (time_range): Times from a configuration.

    Raises:
        Exception: type of start and end time (relative or absolute) are not the same.

    Returns:
        (time_range, bool): Formatted time range, if the time range is absolute or relative.
    """
    if type(times.start) != type(times.end):
        raise Exception("Time start and time end must be the same type")

    abs_time = all([(type(i) == str) for i in times])
    fmt_times = time_range(*[get_unix_timestamp(i) if abs_time else i for i in times])
    return fmt_times, abs_time


def slice_time_range(data : dict[pd.DataFrame], times : time_range) -> dict[pd.DataFrame]:
    """ Slice perfomance metric Dataframes using a time range.
        Authors: Shyam Bhuller (University of Oxford), Matthew Man (University of Toronto), Danaisis Vargas Oliva (University of Toronto)

    Args:
        data (dict[pd.DataFrame]): Performance metric data.
        times (time_range): Time range to slice in. Allowed input:
        [0, x] # first x seconds
        [0, -1] # whole time range
        [x, -1] # from x to end time
        [x, y] # from x to y in seconds

    Raises:
        Exception: Requested time range is out of bounds of the data.

    Returns:
        dict[pd.DataFrame]: Performance metric Dataframes in the specified time range.
    """    
    fmt_times, _ = parse_time_range(times)
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


def match_times(df : pd.DataFrame, run_time : time_range) -> pd.DataFrame:
    """ Match the time range of indices in a Dataframe (assuming time is index)
        and truncate/pad the dataframe if necessary.

    Args:
        df (pd.DataFrame): Dataframe with unix time as the indices.
        run_time (time_range): Time range to match.

    Returns:
        pd.DataFrame: Modified Dataframe.
    """
    if len(df) == 0:
        print("Warning: Dataframe is empty.")
        return df
    recorded_times = time_range(min(df.index), max(df.index))
    
    if recorded_times.start == recorded_times.end:
        step = 10 # assign some default step value
    else:
        step = int(np.mean(df.index[1:] - df.index[:-1]))

    pad_start = None
    pad_end = None
    mask = df.index > 0 # set all to true
    if recorded_times.start > run_time.start:
        pad_start = time_range(run_time.start, min(run_time.end, recorded_times.start))
    else:
        mask = mask & (df.index >= run_time.start)

    if recorded_times.end < run_time.end:
        pad_end = time_range(max(recorded_times.end, run_time.start), run_time.end)
    else:
        mask & (df.index <= run_time.end)

    new_df = df.iloc[mask]

    pad = []
    if pad_end is not None:
        pad = list(range(*pad_end, step))
    if pad_start is not None:
        pad = list(range(*pad_start, step))
    for i in run_time: # make sure the run times are padded in the timestamps
        if (i not in new_df.index) and (i not in pad):
            pad.append(i)

    df2 = pd.DataFrame({c : {i : 0 for i in pad} for c in df.columns})
    new_df = pd.concat([new_df, df2], axis = 0).sort_index()

    return new_df
