#!/usr/bin/env python
from basic_functions import load_json, create_filename
from basic_functions_performance import create_report_performance
from rich import print
import argparse
import pathlib
import json
import os

def main(args : argparse.Namespace):

    test_args = load_json(args.file)

    if test_args["report_name"] is None:
        name = create_filename(test_args, 0) # should this be something unique?
    else:
        name = test_args["report_name"]

    create_report_performance(input_dir = test_args["data_path"], output_dir = "./", all_files = test_args["grafana_data_files"], readout_name = test_args["readout_name"], daqconf_files = test_args["configuration_file"], core_utilization_files = test_args["core_utilisation_files"], parent_folder_dir = os.environ["PERFORMANCE_TEST_PATH"], pdf_name = name, repin_threads_file = test_args["repin_threads_file"], comment = test_args["report_comment"])

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