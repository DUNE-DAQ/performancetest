#!/usr/bin/env python
import pathlib
import argparse

from basic_functions import read_hdf5, load_json

from rich import print

import plotting

def main(args : argparse.Namespace):
    test_args = load_json(args.file)

    for d, f in zip(test_args["dashboard_uid"], test_args["grafana_data_files"]):
        data = read_hdf5(f)
        with plotting.PlotBook(f"{d}_plots.pdf", True) as book:
            try:
                for df in data:
                    print(df)
                    panel = data[df]

                    plt.figure()
                    for i, c in enumerate(panel.columns):
                        plt.plot(panel.index, panel[c], label = c)
                        if i > 10: break # temporary
                    plt.xlabel("Unix time (s)")
                    plt.ylabel(df)
                    plt.legend()
                    plt.tight_layout()
                    book.Save()
                    plt.clf()
            except:
                print(f"{df} could not be plotted")

    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Create basic plots for performance reports.")

    file_arg = parser.add_argument("-f", "--file", type = pathlib.Path, help = "json file which contains the details of the test.", required = True)

    args = parser.parse_args()

    file_arg.required = True
    gen_args = parser.parse_args()

    args = parser.parse_args()

    if args.file.suffix != ".json":
        raise Exception("not a json file")

    print(args)
    main(args)