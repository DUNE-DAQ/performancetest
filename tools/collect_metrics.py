#!/usr/bin/env python
"""
Created on: 13/10/2024 00:06

Author: Shyam Bhuller

Description: Collect metrics from the grafana dashboards.
"""
import os
import argparse
import pathlib

from warnings import warn

from basic_functions import reformat_cpu_util #! this should be deprecated as core utilisation need to be included in the dashboards
import files
import harvester
import utils

from rich import print


def create_dashboard_info(args : argparse.Namespace) -> dict:
    """ Load information about which dashboards to query and which grafana url to use.

    Args:
        args (argparse.Namespace): arguments for the test.

    Returns:
        dict: Grafana url, dashboard uid, and session names for each dashboard.
    """
    dashboard_config = files.load_json(f"{os.environ['PERFORMANCE_TEST_PATH']}/config/dashboard_info.json")

    for i, uid in enumerate(dashboard_config["dashboard_uid"]):
        if uid == "A_CvwTCWk" : continue # pcm dashboard is not tied to a specific dunedaq version
        dashboard_config["dashboard_uid"][i] = f"{args['dunedaq_version'].replace('.', '_')}-{uid}"

    for i, uid in enumerate(dashboard_config["session"]):
        if uid is None:
            dashboard_config["session"][i] = args["session"]

    return dashboard_config


def test_path(test_args : dict) -> pathlib.Path:
    path = f"perftest-run{test_args['run_number']}-{test_args['dunedaq_version'].replace('.', '_')}-{test_args['host'].replace('-', '')}-{test_args['test_name']}"

    path = pathlib.Path(test_args["out_path"] + "/" + path + "/")
    os.makedirs(path, exist_ok = True)
    print(f"created output directory: {path}")
    return path


def collect_metrics(args : argparse.Namespace | dict) -> None | dict:
    if type(args) == argparse.Namespace:
        test_args = files.load_json(args.file)
        new_args = files.load_json(args.file) # reopen config file to add the data file paths
    else:
        test_args = args
        new_args = None

    dashboard_info = create_dashboard_info(test_args)

    core_utilisation_files = []

    if "core_utilisation_files" not in test_args:
        warn("no core utilisation files were specified!!! Skipping.")

    name = utils.create_filename(test_args)
    out_dir = test_path(test_args)

    if "core_utilisation_files" in test_args:
        cu_file = pathlib.Path(f"core_utilisation-{name}.csv")
        # format core util files
        cpu_df = reformat_cpu_util(test_args["core_utilisation_files"])
        cpu_df.to_csv(cu_file.name)
        core_utilisation_files.append(cu_file.resolve().as_posix())

    # extract grafana data
    harvester.extract_grafana_data(dashboard_info, test_args["run_number"], test_args["host"], test_args["session"], output_file = name, out_dir = out_dir)

    if type(args) == argparse.Namespace:
        new_args["data_path"] = str(out_dir) + "/"

        files.save_json(args.file, new_args)
        print(f"{args.file} updated to include data path.")
        return
    else:
        test_args["data_path"] = str(out_dir) + "/"
        return test_args


def main(args : argparse.Namespace):
    collect_metrics(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Collect results from performance tests.")

    file_arg = parser.add_argument("-f", "--file", type = pathlib.Path, help = "json file which contains the details of the test.")

    args = parser.parse_args()

    if args.file.suffix != ".json":
        raise Exception("not a json file")

    print(args)
    main(args)