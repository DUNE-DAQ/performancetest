#!/usr/bin/env python
import argparse
import ast
import os
import pathlib

from collections import namedtuple

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

def get_thread_nums(thread_str : str) -> list[int]:
    """ Get CPU numbers from the formatted strings used in a CPU pinning file. Example is "0,10-54".

    Args:
        thread_str (str): formatted string.

    Returns:
        list[int]: list of CPUs.
    """
    split = thread_str.split(",")

    for i in range(len(split)):
        if "-" in split[i]:
            trange = [int(j) for j in split[i].split("-")]
            split[i] = list(range(min(trange), max(trange) + 1))
        else:
            split[i] = int(split[i])
    return split


def parse_pinning_file(pinning_file : dict, ru_host : str) -> dict[list]:
    """ Parse a CPU pinning file, creating a list of cpus for each thread for every daq application.

    Args:
        pinning_file (dict): CPU pinning file.
        ru_host (str): Readout host name.

    Returns:
        dict[list]: Parsed pinning file.
    """
    target = ru_host.replace("-", "")

    parsed_pinning_file = {}

    for k, v in pinning_file.items():
        if k == "_comment" : continue
        if k == "daq_application":
            for name, application in v.items():
                if target in name:
                    print(name)
                    utils.add_to_dict(parsed_pinning_file, get_thread_nums(application["parent"]), key = "parent")
                    for tname, threads in application["threads"].items():
                        utils.add_to_dict(parsed_pinning_file, get_thread_nums(threads), tname)
    return parsed_pinning_file


def fill_zeros_with_last(arr : np.ndarray, axis : int) -> np.ndarray:
    """ Replace zeroes in an array with the previous non-zero value along a given axis.

    Args:
        arr (np.ndarray): 1 or 2 dimensional array.
        axis (int): axis to loop over.

    Returns:
        np.ndarray: array with the zeroes filled.
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


def cpu_usage_rate(idle : pd.DataFrame | pd.Series, total : pd.DataFrame | pd.Series) -> np.ndarray:
    """ Compute the CPU usage as a rate per time.

    Args:
        idle (pd.DataFrame | pd.Series): Time cpu spends not doing any tasks
        total (pd.DataFrame | pd.Series): Total cpu time.

    Returns:
        np.ndarray : Array of usage rates, has dimensions n - 1 along the time axis.
    """
    return cpu_usage(fill_zeros_with_last(abs(idle[1:].values - idle[:-1].values), axis = 1), fill_zeros_with_last(abs(total[1:].values - total[:-1].values), axis = 1))


def cpu_usage(idle : float | np.ndarray, total : float | np.ndarray) -> float | np.ndarray:
    """ CPU usage, defined as the pecrent of cpu time not idling.

    Args:
        idle (float | np.ndarray): Time cpu spends not doing any tasks
        total (float | np.ndarray): Total cpu time.

    Returns:
        float | np.ndarray: CPU usage.
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




def process_network_info(data : dict[pd.DataFrame], out : str):
    """ Process system network traffic information and make plots.

    Args:
        data (dict[pd.DataFrame]): node exporter data.
        out (str): output file diretory.
    """
    network_rt = utils.search_dict(data, "Network.*\(Bps\)")

    with plotting.PlotBook(out + "network_plots") as book:
        for k, v in network_rt.items():
            plotting.plot(plotting.relative_time(v), v.values, v.columns, "Time (s)", k.split(" (")[0], autofmt = "B/s", book = book)
            total_net = v.sum(axis=0)
            plotting.bar(total_net.index, total_net/1E6, "", "Total " + k.split(" (")[0] + " (MB)", rotation=30, bar_label = True)
            plotting.plt.yscale("log")
            book.save()
    return


def process_memory_info(data : dict[pd.DataFrame], out : str):
    """ Process system memory information and make plots.

    Args:
        data (dict[pd.DataFrame]): node exporter data.
        out (str): output file diretory.
    """
    time = data["Memory Usage (%)"].index.astype(int)
    time = time - time[0]
    tlabel = "Relative time (s)"
    with plotting.PlotBook(out + "memory_plots.pdf") as book:
        plotting.plot(time, data["Memory Usage (%)"], None, tlabel, "Memory Usage (%)")
        plotting.plt.axhline(80, color = "k", linestyle = "--")
        plotting.plt.ylim(0, 100)
        book.save()
    return


def process_tp_info(data : dict[pd.DataFrame], out : str, expected_hit_rate : float = 100, acceptance_hit_rate : float = 500, tp_size : int = 384, n_dlh = 40, n_ch : int = 2560):
    """ Process TP information from a given run.

    Args:
        data (dict[pd.DataFrame]): TP data.
        out (str): Output file edirectory.
        expected_hit_rate (float, optional): Expected hit rate the readout should be able to sustain. Defaults to 100 Hz/ch.
        acceptance_hit_rate (float, optional): Hite rate we would like the readout to be able to sustain. Defaults to 500 Hz/ch.
        tp_size (int, optional): Size of a TP. Defaults to 384 bytes.
        n_dlh (int, optional): Number of datalinkhandlers per APA/CRP. Defaults to 40.
        n_ch (int, optional): Number of channels in an APA/CRP. Defaults to 2560.
    """
    hit_rates = list(utils.search_dict(data, "hit rates").values())[0]

    hits_sent = list(utils.search_dict(data, "TP Sent rates").values())[0]

    tp_writer_info = list(utils.search_dict(data, "TP writing rates").values())[0]

    tph_request_rates = list(utils.search_dict(data, "(?=.*Request rate)(?!.*tphandler)").values())[0]

    total_tp_drop_rates = list(utils.search_dict(data, "dropped").values())[0]
    total_tp_drop_rates = total_tp_drop_rates.sum(axis = 0)

    #* 8 nics * 5 wibs = 40 DLHs
    n_apa = len(hit_rates.columns.values)//n_dlh

    total_hit_rate = hit_rates.sum(axis = 1) # hit rate across entire detector
    total_hit_sent = hits_sent.sum(axis = 1) # hits sent by the DLH to the trigger?

    #? code assumes APA wires are in ascending order, find another way to group DLHs?
    hit_rate_apa = pd.DataFrame({f"APA {i}" : np.sum(hit_rates.values[:, i * n_dlh:(i+1)*n_dlh], axis=1) for i in range(n_apa)})

    with plotting.PlotBook(out + "tp_plots") as book:
        plotting.plot(plotting.relative_time(total_hit_rate), total_hit_rate.values, "np04 hits produced", "Time (s)", "TP rate")
        plotting.plot(plotting.relative_time(total_hit_sent), total_hit_sent.values, "np04 hits sent", "Time (s)", "TP rate", newFigure = False, autofmt = "Hz")
        
        plotting.hline(expected_hit_rate * n_ch * n_apa, "expected hit rate", "red", "--", "Hz")
        plotting.hline(acceptance_hit_rate * n_ch * n_apa, "acceptence hit rate", "k", "--", "Hz")
        plotting.plt.legend()
        book.save()

        plotting.plt.figure()
        for c in hit_rate_apa:
            plotting.plot(plotting.relative_time(hit_rate_apa[c]), hit_rate_apa[c].values, c, "Time (s)", "TP rate", newFigure = False, autofmt = "Hz")
        plotting.hline(expected_hit_rate * n_ch, "expected hit rate per APA", "red", "--", "Hz")
        plotting.hline(acceptance_hit_rate * n_ch, "acceptence hit rate per APA", "k", "--", "Hz")
        plotting.plt.legend()
        book.save()

        plotting.plot(plotting.relative_time(tp_writer_info), tp_writer_info[["TP Received", "TP written"]], ["received", "written"], "Time (s)", "TP rate", autofmt = "Hz")
        plotting.plt.title("TPWriter receieve/write rates")
        plotting.hline(expected_hit_rate * n_ch * n_apa, "expected hit rate", "red", "--", "Hz")
        plotting.hline(acceptance_hit_rate * n_ch * n_apa, "acceptence hit rate", "k", "--", "Hz")
        plotting.plt.legend()
        book.save()

        plotting.plot(plotting.relative_time(tp_writer_info), tp_size * tp_writer_info[["TP Received", "TP written"]], ["received", "written"], "Time (s)", "Rate", autofmt = "b/s")
        plotting.plt.title("TPWriter receieve/write rates")
        plotting.hline(expected_hit_rate * n_ch * n_apa * tp_size, "expected hit rate", "red", "--", "b/s")
        plotting.hline(acceptance_hit_rate * n_ch * n_apa * tp_size, "acceptence hit rate", "k", "--", "b/s")
        plotting.plt.legend()
        book.save()

        plotting.bar(total_tp_drop_rates.index, total_tp_drop_rates.values, "", "Number of TPs", "TPs dropped", bar_label = True)
        plotting.plt.ylim(0)
        book.save()

        plotting.plot(plotting.relative_time(tph_request_rates), tph_request_rates.values, tph_request_rates.columns, "Time (s)", "Request Rates", autofmt = "Hz")
        book.save()

        request_rate_percent = tph_request_rates.sum(axis=0)
        request_rate_percent = request_rate_percent.div(request_rate_percent["Total "], axis = 0)
        request_rate_percent.pop("Total ")
        plotting.bar(request_rate_percent.index, request_rate_percent, "Requst type", "Requests (%)", "Total number of requests", bar_label = True)
        book.save()
    return


def process_frontend_info(data : dict[pd.DataFrame], out : str):
    """ Process frontend readout information and make plots.

    Args:
        data (dict[pd.DataFrame]): node exporter data.
        out (str): output file diretory.
    """
    rx_throughput = list(utils.search_dict(data, "Throughput").values())[0] # bytes recevied from each queue in a readout application
    UDPQueue = namedtuple("UDPQueue", ["application", "queue"])
    dict_cols = {c : UDPQueue(**ast.literal_eval(c)) for c in rx_throughput.columns}
    rx_throughput = rx_throughput.rename(columns = dict_cols)


    adc_size = 14 # bits. Size for single ADC value
    adc_tpc_stream_rate = 1.953125E6 # Hz. ADC sampling rate for TPC for FD1-HD.

    adc_data_stream_rate_per_ch = adc_size * adc_tpc_stream_rate / 8 # B/s
    ch_per_queue = 256 # is this hardcoded or configurable in the DAQ?

    max_rate_per_stream = ch_per_queue * adc_data_stream_rate_per_ch # B/s

    unique_applications = np.unique([c.application for c in rx_throughput.columns])
    unique_queue_num = np.unique([c.queue for c in rx_throughput.columns])

    n_queues_per_app = len(unique_queue_num)
    n_applications = len(unique_applications)

    rx_throughput_apps = {}
    for app in unique_applications:
        app_queues = sum([rx_throughput[c] for c in rx_throughput.columns if c.application == app])
        rx_throughput_apps[app] = app_queues

    rx_throughput_apps = pd.DataFrame(rx_throughput_apps)

    rx_errors = utils.search_dict(data, "(?=.*RX)(?=.*Error)(?!.*Queue)")

    rx_dropped_frames = utils.search_dict(data, "RX Dropped Frames")

    total_errors_dlh = utils.search_dict(data, "Total errors")

    with plotting.PlotBook(out + "fe_plots") as book:
        plotting.plot(plotting.relative_time(rx_throughput_apps), rx_throughput_apps, rx_throughput_apps.columns, "Time (s)", "RX throughput", autofmt = "B/s")
        plotting.hline(max_rate_per_stream * n_queues_per_app, "Acceptance data input", autofmt = "B/s", linestyle = "--")
        plotting.plt.legend()
        book.save()

        plotting.plot(plotting.relative_time(rx_throughput), rx_throughput, None, "Time (s)", "RX throughput", autofmt = "B/s")
        plotting.hline(max_rate_per_stream, "Acceptance data input", autofmt = "B/s", linestyle = "--")
        plotting.plt.legend()
        book.save()

        total_errors = {k : v.sum(axis=0) for k,v in rx_errors.items()}
        label =  [f"APA {i}" for i, _ in enumerate(list(total_errors.values())[0].index)]
        for k, v in total_errors.items():
            plotting.bar(label, v.values, None, "Counts", k, bar_label = True)
            plotting.plt.ylim(0)
            book.save()

        total_dropped_frames = {f"APA {i}" : v.sum().sum() for i, v in enumerate(rx_dropped_frames.values())}
        plotting.bar(list(total_dropped_frames.keys()), list(total_dropped_frames.values()), None, "Counts", "RX Dropped Frames", bar_label = True)
        plotting.plt.ylim(0)
        book.save()

        total_errors_dlh = {f"APA {i}" : v.sum().sum() for i, v in enumerate(total_errors_dlh.values())}
        plotting.bar(list(total_errors_dlh.keys()), list(total_errors_dlh.values()), None, "Counts", "Errors from DLH", bar_label = True)
        plotting.plt.ylim(0)
        book.save()
    return

def analyse_data(test_args : dict):
    plotting.set_plot_style()

    pinning_file = shell.search_data_file("cpupin-all-running", test_args["data_path"])
    if len(pinning_file) == 0:
        pinning_file = None
    else:
        pinning_file = files.load_json(pinning_file[0])

    pinning_file = parse_pinning_file(pinning_file, test_args["host"])

    data_files = shell.search_data_file("hdf5", test_args["data_path"])

    ne_data = files.read_hdf5(search_file(data_files, "node-exporter"))
    tp_data = files.read_hdf5(search_file(data_files, "trigger_primitives"))
    fe_data = files.read_hdf5(search_file(data_files, "frontend_ethernet"))

    out = test_args["plot_path"] + "analysis/"
    os.makedirs(out, exist_ok = True)

    # ru = search_file(data_files, "A_CvwTCWk")
    # data = files.read_hdf5(ru)

    process_disk_info(ne_data, out)
    process_cpu_info(ne_data, out, pinning_file = pinning_file)
    process_memory_info(ne_data, out)
    process_network_info(ne_data, out)

    process_tp_info(tp_data, out)
    process_frontend_info(fe_data, out)
    return

def main(args : argparse.Namespace):
    test_args = files.load_json(args.file)
    analyse_data(test_args)
    return


if __name__ == "__main__":
    args = utils.ApplicationArguments("Analyse performance metrics.").create()
    main(args)