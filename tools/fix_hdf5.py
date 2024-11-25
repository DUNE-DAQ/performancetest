#!/usr/bin/env python
"""
Created on: 25/11/2024 16:33

Author: Shyam Bhuller

Description: Fix hdf5 files whose keys are broken.
"""
import pathlib, tables
import utils, files, shell, harvester

from rich import print

def main(args):
    test_args = files.load_json(args.file)
    fl = shell.search_data_file(".hdf5", test_args["data_path"])

    if len(fl) == 0:
        print(f"no hdf5 files were found under {test_args['data_path']}")
        exit(0)

    bad_keys = []
    for f in fl:
        with tables.open_file(pathlib.Path(f), driver = "H5FD_CORE") as hdf5file:
            for i in hdf5file.root:
                if type(i) == tables.group.Group:
                    for j in hdf5file.root[i._v_pathname[1:]]:
                        if not (("axis" in j._v_pathname[1:]) or ("block" in j._v_pathname[1:])):
                            if f not in bad_keys: bad_keys.append(f)

    if len(bad_keys) == 0:
        print(f"no issues found with hdf5 files!")
        exit(0)

    for k in bad_keys:
        data = files.read_hdf5(k) # data should open as usual
        original_keys = list(data.keys())
        harvester.format_hdf_keys(data)

        if len(data.keys()) != len(original_keys):
            raise Exception("number of keys not equal after fixing names! Aborting...")
        else:
            print("overwritting file with fixed keys")
            files.write_dict_hdf5(data, k, "w")

    return


if __name__ == "__main__":
    parser = utils.ApplicationArguments("Fix hdf5 files whose keys are broken.")
    args = parser.create()
    main(args)