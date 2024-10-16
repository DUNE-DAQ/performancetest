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
    collect_metrics(args)
    test_args = files.load_json(args.file)

    for i in [frontend_ethernet, resource_utilization, tp_metrics, performance_report]:
        i(test_args)

    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Create a performance report with one command.")

    file_arg = parser.add_argument("-f", "--file", type = pathlib.Path, help = "json file which contains the details of the test.", required = True)

    args = parser.parse_args()

    file_arg.required = True
    gen_args = parser.parse_args()

    args = parser.parse_args()

    if args.file.suffix != ".json":
        raise Exception("not a json file")

    print(args)
    main(args)