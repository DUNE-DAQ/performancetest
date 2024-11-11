#!/usr/bin/env python
import argparse
import os
import pathlib

import files
import utils
import plotting

import pandas as pd

from rich import print

"""
cache hits and misses:
 - done already, are there requirements for the fraction of hits?
 
Memory bandwidth should be bewlow 80%:
 - need to figure out the maximum bandwidth
 - same as above, but per node
  
"""


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


def process_cpu_info(data : dict[pd.DataFrame], out : str, max_util : float = 80):
    """ Analyse CPU information and plot the results.
        Calculates maximum, minimum and various quantiles for each core and across all cores.

    Args:
        data (dict[pd.DataFrame]): Node exporter data.
        out (str): Output directory.
        max_util (float): Maximum acceptable utilistation. Defaults to 80
    """
    cpu_metrics = pd.concat(
        [
            data["CPU Usage (%)"].quantile(q = 50/100),
            data["CPU Usage (%)"].quantile(q = 99/100),
            data["CPU Usage (%)"].quantile(q = 99.9/100),
            data["CPU Usage (%)"].max(),
            data["CPU Usage (%)"].min()
        ], axis = 1, keys = ["50% percentile", "99% percentile", "99.9% percentile", "Maximum", "Minimum"])
    cpu_metrics.index = cpu_metrics.index.astype(int)
    total_metrics = cpu_metrics.mean(axis = 0)

    with plotting.PlotBook(out + "cpu_plots.pdf") as book:
        for c in cpu_metrics:
            plotting.bar(cpu_metrics[c].index, cpu_metrics[c], "Core", "Utilization (%)", c)
            if max(cpu_metrics[c]) > 50:
                plotting.plt.axhline(max_util, color  = "k", linestyle = "--")
            book.save()
        plotting.bar(total_metrics.index, total_metrics.values, None, "Total CPU Utilization (%)", None, 30, True)
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


def main(args : argparse.Namespace):
    plotting.set_plot_style()
    test_args = files.load_json(args.file)

    data_files = utils.search_data_file("hdf5", test_args["data_path"])

    ne = search_file(data_files, "node-exporter")

    data = files.read_hdf5(ne)

    out = test_args["data_path"] + "analysis/"
    os.makedirs(out, exist_ok = True)

    # ru = search_file(data_files, "A_CvwTCWk")
    # data = files.read_hdf5(ru)
    # print(data)

    process_disk_info(data, out)
    process_cpu_info(data, out)
    process_memory_info(data, out)

    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Create a performance report with one command.")

    parser.add_argument("-f", "--file", type = pathlib.Path, help = "json file which contains the details of the test.", required = True)

    args = parser.parse_args()
    if args.file.suffix != ".json":
        raise Exception("not a json file")

    print(args)
    main(args)