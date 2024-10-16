#!/usr/bin/env python
import argparse
import pathlib

import files
import plotting
import utils

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


def frontend_ethernet(args : dict):
    plotting.set_plot_style()

    data = files.read_hdf5(utils.search_data_file("frontend_ethernet", args["data_path"]))

    tlabel = "Relative time (s)"

    rx_metrics = []
    for k in data:
        if "RX" in k:
            rx_metrics.append(k)

    with plotting.PlotBook(args["data_path"] + "frontend_ethernet.pdf") as book:
        for i in rx_metrics:
            if i.lower() == "rx good bytes":
                scale = 1E9
            else:
                scale = 1
            df = data[i]
            if df.empty:
                print(f"warning : dataframe for {i} is empty! Skipping.")
                continue

            plotting.plt.figure(figsize=(8*1.2, 6*1.2))
            for c in df.columns:
                plotting.plot(plotting.relative_time(df), df[c]/scale, c, tlabel, i + f" {get_units(i)}", False)
            plotting.plt.ylim(0) # data should never be < 0
            plotting.plt.legend(ncols = 1 + (len(df.columns)**0.5 / 2), fontsize = "small")
            plotting.plt.tight_layout()
            book.save()
            plotting.plt.clf()
    return


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