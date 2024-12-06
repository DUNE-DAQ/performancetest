#!/usr/bin/env python
import argparse

import files, plotting, shell, utils, times

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

        show_label = len(df.columns) <= 20

        for c in df.columns:
            plotting.plot(times.relative_time(df), df[c].astype(float), c if show_label else None, tlabel, metric + f" {get_units(metric)}", False)
        plotting.plt.ylim(0) # data should never be < 0
        return


def tp_metrics(args : dict, display : bool = False):
    plotting.set_plot_style()

    for file in shell.search_data_file("trigger_primitive", args["data_path"]):
        if "hdf5" in file.suffix: break

    data = files.read_hdf5(file)

    metrics = list(data.keys())
    if 'Highest TP rates per channel' in metrics:
        metrics.remove('Highest TP rates per channel') # this dataframe is impractical for a plot

    plotter = tp_plotter(metrics, data)

    if display is True:
        plotter.plot_display()
    else:
        out_dir = utils.make_plot_dir(args)
        plotter.plot_book(out_dir + "trigger_primitive.pdf")


def main(args : argparse.Namespace):
    test_args = files.load_json(args.file)
    tp_metrics(test_args)
    return


if __name__ == "__main__":
    args = utils.ApplicationArguments("Create basic plots for trigger primitive generation metrics.").create()
    main(args)