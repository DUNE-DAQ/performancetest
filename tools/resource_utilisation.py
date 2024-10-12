#!/usr/bin/env python
import argparse
import pathlib

import files
import plotting

from rich import print


def main(args : argparse.Namespace):
    plotting.set_plot_style()
    test_args = files.load_json(args.file)

    pcm_data = "A_CvwTCWk"

    for file in test_args["grafana_data_files"]:
        if pcm_data in file:
            data = files.read_hdf5(file)
            break

    print(data.keys())

    memory_info = []
    for k in data.keys():
        if "Memory Bandwidth (MByte/sec)" in k:
            memory_info.append(k)

    total_cpu_util =  "Core C-state residency" #? is this true? don't think so...

    cache_ratio = {}
    for i in [2, 3]:
        miss = f"L{i} Cache Misses"
        hits = f"L{i} Cache Hits"
        total = data[miss] + data[hits]
        cache_ratio[f"{miss} (%)"] = data[miss] / total
        cache_ratio[f"{hits} (%)"] = data[hits] /  total

    cache_info = []
    for k in data.keys():
        if ("Cache" in k) and ("(Million)" in k):
            cache_info.append(k)

    tlabel = "Relative time (s)"

    with plotting.PlotBook("resourse_utilisation.pdf") as book:
        for i in (memory_info + cache_info):
            plotting.plt.figure()
            df = data[i]
            for c in df.columns:
                plotting.plot(plotting.relative_time(df), df[c].astype(float), c, tlabel, i, False)
            book.save()
            plotting.plt.clf()
            

        for i in cache_ratio:
            plotting.plt.figure()
            df = cache_ratio[i]
            for c in df.columns:
                plotting.plot(plotting.relative_time(df), df[c].astype(float), c, tlabel, i, False)
            book.save()
            plotting.plt.clf()

    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Create plots for resource utilisation metrics.")

    file_arg = parser.add_argument("-f", "--file", type = pathlib.Path, help = "json file which contains the details of the test.", required = True)

    args = parser.parse_args()

    file_arg.required = True
    gen_args = parser.parse_args()

    args = parser.parse_args()

    if args.file.suffix != ".json":
        raise Exception("not a json file")

    print(args)
    main(args)