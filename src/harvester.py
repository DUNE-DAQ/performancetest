"""
Created on: 12/10/2024 22:35

Author: Shyam Bhuller

Description: Collect and parse data from the Grafana dashboards (The spice must flow) 
"""
import copy
import tables
import warnings

import numpy as np
import pandas as pd

from rich import print

import files
import queries
import utils

from queries import time_range

warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning) # cause screw pandas
warnings.simplefilter(action='ignore', category=tables.NaturalNameWarning) # cause screw pandas


def get_run_time(url : str, datasources : list[dict], run_number : int) -> time_range:
    """ Get the start time and end time of the run.

    Args:
        url (str): Grafana url.
        datasources (list[dict]): List of datasources.
        run_number (int): run number of the test.

    Returns:
        time_range: start and end times in unix time.
    """
    query_str = f"SELECT \"run_number\" FROM \"dunedaq.rcif.opmon.RunInfo\" WHERE \"run_number\" >0"
    response = queries.query_var(url, datasources, query_str)

    values = np.array(response["results"][0]["series"][0]["values"])
    times = values[values[:, 1].astype(int) == run_number][:, 0] # select times for the given run number

    utimes = utils.dt_to_unix_array([times[0], times[-1]]).values # get the unix time for start and end times

    return time_range(start = min(utimes), end =max(utimes))


def collect_vars(url : str, datasources : list[dict], time : time_range, partition : str, host : str) -> dict:
    """ Collect relavent variables from the grafana dashboards. This is very specific to the DUNEDAQ,
        so this would be a likely failure point if operational monitoring changes.

    Args:
        url (str): Grafana url.
        datasources (list[dict]): List of datasources.
        time (time_range): Time range of the test.
        partition (str): Partition/session name.
        host (str): Host machine name.

    Returns:
        dict: Dictionary of variables extracted from each dashboard, with all possible values.
    """
    vars_to_collect = {"dhs" : get_dhs, "fe" : get_fe_eth_vars, "dpdk" : get_dpdk_vars} # functions specific to each dashboard, as the queries are unique.

    collected_vars = {}
    for k, v in vars_to_collect.items():
        try:
            collected_vars[k] = v(url, datasources, time, partition)
        except Exception as e:
            print(f"cannot get {k} for session {partition}, Reason: {e}")

    # some variables whose values can be populated from the test configuration file
    var_map = {
        "host" : host, # only true is expr in target?
        "node" : host, # ""
        "parition" : partition,
        "session" : partition,
        "timeFilter" : f"time >= {time.start}s and time <= {time.end}s", # apply time range within query (applicable to influxdb queries)
        "__interval": "10s",
        "{__from}" : str(time.start),
        "{__to}" : str(time.end)
    }

    for v in collected_vars.values():
        var_map = var_map | v

    return var_map


def get_dpdk_vars(url : str, datasources : list[dict], time : time_range, partition : str) -> dict[str]:
    """ Get the different variables and values specific to dpdklibs.

    Args:
        url (str): Grafana url
        datasources (list[dict]): 
        time (time_range): time range of test.
        partition (str): partition/session name.

    Returns:
        dict[str]: variables and their possible values.
    """
    #* query string is unique to the dashboard
    query_str = f'SELECT "bytes", application, queue FROM "dunedaq.dpdklibs.opmon.QueueEthXStats" WHERE session = \'{partition}\' AND time >= {time.start}s and time <= {time.end}s'

    response = queries.query_var(url, datasources, query_str)

    values = np.array(response["results"][0]["series"][0]["values"])

    values = {
        "application" : values[:, 2],
        "queue" : values[:, 3],
    }
    return {k : np.unique(v) for k, v in values.items()}


def get_fe_eth_vars(url : str, datasources : list[dict], time : time_range, partition : str) -> dict[str]:
    """ Get the different variables and values specific to front end ethernet readout.

    Args:
        url (str): Grafana url
        datasources (list[dict]): 
        time (time_range): time range of test.
        partition (str): partition/session name.

    Returns:
        dict[str]: variables and their possible values.
    """
    query_str = f"SELECT \"sent_udp_count\", application, element, detector, crate, slot, queue FROM \"dunedaq.hermesmodules.opmon.LinkInfo\" WHERE session = '{partition}' AND time >= {time.start}s and time <= {time.end}s"

    response = queries.query_var(url, datasources, query_str)

    values = np.array(response["results"][0]["series"][0]["values"])

    values = {
        "CRP" : values[:, 2], # application
        "WIB" : values[:, 3], # element
        "detector" : values[:, 4],
        "crate" : values[:, 5],
        "slot" : values[:, 6],
    }
    values = {k : np.unique(v) for k, v in values.items()}
    return values


def get_dhs(url : str, datasources : list[dict], time : time_range, partition : str) -> dict[str]:
    """ Get the different variables and values specific to the datahandlers.

    Args:
        url (str): Grafana url
        datasources (list[dict]): 
        time (time_range): time range of test.
        partition (str): partition/session name.

    Returns:
        dict[str]: variables and their possible values.
    """
    query_str = f"SELECT element FROM (SELECT \"sum_payloads\", element FROM \"dunedaq.datahandlinglibs.opmon.DataHandlerInfo\" WHERE time >= {time.start}s and time <= {time.end}s)"

    response = queries.query_var(url, datasources, query_str)

    values = response["results"][0]["series"][0]["values"]

    DLH_names = []
    tphandler_names = []
    
    for v in values:
        if "DLH" in v[1]:
            DLH_names.append(v[1])
        if "tphandler" in v[1]:
            tphandler_names.append(v[1])

    return {"DLH" : np.unique(DLH_names), "tphandler" : np.unique(tphandler_names)}


def parse_result_influx(response_data : dict, panel : dict) -> pd.DataFrame:
    parsed_results = {}

    if "series" in response_data["results"][0]:
        for i in response_data["results"][0]["series"]:
            if "tags" in i:
                if len(i["tags"]) > 1:
                    key = f'{i["tags"]}' # convert dictionary to string so the dataframe can be written to hdf5
                else:
                    key = list(i["tags"].values())[0]
                parsed_results[key] = np.array(i["values"])
            else:
                parsed_results[panel["title"]] = np.array(i["values"])

    df = None
    for k, v in parsed_results.items():
        if v is None:
            entry = pd.DataFrame({"time" : [None], k : [None]})
        else:
            entry = pd.DataFrame({"time" : utils.dt_to_unix_array(v[:, 0]), k : v[:, 1]})
            entry = entry.set_index("time")

        if df is None:
            df = entry
        else:
            df = pd.concat([df, entry], axis = 1).astype(float)

    return df


def parse_result_prometheus(response_data, name) -> pd.DataFrame:
    parsed = {}

    for i, result in enumerate(response_data["data"]["result"]):
        if len(response_data["data"]["result"]) == 1:
            key = name
        else:
            key = name + f"x_{i}"
        v = np.array(result["values"])
        parsed["time"] = v[:, 0]
        parsed[key] = v[:, 1]

    return pd.DataFrame(parsed).set_index("time").astype(float)


def format_panels(panels: list[dict], var_map : dict) -> tuple[list[dict], list[str]]:
    """ Replace all the variables with their respective values. If the variable is in the title, the panel is reproduced for each possible value.

    Args:
        panels (list[dict]): Grafana panels
        var_map (dict): map of variable names to the possible values.

    Returns:
        tuple[list[dict], list[str]]: formatted panels and a record of the original query strings.
    """
    new_panels = []

    # duplicate panels if needed (panel title contains a variable)
    for panel in panels:
        if "title" not in panel: continue
        if "$" in panel["title"]: # variable has been found in panel title, this must be duplicated if any variables are a list
            dup = queries.extract_vars(panel["title"])
            for k, v in var_map.items():
                if utils.is_collection(v): # is the variable a list
                    if k in dup: # is it in the title
                        for i in v:
                            new_panels.append(queries.search_panel(copy.deepcopy(panel), queries.replace_var, {"target" : k, "value" : i})) # duplicate panel for each variable
        else:
            new_panels.append(copy.deepcopy(panel))

    # extract the original queries
    original_queries = [queries.get_queries(panel) for panel in new_panels]

    # format the panels
    for panel in new_panels:
        for k, v in var_map.items():
            if utils.is_collection(v): # is the variable a list
                queries.search_panel(panel, queries.replace_var, {"target" : k, "value" : queries.make_names_str(v)}) # replace variable with its names_str
            else:
                queries.search_panel(panel, queries.replace_var, {"target" : k, "value" : v}) # replace variable with value
    return new_panels, original_queries


def extract_grafana_data(url : str, dashboards : list[str], run_number : int, host : str, partition : str, output_file : str) -> list[str]:
    """ Extract data from Grafana dashboards.

    Args:
        url (str): Grafana url.
        dashboard_uid (list[str]): Dashboard uid.
        run_number (int): run number of specific test.
        host (str): Host name.
        partition (str): Partition/session name.
        output_file (str): Output file name.

    Returns:
        list[str]: List of the output files.
    """

    datasource_urls = queries.get_datasources(url) # gather list of all datasources
    time = get_run_time(url, datasource_urls, run_number)

    var_map = collect_vars(url, datasource_urls, time, partition, host) # get list of relavent variables used by the dashboards

    out_files = []
    for dashboard in dashboards: # iterate over each dashboard
        panels = queries.get_grafana_panels(url, dashboard) # get panels from dashboard

        if not panels:
            print("no panels were found in the dashboard!")
            return

        panels, original_queries = format_panels(panels, var_map) # populate the panels with the variable values

        dashboard_data = {}
        for p, panel in enumerate(panels): # iterate over each panel

            if 'targets' not in panel: # if a panel has no target is does not have any data
                print(f'Skipping panel {panel_title}, with no targets.')
                continue

            if "panels" in panel: # this is true if the panel contains its own panels
                if len(panel["panels"]) == 0:
                        data_type = panel["datasource"]["type"]
                else:
                    data_type = panel["panels"][0]["datasource"]["type"]
            else:
                data_type = panel["datasource"]["type"]

            if panel=='Runs': continue # unsure why this is skipped

            panel_title = panel.get('title', '') # if a panel has not title ignore it (we wont know what the data is)
            if not panel_title: continue

            # for now ignore panels at the first pass #TODO implement 
            if ("resultFormat" in panel["targets"][0]) and (panel["targets"][0]["resultFormat"] == "table"): continue

            query_strs = queries.get_queries(panel) # get the query strings from the panel

            vars_in_query = [queries.extract_vars(v) for v in original_queries[p].values()] # get any variables which were used in the query

            if len(query_strs) == 0: continue

            data_from_panel = {}
            for (query_name, query), var in zip(query_strs.items(), vars_in_query): # loop over all queries

                response_data = queries.make_query(datasource_urls, url, query, time) # make the query

                # get the data from the response, will be specific to the datasource type
                if response_data:
                    if data_type == "prometheus":
                        data_from_panel[query_name] = parse_result_prometheus(response_data, query_name)

                    elif data_type == "influxdb":
                        data_from_panel[query_name] = parse_result_influx(response_data, panel)

                    else:
                        print(f"not sure how to parse this data type: {data_type}")
            
            # organise the DataFrames to save to file
            single_columns = all([len(data.columns) == 1 for data in data_from_panel.values() if data is not None]) # check the panel returned multiple query DataFrames with a single column

            if single_columns: # condense data for panels which returned multiple DataFrames
                merged_df = None
                for v in data_from_panel.values():
                    if merged_df is None:
                        merged_df = v
                    else:
                        merged_df = pd.concat([merged_df, v], axis = 1)
                data_from_panel = merged_df
            elif len(data_from_panel) == 1:
                data_from_panel = list(data_from_panel.values())[0]
            else: # not sure how we end up here...
                print(f"don't know what to do for {panel_title}")
                pass

            if data_from_panel is None:
                dashboard_data[panel_title] = pd.DataFrame({})
            else:
                dashboard_data[panel_title] = data_from_panel

        print(dashboard_data)

        # Save the dataframes
        filename = output_file.replace(".hdf5", "")
        output = f'grafana-{dashboard}-{filename}.hdf5'
        try:
            files.write_dict_hdf5(dashboard_data, output)
            out_files.append(output)
            print(f'Data saved to HDF5 successfully: {output}')
        except Exception as e:
            print(f'Exception Error: Failed to save data to HDF5: {str(e)}')

    return out_files
