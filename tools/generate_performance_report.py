#!/usr/bin/env python
"""
Created on: 13/10/2024 00:10

Author: Shyam Bhuller

Description: Deprecated, likely does not work with current data files.
"""
import pathlib
import argparse

import files

from collect_metrics import collect_metrics
from fronted_ethernet_metrics import frontend_ethernet
from resource_utilization import resource_utilization
from tp_metrics import tp_metrics
from performance_report import performance_report

from rich import print


def main(args : argparse.Namespace):

    test_args = files.load_json(args.file)
    collect = True
    if "data_path" not in test_args:
        print("data path was not created, collecting metrics")
    elif args.regen is True:
        print("force collecting metrics")
    else:
        collect = False

    if collect: collect_metrics(args)
    test_args = files.load_json(args.file) # reload the config because collect metrics modifies the config

    test_args["out_path"] = test_args["data_path"] # for all in one usage pdf and data are stored in the same directory to correctly generate urls
    for i in [frontend_ethernet, resource_utilization, tp_metrics, performance_report]:
        i(test_args)

    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Create a performance report with one command.")

    parser.add_argument("-f", "--file", type = pathlib.Path, help = "json file which contains the details of the test.", required = True)
    parser.add_argument("-r", "--regen", action = "store_true", help = "enable flag to re-collect data from the dashboard (data is collected by default if this is run for the first time.)")

    args = parser.parse_args()
    if args.file.suffix != ".json":
        raise Exception("not a json file")

    print(args)
    main(args)