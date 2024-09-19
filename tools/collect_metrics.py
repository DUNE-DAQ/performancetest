#!/usr/bin/env python
import dateutil.parser
from basic_functions import extract_grafana_data, process_files, load_json, reformat_cpu_util
from basic_functions_performance import create_report_performance
from rich import print
import argparse
import pathlib
import json


def generate_config_template():
    cfg = {
        "datasource_url" : "url of the prometheus datasource",
        "grafana_url" : "grafana url to access monitoring",
        "dashboard_uid" : "dashboard uid",
        "delta_time" : " time range of tests",
        "host" : "server being tested e.g. np02-srv-003",
        "partition" : "grafana partition name",
        "input_dir" : "test directory",
        "output_csv_file": "name of output file",
        "core_utilisation_file" : "core utilisation file generated during the run"
    }
    with open("./template_report.json", 'w') as f:
        json.dump(cfg, f, indent = 4)
    print("template config file ./template_report.json created")


def main(args : argparse.Namespace):

    test_args = load_json(args.file)

    print(pathlib.Path(test_args["core_utilisation_file"]).name)

    cpu_df = reformat_cpu_util(test_args["core_utilisation_file"])
    print(cpu_df)
    cpu_df.to_csv(f"reformatted-{pathlib.Path(test_args['core_utilisation_file']).name}")

    test_args.pop("core_utilisation_file")

    extract_grafana_data(**test_args)

    # process_files(input_dir=test_args["input_dir"], process_pcm_files=True, process_uprof_files=False, process_core_files=True)
    # process_files(input_dir=args["input_dir"] + "/Emu_stream_scaling/", process_pcm_files=False, process_uprof_files=False, process_core_files=True)

    args = {
            "input_dir" : "/nfs/home/sbhuller/fddaq_v4_4_8/work/v4_4_8-np02srv003-1-eth-Emu_stream_scaling/",
            "output_dir" : "/nfs/home/sbhuller/fddaq_v4_4_8/work/v4_4_8-np02srv003-1-eth-Emu_stream_scaling/",
            "all_files" : ["grafana-v4_4_8-np02srv003-1-eth-emu_stream_scale"],
            "readout_name" : [["runp02srv003eth0"]],
            "daqconf_files" : ["daqconf-eth-Emu_stream_scaling-np02srv003-1"],
            "core_utilization_files" : ["Emu_stream_scaling/reformatted_core_utilization-Emu_stream_scaling"],
            "parent_folder_dir" : '/nfs/home/sbhuller/fddaq_v4_4_8/sourcecode/performancetest/',
            "print_info" : True,
            "pdf_name" : "stream_scale_test_np02srv003_1_emu",
            "repin_threads_file" : [None],
            "comment" : ["Test report for the stream scale test, performed using np02-srv-003 and fddaq-v4.4.8."]

        }
    # create_report_performance(**args)

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

    args = parser.parse_args()

    if args.file.suffix != ".json":
        raise Exception("not a json file")

    print(args)

    main(args)