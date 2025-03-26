#!/usr/bin/env python
"""
Created on: 17/02/2025 12:58

Authors: Shyam Bhuller (University of Oxford)

Description: Basic plot of metrics from hdf5 files.
"""
import argparse
import multiprocessing
import os

import files, plotting, shell, utils, times

import pandas as pd

from rich import print


class plotter(plotting.PlotEngine):
    """ Class for handling resource utilization plotting.
        Authors: Shyam Bhuller (University of Oxford)
    """
    def __init__(self, metrics, data, test_args):
        self.test_args = test_args
        super().__init__(metrics, data)


    def plot_metric(self, metric: str):
        tlabel = "Relative time (s)"
 
        df = self.data[metric]

        if "(Bps)" in metric:
            df = df / 1E9
            metric = metric.replace("Bps", "GB/s")

        if "(B)" in metric:
            df = df / 1E9
            metric = metric.replace("B", "GB")

        if "pps" in metric:
            metric = metric.replace("pps", "p/s")

        make_labels = (len(df.columns) < 20) and (len(df.columns) > 1)
        for c in df.columns:
            try:
                v = df[c].astype(float)
            except:
                v = df[c]
            plotting.plot(times.relative_time(df), v, c if make_labels else None, tlabel, metric, False)
            plotting.add_metadata(self.test_args, int(df.index[0]))
        plotting.plt.ylim(0, 1.1 * max(plotting.plt.gca().get_ylim()))

        if "(%)" in metric:
            plotting.plt.ylim(0, 100)
        return


def search_hdf5(search_term : str, path : str) -> str | None:
    """ Search for hdf5 files with a specific term in a directory.
        Authors: Shyam Bhuller (University of Oxford)

    Args:
        search_term (str): Term to search for.
        path (str): Directory.

    Returns:
        str | None: hdf5 file path if found.
    """
    for file in shell.search_data_file(search_term, path):
        if "hdf5" in file.suffix: return file
    return


def plot(args : argparse.Namespace, display : bool = False):
    plotting.set_plot_style()
    out_dir = utils.make_plot_dir(args)

    dashboard_config = files.read_json(f"{os.environ['PERFORMANCE_TEST_PATH']}/config/dashboard_info.json")

    hdf_files = {}
    for n in dashboard_config["dashboard_uid"] + ["uprof-pcm", "uprof-power", "node-exporter"]:
        hdf_files[n] = search_hdf5(n, args["data_path"])


    blacklist = ["Highest TP rates per channel"] # blacklist data that should not be plotted e.g. takes too long

    for f in hdf_files:
        keys = []
        values = {}
        if hdf_files[f] is None: continue
        data = files.read_hdf5(hdf_files[f])
        for k in data:
            if data[k].empty: continue

            if k in blacklist:
                continue

            keys.append(k)
            if type(data[k]) == pd.Series:
                values[k] = data[k].to_frame()
            else:
                values[k] = data[k]
        plt = plotter(keys, values, args)

        procs = []
        q = multiprocessing.Queue()
        if display is False:
            for i, m in enumerate(plt.metrics):
                proc = multiprocessing.Process(target = plt.plot_book_fig, args = [i, m, q])
                procs.append(proc)
                proc.start()

            output = [None]*len(procs)
            for proc in procs:
                o = q.get()
                output[o[0]] = o[1]

            with plotting.PlotBook(out_dir + f, True) as book:
                for o in output:
                    book.save(o)
        else:
            plt.plot_display()
    return


def main(args : argparse.Namespace):
    test_args = files.read_config(args.file)
    plot(test_args)
    return


if __name__ == "__main__":
    args = utils.ApplicationArguments("Create plots for resource utilization metrics.").create()
    main(args)