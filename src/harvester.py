"""
Created on: 12/10/2024 22:35

Authors: Shyam Bhuller (University of Oxford), Matthew Man (University of Toronto), Danaisis Vargas Oliva (University of Toronto)

Description: Collect and parse data from the Grafana dashboards (The spice must flow).
"""
import asyncio
import aiohttp
import copy
import datetime
import multiprocessing
import re
import shutil
import tables
import warnings

import numpy as np
import pandas as pd

from rich import print

import files
import queries
import times
import utils

from times import time_range

warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning) # cause screw pandas
warnings.simplefilter(action='ignore', category=tables.NaturalNameWarning) # cause screw pandas


def get_influx_db_id(dunedaq_version : str) -> int:
    """ Get the correct influx database id, datbase is dependant on if the dunedaq version for the test is v4 or v5.
        Authors: Shyam Bhuller (University of Oxford)

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


def get_run_time(dashboard_info : dict[str], run_number : int, test_session : str, dunedaq_version : str) -> time_range:
    """ Get the start time and end time of the run.
        Authors: Shyam Bhuller (University of Oxford)

    Args:
        url (str): Grafana url.
        datasources (list[dict]): influx datasource.
        run_number (int): run number of the test.

    Returns:
        time_range: start and end times in unix time.
    """
    url = dashboard_info["grafana_url"]
    datasource = get_valid_datasources(queries.aquery_single(queries.get_datasources, url = url), dunedaq_version)["influxdb"]

    if utils.dunedaq_major_version(dunedaq_version) == 4:
        query_str = f"SELECT \"runno\" FROM \"dunedaq.rcif.runinfo.Info\" WHERE (\"partition_id\" = '{test_session}' AND \"runno\" = {run_number})"
    elif utils.dunedaq_major_version(dunedaq_version) == 5:
        query_str = f"SELECT \"run_number\" FROM \"dunedaq.rcif.opmon.RunInfo\" WHERE \"run_number\" = {run_number}"
    else:
        raise Exception(f"version {dunedaq_version} is not supported.")

    response = queries.aquery_single(queries.query_var_influx, url = url, datasource = datasource, query_str = query_str)
    # response = queries.query_var_influx(url, datasource, query_str)
    values = np.array(response["results"][0]["series"][0]["values"])
    t = values[values[:, 1].astype(int) == run_number][:, 0] # select times for the given run number
    utimes = times.dt_to_unix_array([t[0], t[-1]]).values # get the unix time for start and end times

    return time_range(start = min(utimes), end =max(utimes))


async def collect_vars(cs : aiohttp.ClientSession, url : str, datasource : dict, run_number : int, time : time_range, partition : str, host : str) -> dict:
    """ Collect relavent variables from the grafana dashboards. This is very specific to the DUNEDAQ,
        so this would be a likely failure point if operational monitoring changes.
        Authors: Shyam Bhuller (University of Oxford)

    Args:
        cs (aiohttp.ClientSession): open ClientSession from which to make the http request.
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
            collected_vars[k] = await v(cs, url, datasource, time, partition)
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


async def get_dpdk_vars(cs : aiohttp.ClientSession, url : str, datasource : dict, time : time_range, partition : str) -> dict[str]:
    """ Get the different variables and values specific to dpdklibs.
        Authors: Shyam Bhuller (University of Oxford)

    Args:
        cs (aiohttp.ClientSession): open ClientSession from which to make the http request.
        url (str): Grafana url.
        datasources (dict): influx datasource.
        time (time_range): time range of test.
        partition (str): partition/session name.

    Returns:
        dict[str]: variables and their possible values.
    """
    #* query string is unique to the dashboard
    query_str = f'SELECT "bytes", application, queue FROM "dunedaq.dpdklibs.opmon.QueueEthXStats" WHERE session = \'{partition}\' AND time >= {time.start}s and time <= {time.end}s'
    # 'SELECT "bytes", application, queue FROM "dunedaq.dpdklibs.opmon.QueueEthXStats" WHERE session = 'partition' AND time >= 1730819865s and time <= 1730820290s'

    response = await queries.query_var_influx(cs, url, datasource, query_str)
    # response = queries.query_var_influx(url, datasource, query_str)

    values = np.array(response["results"][0]["series"][0]["values"])

    values = {
        "application" : values[:, 2],
        "queue" : values[:, 3],
    }
    values = {k : np.unique(v) for k, v in values.items()}

    rx_queue_num = []
    for i in values["queue"]:
        if "rx" in i:
            rx_queue_num.append(re.findall(r"\d+", i))

    values["queue"] = np.array(rx_queue_num).flatten() # replace queues with just the rx variant

    return values


async def get_fe_eth_vars(cs : aiohttp.ClientSession, url : str, datasource : dict, time : time_range, partition : str) -> dict[str]:
    """ Get the different variables and values specific to front end ethernet readout.
        Authors: Shyam Bhuller (University of Oxford)

    Args:
        cs (aiohttp.ClientSession): open ClientSession from which to make the http request.
        url (str): Grafana url.
        datasources (dict): influx datasource.
        time (time_range): time range of test.
        partition (str): partition/session name.

    Returns:
        dict[str]: variables and their possible values.
    """
    query_str = f"SELECT \"sent_udp_count\", application, element, detector, crate, slot, queue FROM \"dunedaq.hermesmodules.opmon.LinkInfo\" WHERE session = '{partition}' AND time >= {time.start}s and time <= {time.end}s"

    response = await queries.query_var_influx(cs, url, datasource, query_str)
    # response = queries.query_var_influx(url, datasource, query_str)

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


async def get_dhs(cs : aiohttp.ClientSession, url : str, datasource : dict, time : time_range, partition : str) -> dict[str]:
    """ Get the different variables and values specific to the datahandlers.
        Authors: Shyam Bhuller (University of Oxford)

    Args:
        cs (aiohttp.ClientSession): open ClientSession from which to make the http request.
        url (str): Grafana url.
        datasources (dict): influx datasource.
        time (time_range): time range of test.
        partition (str): partition/session name.

    Returns:
        dict[str]: variables and their possible values.
    """
    query_str = f"SELECT element FROM (SELECT \"sum_payloads\", element FROM \"dunedaq.datahandlinglibs.opmon.DataHandlerInfo\" WHERE time >= {time.start}s and time <= {time.end}s)"

    response = await queries.query_var_influx(cs, url, datasource, query_str)
    # queries.query_var_influx(url, datasource, query_str)

    values = response["results"][0]["series"][0]["values"]

    DLH_names = []
    tphandler_names = []
    
    for v in values:
        if "DLH" in v[1]:
            DLH_names.append(v[1])
        if "tphandler" in v[1]:
            tphandler_names.append(v[1])

    return {"DLH" : np.unique(DLH_names), "tp_handler" : np.unique(tphandler_names)}


def parse_result_postgres(response_data : dict, name : str) -> pd.DataFrame:
    warnings.warn("postgres data not yet implemented.")
    return pd.DataFrame({})


def parse_result_influx(response_data : dict, name : str) -> pd.DataFrame:
    """ Parse the Grafana api reponse from the prometheus database and write the data into dataframes.
        Authors: Shyam Bhuller (University of Oxford)

    Args:
        response_data (dict): API response in json format.
        name (str): information from the panel the data was extracted from.

    Returns:
        pd.DataFrame: data in pandas DataFrame.
    """
    parsed_results = {}

    if response_data is None:
        return pd.DataFrame()

    if "series" in response_data["results"][0]:
        for i in response_data["results"][0]["series"]:
            if "tags" in i:
                if len(i["tags"]) > 1:
                    key = f'{i["tags"]}' # convert dictionary to string so the dataframe can be written to hdf5
                else:
                    key = list(i["tags"].values())[0]
                parsed_results[key] = np.array(i["values"])
            else:
                parsed_results[name] = np.array(i["values"])

    df = None
    for k, v in parsed_results.items():
        if v is None:
            entry = pd.DataFrame({"time" : [None], k : [None]})
        else:
            entry = pd.DataFrame({"time" : times.dt_to_unix_array(v[:, 0]), k : v[:, 1]})
            entry = entry.set_index("time")
            entry.set_index(entry.index.astype(int), inplace = True)
        if df is None:
            df = entry
        else:
            df = pd.concat([df, entry], axis = 1).astype(float)

    return df


def parse_result_prometheus(response_data : dict, name : str) -> pd.DataFrame:
    """ Parse the Grafana api reponse from the prometheus database and write the data into dataframes.
        Authors: Shyam Bhuller (University of Oxford), Matthew Man (University of Toronto), Danaisis Vargas Oliva (University of Toronto)

    Args:
        response_data (dict): API response in json format.
        name (str): Name of metric retreived.

    Returns:
        pd.DataFrame: data in pandas DataFrame.
    """
    parsed = {}

    if response_data is None:
        return pd.DataFrame()

    if len(response_data["data"]["result"]) == 0:
        return pd.DataFrame()
    else:
        for i, result in enumerate(response_data["data"]["result"]):
            if len(response_data["data"]["result"]) == 1:
                key = name
            else:
                key = name + f"_{i}"
            v = np.array(result["values"])
            parsed["time"] = v[:, 0]
            parsed[key] = v[:, 1]
        df = pd.DataFrame(parsed).set_index("time").astype(float)
        df.set_index(df.index.astype(int), inplace = True)
        return df


def format_panels(panels: list[dict], var_map : dict) -> tuple[list[dict], list[str]]:
    """ Replace all the variables with their respective values. If the variable is in the title, the panel is reproduced for each possible value.
        Authors: Shyam Bhuller (University of Oxford)

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
        Authors: Shyam Bhuller (University of Oxford)

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


def extract_node_exporter_data(dashboard_info : dict[str], host : str, time : str, dunedaq_version : str, output_file : str, out_dir : str):
    """ Extract node exporter data form the prometheus database directly i.e. not through the Grafana api.
        Authors: Shyam Bhuller (University of Oxford)

    Args:
        dashboard_info (dict[str]): url, uid and sesssion names for the grafana page.
        run_number (int): run number of specific test.
        host (str): Host name.
        partition (str): Partition/session name of the test.
        output_file (str): Output file name.
        out_dir (str): Directory to write files to.
    """
    query_dict = {
        "CPU Usage (%)" : f"100 * (1 - irate(node_cpu_seconds_total{{nodename=\"{host}\", mode=\"idle\"}}[10m]))",

        "Total Memory (B)" : f"node_memory_MemTotal_bytes{{nodename=\"{host}\"}}",
        "Available Memory (B)" : f"node_memory_MemAvailable_bytes{{nodename=\"{host}\"}}",
        "Memory Usage (%)" : f"100 * (node_memory_MemTotal_bytes{{nodename=\"{host}\"}} - node_memory_MemAvailable_bytes{{nodename=\"{host}\"}}) / node_memory_MemTotal_bytes{{nodename=\"{host}\"}}",

        "Network Speed (B) " : f"node_network_speed_bytes{{nodename=\"{host}\"}}",
        "Network MTU (B)" : f" node_network_mtu_bytes{{nodename=\"{host}\"}}",
        "Softnet Packets Processed (pps)" : f"irate(node_softnet_processed_total{{nodename=\"{host}\"}}[10m])",
        "Softnet Packets Dropped (pps) "  : f"irate(node_softnet_dropped_total{{nodename=\"{host}\"}}[10m])",
        "Softnet Packets Squeezed (pps)"  : f"irate(node_softnet_times_squeezed_total{{nodename=\"{host}\"}}[10m])",

        "Disk Total Written (B)" : f"node_disk_written_bytes_total{{nodename=\"{host}\"}}",
        "Disk Written (Bps)" : f"irate(node_disk_written_bytes_total{{nodename=\"{host}\"}}[10m])",
        "Disk IO time (s)"   : f"node_disk_io_time_seconds_total{{nodename=\"{host}\"}}",
        "Disk Read (Bps) "   : f"irate(node_disk_read_bytes_total{{nodename=\"{host}\"}}[10m])",
    }

    rt = ["bytes", "packets", "fifo", "errs", "drop", "compressed"]
    t = ["queue_length", "carrier", "colls"]
    r = ["frame"]

    cpu_times = ["idle", "iowait", "irq", "nice", "softirq", "steal", "system", "user"]
    for i in cpu_times:
        query_dict[f"CPU {i} (s)"] = f"node_cpu_seconds_total{{nodename=\"{host}\", mode=\"{i}\"}}"

    names = {
        "bytes" : "(Bps)",
        "packets" : "(pps)",
        "fifo" : "FIFO (pps)",
        "errs" : "Errors (pps)",
        "drop" : "Dropped (pps)",
        "colls" : "Colls (counter)",
        "compressed" : "Compressed (pps)",
        "carrier" : "Carrier (counts)",
        "queue_length" : "Queue Length (pps)",
        "frame" : "Frame (pps)",
    }

    for i in ["receive", "transmit"]:
        if i == "receive":
            metrics = rt + r
            suffix = "received"
        if i == "transmit":
            metrics = rt + t
            suffix = "transmitted"
        for m in metrics:
            name = f"Network {suffix} {names[m]}"
            query = f"node_network_{i}_{m}_total{{nodename=\"{host}\"}}"
            if "ps" in name:
                query = f"irate({query}[10m])"
            query_dict[name] = query

    url = dashboard_info["grafana_url"]

    valid_ds = get_valid_datasources(queries.aquery_single(queries.get_datasources, url = url), dunedaq_version)
    prometheus_url = valid_ds["prometheus"]["url"]

    # time = get_run_time(url, valid_ds["influxdb"], run_number, test_session, dunedaq_version)

    print(f"{time=}")

    dfs = {}
    for query in query_dict:
        response = queries.query_prometheus(prometheus_url, query_str = query_dict[query], time_range = time)
        metrics = {}
        values = []

        # get the metrics and values for each sample
        if len(response["data"]["result"]) == 0:
            dfs[query] = pd.DataFrame()

        for r in response["data"]["result"]:
            for k in r["metric"]:
                if k not in metrics:
                    metrics[k] = [r["metric"][k]]
                else:
                    metrics[k].append(r["metric"][k])
            values.append(np.array(r["values"]))

        # construct a sample name from the metrics
        tags = {}
        for k in metrics:
            if len(np.unique(metrics[k])) > 1:
                tags[k] = metrics[k]

        sample_label = None
        name = None
        for k, v in tags.items():
            if sample_label is None:
                sample_label = np.array(v)
                name = k
            else:
                sample_label = np.char.add(np.char.add(sample_label, "_"), np.array(v))
                name = name + "_" + k

        if sample_label is None: sample_label = ["total"]

        # construct the dataframe
        parsed = {}
        for s, v in zip(sample_label, values):
            parsed["time"] = v[:, 0]
            parsed[s] = v[:, 1]

        if len(parsed) != 0:
            dfs[query] = pd.DataFrame(parsed).set_index("time").astype(float)
            dfs[query].set_index(dfs[query].index.astype(int), inplace = True)
        else:
            warnings.warn(f"no data found for {query}")
            dfs[query] = pd.DataFrame()

    print(dfs)
    output = str(out_dir) + f"node-exporter-{output_file}.hdf5"
    try:
        files.write_dict_hdf5(dfs, output)
        print(f'Data saved to HDF5 successfully: {output}')
    except Exception as e:
        print(f'Exception Error: Failed to save data to HDF5: {str(e)}')
    return


def format_hdf_keys(dashboard_data : dict[pd.DataFrame]):
    """ Format keys so they do not break the file structure in hdf5.
        Authors: Shyam Bhuller (University of Oxford)

    Args:
        dashboard_data (dict[pd.DataFrame]): dashboard data to be written to hdf5.
    """
    for k in list(dashboard_data):
        if "/" in k: # / is used to break items in to subdirectories in hdf5.
            if k.split("/")[0].find("(") > 0:
                rep = " per "
            else:
                rep = " "
            dashboard_data[k.replace("/", rep)] = dashboard_data.pop(k)
    return


def run_mp(args : tuple):
    """ Simple function to run extract_grafana_data (as multiprocessing will not allow nested functions).

    Args:
        args (tuple): Function arguments.
    """
    asyncio.run(extract_grafana_data(*args))
    return

@utils.timer
def extract_daq_dashboards(dashboard_info : dict[str], run_number : int, host : str, time : times.time_range, dunedaq_version : str, output_file : str, out_dir : str):
    """ Extract data from the DAQ grafana dashboards.

    Args:
        dashboard_info (str): url, uid and sesssion names for the grafana page.
        run_number (int): run number of specific test.
        host (str): Host name.
        partition (str): Partition/session name of the test.
        output_file (str): Output file name.
        out_dir (str): Directory to write files to.
    """
    print(f"{time=}")
    url = dashboard_info["grafana_url"]

    valid_ds = get_valid_datasources(queries.aquery_single(queries.get_datasources, url = url), dunedaq_version)
    ds_parser = {"influxdb" : parse_result_influx, "prometheus" : parse_result_prometheus, "postgres" : parse_result_postgres}

    pool = multiprocessing.Pool(len(dashboard_info["dashboard_uid"]))
    args = []
    for dashboard, session in zip(dashboard_info["dashboard_uid"], dashboard_info["session"]):
        args.append([[dashboard, session, url, run_number, host, time, valid_ds, ds_parser, output_file, out_dir]])

    result = pool.starmap_async(run_mp, args)
    result.get()
    return


async def extract_grafana_data(dashboard : str, session : str, url : str, run_number : int, host : str, time : times.time_range, valid_ds : dict, ds_parser : dict[callable], output_file : str, out_dir : str):
    """ Extract data from grafana dashboards.
        Authors: Shyam Bhuller (University of Oxford), Matthew Man (University of Toronto), Danaisis Vargas Oliva (University of Toronto)

    Args:
        dashboard (str): Dashboard name.
        session (str): Run session.
        url (str): Grafana dashboard url.
        run_number (int): Run number.
        host (str): Host name.
        time (times.time_range): Time elapsed during the run.
        valid_ds (dict): Datasources that can be queried from.
        ds_parser (dict[callable]): Functions to parse various datasources based on the database type.
        output_file (str): Output file name.
        out_dir (str): Directory to write files to.
    """
    async with aiohttp.ClientSession() as cs:
        var_map = await collect_vars(cs, url, valid_ds["influxdb"], run_number, time, session, host) # get list of relavent variables used by the dashboards

        panels = await queries.get_grafana_panels(cs, url, dashboard)
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
                response_data = await queries.make_query(cs, valid_ds[data_type], url, query, time) # make the query
                data_from_panel[query_name] = ds_parser[data_type](response_data, query_name) # get the data from the response, will be specific to the datasource type

            # organise the DataFrames to save to file
            single_columns = all([len(data.columns) == 1 for data in data_from_panel.values() if data is not None]) # check the panel returned multiple query DataFrames with a single column

            # if each query is a dataframe with single columns
            if single_columns:
                element_names = [data.columns[0] for data in data_from_panel.values() if data is not None]
                if len(element_names) > 0:
                    single_elements = element_names.count(element_names[0]) == len(element_names)

                    if single_elements:
                        for k, v in data_from_panel.items():
                            v.rename(columns = {element_names[0] : k}, inplace = True)

            # condense data for panels which returned multiple DataFrames
            merged_df = None
            for v in data_from_panel.values():
                if merged_df is None:
                    merged_df = v
                else:
                    merged_df = pd.concat([merged_df, v], axis = 1)

            if merged_df is None:
                dashboard_data[panel_title] = pd.DataFrame({})
            else:
                try:
                    dashboard_data[panel_title] = merged_df.astype(float).sort_index() # make sure data is kept in time order
                except ValueError:
                    dashboard_data[panel_title] = merged_df.sort_index()

    for data in dashboard_data.values():
        if type(data) == "dict":
            for v in data.values():
                if not v.empty:
                    break
        elif (type(data) == pd.DataFrame) and (not data.empty):
            break
        else:
            warnings.warn(f"no data was extracted from the dashboard {dashboard}. Check the data has not expired!")

    format_hdf_keys(dashboard_data)
    # print(dashboard_data)

    # Save the dataframes
    output = str(out_dir) + f"grafana-{dashboard}-{output_file}.hdf5"
    try:
        files.write_dict_hdf5(dashboard_data, output)
        print(f'Data saved to HDF5 successfully: {output}')
    except Exception as e:
        print(f'Exception Error: Failed to save data to HDF5: {str(e)}')

    return


def uprof_to_df(file : str) -> pd.DataFrame:
    """ Convert a uProf output file to a DataFrame.

    Args:
        file (str): uProf output file.

    Returns:
        pd.DataFrame: Formatted data.
    """
    formatted = {"pcm" : [], "power" : []}

    timechart = False
    timechart_header = True
    with open(file, 'r') as f:
        for line in f:
            if "AMDPROFILER POWER PROFILE REPORT" in line: timechart = True
            if not timechart:
                #* pcm stats
                # extract initial time
                if 'Profile Time:' in line:
                    full_date = line[14:-1]
                    full_date = full_date.replace('/', '-')
                    msec0 = int(full_date[20:23])
                    sec0  = int(full_date[17:19])
                    min0  = int(full_date[14:16])
                    hour0 = int(full_date[11:13])
                    day0  = int(full_date[8:10])
                
                # append package numbers to headers,
                if 'Package' in line:
                    header1 = line.split(',')[1:]
                if 'Timestamp' in line:
                    header2 = line.split(',')[1:]

                    package_num = '0'
                    header_new = ['Timestamp']
                    for package,header in zip(header1,header2):
                        if (package=='\n') or (header=='\n'):
                            header_new += ['CPU Utilization']
                            header_new_str = ','.join(header_new)
                            formatted["pcm"].append(header_new_str)
                        if 'Package' in package:
                            package_num = package[-1]
                        header_new += [header+' Socket' + package_num]

                # generate full timestamps
                if re.search('..:..:..:...,', line):
                    msec_n_old = int(line[9:12])
                    sec_n_old = int(line[6:8])
                    min_n_old = int(line[3:5])
                    hour_n_old = int(line[0:2])
                    
                    msec_n = (msec_n_old + msec0) % 1000
                    msec_carryover = (msec_n_old + msec0) // 1000
                    sec_n  = (sec_n_old + sec0 + msec_carryover) % 60
                    sec_carryover  = (sec_n_old + sec0 + msec_carryover) // 60
                    min_n  = (min_n_old + min0 + sec_carryover) % 60
                    min_carryover = (min_n_old + min0 + sec_carryover) // 60
                    hour_n = (hour_n_old + hour0 + min_carryover) % 24
                    hour_carryover = (hour_n_old + hour0 + min_carryover) // 24
                    day_n  = (day0 + hour_carryover)
                    date_n = f'{full_date[0:7]}-{day_n:02d} {hour_n:02d}:{min_n:02d}:{sec_n:02d}'
                    line_n = re.sub('..:..:..:...', date_n, line)
                    line_list = line_n.split(',')

                    # CPU Utilization
                    cpu_utiliz = float(line_list[1]) + float(line_list[22])
                    cpu_utiliz = str(round(cpu_utiliz, 2))
                    line_list[-1] = cpu_utiliz
                    # line_list.append('\n')
                    line_n = ','.join(line_list)
                    formatted["pcm"].append(line_n)
            else:
                #* timechart parsing for power stats
                # get & reformat full date
                if 'Profile Start Time:' in line:
                    full_date = line.split(',')[1]
                    month = times.month2num(full_date[0:3])
                    date = int(full_date[4:6])
                    year = int(full_date[7:11])
                    full_date_new = f'{year}-{month:02d}-{date:02d}'

                # Reformat timestamps
                if not timechart_header:
                    timestamp_n = line.split(',')[1]
                    timestamp_n = timestamp_n.split(':')
                    hour_n = int(timestamp_n[0])
                    min_n = int(timestamp_n[1])
                    sec_n = int(timestamp_n[2])
                    date_n = f',{full_date_new} {hour_n:02d}:{min_n:02d}:{sec_n:02d},'

                    line_n = re.sub(',.*:.*:.*:...,', date_n, line)
                    formatted["power"].append(line_n)

                # header=False indicates next line is data
                if 'Timestamp' in line:
                    timechart_header = False
                    formatted["power"].append(line)

    df = {k : [] for k in formatted}
    for k, v in formatted.items():
        for f in v:
            df[k].append(f.split(","))

    for k, v in df.items():
        df[k] = pd.DataFrame(v[1:], columns=v[0])
        df[k].set_index("Timestamp", inplace = True)

        # hack to ensure timezones matches the timezone from gafana (timezone of the server).
        tz = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
        t = pd.to_datetime(df[k].index).tz_localize(tz)
        t = (t - pd.Timestamp("1970-01-01").tz_localize("UTC")) // pd.Timedelta('1s')

        df[k] = df[k].set_index(t)
        df[k] = df[k].astype(float)
    return df


def extract_uprof_data(uprof_output : str, run_time : times.time_range, output_file : str, out_dir : str):
    """ Write uProf output to hdf5 file.

    Args:
        uprof_output (str): uProf output file.
        output_file (str): Output file name.
        out_dir (str): Output diretory.
    """
    dfs = uprof_to_df(uprof_output)

    for k in dfs:
        dfs[k] = times.match_times(dfs[k], run_time)

    for k, v in dfs.items():
        output = str(out_dir) + f"uprof-{k}-{output_file}.hdf5"
        v.to_hdf(output, key = "df")
        print(f'Data saved to HDF5 successfully: {output}')
    try:
        shutil.copy(uprof_output, out_dir + files.pathlib.Path(uprof_output).name)
        print("uProf output copied to output directory.")
    except shutil.SameFileError:
        print("uProf output already copied to output directory.")
    return