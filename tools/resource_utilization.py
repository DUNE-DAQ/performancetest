#!/usr/bin/env python
import argparse

import files, plotting, shell, utils, times

import pandas as pd

from rich import print


class ru_plotter(plotting.PlotEngine):
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

    Args:
        search_term (str): Term to search for.
        path (str): Directory.

    Returns:
        str | None: hdf5 file path if found.
    """
    for file in shell.search_data_file(search_term, path):
        if "hdf5" in file.suffix: return file
    return


def process_ru(ru_data : dict) -> tuple[list[str], dict[pd.DataFrame]]:
    """ Process resource utilisation metrics to calculate cache information.

    Args:
        ru_data (dict): Resource utilisation data.

    Returns:
        tuple[list[str], dict[pd.DataFrame]]: metric names and data
    """
    cache_ratio = {}
    for i in [2, 3]:
        miss = f"L{i} Cache Misses"
        hits = f"L{i} Cache Hits"
        if (miss not in ru_data) or (hits not in ru_data):
            continue
        else:
            total = ru_data[miss] + ru_data[hits]
            cache_ratio[f"{miss} (%)"] = ru_data[miss] / total
            cache_ratio[f"{hits} (%)"] = ru_data[hits] /  total

    cache_info = []
    for k in ru_data.keys():
        if ("Cache" in k) and ("(Million)" in k):
            cache_info.append(k)

    return cache_info, cache_ratio


def resource_utilization(args : dict, display : bool = False):
    plotting.set_plot_style()

    fp = {
        "ru" : search_hdf5("A_CvwTCWk", args["data_path"]),
        "ne" : search_hdf5("node-exporter", args["data_path"])
    }

    data = {}
    for k, v in fp.items():
        if v:
            data[k] = files.read_hdf5(v)

    keys = []
    values = {}

    if "ru" in data:
        memory_info = []
        for k in data["ru"].keys():
            if "Memory Bandwidth (MByte per sec)" in k:
                memory_info.append(k)

        cache_info, cache_ratio = process_ru(data["ru"])
        keys = keys + memory_info + cache_info
        values = values | data["ru"] | cache_ratio

    if "ne" in data:
        for k in data["ne"]:
            if ("(%)" in k) or ("Network" in k) or ("Softnet" in k) or ("Disk") in k:
                keys.append(k)
                values[k] = data["ne"][k]

    plotter = ru_plotter(keys, values)

    if display is True:
        plotter.plot_display()
    else:
        out_dir = utils.make_plot_dir(args)
        plotter.plot_book(out_dir + "resourse_utilization.pdf")

    return


def main(args : argparse.Namespace):
    test_args = files.load_json(args.file)
    resource_utilization(test_args)
    return


if __name__ == "__main__":
    args = utils.ApplicationArguments("Create plots for resource utilization metrics.").create()
    main(args)