#!/usr/bin/env python
"""
Created on: 12/12/2024 11:09

Author: Shyam Bhuller (University of Oxford)

Description: Plot data collected from the frontend ethernet dashboard.
"""
import argparse
import os

import files, plotting, shell, utils, times

import pandas as pd

from rich import print


def get_units(x : str) -> str:
    """ From the metric name, try to infer the units of measurement.

    Args:
        x (str): metric name.

    Returns:
        str: units of measurement.
    """
    label = x.lower()
    if "packet" in label:
        return "(p/s)"
    elif "error" in label or "rate" in label:
        return "(c/s)"
    elif label == "rx good bytes":
        return "(Gib/s)"
    else:
        return ""


class feplotter(plotting.PlotEngine):
    """ Class for handling resource utilization plotting.
    """
    def plot_metric(self, metric : str):
        tlabel = "Relative time (s)"

        if metric.lower() == "rx good bytes":
            scale = 1E9
        else:
            scale = 1
        df = self.data[metric]
        if df.empty:
            print(f"warning : dataframe for {metric} is empty! Skipping.")
            return

        for c in df.columns:
            plotting.plot(times.relative_time(df), df[c]/scale, c if len(df.columns) <= 20 else None, tlabel, metric + f" {get_units(metric)}", False)
        plotting.plt.ylim(0) # data should never be < 0
        if len(df.columns) <= 20:
            plotting.plt.legend(ncols = 1, fontsize = "small")
        
        plotting.plt.tight_layout()
        return


def frontend_ethernet(args : dict, display : bool = False):
    """ Main function that plots metrics from the frontend ethernet dashboard.

    Args:
        args (dict): performance test configuration.
        display (bool, optional): display the plot in an external window in grid form. Used for the notebook service. Defaults to False.
    """
    plotting.set_plot_style()

    for file in shell.search_data_file("frontend_ethernet", args["data_path"]):
        if "hdf5" in file.suffix: break

    data = files.read_hdf5(file)

    metrics = []
    for k in data:
        if "RX" in k:
            metrics.append(k)

    plotter = feplotter(metrics, data)

    if display is True:
        plotter.plot_display()
    else:
        out_dir = utils.make_plot_dir(args)
        plotter.plot_book(out_dir + "frontend_ethernet.pdf")


def main(args : argparse.Namespace):
    test_args = files.read_config(args.file)
    frontend_ethernet(test_args)
    return


if __name__ == "__main__":
    args = utils.ApplicationArguments("Create plots for the frontend ethernet metrics.").create()
    main(args)