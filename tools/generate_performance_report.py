#!/usr/bin/env python
"""
Created on: 13/10/2024 00:10

Author: Shyam Bhuller

Description: Deprecated, likely does not work with current data files.
"""
import pathlib
import argparse

import files
import utils

from collect_metrics import collect_metrics
from fronted_ethernet_metrics import frontend_ethernet
from resource_utilization import resource_utilization
from tp_metrics import tp_metrics
from performance_report import performance_report
from workarea_info import get_info
from analyze_data import analyse_data

from rich import print


def main(args : argparse.Namespace):

    test_args = files.load_json(args.file)
    collect = True
    if test_args["data_path"] is None:
        print("data path was not created, collecting metrics")
    elif args.regen is True:
        print("force collecting metrics")
    else:
        collect = False

    if collect: collect_metrics(args)
    test_args = files.load_json(args.file) # reload the config because collect metrics modifies the config

    if test_args["workarea"] is not None:
        get_info(test_args["workarea"], test_args["data_path"])
    else:
        print("configuration has no workarea and it was not supplied. Software and DAQ config information cannot be calculated.")

    for i in [frontend_ethernet, resource_utilization, tp_metrics, performance_report, analyse_data]:
        i(test_args)

    return


if __name__ == "__main__":
    parser = utils.ApplicationArguments("Create a performance report with one command.")
    parser.add_argument("-r", "--regen", action = "store_true", help = "enable flag to re-collect data from the dashboard (data is collected by default if this is run for the first time.)")
    args = parser.create()
    main(args)