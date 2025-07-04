#!/usr/bin/env python3

import click

import files, utils

@click.command()
@click.argument('filename', nargs=1, type=click.Path(exists=True))
def main(filename : click.Path):
    with open("storage_info.txt", "w") as outfile:
        xml = files.read_xml(filename)
        for i in utils.xml_search_elem(xml, "class", "storage"):
            info = {j : utils.xml_search_elem_name_single(i, j) for j in ["description", "product", "vendor", "size"]}
            for k, v in info.items():
                outfile.write("\n")
                if v is not None:
                    s = f"{k} : {v.text}"
                    if "units" in v.attrib: s += f" {v.attrib['units']}"
                    outfile.write(s)
    return

if __name__ == "__main__":
    main()
