#!/usr/bin/env python
"""
Created on: 15/01/2026 12:34

Author: Shyam Bhuller

Description: Harvester code for a single dashboard without parallel processing. Only process DAQ grafana dashbaords (not node exporter, or uprof data)
"""
import os
import argparse

import files
import harvester
import times
import utils

from collect_metrics import create_dashboard_info

from rich import print

def main(args : argparse.Namespace):
    if type(args) == argparse.Namespace:
        test_args = files.read_config(args.file)
    else:
        test_args = args

    name = utils.create_filename(test_args)
    out_dir = str(utils.test_path(test_args)) + "/data/"
    os.makedirs(out_dir, exist_ok = True)

    dashboard_info = create_dashboard_info(test_args)

    if args.uid != "node_exporter":
      dashboard_info["dashboard_uid"] = [f"{test_args['dunedaq_version'].replace('.', '_')}-{args.uid}"]
    dashboard_info["session"] = [test_args["session"]]

    # get datsources from which the data is harvested
    datasources = harvester.extract_datasources(dashboard_info["grafana_url"], test_args["dunedaq_version"])

    # get run time (or time range from arguments)

    # check if this a relative time range (integers) or a custom, aboslute time range (string, in ddmmyy)
    # then, if an absolute time range, pass this along in unix time, otherwise, pass the default time range (what is specified in the run)
    time_range, abs_time = times.parse_time_range(times.time_range(*test_args["time_range"]))
    if not abs_time:
        time_range = harvester.get_run_time(dashboard_info, test_args["run_number"], test_args["session"], test_args["dunedaq_version"], datasources)

    # setup harvester functions
    if args.uid == "node_exporter":
        harvesters = harvester.setup_node_exporter_harvesters(test_args["host"], time_range, name, out_dir, datasources)
    else:
        harvesters = harvester.setup_daq_harvesters(dashboard_info, test_args["dunedaq_version"], test_args["run_number"], test_args["host"], time_range, name, out_dir, datasources)

    print(f"{harvesters=}")
    # harvester.extract_data(harvesters) # extract the data in parallel
    harvester.run_harvester(harvesters[0][0], harvesters[0][1])


if __name__ == "__main__":
    parser = utils.ApplicationArguments("Collect results from performance tests.")
    parser.add_argument("-d", "--dashboard-uid", dest = "uid", type = str, help = "dashboard UID to harvest data from.", required = True)
    args = parser.create()
    main(args)