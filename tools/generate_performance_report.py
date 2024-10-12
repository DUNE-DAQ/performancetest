#!/usr/bin/env python
"""
Created on: 13/10/2024 00:10

Author: Shyam Bhuller

Description: Deprecated, likely does not work with current data files.
"""
import argparse
import os
import pathlib

from basic_functions_performance import create_report_performance

import files
import utils

from rich import print

def main(args : argparse.Namespace):

    test_args = files.load_json(args.file)

    if test_args["report_name"] is None:
        name = utils.create_filename(test_args, 0) # should this be something unique?
    else:
        name = test_args["report_name"]

    if "reformatted_utilisation_files" not in test_args:
        test_args["reformatted_utilisation_files"] = [None]*len(test_args["grafana_data_files"])

    create_report_performance(
        all_files = test_args["grafana_data_files"],
        readout_name = test_args["readout_name"],
        daqconf_files = test_args["configuration_file"],
        core_utilization_files = test_args["reformatted_utilisation_files"],
        parent_folder_dir = os.environ["PERFORMANCE_TEST_PATH"],
        pdf_name = name,
        repin_threads_file = test_args["repin_threads_file"],
        comment = test_args["report_comment"],
        times = test_args["delta_time"]
        )

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Create the performance reports.")

    file_arg = parser.add_argument("-f", "--file", type = pathlib.Path, help = "json file which contains the details of the test.", required = True)

    args = parser.parse_args()

    file_arg.required = True
    gen_args = parser.parse_args()

    args = parser.parse_args()

    if args.file.suffix != ".json":
        raise Exception("not a json file")

    print(args)
    main(args)