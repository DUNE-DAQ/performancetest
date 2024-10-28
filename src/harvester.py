"""
Created on: 12/10/2024 22:35

Author: Shyam Bhuller

Description: Collect and parse data from the Grafana dashboards (The spice must flow) 
"""
import copy
import pathlib
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


def get_influx_db_id(dunedaq_version : str) -> int:
    """ Get the correct influx database id, databse is dependant on if the dunedaq version for the test is v4 or v5.

    Args:
        dunedaq_version (str): version string (format is vX.Y.Z).

    Raises:
        Exception: dunedaq version is not supported by performenace test tools.

    Returns:
        int: influxdb id number.
    """
    mv = utils.dunedaq_major_version(dunedaq_version)
    if mv == 4:
        db_id = 5
    elif mv == 5:
        db_id = 11
    else:
        raise Exception(f"version {dunedaq_version} not supported for ")
    return db_id


def get_run_time(url : str, datasource : dict, run_number : int, partition : str, dunedaq_version : str) -> time_range:
    """ Get the start time and end time of the run.

    Args:
        url (str): Grafana url.
        datasources (list[dict]): influx datasource.
        run_number (int): run number of the test.

    Returns:
        time_range: start and end times in unix time.
    """

    if utils.dunedaq_major_version(dunedaq_version) == 4:
        query_str = f"SELECT \"runno\" FROM \"dunedaq.rcif.runinfo.Info\" WHERE (\"partition_id\" = '{partition}' AND \"runno\" = {run_number})"
    elif utils.dunedaq_major_version(dunedaq_version) == 5:
        query_str = f"SELECT \"run_number\" FROM \"dunedaq.rcif.opmon.RunInfo\" WHERE \"run_number\" = {run_number}"
    else:
        raise Exception(f"version {dunedaq_version} not supported for ")

    response = queries.query_var_influx(url, datasource, query_str)
    values = np.array(response["results"][0]["series"][0]["values"])
    times = values[values[:, 1].astype(int) == run_number][:, 0] # select times for the given run number
    utimes = utils.dt_to_unix_array([times[0], times[-1]]).values # get the unix time for start and end times

    return time_range(start = min(utimes), end =max(utimes))


def collect_vars(url : str, datasource : dict, run_number : int, time : time_range, partition : str, host : str) -> dict:
    """ Collect relavent variables from the grafana dashboards. This is very specific to the DUNEDAQ,
        so this would be a likely failure point if operational monitoring changes.

    Args:
        url (str): Grafana url.
        datasource (dict): influx datasource.
        time (time_range): Time range of the test.
        run_number (int) : run number.
        partition (str): Partition/session name.
        host (str): Host machine name.

    Returns:
        dict: Dictionary of variables extracted from each dashboard, with all possible values.
    """
    vars_to_collect = {"dhs" : get_dhs, "fe" : get_fe_eth_vars, "dpdk" : get_dpdk_vars} # functions specific to each dashboard, as the queries are unique.

    collected_vars = {}
    for k, v in vars_to_collect.items():
        try:
            collected_vars[k] = v(url, datasource, time, partition)
        except Exception as e:
            print(f"cannot get {k} for session {partition}, Reason: {e}")

    # some variables whose values can be populated from the test configuration file
    var_map = {
        "host" : host, # only true is expr in target?
        "node" : host, # ""
        "runno" : str(run_number),
        "run_number" : str(run_number),
        "partition" : partition,
        "session" : partition,
        "timeFilter" : f"time >= {time.start}s and time <= {time.end}s", # apply time range within query (applicable to influxdb queries)
        "__interval": "10s",
        "{__from}" : str(time.start),
        "{__to}" : str(time.end)
    }

    for v in collected_vars.values():
        var_map = var_map | v

    return var_map


def get_dpdk_vars(url : str, datasource : dict, time : time_range, partition : str) -> dict[str]:
    """ Get the different variables and values specific to dpdklibs.

    Args:
        url (str): Grafana url.
        datasources (dict): influx datasource.
        time (time_range): time range of test.
        partition (str): partition/session name.

    Returns:
        dict[str]: variables and their possible values.
    """
    #* query string is unique to the dashboard
    query_str = f'SELECT "bytes", application, queue FROM "dunedaq.dpdklibs.opmon.QueueEthXStats" WHERE session = \'{partition}\' AND time >= {time.start}s and time <= {time.end}s'

    response = queries.query_var_influx(url, datasource, query_str)

    values = np.array(response["results"][0]["series"][0]["values"])

    values = {
        "application" : values[:, 2],
        "queue" : values[:, 3],
    }
    return {k : np.unique(v) for k, v in values.items()}


def get_fe_eth_vars(url : str, datasource : dict, time : time_range, partition : str) -> dict[str]:
    """ Get the different variables and values specific to front end ethernet readout.

    Args:
        url (str): Grafana url.
        datasources (dict): influx datasource.
        time (time_range): time range of test.
        partition (str): partition/session name.

    Returns:
        dict[str]: variables and their possible values.
    """
    query_str = f"SELECT \"sent_udp_count\", application, element, detector, crate, slot, queue FROM \"dunedaq.hermesmodules.opmon.LinkInfo\" WHERE session = '{partition}' AND time >= {time.start}s and time <= {time.end}s"

    response = queries.query_var_influx(url, datasource, query_str)

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


def get_dhs(url : str, datasource : dict, time : time_range, partition : str) -> dict[str]:
    """ Get the different variables and values specific to the datahandlers.

    Args:
        url (str): Grafana url.
        datasources (dict): influx datasource.
        time (time_range): time range of test.
        partition (str): partition/session name.

    Returns:
        dict[str]: variables and their possible values.
    """
    query_str = f"SELECT element FROM (SELECT \"sum_payloads\", element FROM \"dunedaq.datahandlinglibs.opmon.DataHandlerInfo\" WHERE time >= {time.start}s and time <= {time.end}s)"

    response = queries.query_var_influx(url, datasource, query_str)

    values = response["results"][0]["series"][0]["values"]

    DLH_names = []
    tphandler_names = []
    
    for v in values:
        if "DLH" in v[1]:
            DLH_names.append(v[1])
        if "tphandler" in v[1]:
            tphandler_names.append(v[1])

    return {"DLH" : np.unique(DLH_names), "tphandler" : np.unique(tphandler_names)}


def parse_result_postgres(response_data : dict, panel : dict) -> pd.DataFrame:
    warnings.warn("postgres data not yet implemented.")
    return pd.DataFrame({})


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

    if len(response_data["data"]["result"]) == 0:
        return pd.DataFrame()
    else:
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


def get_valid_datasources(datasources : list[dict], dunedaq_version : str) -> dict[dict]:
    """ Get the valid datasources that can be queried for the given dunedaq version.

    Args:
        datasources (list[dict]): list of all datasources.
        dunedaq_version (str): version string (format is vX.Y.Z).

    Returns:
        dict[dict]: datsources that can be queried
    """
    inf_id = get_influx_db_id(dunedaq_version)
    valid_datasources = {}
    for d in datasources:
        if (d["id"] == inf_id) or (d["type"] in ["prometheus", "postgres"]):
            valid_datasources[d["type"]] = d
    return valid_datasources


def extract_grafana_data(dashboard_info : dict[str], run_number : int, host : str, test_session : str, dunedaq_version : str, output_file : str, out_dir : str) -> list[str]:
    """ Extract data from Grafana dashboards.

    Args:
        dashboard_info (dict[str]): url, uid and sesssion names for the grafana page.
        run_number (int): run number of specific test.
        host (str): Host name.
        partition (str): Partition/session name of the test.
        output_file (str): Output file name.

    Returns:
        list[str]: List of the output files.
    """
    url = dashboard_info["grafana_url"]
    datasource_urls = queries.get_datasources(url) # gather list of all datasources

    valid_ds = get_valid_datasources(datasource_urls, dunedaq_version)
    ds_parser = {"influxdb" : parse_result_influx, "prometheus" : parse_result_prometheus, "postgres" : parse_result_postgres}

    time = get_run_time(url, valid_ds["influxdb"], run_number, test_session, dunedaq_version)

    print(f"{time=}")

    out_files = []
    for dashboard, session in zip(dashboard_info["dashboard_uid"], dashboard_info["session"]): # iterate over each dashboard
        var_map = collect_vars(url, valid_ds["influxdb"], run_number, time, session, host) # get list of relavent variables used by the dashboards

        panels = queries.get_grafana_panels(url, dashboard) # get panels from dashboard

        if not panels:
            print("no panels were found in the dashboard!")
            return

        panels, original_queries = format_panels(panels, var_map) # populate the panels with the variable values

        dashboard_data = {}
        for p, panel in enumerate(panels): # iterate over each panel
            panel_title = panel.get('title', '') # if a panel has not title ignore it (we wont know what the data is)
            if 'targets' not in panel: # if a panel has no target is does not have any data
                print(f'Skipping panel {panel_title}, with no targets.')
                continue
            data_type = panel["datasource"].get("type", None)
            if data_type is None:
                data_type = panel["datasource"].get("uid", None)
                if data_type:
                    data_type = data_type.replace("${", "").replace("}", "")

            if (data_type is None) and ("panels" in panel):
                if len(panel["panels"]) == 0:
                        data_type = panel["datasource"]["type"]
                else:
                    data_type = panel["panels"][0]["datasource"]["type"]

            if panel=='Runs': continue # unsure why this is skipped

            if not panel_title: continue

            # for now ignore tables at the first pass #TODO implement
            if ("resultFormat" in panel["targets"][0]) and (panel["targets"][0]["resultFormat"] == "table"): continue

            query_strs = queries.get_queries(panel) # get the query strings from the panel

            if len(query_strs) == 0: continue
            
            data_from_panel = {}
            for query_name, query in query_strs.items(): # loop over all queries

                response_data = queries.make_query(valid_ds[data_type], url, query, time) # make the query
                data_from_panel[query_name] = ds_parser[data_type](response_data, panel) # get the data from the response, will be specific to the datasource type

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

        for data in dashboard_data.values():
            if type(data) == "dict":
                for v in data.values():
                    if not v.empty:
                        break
            elif type(data) == pd.DataFrame and (not data.empty):
                break
            else:
                warnings.warn("no data was extracted from the dashboard. Check the data has not expired!")

        # Save the dataframes
        output = str(out_dir) + f"grafana-{dashboard}-{output_file}.hdf5"
        try:
            files.write_dict_hdf5(dashboard_data, output)
            out_files.append(output)
            print(f'Data saved to HDF5 successfully: {output}')
        except Exception as e:
            print(f'Exception Error: Failed to save data to HDF5: {str(e)}')

    return out_files
