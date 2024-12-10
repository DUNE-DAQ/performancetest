#!/usr/bin/env python
"""
Created on: 09/12/2024 10:43

Author: Shyam Bhuller

Description: Run certain performance test tools in batch.
#? add multiprocessing?
"""
import argparse
import os

import shell

from rich import print

def main(args : argparse.ArgumentParser):
    for cfg in args.configs:
        shell.run(f"{args.script} -f {cfg}")
    return

if __name__ == "__main__":
    blacklist = [os.path.basename(__file__), "generate_test_config.py", "recreate_workarea.py"] # scripts that we don't want to allow the use of batch processing
    tools = [i.name for i in shell.search_data_file(".*py$", f"{os.environ['PERFORMANCE_TEST_PATH']}/tools/") if i.name not in blacklist] # retreive the list of valid tools to bath process with
    args = argparse.ArgumentParser("Run certain performance test tools in batch i.e. pass multiple configuration jsons to a valid tool.")
    args.add_argument(dest = "script", choices = tools, type = str, help = "script to run")
    args.add_argument(dest = "configs", nargs = "+", type = str, help = "Configuration files to run script on.")
    args = args.parse_args()
    print(args)
    main(args)