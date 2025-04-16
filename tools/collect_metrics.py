#!/usr/bin/env python
"""
Created on: 13/10/2024 00:06

Authors: Shyam Bhuller (University of Oxford), Matthew Man (University of Toronto), Danaisis Vargas Oliva (University of Toronto)

Description: Collect metrics from the grafana dashboards.
"""
import os
import argparse

import files
import harvester
import times
import utils

from rich import print


def create_dashboard_info(args : dict) -> dict:
    """ Load information about which dashboards to query and which grafana url to use.

    Args:
        args (dict): arguments for the test.

    Returns:
        dict: Grafana url, dashboard uid, and session names for each dashboard.
    """
    dashboard_config = files.read_json(f"{os.environ['PERFORMANCE_TEST_PATH']}/config/dashboard_info.json")

    for i, uid in enumerate(dashboard_config["dashboard_uid"]):
        if uid == "A_CvwTCWk" : continue # pcm dashboard is not tied to a specific dunedaq version
        dashboard_config["dashboard_uid"][i] = f"{args['dunedaq_version'].replace('.', '_')}-{uid}"

    for i, uid in enumerate(dashboard_config["session"]):
        if uid is None:
            dashboard_config["session"][i] = args["session"]

    return dashboard_config


def collect_metrics(args : argparse.Namespace | dict) -> None | dict:
    if type(args) == argparse.Namespace:
        test_args = files.read_config(args.file)
        new_args = files.read_config(args.file) # reopen config file to add the data file paths
    else:
        test_args = args
        new_args = None

    name = utils.create_filename(test_args)
    out_dir = str(utils.test_path(test_args)) + "/data/"
    os.makedirs(out_dir, exist_ok = True)

    dashboard_info = create_dashboard_info(test_args)

    # get datsources from which the data is harvested
    datasources = harvester.extract_datasources(dashboard_info["grafana_url"], test_args["dunedaq_version"])

    # get run time (or time range from arguments)
    time_range = times.parse_time_range(times.time_range(*test_args["time_range"]))
    if type(time_range.start) == int:  
        time_range = harvester.get_run_time(dashboard_info, test_args["run_number"], test_args["session"], test_args["dunedaq_version"], datasources)
    else:
        time_range = time_range

    # setup harvester functions
    harvesters = harvester.setup_daq_harvesters(dashboard_info, test_args["run_number"], test_args["host"], time_range, name, out_dir, datasources)

    harvesters.extend(harvester.setup_node_exporter_harvesters(test_args["host"], time_range, name, out_dir, datasources))

    # if uprof csv was provided
    if ("uprof_file" in test_args) and (len(test_args["uprof_file"]) > 0):
        harvesters.extend(harvester.setup_uprof_harvesters(test_args["uprof_file"], time_range, name, out_dir))

    harvester.extract_data(harvesters) # extract the data in parallel

    if type(args) == argparse.Namespace:
        new_args["data_path"] = out_dir
        files.write_json(args.file, new_args)
        print(f"{args.file} updated to include data path.")
        return
    else:
        test_args["data_path"] = out_dir
        return test_args


def main(args : argparse.Namespace):
    collect_metrics(args)


if __name__ == "__main__":
    args = utils.ApplicationArguments("Collect results from performance tests.").create()
    main(args)