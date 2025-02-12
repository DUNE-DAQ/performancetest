#!/usr/bin/env python
"""
Created on: 12/12/2024 11:01

Author: Shyam Bhuller (University of Oxford)

Description: Convert a text file to pdf using weasyprint as a middle-man.
"""
import weasyprint
import pathlib
import argparse

def main(args : argparse.Namespace):
    with args.file.open("r") as file:
        file = file.readlines()

    html_str = ""
    for l in file:
        n_indent = len(l.split("\t"))-1

        pointer = "-" if n_indent > 0 else ""

        html_str += f'<p style="margin-left: {20*n_indent}px;">' + pointer + l.replace("\t", "").replace("\n", "") + "</p>\n"

    weasyprint.HTML(string = html_str).write_pdf(args.out.with_suffix(".pdf"))
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser("convert a text file to pdf using weasyprint as a middle-man.")
    
    parser.add_argument(dest = "file", type = pathlib.Path, help = "txt file.")
    parser.add_argument(dest = "out", type = pathlib.Path, help = "output file path")

    args = parser.parse_args()
    main(args)