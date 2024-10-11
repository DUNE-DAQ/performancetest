import os
import copy
import pathlib
import json
import re
import struct
import warnings
import pandas as pd
import tables
import numpy as np

from datetime import datetime as dt

from urllib.parse import urljoin, urlencode
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
from http.client import HTTPResponse

from rich import print

warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning) # cause screw pandas
warnings.simplefilter(action='ignore', category=tables.NaturalNameWarning) # cause screw pandas

not_alma9_os = ['np04srv008', 'np04srv010', 'np04srv014', 'np04srv023', 'np04onl003', 'np04srv007', 'np04srv009', 'np04crt001']

def write_dict_hdf5(dictionary : dict, file : str):
    """ Write dictionary to a HDF5 file.

    Args:
        dictionary (dict): dictionary to save
        file (str): file
    """
    with pd.HDFStore(file) as hdf:
        for k, v in dictionary.items():
            try:
                hdf.put(k, v)
            except Exception as e:
                print(f"cannot write {k} to file: {e}")
                pass
    return


def read_hdf5(file : str):
    """ Reads a HDF5 file and unpacks the contents into pandas dataframes.

    Args:
        file (str): file path.

    Returns:
        pd.DataFrame : if hdf5 file only has 1 key
        dict : if hdf5 file contains more than 1 key
    """
    keys = []
    with tables.open_file(file, driver = "H5FD_CORE") as hdf5file:
        for i in hdf5file.root:
            keys.append(i._v_pathname[1:])
            if type(i) == tables.group.Group:
                for j in hdf5file.root[i._v_pathname[1:]]:
                    if type(j) == tables.group.Group:
                        keys.append(j._v_pathname[1:])

    data = {}
    if len(keys) == 1:
        return pd.read_hdf(file)
    else:
        for k in keys:
            try:
                data[k] = pd.read_hdf(file, key = k)
            except:
                print(f"could not open {k}")
                pass
    return data


def urljson(response : HTTPResponse) -> dict | None:
    """Attempt to decode http content in json format.

    Args:
        response (HTTPResponse): http response.

    Returns:
        dict | None: dictionary of json, or None if content type does not match.
    """
    content_type = response.headers.get('Content-Type')
    if content_type == 'application/json':
        return json.loads(response.read())
    else:
        print(f'Warning: Response is not in JSON format. Content-Type: {content_type}')


def load_json(file : str | pathlib.Path) -> dict:
    """Open json file as dictionary.

    Args:
        file (str | pathlib.Path): json file to open.

    Returns:
        dict: loaded file.
    """
    with pathlib.Path(file).open("r") as f:
        return json.load(f)


def save_json(file : str | pathlib.Path, data : dict):
    """Save dictionary to json file.

    Args:
        file (str | pathlib.Path): path to save dictonary to.
        data (dict): dictionary to save.
    """
    with pathlib.Path(file).open("w") as f:
        json.dump(data, f, indent = 4)


def create_filename(test_args : dict, test_num : int) -> str:
    """Create filename based on the test report information.

    Args:
        test_args (dict): test report information.
        test_num (int): test number/index.

    Returns:
        str: filename.
    """
    return "-".join([
        test_args["dunedaq_version"].replace(".", "_"),
        test_args["host"].replace("-", ""),
        str(test_args["socket_num"][test_num]),
        test_args["data_type"],
        test_args["test_name"][test_num]
        ])


def current_time():
    now = dt.now()
    current_dnt = now.strftime('%Y-%m-%d %H:%M:%S')
    return current_dnt


def dt_to_unix_array(times : np.array):
    s = pd.to_datetime(pd.Series(times).str.replace("T", " ").str.replace("Z", " "))
    return (s - pd.Timestamp("1970-01-01")) // pd.Timedelta('1s')


def get_unix_timestamp(time_str):
    formats = ['%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S']
    for fmt in formats:
        try:
            timestamp = dt.strptime(time_str, fmt).timestamp()
            return int(timestamp * 1000) if '.' in time_str else int(timestamp)
        except ValueError:
            pass
    raise ValueError(f'Invalid time format: {time_str}')


def make_column_list(file, input_dir):
    data_frame = pd.read_csv(f'{input_dir}/{file}.csv')
    columns_list = list(data_frame.columns) 
    return columns_list


def date_num(d, d_base): 
    t_0 = d_base.toordinal() 
    t_1 = dt.fromordinal(t_0)
    T = (d - t_1).total_seconds()
    return T


def is_hidden(input_dir): 
    name = os.path.basename(os.path.abspath(input_dir))
    return True if name.startswith('.') else False


def make_file_list(input_dir):
    file_list =  []
    for root, dirs, files in os.walk(input_dir):
        for name in files:
            if is_hidden(name):  
                print (name, ' is hidden, trying to delete it')
                os.remove(os.path.join(input_dir, name))
            else:
                file_list.append(os.path.join(input_dir, name))
                
    return file_list


def make_name_list_benchmark(input_dir):
    l=os.listdir(input_dir)
    benchmark_list=[x.split('.')[0] for x in l]

    return benchmark_list


def make_name_list(input_dir):
    l=os.listdir(input_dir)
    name_list=[x.split('.')[0] for x in l]
    
    pcm_list, uprof_list, core_utilization_list, all_list = [], [], [], []
    
    for i, name_i in enumerate(name_list):
        if 'core_utilization-' in name_i: 
            core_utilization_list.append(name_i)
            
        elif 'uprof-' in name_i:
            uprof_list.append(name_i)
            all_list.append(name_i)
            
        elif 'grafana-' in name_i:
            pcm_list.append(name_i)
            all_list.append(name_i)
            
        else:
            pass

    return pcm_list, uprof_list, core_utilization_list, all_list


def create_var_list(file_list, var_list):
    files_srv_list = [] 
    for var_j in  var_list:
        tmp = []
        for name_i in file_list:
            tmp.append(name_i) if f'{var_j}' in name_i else print(var_j, 'not in ', name_i )

        files_srv_list.append(tmp)
        
    return files_srv_list


def reformat_cpu_util(file : str | pathlib.Path) -> pd.DataFrame:
    """Converts the output from the core utilisation into a pandas friendly format (and drops the average report).

    Args:
        file (str | pathlib.Path): core utilisation output file.

    Returns:
        pd.DataFrame: data frame of the formatted file
    """
    with pathlib.Path(file).open() as f:
        df = []
        for i, line in enumerate(f):
            if 'Average:'in line or 'all' in line or 'CPU' in line or '                      ' in line or i < 3:
                pass # skip extra headers and average metrics
            else:
                line = line.replace("\n", "")
                list_new = list(re.sub(' +', ' ', line).split(" ")) # get elements in each row in list format
                df.append(list_new)

    df = pd.DataFrame(df, columns = ["Timestamp","CPU","user (%)","nice (%)","system (%)","iowait (%)","steal (%)","idle (%)"])
    df = df.dropna() # drop emtpy lines from the dataframe

    ts = pd.to_datetime(df["Timestamp"])
    rel_time = (ts - ts[0]).dt.total_seconds() / 60 # calculate a relative time in units of fractional minutes
    rel_time.name = "NewTime"
    df = pd.concat([rel_time, df], axis = 1)

    df.CPU = df.CPU.astype(int) # ensure CPU number is integer type

    return df


def cpupins_utilazation_reformatted(input_dir, core_utilization_file):
    for file in core_utilization_file:
        f = open(f'{input_dir}/{file}.csv','r')
        f_new = open(f'{input_dir}/reformatted_{file}.csv','w')
        header = 'Timestamp,CPU,user (%),nice (%),system (%),iowait (%),steal (%),idle (%)\n'
        f_new.write(header)   
        
        for i, line in enumerate(f):
            if 'Average:'in line or 'all' in line or 'CPU' in line or '                      ' in line or i < 3:
                pass
            else:
                list_new = list(re.sub(' +', ' ', line).split(" "))
                formatted_line = ','.join(list_new)
                f_new.write(formatted_line)   

        print(f'New CSV file saved as: reformatted_{file}.csv')   


def fetch_grafana_panels(grafana_url : str, dashboard_uid : str) -> list[dict]:
    """Get grafana dashboard information.

    Args:
        grafana_url (str): grafana url.
        dashboard_uid (str): dashboard uid.

    Returns:
        list[dict]: list of each panel on the dashboard containing information required to make queries.
    """
    panels = []
    # Get dashboard configuration
    dashboard_url = urljoin(grafana_url, f"api/dashboards/uid/{dashboard_uid}")

    with urlopen(dashboard_url) as response:
        try:
            if response.status == 200:
                panels = urljson(response)['dashboard']['panels'] # Extract panels data
                return panels
        except HTTPError as e:
            print('Error code: ', e.code)
        except URLError as e:
            print('Reason: ', e.reason)


def get_query_urls(panel : dict) -> dict:

    targets = panel.get('targets', [])
    queries = {}

    for target in targets:
        if ('expr' in target) and (target["expr"] != ""):
            queries[target["legendFormat"]] = target["expr"]
        elif 'query' in target:
            queries[panel["title"]] = target["query"]
        elif 'rawSql' in target:
            print(target)
            queries[target["table"]] = target["rawSql"]

    return queries


def get_query_urls_old(panel : dict, host : str, partition : str, start_time : str, end_time : str) -> dict:
    """Get urls required to make queries to the datasource.

    Args:
        panel (dict): panel information.
        host (str): host machine name.
        partition (str): run control partition name.

    Returns:
        tuple[list, list | None]: list of urls and their labels if urls were found.
    """
    targets = panel.get('targets', [])

    queries = {}
    for target in targets:
        if ('expr' in target) and (target["expr"] != ""):
            for var in ['${host}', '$node']:
                if var in target['expr']:
                    query = target['expr'].replace(var, host)

            for uid in ['${DS_PROMETHEUS}', '${datasource}']:
                target['datasource']['uid'].replace(uid, partition)

            queries[target["legendFormat"]] = query

        elif 'query' in target:
            query = target['query'].replace('${partition}', partition)
            query = query.replace('${session}', partition)
            target['datasource']['uid'].replace('${influxdb}', partition)

            query = query.replace("$timeFilter", f"time >= {start_time}s and time <= {end_time}s") # apply time range within query (applicable for influxdb queries)

            query = query.replace("$__interval", "10s") # tick rata of plots, unsure why this is an environment variable

            queries[panel["title"]] = query
        
        elif 'rawSql' in target:
            query = target['rawSql'].replace('${partition}', partition)
            query = target['rawSql'].replace('${session}', partition)
            target['datasource']['uid'].replace('${influxdb}', partition)
            
            query = query.replace("${__from}", str(start_time))
            query = query.replace("${__to}", str(end_time))

            queries[target["legendFormat"]] = query
        
        else:
            print(f'Missing [expr , query, rawSql] in targets. Check the json file related to the dashboard.')
            pass

    return queries


def get_datasource_urls(grafana_url : str) -> list[str]:
    with urlopen(urljoin(grafana_url, "api/datasources")) as response:
        if response.status == 200:
            return urljson(response)
        else:
            raise Exception(f"http request resulted in code: {response.status_code}")


def get_datasource_url(grafana_url : str) -> str:
    """ Get the prometheus url through Grafana's api.

    Args:
        grafana_url (str): Dashboard url.

    Raises:
        Exception: http request fails.
        Exception: Datasource url was not found.

    Returns:
        str: Prometheus url.
    """

    with urlopen(urljoin(grafana_url, "api/datasources")) as response:
        if response.status == 200:
            datasources = urljson(response)
        else:
            raise Exception(f"http request resulted in code: {response.status_code}")

    for d in datasources:
        if d["name"] == "np04-daq": #? should the datasource name for operational monitoring always be np04-daq?
            return d["url"]
    raise Exception("datasource url for np04-daq not found.")


def query_data(datasource_urls : list[dict], grafana_url : str, query_url : str, start_time : str, end_time : str):
    response_data = None
    error = None
    for i in datasource_urls:
        if i["name"] in ["CERN IT Networking SNMP", "KluPrometheus"]: continue

        url_extension = "query"
        if i["type"] == "influxdb":
            # data for influxdb v1
            data = {
                "q" : query_url,
                "db" : i["jsonData"]["dbName"]
            }
        elif i["type"] == "prometheus":
            # data for prometheus query
            data = {
                'query': query_url,
                'start': start_time,
                'end': end_time,
                'step': 2
            }
            url_extension = "api/v1/query_range"
        elif i["type"] == "postgres":
            data = {
                "query" : query_url,
            }
        else:
            print("unknown database type")
            continue

        try:
            with urlopen(urljoin(grafana_url, f"api/datasources/proxy/uid/{i['uid']}/{url_extension}"), urlencode(data).encode()) as response:
                if response.status == 200:
                    response_data = urljson(response)
                    break
        except HTTPError as e:
            error = e
            pass
        except URLError as e:
            error = e
            pass
        except ValueError as e:
            error = e
            pass

    if not response_data:
        print(f"query could not be made to any database: {error}")


    return response_data


def make_names_str(names : list):
    names_str = "("
    for i, n in enumerate(names):
        if i == (len(names) - 1):
            names_str += f"{n})"
        else:
            names_str += f"{n}|"

    return names_str


def get_dpdk_vars(grafana_url, datasource_urls, start_time, end_time, partition):
    query_str = f'SELECT "bytes", application, queue FROM "dunedaq.dpdklibs.opmon.QueueEthXStats" WHERE session = \'{partition}\' AND time >= {start_time}s and time <= {end_time}s'

    response = query_var(grafana_url, datasource_urls, query_str, start_time)

    values = np.array(response["results"][0]["series"][0]["values"])
    
    values = {
        "application" : values[:, 2], # application
        "queue" : values[:, 3], # element
    }
    return {k : np.unique(v) for k, v in values.items()}


def get_fe_eth_vars(grafana_url, datasource_urls, start_time, end_time, partition):
    query_str = f"SELECT \"sent_udp_count\", application, element, detector, crate, slot, queue FROM \"dunedaq.hermesmodules.opmon.LinkInfo\" WHERE session = '{partition}' AND time >= {start_time}s and time <= {end_time}s"

    response = query_var(grafana_url, datasource_urls, query_str, start_time)

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


def get_dhs(grafana_url, datasource_urls, start_time, end_time, partition):

    query_str = f'SELECT element FROM (SELECT "sum_payloads", element FROM "dunedaq.datahandlinglibs.opmon.DataHandlerInfo" WHERE time >= {start_time}s and time <= {end_time}s)'

    response = query_var(grafana_url, datasource_urls, query_str, start_time)
    values = response["results"][0]["series"][0]["values"]

    DLH_names = []
    tphandler_names = []
    
    for v in values:
        if "DLH" in v[1]:
            DLH_names.append(v[1])
        if "tphandler" in v[1]:
            tphandler_names.append(v[1])

    return {"DLH" : np.unique(DLH_names), "tphandler" : np.unique(tphandler_names)}

def query_var(grafana_url, datasource_urls, query_str, start_time):

    for i in datasource_urls:
        if i["id"] != 11: continue
        data = {
            "q" : query_str,
            "db" : i["jsonData"]["dbName"]
        }
        try:
            with urlopen(urljoin(grafana_url, f"api/datasources/proxy/uid/{i['uid']}/query"), urlencode(data).encode()) as response:
                return urljson(response)
        except HTTPError as e:
            print(e)
    return


def dict_to_str(d : dict) -> str:
    return "".join([f"{k}:{v}," for k, v in d.items()])


def parse_result_influx(response_data : dict, panel : dict, iter_vals : dict) -> pd.DataFrame:
    parsed_results = {}

    if "series" in response_data["results"][0]:
        for i in response_data["results"][0]["series"]:
            if "tags" in i:
                if len(i["tags"]) > 1:
                    key = dict_to_str(i["tags"])
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
            entry = pd.DataFrame({"time" : dt_to_unix_array(v[:, 0]), k : v[:, 1]})
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


def is_collection(x : any) -> bool:
    return (type(x) != str) and hasattr(x, "__iter__")


def replace(x, target, value):
    if type(x) != str: return x

    if target in x:
        x = x.replace(f"${{{target}}}", value)
        x = x.replace(f"${target}", value)
    return x


def search_panel(d, action : callable, args : dict):
    if (type(d) == dict) and is_collection(d):
        for k in d:

            if k == "datasource" : d[k]["uid"] = None # we need to try each uid

            if is_collection(d):
                new = search_panel(d[k], action, args)
                d[k] = new
    elif is_collection(d):
        for i in range(len(d)):
            if is_collection(d[i]):
                new = search_panel(d[i], action, args)
                d[i] = new
    else:
        return action(d, **args)
    return d


def collect_vars(grafana_url, datasource_urls, start_time, end_time, partition, host) -> dict:

    vars_to_collect = {"dhs" : get_dhs, "fe" : get_fe_eth_vars, "dpdk" : get_dpdk_vars}

    collected_vars = {}
    for k, v in vars_to_collect.items():
        try:
            collected_vars[k] = v(grafana_url, datasource_urls, start_time, end_time, partition)
        except:
            print(f"cannot get {k} for session {partition}")

    var_map = {
        "host" : host, # only true is expr in target?
        "node" : host, # ""
        "parition" : partition,
        "session" : partition,
        "timeFilter" : f"time >= {start_time}s and time <= {end_time}s", # apply time range within query (applicable to influxdb queries)
        "__interval": "10s",
        "{__from}" : str(start_time),
        "{__to}" : str(end_time)
    }

    for v in collected_vars.values():
        var_map = var_map | v
    return var_map


def extract_vars(x):
    v = []
    for i in x.split("$")[1:]: # first part doesnt matter
        v.append(i.split(" ")[0].replace("{", "").replace("}", "").replace("'", "").replace("/", "")) # this is ugly
    return v


def format_panels(panels: list[dict], var_map : dict) -> tuple[list[dict], list[str]]:
    new_panels = []

    for panel in panels:
        if "title" not in panel: continue
        if "$" in panel["title"]: # variable has been found in panel title, this must be duplicated if any variables are a list
            dup = extract_vars(panel["title"])
            for k, v in var_map.items():
                if is_collection(v): # is the variable a list
                    if k in dup: # is it in the title
                        for i in v:
                            new_panels.append(search_panel(copy.deepcopy(panel), replace, {"target" : k, "value" : i})) # duplicate panel for each variable
        else:
            new_panels.append(copy.deepcopy(panel))

    original_queries = [get_query_urls(panel) for panel in new_panels]

    for panel in new_panels:
        for k, v in var_map.items():
            if is_collection(v): # is the variable a list
                search_panel(panel, replace, {"target" : k, "value" : make_names_str(v)}) # replace variable with its names_str
            else:
                search_panel(panel, replace, {"target" : k, "value" : v}) # replace variable with value
    return new_panels, original_queries


def extract_grafana_data(grafana_url, dashboard_uid, delta_time, host, partition, output_csv_file) -> str:

    datasource_urls = get_datasource_urls(grafana_url)
        
    start_time = get_unix_timestamp(delta_time[0])
    end_time = get_unix_timestamp(delta_time[1])

    var_map = collect_vars(grafana_url, datasource_urls, start_time, end_time, partition, host)

    out_files = []

    for dashboard_uid_to_use in dashboard_uid:
        panels = fetch_grafana_panels(grafana_url, dashboard_uid_to_use)

        if not panels:
            print('Error in extract_grafana_data: Failed to fetch dashboard panels data.')
            return

        panels, original_queries = format_panels(panels, var_map)

        dashboard_data = {}
        for p, panel in enumerate(panels):

            if 'targets' not in panel:
                print(f'Skipping panel {panel_title}, with no targets.')
                continue

            if "panels" in panel:
                if len(panel["panels"]) == 0:
                        data_type = panel["datasource"]["type"]
                else:
                    data_type = panel["panels"][0]["datasource"]["type"]
            else:
                data_type = panel["datasource"]["type"]

            if panel=='Runs': continue

            panel_title = panel.get('title', '')
            if not panel_title:
                continue

            if ("resultFormat" in panel["targets"][0]) and (panel["targets"][0]["resultFormat"] == "table"): continue

            query_urls = get_query_urls(panel)

            vars_in_query = [extract_vars(v) for v in original_queries[p].values()]

            if len(query_urls) == 0:
                print(f'Skipping panel {panel_title}, with no valid query URL')
                continue

            data_from_panel = {}
            for (query_name, query), var in zip(query_urls.items(), vars_in_query):

                iter_vals = {}
                for v in var:
                    iter_val = var_map.get(v)
                    if is_collection(iter_val):
                        iter_vals[v] = iter_val
                response_data = query_data(datasource_urls, grafana_url, query, start_time, end_time)

                if response_data:
                    if data_type == "prometheus":
                        data_from_panel[query_name] = parse_result_prometheus(response_data, query_name)
                        # dashboard_data[panel_title] = parse_result_prometheus(response_data, query_name)

                    elif data_type == "influxdb":
                        data_from_panel[query_name] = parse_result_influx(response_data, panel, iter_vals)
                        # dashboard_data[panel_title] = parse_result_influx(response_data, panel, iter_vals)

                    else:
                        print(f"not sure how to parse this data type: {data_type}")
            
            single_columns = all([len(data.columns) == 1 for data in data_from_panel.values() if data is not None])

            if single_columns:
                merged_df = None
                for k, v in data_from_panel.items():
                    if merged_df is None:
                        merged_df = v
                    else:
                        merged_df = pd.concat([merged_df, v], axis = 1)
                data_from_panel = merged_df
            elif len(data_from_panel) == 1:
                data_from_panel = list(data_from_panel.values())[0]
            else:
                print(f"don't know what to do for {panel_title}")
                pass

            if data_from_panel is None:
                dashboard_data[panel_title] = pd.DataFrame({})
            else:
                dashboard_data[panel_title] = data_from_panel

        print(dashboard_data)

        # Save the dataframes
        filename = output_csv_file.replace(".hdf5", "")
        output = f'grafana-{dashboard_uid_to_use}-{filename}.hdf5'
        try:
            write_dict_hdf5(dashboard_data, output)
            out_files.append(output)
            print(f'Data saved to HDF5 successfully: {output}')
        except Exception as e:
            print(f'Exception Error: Failed to save data to HDF5: {str(e)}')

    return out_files


def uprof_pcm_formatter(input_dir, file):
    f = open(f'{input_dir}/{file}.csv','r')
    f_new = open(f'{input_dir}/reformatted_{file}.csv','w')
    
    for line in f:
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
            header1 = line.split(',')
        if 'Timestamp' in line:
            header2 = line.split(',')[1:]

            package_num = '0'
            header_new = ['Timestamp']
            for package,header in zip(header1,header2):
                if (package=='\n') or (header=='\n'):
                    header_new += ['CPU Utilization', '\n']
                    header_new_str = ','.join(header_new)
                    f_new.write(header_new_str)
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
            line_list.append('\n')
            line_n = ','.join(line_list)
            f_new.write(line_n)   
            
    f.close()
    f_new.close()


def uprof_timechart_formatter(input_dir, file):
    f = open(f'{input_dir}/{file}.csv','r')
    f_new = open(f'{input_dir}/reformatted_{file}.csv','w')

    header = True
    for line in f:
        # get & reformat full date
        if 'Profile Start Time:' in line:
            full_date = line.split(',')[1]
            month = month2num(full_date[0:3])
            date = int(full_date[4:6])
            year = int(full_date[7:11])
            full_date_new = f'{year}-{month:02d}-{date:02d}'

        # Reformat timestamps
        if not header:
            timestamp_n = line.split(',')[1]
            timestamp_n = timestamp_n.split(':')
            hour_n = int(timestamp_n[0])
            min_n = int(timestamp_n[1])
            sec_n = int(timestamp_n[2])
            date_n = f',{full_date_new} {hour_n:02d}:{min_n:02d}:{sec_n:02d},'

            line_n = re.sub(',.*:.*:.*:...,', date_n, line)
            f_new.write(line_n)

        # header=False indicates next line is data
        if 'Timestamp' in line:
            header = False
            f_new.write(line)

    f.close()
    f_new.close()


def month2num(month_str):
    months = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
    return months[month_str] if month_str in months else print('Warning: invalid month')


def combine_time_and_uprof_files(input_dir, time_file, uprof_file):
    input_file0 = f'{input_dir}/{time_file}.csv'
    input_file1 = f'{input_dir}/{uprof_file}.csv'
        
    data_frame0 = pd.read_csv(input_file0) 
    data_frame1 = pd.read_csv(input_file1) 
    df_merged = data_frame0.merge(data_frame1, how='outer')
    
    output = f'{input_dir}/{uprof_file}.csv'
    try:
        df_merged.to_csv(output, index=False)
        print(f'Data saved to CSV successfully: {output}')
    except Exception as e:
        print(f'Error in combine_time_and_uprof_files: Failed to save data to CSV: {str(e)}')


def process_files(input_dir, process_pcm_files=False, process_uprof_files=False, process_core_files=False):
    pcm_file, uprof_file, core_utilization_file, all_files = make_name_list(input_dir)
    
    if process_pcm_files:
        for i, file_pcm_i in enumerate(pcm_file):
            add_new_time_format_old(input_dir, file_pcm_i)

    if process_uprof_files:
        for i, file_uprof_i in enumerate(uprof_file):
            uprof_pcm_formatter(input_dir, file_uprof_i)
            add_new_time_format_old(input_dir, f'reformatted_{file_uprof_i}')
    
    if process_core_files:
        cpupins_utilazation_reformatted(input_dir, core_utilization_file)
        for i, file_core_i in enumerate(core_utilization_file):
            add_new_time_format_utilization(input_dir, f'reformatted_{file_core_i}')
        
    print('Finish the processing of the data.')


def break_file_name(file):
    return file.split(".")[0].split("/")[-1].split('-')


def sanitize_label(label):
    return re.sub('_', ' ', label)


def check_OS(server):
    return 'CS8/C7' if server in not_alma9_os else 'Alma9'


def add_new_time_format(df : pd.DataFrame):
    rel_time = (df["Timestamp"] - df["Timestamp"][0]).dt.total_seconds() / 60
    rel_time.name = "NewTime"
    df = pd.concat([rel_time, df], axis = 1)
    return df


def add_new_time_format_old(input_dir, file):
    data_frame = pd.read_csv(f'{input_dir}/{file}.csv')  

    new_time=[]
    x_0 = data_frame['Timestamp'][0]
    d_0 = dt.strptime(x_0,'%Y-%m-%d %H:%M:%S')
    for index, value in enumerate(data_frame['Timestamp']):   
        d = dt.strptime(value,'%Y-%m-%d %H:%M:%S')
        d_new = (date_num(d, d_0)-date_num(d_0, d_0))/60.
        new_time.append(d_new) 

    data_frame.insert(0, 'NewTime', new_time, True)
    data_frame.to_csv(f'{input_dir}/{file}.csv', index=False)


def add_new_time_format_utilization(input_dir, file): 
    data_frame = pd.read_csv(f'{input_dir}/{file}.csv')  

    new_time=[]
    x_0_tmp = data_frame['Timestamp'][0]
    # x_0 = convert_to_24_hour_format(x_0_tmp)
    x_0 = x_0_tmp
    d_0 = dt.strptime(x_0,'%H:%M:%S')
    for index, value_tmp in enumerate(data_frame['Timestamp']):  
        # value = convert_to_24_hour_format(value_tmp)
        value = value_tmp
        d = dt.strptime(value,'%H:%M:%S')
        d_new = (date_num(d, d_0)-date_num(d_0, d_0))/60.
        new_time.append(d_new) 

    data_frame.insert(0, 'NewTime', new_time, True)
    data_frame.to_csv(f'{input_dir}/{file}.csv', index=False)   


def convert_to_24_hour_format(time_str):
    dt_object = dt.strptime(time_str, "%I:%M:%S %p")
    time_24_hour = dt_object.strftime("%H:%M:%S")
    
    return time_24_hour


def output_file_check(input_dir, file, output_dir, chunk_size):
    try:
        with open('{}/{}.out'.format(input_dir, file), 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                print(chunk)
                yield chunk  # Use a generator to yield data chunks

    except FileNotFoundError:
        print('The file {}/{}.out was not found'.format(output_dir, file))
    except Exception as e:
        print('An error occurred: {}'.format(str(e)))


def parse_data(data_chunk):
    if len(data_chunk) != 10:  # Adjust this length to match your actual data structure
        return None  # Handle incomplete data

    # Define a format string according to your data structure
    format_string = "Ih4s"  # Example format for a 4-byte unsigned int, 2-byte short, and 4-byte string
    # Unpack the binary data
    unpacked_data = struct.unpack(format_string, data_chunk)
    return unpacked_data
