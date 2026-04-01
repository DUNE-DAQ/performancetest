#!/usr/bin/env python
"""
Created on: 12/12/2024 11:12

Author: Shyam Bhuller (University of Oxford)

Description: Creates performance reports from existing plots and provided documentation in the configuration.
"""
import argparse
import os
import pathlib

import files, shell, utils
import workarea_info

import weasyprint
import pymupdf

from rich import print

plot_to_extract = {
    "cache_plots" : {"l2_cache" : 1, "l3_cache" : 3},
    "cpu_plots" : {"thread" : 5, "total" : 10},
    "disk_plots" : {"rate" : 4, "total" : 5},
    "fe_plots" : {"throughput" : 0, "missed" : 1, "dropped" : 2},
    "memory_plots" : {"usage" : 0, "bandwidth" : 1},
    "tp_plots" : {"rate" : 0},
}

def extract_image(file_path : str, out_path : str, pages : dict[str, int], zoom : float = 5, prefix : str = "page"):
    doc = pymupdf.open(file_path)  # open document

    files = {}
    for k, v in pages.items():
        try:
            page = doc.load_page(v)
        except ValueError:
            print(f"could not extract image of plot: {k} in {prefix}")
            continue
        mat = pymupdf.Matrix(zoom, zoom)  # zoom factor to increase resolution
        pix = page.get_pixmap(matrix=mat)  # convert page to pixel map
        fp = f"{out_path}/{prefix}_{k}.png"
        pix.save(fp) # save to png
        files[f"{prefix}_{k}"] = fp
    return files


def search_plots(args : dict):
    if args["plot_path"] is None:
        args["plot_path"] = utils.make_plot_dir(args)

    report_out = args["plot_path"] + "/report_plots/"
    os.makedirs(args["plot_path"] + "/report_plots/", exist_ok = True)

    plot_file_list = [p for p in pathlib.Path(args["plot_path"]).glob("**/*.pdf")]

    extracted_files_map = {"daq" : {}} | {h : {} for h in args["host"]}
    for p in plot_file_list:
        for k, v in plot_to_extract.items():
            if k in p.name:
                for h in args["host"]:
                    if h in p.stem:
                        dest = h
                    else:
                        dest = "daq"
                files = extract_image(p, report_out, v, prefix = p.stem)
                extracted_files_map[dest] = extracted_files_map[dest] | files
                # dest[key] = extract_image(p, "test", v, prefix = p.stem)

    return extracted_files_map

def create_urls(args : dict) -> dict:
    """ Create cernbox urls for the files in the performance report directory.

    Args:
        args (dict): Performance test configuration.

    Returns:
        dict: Created urls.
    """
    paths = {"data" : args["data_path"], "plots" : args["plot_path"]}

    head_name = str(utils.test_path(args)).split(args["out_path"])[-1]

    urls = {"data" : {}, "plots" : {}}
    for k, v in paths.items():
        print(v)
        for p in pathlib.Path(v).glob("**/*"):
            print(p)
            if p.is_file:
                if p.suffix == ".png": continue
                link = utils.make_public_link(head_name + f"/{k}/" + str(p).split(args["plot_path"])[-1])
                urls[k][p.name] = link

    print(urls)

    return urls


def html_to_str(path : pathlib.Path | str) -> str:
    """ Open html file as a string.

    Args:
        path (pathlib.Path | str): html file path.

    Returns:
        str: html string.
    """
    with pathlib.Path(path).open("r") as f:
        return f.read()


def get_defaults() -> dict:
    """ Get html files that contain defualt text for certain entries in the performance report.

    Returns:
        dict: Default text read as html strings.
    """
    defs = {}
    for p in pathlib.Path(os.environ["PERFORMANCE_TEST_PATH"] + "/html/defaults/").glob("**/*"):
        defs[p.stem] = html_to_str(p)
    return defs


def write_url(url : str, link_text : str) -> str:
    """ Write a url in html.

    Args:
        url (str): url string.
        link_text (str): Text the url appears as.

    Returns:
        str: html formatted url string.
    """
    return f'<a href="{url}">{link_text}</a>'


def create_url_list(urls : dict) -> str:
    """ Create a bullet point list of urls in html.

    Args:
        urls (dict): Dictionary of urls, where the key is the link text.

    Returns:
        str: html string of the url list.
    """
    l = "<ul>\n"
    for k, v in urls.items():
        l += f"<li> {write_url(v, k)} </li>\n"
    l += "</ul>"
    return l


def performance_report(test_args : dict):
    """ Create the performance report.

    Args:
        test_args (dict): Performance test configuration.
    """
    defaults = get_defaults()

    host = test_args["host"]
    run = test_args["run_number"]

    html = html_to_str(os.environ["PERFORMANCE_TEST_PATH"] + "/html/report_template.html")

    html = html.replace("&run", str(run))
    html = html.replace("&host", str(host))
    html = html.replace("&topology", test_args["data_source"])

    if test_args["workarea"] is not None:
        winfo = shell.search_data_file("workarea_info", test_args["data_path"])
        if len(winfo) > 0:
            winfo = files.read_json(winfo[0])

            html = html.replace("&daq_version", "release information: \n" + workarea_info.make_release_table(winfo["release"]))
            html = html.replace("&commit_hashes", f"release packages: \n {workarea_info.make_repo_table(winfo['release_commit'])} \n local packages: \n {workarea_info.make_repo_table(winfo['local_commit'])} \n")
            html = html.replace(f"&configuration", workarea_info.make_repo_table(winfo["configuration"]))
            test_args["documentation"].pop("configuration")
        else:
            print("Warning: no workarea information was found!")


    for k, v in test_args["documentation"].items():
        if v is not None:
            text = v
        else:
            text = defaults.get(k, "")
        html = html.replace(f"&{k}", text)


    if test_args["plot_path"] is None:
        test_args["plot_path"] = utils.make_plot_dir(test_args)
    urls = create_urls(test_args)

    data = create_url_list(urls["data"])
    plots = create_url_list(urls["plots"])

    html = html.replace("&data-urls", data)
    html = html.replace("&plot-urls", plots)

    hw_specs = ["dmidecode", "lshw"]
    environment = ""
    for i in hw_specs:
        environment += write_url(utils.make_public_link(f"hwinfo_{host}/{host}-{i}.pdf"), i) + "\n"

    html = html.replace("&environment", environment)

    ### Summary Plots
    fig_map = search_plots(test_args)

    print(fig_map)

    html += "<h1>Performance Report Summary Plots</h1>"

    html += html_to_str(os.environ["PERFORMANCE_TEST_PATH"] + "/html/figs/DAQ_figs.html")

    for k, v in fig_map["daq"].items():
        html = html.replace(f"&{k}", str(pathlib.Path(v).absolute()))

    fig_map.pop("daq")
    for k, v in fig_map.items():
        html_srv = html_to_str(os.environ["PERFORMANCE_TEST_PATH"] + "/html/figs/server_figs.html")
        for k1, v1 in v.items():
            search_term = "&" + k1.replace(f"_{k}", "")
            html_srv = html_srv.replace(search_term, str(pathlib.Path(v1).absolute()))
        html += html_srv
    # weasyprint.HTML(string = html, base_url="/").write_pdf("test.pdf")

    file_path = str(utils.test_path(test_args)) + "/" + f"performance_report-run{run}.pdf"

    weasyprint.HTML(string = html, base_url="/").write_pdf(file_path)

    print(f"performance report written to {file_path}")
    return


def main(args : argparse.Namespace):
    test_args = files.read_config(args.file)
    performance_report(test_args)
    return


if __name__ == "__main__":
    args = utils.ApplicationArguments("Creates performance reports from existing plots and provided documentation in the configuration.").create()
    main(args)