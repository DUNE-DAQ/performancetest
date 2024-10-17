#!/usr/bin/env python
import argparse
import pathlib

import files
import plotting
import utils

from rich import print


def get_units(name : str):
    if "rate" in name.lower():
        return "(Hz)"
    else:
        return ""


class tp_plotter(plotting.PlotEngine):
    def plot_metric(self, metric: str):
        tlabel = "Relative time (s)"
        df = self.data[metric]

        for c in df.columns:
            plotting.plot(plotting.relative_time(df), df[c].astype(float), c, tlabel, metric + f" {get_units(metric)}", False)
        plotting.plt.ylim(0) # data should never be < 0
        
        if len(df.columns) > 10:
            plotting.plt.legend(ncols = 1 + (len(df.columns)**0.5 / 2), fontsize = "x-small", bbox_to_anchor=(1.10, 1))
            plotting.plt.tight_layout()
            plotting.plt.gcf().set_size_inches(18, 6)

        return


def tp_metrics(args : dict, display : bool = False):
    plotting.set_plot_style()

    for file in utils.search_data_file("trigger_primitive", args["data_path"]):
        if "hdf5" in file.suffix: break

    data = files.read_hdf5(file)

    tlabel = "Relative time (s)"

    metrics = list(data.keys())
    metrics.remove('Highest TP rates per channel') # this dataframe is impractical for a plot

    plotter = tp_plotter(metrics, data)

    if display is True:
        plotter.plot_display()
    else:
        plotter.plot_book(args["data_path"] + f"trigger_primitive.pdf")


def main(args : argparse.Namespace):
    test_args = files.load_json(args.file)
    tp_metrics(test_args)
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Create basic plots for trigger primitive generation metrics.")

    file_arg = parser.add_argument("-f", "--file", type = pathlib.Path, help = "json file which contains the details of the test.", required = True)

    args = parser.parse_args()

    file_arg.required = True
    gen_args = parser.parse_args()

    args = parser.parse_args()

    if args.file.suffix != ".json":
        raise Exception("not a json file")

    print(args)
    main(args)