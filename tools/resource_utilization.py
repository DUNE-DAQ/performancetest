#!/usr/bin/env python
import argparse

import files
import plotting
import utils

import pandas as pd

from rich import print


class ru_plotter(plotting.PlotEngine):
    def plot_metric(self, metric: str):
        tlabel = "Relative time (s)"
 
        df = self.data[metric]
        for c in df.columns:
            plotting.plot(plotting.relative_time(df), df[c].astype(float), c, tlabel, metric, False)

        return


def resource_utilization(args : dict, display : bool = False):
    plotting.set_plot_style()

    data = files.read_hdf5(utils.search_data_file("A_CvwTCWk", args["data_path"])[0])

    memory_info = []
    for k in data.keys():
        if "Memory Bandwidth (MByte/sec)" in k:
            memory_info.append(k)

    total_cpu_util =  "Core C-state residency" #? is this true? don't think so...

    cache_ratio = {}
    for i in [2, 3]:
        miss = f"L{i} Cache Misses"
        hits = f"L{i} Cache Hits"
        if (miss not in data) or (hits not in data):
            continue
        else:
            total = data[miss] + data[hits]
            cache_ratio[f"{miss} (%)"] = data[miss] / total
            cache_ratio[f"{hits} (%)"] = data[hits] /  total

    cache_info = []
    for k in data.keys():
        if ("Cache" in k) and ("(Million)" in k):
            cache_info.append(k)

    plotter = ru_plotter(memory_info + cache_info, data | cache_ratio)

    if display is True:
        plotter.plot_display()
    else:
        plotter.plot_book(args["out_path"] + f"resourse_utilization.pdf")

    return


def main(args : argparse.Namespace):
    test_args = files.load_json(args.file)
    resource_utilization(test_args)
    return


if __name__ == "__main__":
    args = utils.create_app_args("Create plots for resource utilization metrics.")
    main(args)