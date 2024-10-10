#!/usr/bin/env python
import pathlib
import argparse
import warnings

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from basic_functions import read_hdf5, load_json

from rich import print

class PlotBook:
    def __init__(self, name : str, open : bool = True) -> None:
        self.name = name
        if ".pdf" not in self.name: self.name += ".pdf" 
        if open: self.open()
        self.is_open = True

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()
        self.is_open = False

    def Save(self):
        if hasattr(self, "pdf"):
            try:
                self.pdf.savefig(bbox_inches='tight')
            except AttributeError:
                pass

    def open(self):
        if not hasattr(self, "pdf"):
            self.pdf = PdfPages(self.name)
            print(f"pdf {self.name} has been opened")
        else:
            warnings.warn("pdf has already been opened")
        return

    def close(self):
        if hasattr(self, "pdf"):
            self.pdf.close()
            delattr(self, "pdf")
            print(f"pdf {self.name} has been closed")
        else:
            warnings.warn("pdf has not been opened.")
        return

    @classmethod
    @property
    def null(cls):
        return cls(name = "", open = False)


def main(args : argparse.Namespace):
    test_args = load_json(args.file)

    for d, f in zip(test_args["dashboard_uid"], test_args["grafana_data_files"]):
        data = read_hdf5(f)
        with PlotBook(f"{d}_plots.pdf", True) as book:
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