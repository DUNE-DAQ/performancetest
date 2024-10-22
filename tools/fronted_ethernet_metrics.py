#!/usr/bin/env python
import argparse
import pathlib

import files
import plotting
import utils

import pandas as pd

from rich import print


def get_units(x : str):
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
            plotting.plot(plotting.relative_time(df), df[c]/scale, c, tlabel, metric + f" {get_units(metric)}", False)
        plotting.plt.ylim(0) # data should never be < 0
        plotting.plt.legend(ncols = 1 + (len(df.columns)**0.5 / 2), fontsize = "small")
        plotting.plt.tight_layout()
        return


def frontend_ethernet(args : dict, display : bool = False):
    plotting.set_plot_style()

    data = files.read_hdf5(utils.search_data_file("frontend_ethernet", args["data_path"])[0])

    metrics = []
    for k in data:
        if "RX" in k:
            metrics.append(k)

    plotter = feplotter(metrics, data)

    if display is True:
        plotter.plot_display()
    else:
        plotter.plot_book(args["out_path"] + f"frontend_ethernet.pdf")


def main(args : argparse.Namespace):
    test_args = files.load_json(args.file)
    frontend_ethernet(test_args)
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Create plots for the frontend ethernet metrics.")

    file_arg = parser.add_argument("-f", "--file", type = pathlib.Path, help = "json file which contains the details of the test.", required = True)

    args = parser.parse_args()

    file_arg.required = True
    gen_args = parser.parse_args()

    args = parser.parse_args()

    if args.file.suffix != ".json":
        raise Exception("not a json file")

    print(args)
    main(args)