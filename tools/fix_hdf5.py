#!/usr/bin/env python
"""
Created on: 25/11/2024 16:33

Author: Shyam Bhuller (University of Oxford)

Description: Check potential issues with the hdf5 files and fix them.
"""
import pathlib, tables
import utils, files, shell, harvester

from rich import print

def fix_keys(file_list : list[str]):
    bad_keys = []
    for f in file_list:
        with tables.open_file(pathlib.Path(f), driver = "H5FD_CORE") as hdf5file:
            for i in hdf5file.root:
                if type(i) == tables.group.Group:
                    for j in hdf5file.root[i._v_pathname[1:]]:
                        if not (("axis" in j._v_pathname[1:]) or ("block" in j._v_pathname[1:])):
                            if f not in bad_keys: bad_keys.append(f)

    if len(bad_keys) == 0:
        print(f"no issues found with paths in the hdf5 files!")
        # exit(0)
    else:
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


def fix_indices(file_list : list[str]):
    for f in file_list:
        data = files.read_hdf5(f)
        print(f)
        changes = 0
        for k, v in data.items():
            # first check the index is in time and it is a numeric type not a string
            if v.index.name == "time":
                if "int" not in str(v.index.dtype):
                    v.set_index(v.index.astype(int), inplace = True)
                    changes += 1
                if any((v.index[1:] - v.index[:-1]) < 0):
                    print(f"{k} not in time order")
                    v.sort_index(inplace = True)
                    changes += 1
        if changes > 0:
            files.write_dict_hdf5(data, f, "a")
        else:
            print("no fixes to the indices were needed")
    return


def main(args):
    test_args = files.read_json(args.file)
    fl = shell.search_data_file(".hdf5", test_args["data_path"])

    if len(fl) == 0:
        print(f"no hdf5 files were found under {test_args['data_path']}")
        exit(0)

    fix_keys(fl)
    fix_indices(fl)
    return


if __name__ == "__main__":
    parser = utils.ApplicationArguments("Fix hdf5 files whose keys are broken.")
    args = parser.create()
    main(args)