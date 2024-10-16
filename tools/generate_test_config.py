#!/usr/bin/env python
import argparse
import pathlib

import files

from rich import print


def generate_config_template(name : str | pathlib.Path):
    """Generate a template json file for the test reports.
    """
    cfg = {
        "dunedaq_version" : "version of DUNEDAQ used to perform tests e.g. v4.4.8",
        "host" : "server being tested e.g. np02-srv-003",
        "data_source" : "source of the data, crp, apa or emu",
        "socket_num" : "socket number tested on the host machine, 0, 1 or 01 for both",
        "test_name" : "short test name",
        "run_number" : "run number of the test",
        "session" : "grafana partition name for the given test",
        "out_path" : "override this if you want to save data and reports locally.",
        "documentation" : {
            "purpose" : "state the purpose of your test, if not provided, default text will be added instead",
            "goals" : "state the goals of this sepcific test, if not provided, default text will be added instead",
            "method" : "state how you will attempt to reach the goal, if not provided, default text will be added instead",
            "control plane" : "how was the system controlled during the test i.e. proceess manager configuration",
            "configuration" : "path to configuration or git commit hash from ehn1configs",
            "concurrancy" : "active users on the readout machine during the time of the run, what applications were run in parallel on the machine",
            "summary" : "summary/conclusions of the test"
        }
        # "configuration_file" : [
        #     "daqconf or oks configuration file used in each test"
        # ],
        # "repin_threads_file" : [None],
        # "report_name" : None,
        # "report_comment" : ["comment for each test"]

    }
    files.save_json(name, cfg)
    print(f"template config file {name.with_suffix('.json')} created")


def main(args : argparse.Namespace):
    generate_config_template(args.name)
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Generate template json configuration for performance tests.")

    parser.add_argument("-n", "--name", type = pathlib.Path, help = "name of json file")

    args = parser.parse_args()

    print(args)
    main(args)