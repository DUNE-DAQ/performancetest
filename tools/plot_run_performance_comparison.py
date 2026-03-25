#!/usr/bin/env python
"""
Created on: 25/03/2026 17:46

Author: Pawel Plesniak

Description: Generate plots that compare the performance between two runs.
Primary use case - generate the performance between SSH and K8s process orchestration.
"""
import os
import multiprocessing
import pandas as pd
import click
import utils
import files
import plotting

def plot_comparison(first_run_file_name: str, second_run_file_name: str):
    plotting.set_plot_style()
    out_dir = utils.make_plot_dir(args) + "comparison_plots/"
    os.makedirs(out_dir, exist_ok=True)

    # 1. Fetch files - assuming args contains two specific paths or identifiers
    # If the search returns a dict, we extract the two we care about
    hdf_files = utils.search_hdf5_data(args["data_path"], args["dunedaq_version"])
    
    if len(hdf_files) < 2:
        print("Error: Comparison requires at least two HDF5 files.")
        return

    # For simplicity, let's take the first two found, or use specific args keys
    file_keys = list(hdf_files.keys())
    f1_name, f2_name = file_keys[0], file_keys[1]
    
    # 2. Load Data
    data1 = files.read_hdf5(hdf_files[f1_name])
    data2 = files.read_hdf5(hdf_files[f2_name])

    blacklist = ["Highest TP rates per channel", "Message Reporting"]
    
    # 3. Align Metrics (Intersection of keys)
    common_keys = [k for k in data1.keys() if k in data2.keys() and k not in blacklist]
    
    comparison_values = {}
    for k in common_keys:
        df1 = data1[k].to_frame() if isinstance(data1[k], pd.Series) else data1[k]
        df2 = data2[k].to_frame() if isinstance(data2[k], pd.Series) else data2[k]
        
        if df1.empty or df2.empty:
            continue
            
        # We store them as a tuple or a combined DF depending on what your 'plotter' expects
        # Here we assume your plotter is updated to handle multiple data sources
        comparison_values[k] = (df1, df2)

    # 4. Initialize Plotter
    # Note: You may need to update your 'plotter' class to accept a list of values 
    # and labels (e.g., f1_name vs f2_name)
    plt = plotter(common_keys, comparison_values, args, labels=[f1_name, f2_name])

    if display:
        plt.plot_display()
    else:
        # 5. Multiprocessing (Matching your repo's pattern)
        cpu_count = max(1, multiprocessing.cpu_count() - 1)
        q = multiprocessing.Queue()
        
        procs = []
        for i, m in enumerate(plt.metrics):
            # Assumes plot_book_fig is designed to handle the comparison data internally
            proc = multiprocessing.Process(target=plt.plot_book_fig, args=[i, m, q])
            procs.append(proc)

        output = [None] * len(procs)
        for i in range(0, len(procs), cpu_count):
            batch = procs[i : i + cpu_count]
            for p in batch: p.start()
            for p in batch:
                res = q.get()
                output[res[0]] = res[1]
            for p in batch: p.join()

        # 6. Save to a single PlotBook named after the comparison
        comparison_filename = f"cmp_{f1_name}_vs_{f2_name}"
        with plotting.PlotBook(out_dir + comparison_filename, True) as book:
            for o in output:
                if o is not None:
                    book.save(o)


@click.command()
@click.argument(
    "first_run_file_name",
    type=str,
    required=True,
)
@click.argument(
    "second_run_file_name",
    type=str,
    required=True,
)
@click.option(
    "--first_file_time_start_offset",
    type=float,
    default=0.0,
    help="Number of seconds to skip from the start of the first file.",
)
@click.option(
    "--second_file_time_start_offset",
    type=float,
    default=0.0,
    help="Number of seconds to skip from the start of the second file.",
)
@click.option(
    "--first_file_time_end_cut",
    type=float,
    default=0.0,
    help="Number of seconds to cut from the end of the first file.",
)
@click.option(
    "--second_file_time_end_cut",
    type=float,
    default=0.0,
    help="Number of seconds to cut from the end of the second file.",
)
@click.option(
    "--make_same_time_range",
    type=bool,
    default=False,
    help="Only plot the differnce between the two files for the time range that is common to both files (after applying the offsets and cuts).",
)
def main(first_run_file_name: str, second_run_file_name: str, first_file_time_start_offset: float, second_file_time_start_offset: float, first_file_time_end_cut: float, second_file_time_end_cut: float, make_same_time_range: bool):
    plot_comparison(first_run_file_name, second_run_file_name)
    return


if __name__ == "__main__":
    main()