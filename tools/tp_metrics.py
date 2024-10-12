#!/usr/bin/env python
import argparse
import pathlib

import files
import plotting

from rich import print


def get_units(name : str):
    if "rate" in name.lower():
        return "(Hz)"
    else:
        return ""


def main(args : argparse.Namespace):
    plotting.set_plot_style()
    test_args = files.load_json(args.file)

    tp_data = "trigger_primitive"

    for file in test_args["grafana_data_files"]:
        if tp_data in file:
            data = files.read_hdf5(file)
            break

    tlabel = "Relative time (s)"

    metrics = list(data.keys())
    metrics.remove('Highest TP rates per channel') # this dataframe is impractical for a plot

    with plotting.PlotBook("trigger_primitive.pdf") as book:
        for i in metrics:
            df = data[i]
            if df.empty:
                print(f"warning : dataframe for {i} is empty! Skipping.")
                continue

            plotting.plt.figure(figsize=(8, 6))
            for c in df.columns:
                plotting.plot(plotting.relative_time(df), df[c].astype(float), c, tlabel, i + f" {get_units(i)}", False)
            plotting.plt.ylim(0) # data should never be < 0
            
            if len(df.columns) > 10:
                plotting.plt.legend(ncols = 1 + (len(df.columns)**0.5 / 2), fontsize = "x-small", bbox_to_anchor=(1.10, 1))
                plotting.plt.tight_layout()
                plotting.plt.gcf().set_size_inches(18, 6)

            book.save()
            plotting.plt.clf()

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