#!/usr/bin/env python
import argparse
import os
import pathlib

import files, shell, plotting, utils

import numpy as np
import pandas as pd

from rich import print

"""
cache hits and misses:
 - done already, are there requirements for the fraction of hits?
 
Memory bandwidth should be bewlow 80%:
 - need to figure out the maximum bandwidth
 - same as above, but per node
  
"""


def fill_zeros_with_last(arr : np.array, axis : int) -> np.array:
    """ Replace zeroes in an array with the previous non-zero value along a given axis.

    Args:
        arr (np.array): 1 or 2 dimensional array.
        axis (int): axis to loop over.

    Returns:
        np.array: array with the zeroes filled.
    """
    if len(arr.shape) == 1:
        return fill_zeros_with_last(np.expand_dims(arr, axis = 1), 1).flatten() # convert flat array to 2d, then flatten again.

    new = []
    for i in range(arr.shape[axis]):
        a = np.take(arr, i, axis = axis)
        prev = np.arange(len(a))
        prev[a == 0] = 0
        new.append(a[np.maximum.accumulate(prev)])
    new = np.array(new).T
    return new


def search_file(data_files : list, signature : str) -> pathlib.Path | None:
    """ Return first file in a list which contains the signrature.

    Args:
        data_files (list): list of files.
        signature (str): signature to search for.

    Returns:
        pathlib.Path | None: found file path or None.
    """
    for f in data_files:
        if signature in str(f):
            return f
    return


def cpu_usage_rate(idle : pd.DataFrame | pd.Series, total : pd.DataFrame | pd.Series) -> np.array:
    """ Compute the CPU usage as a rate per time.

    Args:
        idle (pd.DataFrame | pd.Series): Time cpu spends not doing any tasks
        total (pd.DataFrame | pd.Series): Total cpu time.

    Returns:
        np.array : Array of usage rates, has dimensions n - 1 along the time axis.
    """
    return cpu_usage(fill_zeros_with_last(abs(idle[1:].values - idle[:-1].values), axis = 1), fill_zeros_with_last(abs(total[1:].values - total[:-1].values), axis = 1))


def cpu_usage(idle : float | np.array, total : float | np.array) -> float | np.array:
    """ CPU usage, defined as the pecrent of cpu time not idling.

    Args:
        idle (float | np.array): Time cpu spends not doing any tasks
        total (float | np.array): Total cpu time.

    Returns:
        float | np.array: CPU usage.
    """
    return 100 * (1 - (idle/total))


def process_cpu_info(data : dict[pd.DataFrame], out : str, max_util : float = 80, pinning_file : dict = None):
    """ Analyse CPU information and plot the results.
        Calculates maximum, minimum and various quantiles for each core and across all cores.

    Args:
        data (dict[pd.DataFrame]): Node exporter data.
        out (str): Output directory.
        max_util (float): Maximum acceptable utilistation. Defaults to 80
    """

    total_time_per_core = sum(utils.search_dict(data, "(?=.*CPU)(?!.*Usage)").values()) # total time per core

    cpu_time_total = total_time_per_core.sum(axis=1) # total time across all cores
    cpu_time_idle = data["CPU idle (s)"].sum(axis=1) # total idle time across all cores

    usage = pd.DataFrame(cpu_usage_rate(data["CPU idle (s)"], total_time_per_core), columns = total_time_per_core.columns) # usage per core
    total_usage = pd.Series(cpu_usage_rate(cpu_time_idle, cpu_time_total)) # usage of whole CPU

    # metrics for the entire CPU
    total_metrics = pd.DataFrame(np.expand_dims(np.array([
            total_usage.quantile(q = 50/100),
            total_usage.quantile(q = 99/100),
            total_usage.quantile(q = 99.9/100),
            total_usage.max(),
            total_usage.min()
        ]), axis=1), index = ["50% percentile", "99% percentile", "99.9% percentile", "Maximum", "Minimum"])


    # metrics per CPU core
    cpu_metrics = pd.concat(
        [
            usage.quantile(q = 50/100),
            usage.quantile(q = 99/100),
            usage.quantile(q = 99.9/100),
            usage.max(),
            usage.min()
        ], axis = 1, keys = ["50% percentile", "99% percentile", "99.9% percentile", "Maximum", "Minimum"])
    cpu_metrics.index = cpu_metrics.index.astype(int)

    # metrics per thread
    thread_usage = {}
    for name, num in pinning_file.items():
        mask = total_time_per_core.columns[np.array(num).flatten()]
        thread_total_time = total_time_per_core[mask].sum(axis=1)
        thread_idle_time = data["CPU idle (s)"][mask].sum(axis=1)
        thread_usage[name] = cpu_usage_rate(thread_idle_time, thread_total_time)
    thread_usage = pd.DataFrame(thread_usage)

    thread_metric = pd.concat(
        [
            thread_usage.quantile(q = 50/100),
            thread_usage.quantile(q = 99/100),
            thread_usage.quantile(q = 99.9/100),
            thread_usage.max(),
            thread_usage.min()
        ], axis = 1, keys = ["50% percentile", "99% percentile", "99.9% percentile", "Maximum", "Minimum"])

    # plotting
    with plotting.PlotBook(out + "cpu_plots.pdf") as book:
        for c in cpu_metrics:
            plotting.bar(cpu_metrics[c].index, cpu_metrics[c], "Core", "Utilization (%)", c)
            if max(cpu_metrics[c]) > 50:
                plotting.plt.axhline(max_util, color  = "k", linestyle = "--")
            book.save()

        for c in thread_metric:
            plotting.plt.figure(figsize=(6.4, 1.5 * 6))
            plotting.bar(thread_metric[c].index, thread_metric[c].values, "Utilization (%)", "Thread", horizontal = True, newFigure = False, title = c)
            if max(cpu_metrics[c]) > 50:
                plotting.plt.axvline(max_util, color  = "k", linestyle = "--")

            plotting.plt.xlim(0, 100)
            plotting.plt.tight_layout()
            book.save()

        plotting.bar(total_metrics.index, total_metrics.values.flatten(), None, "Total CPU Utilization (%)", None, 30, True)
        plotting.plt.axhline(max_util, color  = "k", linestyle = "--")
        plotting.plt.ylim(0, 100)
        book.save()

    return


def process_disk_info(data : dict[pd.DataFrame], out : str, max_write_time : float = 100, max_write_APA : float = 876.25):
    """ Analyse disk information for the NVME and RAID devices and plots the results.
        Calculates total IO time, disk write rate during the test and total amount written to disk.

    Args:
        data (dict[pd.DataFrame]): Node exporter data.
        out (str): Output directory.
        max_write_time (float, optional): maxmium time data should be written in seconds. Defaults to 100.
        max_write_APA (float, optional): maximum amount of data to be written for a single APA in GB. Defaults to 876.25.
    """

    nvme_sample = data["Disk IO time (s)"].filter(regex=("nvme|md")).columns

    time = data["Disk IO time (s)"].index.astype(int)
    time = time - time[0]
    tlabel = "Relative time (s)"

    dt = data["Disk IO time (s)"] - data["Disk IO time (s)"].iloc[0]
    io_time = dt[nvme_sample]

    write_rate = 8 * data["Disk Written (Bps)"][nvme_sample]/(1000**3)
    total_written =  write_rate * io_time / 8

    max_io = io_time.max()
    max_wr = write_rate.max()
    max_tw = total_written.max()

    with plotting.PlotBook(out + "disk_plots.pdf") as book:
        plotting.plot(time, io_time, io_time.columns, tlabel, "Disk IO time (s)")
        plotting.plt.axhline(max_write_time, color = "k", linestyle = "--", label = "Expected\nwrite time (100 s)")
        plotting.plt.legend()
        book.save()
        plotting.plot(time, write_rate, write_rate.columns, tlabel, "Disk write rate (Gb/s)")
        plotting.plt.legend()
        book.save()
        plotting.plot(time, total_written, total_written.columns, tlabel, "Total written to disk (GB)")
        plotting.plt.axhline(max_write_APA, color = "k", linestyle = "--", label = "Expected data written\nper APA (876.25 GB)")
        plotting.plt.legend()
        book.save()

        # bar plots
        plotting.bar(max_io.index, max_io.values, "Device", ylabel = "Total IO time (s)", rotation = 30, bar_label = True)
        plotting.plt.axhline(max_write_time, color = "k", linestyle = "--", label = "Expected\nwrite time (100 s)")
        plotting.plt.legend()
        book.save()

        plotting.bar(max_wr.index, max_wr.values, "Device", ylabel = "Maximum Disk write rate (Gb/s)", rotation = 30, bar_label = True)
        book.save()

        plotting.bar(max_tw.index, max_tw.values, "Device", ylabel = "Total written to disk (GB)", rotation = 30, bar_label = True)
        plotting.plt.axhline(max_write_APA, color = "k", linestyle = "--", label = "Expected data written\nper APA (876.25 GB)")
        plotting.plt.legend()
        book.save()

    return


def process_memory_info(data :dict[pd.DataFrame], out : str):
    time = data["Memory Usage (%)"].index.astype(int)
    time = time - time[0]
    tlabel = "Relative time (s)"
    with plotting.PlotBook(out + "memory_plots.pdf") as book:
        plotting.plot(time, data["Memory Usage (%)"], None, tlabel, "Memory Usage (%)")
        plotting.plt.axhline(80, color = "k", linestyle = "--")
        plotting.plt.ylim(0, 100)
        book.save()
    return


def get_thread_nums(thread_str):

    split = thread_str.split(",")

    for i in range(len(split)):
        if "-" in split[i]:
            trange = [int(j) for j in split[i].split("-")]
            split[i] = list(range(min(trange), max(trange) + 1))
        else:
            split[i] = int(split[i])
    return split

def add_to_dict(dictionary : dict, item : list, key : any):
    if key not in dictionary:
        dictionary[key] = item
    else:
        dictionary[key] = dictionary[key] + item
    return


def parse_pinning_file(pinning_file, ru_host : str):
    target = ru_host.replace("-", "")

    parsed_pinning_file = {}

    for k, v in pinning_file.items():
        if k == "_comment" : continue
        if k == "daq_application":
            for name, application in v.items():
                if target in name:
                    print(name)
                    add_to_dict(parsed_pinning_file, get_thread_nums(application["parent"]), key = "parent")
                    for tname, threads in application["threads"].items():
                        add_to_dict(parsed_pinning_file, get_thread_nums(threads), tname)
    return parsed_pinning_file


def main(args : argparse.Namespace):
    plotting.set_plot_style()
    test_args = files.load_json(args.file)

    pinning_file = shell.search_data_file("cpupin-all-running", test_args["data_path"])
    if len(pinning_file) == 0:
        pinning_file = None
    else:
        pinning_file = files.load_json(pinning_file[0])

    pinning_file = parse_pinning_file(pinning_file, test_args["host"])

    data_files = shell.search_data_file("hdf5", test_args["data_path"])

    ne = search_file(data_files, "node-exporter")

    data = files.read_hdf5(ne)

    out = test_args["data_path"] + "analysis/"
    os.makedirs(out, exist_ok = True)

    # ru = search_file(data_files, "A_CvwTCWk")
    # data = files.read_hdf5(ru)

    # process_disk_info(data, out)
    process_cpu_info(data, out, pinning_file = pinning_file)
    # process_memory_info(data, out)




    return


if __name__ == "__main__":
    args = utils.ApplicationArguments("Analyse performance metrics.").create()
    main(args)