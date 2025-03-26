#!/usr/bin/env python
"""
Created on: 13/10/2024 00:10

Author: Shyam Bhuller (University of Oxford)

Description: Create a performance report with one command.
"""
import argparse

import files
import utils
import shell

from collect_metrics import collect_metrics
from basic_plotter import plot
from performance_report import performance_report
from workarea_info import change_git_config, get_info
from analyze_data import analyse_data
from get_server_info import server_info

from rich import print


def main(args : argparse.Namespace):

    test_args = files.read_config(args.file)
    collect = True
    if test_args["data_path"] is None:
        print("data path was not created, collecting metrics")
    elif args.regen is True:
        print("force collecting metrics")
    else:
        collect = False

    if collect: collect_metrics(args)
    test_args = files.read_config(args.file) # reload the config because collect metrics modifies the config

    if test_args["workarea"] is not None:
        with change_git_config(): get_info(test_args["workarea"], test_args["data_path"], test_args["config_repo"])
    else:
        print("configuration has no workarea and it was not supplied. Software and DAQ config information cannot be calculated.")

    if "pinning" in test_args:
        print("copying custom pinning file for report generation.")
        shell.run(f"cp {test_args['pinning']} {test_args['data_path']}cpupin-all-running.json")

    for i in [server_info, plot, analyse_data, performance_report]:
        i(test_args)

    return


if __name__ == "__main__":
    parser = utils.ApplicationArguments("Create a performance report with one command.")
    parser.add_argument("-r", "--regen", action = "store_true", help = "enable flag to re-collect data from the dashboard (data is collected by default if this is run for the first time.)")
    args = parser.create()
    main(args)