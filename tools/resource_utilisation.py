#!/usr/bin/env python
import pathlib
import argparse

import pandas as pd

from basic_functions import read_hdf5, load_json

from rich import print

import plotting

def main(args : argparse.Namespace):
    test_args = load_json(args.file)

    pcm_data = "A_CvwTCWk"

    for file in test_args["grafana_data_files"]:
        if pcm_data in file:
            data = read_hdf5(file)
            break

    print(data.keys())

    memory_info = []
    for k in data.keys():
        if "Memory Bandwidth (MByte/sec)" in k:
            memory_info.append(k)

    total_cpu_util =  "Core C-state residency"

    tlabel = "Relative time (s)"

    with plotting.PlotBook("resourse_utilisation.pdf") as book:
        for i in memory_info:
            plotting.plt.figure()
            df = data[i]
            for c in df.columns:
                plotting.plot(plotting.relative_time(df), df[c].astype(float), c, tlabel, i, False)
            book.Save()
            plotting.plt.clf()

        plotting.plot(plotting.relative_time(data[total_cpu_util]), data[total_cpu_util]["C0"].astype(float), label= None, xlabel= tlabel, ylabel = total_cpu_util, book = book)

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