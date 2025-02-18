#!/usr/bin/env python
"""
Created on: 17/02/2025 12:58

Authors: Shyam Bhuller (University of Oxford)

Description: Basic plot of metrics from hdf5 files.
"""
import argparse
import os

import files, plotting, shell, utils, times

import pandas as pd

from rich import print


class plotter(plotting.PlotEngine):
    """ Class for handling resource utilization plotting.
        Authors: Shyam Bhuller (University of Oxford)
    """
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
            plotting.plot(times.relative_time(df), df[c].astype(float), c if make_labels else None, tlabel, metric, False)
        plotting.plt.ylim(0)

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
    
    dashboard_config = files.load_json(f"{os.environ['PERFORMANCE_TEST_PATH']}/config/dashboard_info.json")

    hdf_files = {}
    for n in dashboard_config["dashboard_uid"] + ["uprof", "node-exporter"]:
        hdf_files[n] = search_hdf5(n, args["data_path"])

    for f in hdf_files:
        keys = []
        values = {}
        data = files.read_hdf5(hdf_files[f])
        for k in data:
            if data[k].empty: continue
            keys.append(k)
            if type(data[k]) == pd.Series:
                values[k] = data[k].to_frame()
            else:
                values[k] = data[k]
        plt = plotter(keys, values)

        if display is True:
            plt.plot_display()
        else:
            plt.plot_book(out_dir + f)

    return


def main(args : argparse.Namespace):
    test_args = files.load_json(args.file)
    plot(test_args)
    return


if __name__ == "__main__":
    args = utils.ApplicationArguments("Create plots for resource utilization metrics.").create()
    main(args)