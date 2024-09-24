#!/usr/bin/env python
from basic_functions import extract_grafana_data, process_files, load_json, save_json, reformat_cpu_util, create_filename
from basic_functions_performance import create_report_performance
from rich import print
import argparse
import pathlib
import json


def generate_config_template():
    """Generate a template json file for the test reports.
    """
    cfg = {
        "dunedaq_version" : "version of DUNEDAQ used to perform tests e.g. v4.4.8",
        "host" : "server being tested e.g. np02-srv-003",
        "data_type" : "type of readout data, e.g. eth",
        "socket_num" : ["socket number tested on the host machine, 0, 1 or 01 for both"],
        "test_name" : ["name of test performed"],

        "grafana_url" : "grafana url to access monitoring",
        "dashboard_uid" : ["dashboard uid"],
        "delta_time" : [["start time of test", "end time of test"]],
        "partition" : ["grafana partition name for the given test"],

        "core_utilisation_file" : "core utilisation file generated during the run",

        "data_path" : "path the data is located (should be removed)",

        "grafana_data_files" : [
            "grafana data files, generated using collect_metrics.py"
        ],
        "core_utilisation_files" : [
            "formatted core utilisation files, generated using collect_metrics.py"
        ],
        "readout_name" : [
            [
                "readouthost names in daqconf file, for each test"
            ]
        ],
        "configuration_file" : [
            "daqconf or oks configuration file used in each test"
        ],

        "repin_threads_file" : [None],
        "report_name" : None,
        "report_comment" : ["comment for each test"]

    }
    save_json("template_report.json", cfg)
    print("template config file template_report.json created")

def main(args : argparse.Namespace):

    test_args = load_json(args.file)

    new_args = load_json(args.file) # reopen config file to add the data file paths
    core_utilisation_files = []
    grafana_files = []
    for i in range(len(test_args["test_name"])):
        name = create_filename(test_args, i)

        cu_file = pathlib.Path(f"core_utilisation-{name}.csv")
        gr_file = pathlib.Path(f"grafana-{name}.csv")

        # format core util files
        cpu_df = reformat_cpu_util(test_args["core_utilisation_file"][i])
        print(cpu_df)
        cpu_df.to_csv(cu_file.name)

        core_utilisation_files.append(cu_file.resolve().as_posix())

        # extract grafana data
        extract_grafana_data(test_args["grafana_url"], test_args["dashboard_uid"], test_args["delta_time"][i], test_args["host"], test_args["partition"][i], name)
        grafana_files.append(gr_file.resolve().as_posix())

    new_args["grafana_data_files"] = grafana_files
    new_args["core_utilisation_files"] = core_utilisation_files

    save_json(args.file, new_args)
    print(f"{args.file} updated to include processed data files.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Collect results from performance tests.")

    parser.add_argument("-g", "--generate-template", action = "store_true", help = "Generate template json file for report arguments")

    file_arg = parser.add_argument("-f", "--file", type = pathlib.Path, help = "json file which contains the details of the test.")

    args = parser.parse_args()

    if args.generate_template is False:
        file_arg.required = True
        gen_args = parser.parse_args()
    else:
        generate_config_template()
        exit()

    args = parser.parse_args()

    if args.file.suffix != ".json":
        raise Exception("not a json file")

    print(args)
    main(args)