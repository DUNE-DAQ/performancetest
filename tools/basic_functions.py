import os
import pathlib
import json
import re
import struct
import pandas as pd

from datetime import datetime as dt

from urllib.parse import urljoin, urlencode
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
from http.client import HTTPResponse

from rich import print

not_alma9_os = ['np04srv008', 'np04srv010', 'np04srv014', 'np04srv023', 'np04onl003', 'np04srv007', 'np04srv009', 'np04crt001']


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


def get_query_urls(panel : dict, host : str, partition : str) -> tuple[list, list | None]:
    """Get urls required to make queries to the datasource.

    Args:
        panel (dict): panel information.
        host (str): host machine name.
        partition (str): run control partition name.

    Returns:
        tuple[list, list | None]: list of urls and their labels if urls were found.
    """
    targets = panel.get('targets', [])
    queries = []
    queries_label = []
    for target in targets:
        if 'expr' in target:
            for var in ['${host}', '$node']:
                if var in target['expr']:
                    query = target['expr'].replace(var, host)

            for uid in ['${DS_PROMETHEUS}', '${datasource}']:
                target['datasource']['uid'].replace(uid, partition)

            queries.append(query)
            queries_label.append(target['legendFormat'])

        elif 'query' in target:
            query = target['query'].replace('${partition}', partition)
            target['datasource']['uid'].replace('${influxdb}', partition)
            
            queries.append(query)
            queries_label.append(target['refId'])
        
        elif 'rawSql' in target:
            query = target['rawSql'].replace('${partition}', partition)
            target['datasource']['uid'].replace('${influxdb}', partition)
            
            queries.append(query)
            queries_label.append(target['refId'])
        
        else:
            print(f'Missing [expr , query, rawSql] in targets. Check the json file related to the dashboard.')
            pass

    return queries, queries_label if queries else None


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


def extract_grafana_data(grafana_url, dashboard_uid, delta_time, host, partition, output_csv_file):
    for dashboard_uid_to_use in dashboard_uid:
        panels_data = fetch_grafana_panels(grafana_url, dashboard_uid_to_use)
        if not panels_data:
            print('Error in extract_grafana_data: Failed to fetch dashboard panels data.')
            return
        
        if grafana_url == 'http://np04-srv-009.cern.ch:3000':
            url = urljoin(grafana_url, "api/datasources/proxy/1/api/v1/query_range")
        
        else:
            url = urljoin(get_datasource_url(grafana_url), "api/v1/query_range")

        start_timestamp = get_unix_timestamp(delta_time[0])
        end_timestamp = get_unix_timestamp(delta_time[1])
        all_dataframes = []

        for panel_i, panel in enumerate(panels_data):
            if panel=='Runs':
                continue
            
            else:
                panel_title = panel.get('title', '')
                if not panel_title:
                    print(f'Skipping panel with no title.')
                    continue
                    
                if 'targets' not in panel:
                    print(f'Skipping panel {panel_title}, with no targets.')
                    continue

                query_urls, queries_labels = get_query_urls(panel, host, partition)

                if not query_urls:
                    print(f'Skipping panel {panel_title}, with no valid query URL')
                    continue

                for i, query_url in enumerate(query_urls):
                    try:
                        column_label = queries_labels[i] # type: ignore
                        column_name = f'{column_label} {panel_title}'
                    except KeyError:
                        continue

                    data = {
                        'query': query_url,
                        'start': start_timestamp,
                        'end': end_timestamp,
                        'step': 2
                    }
                    with urlopen(url, urlencode(data).encode()) as response:
                        response_data = urljson(response)

                        if response.status != 200:
                            print('Error in extract_grafana_data: Failed to fetch dashboard data.')
                            print(f'Status code:content {response.status_code}:{response.content}')
                            print(f'Response panel:data:content for panel {panel_title}:{response_data}')
                            return None

                        if 'data' not in response_data or 'resultType' not in response_data['data'] or response_data['data']['resultType'] != 'matrix':
                            print(f'Skipping query with no valid response in panel: {panel_title}')
                            continue

                        result = response_data['data']['result']
                        if not result:
                            print(f'Skipping query with no result in panel: {panel_title}')
                            continue

                        result = result[0]
                        values = result.get('values', [])
                        values_without_first_column = [row[1:] for row in values]

                        if not values:
                            print(f'Skipping query with no valid response in panel: {panel_title}')
                            continue

                        df_first = pd.DataFrame(values, columns=['Timestamp', column_name])
                        df_first['Timestamp'] = pd.to_datetime(df_first['Timestamp'], unit='s')
                        df = pd.DataFrame(values_without_first_column, columns=[column_name])

                        df_tmp = df_first if panel_i == 0 and i == 0 else df
                        all_dataframes.append(df_tmp)

        # Combine all dataframes into a single dataframe
        combined_df = pd.concat(all_dataframes, axis=1)
        combined_df = add_new_time_format(combined_df)

        print(combined_df)

        # Save the combined dataframe as a CSV file
        filename = output_csv_file.replace(".csv", "")
        output = f'grafana-{filename}.csv'
        try:
            combined_df.to_csv(output, index=False)
            print(f'Data saved to CSV successfully: {output}')
        except Exception as e:
            print(f'Exception Error: Failed to save data to CSV: {str(e)}')


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
