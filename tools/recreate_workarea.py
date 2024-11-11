"""
Created on: 11/11/2024 14:15

Author: Shyam Bhuller

Description: Re-create a workarea provided the software and configuration information from a given performance report. 
"""

import argparse

def main(args : argparse.Namespace):
    global printout
    printout = True
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Re-create a workarea provided the software and configuration information from a given performance report.")

    parser.add_argument(dest = "path", type = str, help = "dunedaq working directory.")

    args = parser.parse_args()

    print(args)
    main(args)