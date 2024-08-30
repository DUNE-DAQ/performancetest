import os
import sys
import csv
#import time
#import glob
import json
import re
#import shutil
#import subprocess
import requests
#import getpass
import matplotlib
import matplotlib.pyplot as plt 
#import matplotlib.cm as cm
#import matplotlib.colors as mcolors
#import matplotlib.dates as mdates
import numpy as np
#import pickle as pkl
import pandas as pd
from pathlib import Path
from datetime import datetime as dt
from dateutil.parser import parse
from tabulate import tabulate
import struct
import warnings
warnings.simplefilter('default', DeprecationWarning)
from fpdf import FPDF 
from fpdf.enums import XPos, YPos
from PIL import Image

color_list = ['red', 'blue', 'green', 'cyan', 'orange', 'navy', 'magenta', 'lime', 'purple', 'hotpink', 'olive', 'salmon', 'teal', 'darkblue', 'darkgreen', 'darkcyan', 'darkorange', 'deepskyblue', 'darkmagenta', 'sienna', 'chocolate'] 
linestyle_list = ['solid', 'dotted', 'dashed', 'dashdot','solid', 'dotted', 'dashed', 'dashdot']
marker_list = ['s','o','.','p','P','^','<','>','*','+','x','X','d','D','h','H'] 
not_alma9_os = ['np04srv008', 'np04srv010', 'np04srv014', 'np04srv023', 'np04onl003', 'np04srv007', 'np04srv009', 'np04crt001']

def directory(input_dir):
    for dir_path in input_dir:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

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

def cpupins_utilazation_reformatted(input_dir, core_utilization_file):
    for file in core_utilization_file:
        f = open(f'{input_dir}/{file}.csv','r')
        f_new = open(f'{input_dir}/reformatted_{file}.csv','w')
        header = 'Timestamp,CPU,user (%),nice (%),system (%),iowait (%),steal (%),idle (%)'
        f_new.write(header)   
        
        for i, line in enumerate(f):
            if 'Average:'in line or 'all' in line or 'CPU' in line or '                      ' in line or i < 3:
                pass
            else:
                list_new = list(line.split("    "))
                formatted_line = ','.join(list_new)
                f_new.write(formatted_line)   

        print(f'New CSV file saved as: reformatted_{file}.csv')   

def fetch_grafana_panels(grafana_url, dashboard_uid):
    panels = []
    # Get dashboard configuration
    dashboard_url = f'{grafana_url}/api/dashboards/uid/{dashboard_uid}' 
    
    try:
        response = requests.get(dashboard_url)
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type')

            if content_type and 'application/json' in content_type:
                dashboard_data = response.json()  
                panels = dashboard_data['dashboard']['panels']        # Extract panels data
                return panels
            else:
                print(f'Warning: Response is not in JSON format. Content-Type: {content_type}')
                html_content = response.text
                
        else:
            print(f'Error in fetch_grafana_panels: Failed to fetch dashboard data. Status code: {response.status_code}')
        
    except requests.exceptions.RequestException as e:
        print(f'Error: Request failed with the following exception: {e}')

def get_query_urls(panel, host, partition, grafana_url):
    targets = panel.get('targets', [])
    queries = []
    queries_label = []
    for target in targets:
        if 'expr' in target:
            if grafana_url == 'http://np04-srv-009.cern.ch:3000':
                query = target['expr'].replace('${host}', host)
            
            elif grafana_url == 'http://np04-srv-017.cern.ch:31023':
                query = target['expr'].replace('$node', host)
                datasource_uid = target['datasource']['uid'].replace('${DS_PROMETHEUS}', partition)
            
            elif grafana_url == 'http://http://np04-srv-017:31003':
                query = target['expr'].replace('$node', host)
                datasource_uid = target['datasource']['uid'].replace('${datasource}', partition)
            
            else:
                print(f'Error in url, not a valid grafana_url {grafana_url}')
                pass
        
            queries.append(query)
            queries_label.append(target['legendFormat'])
        
        elif 'query' in target:
            query = target['query'].replace('${partition}', partition)
            datasource_uid = target['datasource']['uid'].replace('${influxdb}', partition)
            
            queries.append(query)
            queries_label.append(target['refId'])
        
        elif 'rawSql' in target:
            query = target['rawSql'].replace('${partition}', partition)
            datasource_uid = target['datasource']['uid'].replace('${influxdb}', partition)
            
            queries.append(query)
            queries_label.append(target['refId'])
        
        else:
            print(f'Missing [expr , query, rawSql] in targets. Check the json file related to the dashboard.')
            pass

    return queries, queries_label if queries else None

def extract_grafana_data(datasource_url, grafana_url, dashboard_uid, delta_time, host, partition, input_dir, output_csv_file):
    for dashboard_uid_to_use in dashboard_uid:
        panels_data = fetch_grafana_panels(grafana_url, dashboard_uid_to_use)
        if not panels_data:
            print('Error in extract_data_and_stats_from_panel: Failed to fetch dashboard panels data.')
            return
        
        if grafana_url == 'http://np04-srv-009.cern.ch:3000':
            url = f'{grafana_url}/api/datasources/proxy/1/api/v1/query_range'
        
        else:
            url = f'{datasource_url}/api/v1/query_range'
            
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

                query_urls, queries_labels = get_query_urls(panel, host, partition, grafana_url)

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

                    response = requests.post(url, data=data)
                    response_data = response.json()

                    if response.status_code != 200:
                        print('Error in extract_data_and_stats_from_panel: Failed to fetch dashboard data.')
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
                    metric = result['metric']
                    values = result.get('values', [])
                    values_without_first_column = [row[1:] for row in values]

                    if not values:
                        print(f'Skipping query with no valid response in panel: {panel_title}')
                        continue

                    timestamps = [val[0] for val in values]
                    df_first = pd.DataFrame(values, columns=['Timestamp', column_name])
                    df_first['Timestamp'] = pd.to_datetime(df_first['Timestamp'], unit='s')
                    df = pd.DataFrame(values_without_first_column, columns=[column_name])

                    df_tmp = df_first if panel_i == 0 and i == 0 else df
                    all_dataframes.append(df_tmp)

        # Combine all dataframes into a single dataframe
        combined_df = pd.concat(all_dataframes, axis=1)

        # Save the combined dataframe as a CSV file
        output = f'{input_dir}/grafana-{output_csv_file}.csv'
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
            add_new_time_format(input_dir, file_pcm_i)

    if process_uprof_files:
        for i, file_uprof_i in enumerate(uprof_file):
            uprof_pcm_formatter(input_dir, file_uprof_i)
            add_new_time_format(input_dir, f'reformatted_{file_uprof_i}')
    
    if process_core_files:
        cpupins_utilazation_reformatted(input_dir, core_utilization_file)
        for i, file_core_i in enumerate(core_utilization_file):
            add_new_time_format_utilization(input_dir, f'reformatted_{file_core_i}')
        
    print('Finish the processing of the data.')

def break_file_name(file):
    return file.split('-')

def sanitize_label(label):
    return re.sub('_', ' ', label)

def check_OS(server):
    return 'CS8/C7' if server in not_alma9_os else 'Alma9'

def add_new_time_format(input_dir, file):
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
    x_0 = convert_to_24_hour_format(x_0_tmp)
    d_0 = dt.strptime(x_0,'%H:%M:%S')
    for index, value_tmp in enumerate(data_frame['Timestamp']):  
        value = convert_to_24_hour_format(value_tmp)
        d = dt.strptime(value,'%H:%M:%S')
        d_new = (date_num(d, d_0)-date_num(d_0, d_0))/60.
        new_time.append(d_new) 

    data_frame.insert(0, 'NewTime', new_time, True)
    data_frame.to_csv(f'{input_dir}/{file}.csv', index=False)   

def convert_to_24_hour_format(time_str):
    dt_object = dt.strptime(time_str, "%I:%M:%S %p")
    time_24_hour = dt_object.strftime("%H:%M:%S")
    
    return time_24_hour

def convert(s):
    return list(map(lambda x: x, s))

def get_column_val(df, columns, labels, file):
    val = []
    label = []
    info = break_file_name(file)
    
    for j, (columns_j, label_j) in enumerate(zip(columns, labels)):
        if columns_j in ['NewTime', 'Timestamp']:
            continue
        elif columns_j in ['Socket0 L2 Cache Hits']:
            Y_tmp =  df['Socket0 L2 Cache Misses'].div(df[columns_j]+df['Socket0 L2 Cache Misses']).mul(100)
            Y = Y_tmp.values.tolist()
            val.append(Y)
            label.append(f'{info[1]} {info[5]} {info[2]} {label_j}')
        elif columns_j in ['Socket0 L3 Cache Hits']:
            Y_tmp =  df['Socket0 L3 Cache Misses'].div(df[columns_j]+df['Socket0 L3 Cache Misses']).mul(100)
            Y = Y_tmp.values.tolist()
            val.append(Y)
            label.append(f'{info[1]} {info[5]} {info[2]} {label_j}')  
        elif columns_j in ['Socket1 L2 Cache Hits']:
            Y_tmp = df['Socket1 L2 Cache Misses'].div(df[columns_j]+df['Socket1 L2 Cache Misses']).mul(100)
            Y = Y_tmp.values.tolist()
            val.append(Y)
            label.append(f'{info[1]} {info[5]} {info[2]} {label_j}')  
        elif columns_j in ['Socket1 L3 Cache Hits']:
            Y_tmp = df['Socket1 L3 Cache Misses'].div(df[columns_j]+df['Socket1 L3 Cache Misses']).mul(100)
            Y = Y_tmp.values.tolist()
            val.append(Y)
            label.append(f'{info[1]} {info[5]} {info[2]} {label_j}')  
        elif columns_j in ['L2 Access (pti) Socket0']:
            Y_tmp = df['L2 Miss (pti) Socket0'].div(df[columns_j]).mul(100)
            Y = Y_tmp.values.tolist()
            val.append(Y)
            label.append(f'{info[1]} {info[5]} {info[2]} {label_j}')  
        elif columns_j in ['L2 Access (pti) Socket1']:
            Y_tmp = df['L2 Miss (pti) Socket1'].div(df[columns_j]).mul(100)
            Y = Y_tmp.values.tolist()
            val.append(Y)
            label.append(f'{info[1]} {info[5]} {info[2]} {label_j}')
        elif columns_j in ['L2 Access (pti) Socket1.1']:
            Y_tmp = df['L2 Miss (pti) Socket1.1'].div(df[columns_j]).mul(100)
            Y = Y_tmp.values.tolist()
            val.append(Y)
            label.append(f'{info[1]} {info[5]} {info[2]} {label_j}')  
        elif columns_j in ['Socket0 L2 Cache Misses', 'Socket1 L2 Cache Misses', 'L2 Miss (pti) Socket0', 'L2 Miss (pti) Socket1', 'Socket0 L3 Cache Misses', 'Socket1 L3 Cache Misses', 'L3 Miss % Socket0', 'L3 Miss % Socket1', 'Ave L3 Miss Latency Socket0', 'Ave L3 Miss Latency Socket1']:
            Y_tmp = df[columns_j].div(1)
            Y = Y_tmp.values.tolist()
            val.append(Y)
            label.append(f'{info[1]} {info[5]} {info[2]} {label_j}')
        elif columns_j in ['L3 Miss Socket0', 'L3 Miss Socket1', 'L3 Miss Socket1.1']:
            Y_tmp = df[columns_j].div(1000000000)
            Y = Y_tmp.values.tolist()
            val.append(Y)
            label.append(f'{info[1]} {info[5]} {info[2]} {label_j}')
        elif columns_j in ['Socket0 Memory Bandwidth', 'Socket1 Memory Bandwidth']:
            Y_tmp = df[columns_j].div(1000)
            Y = Y_tmp.values.tolist()
            val.append(Y)
            label.append(f'{info[1]} {info[5]} {info[2]} {label_j}')
        elif columns_j in ['Socket0 L2 Cache Misses Per Instruction', 'Socket1 L2 Cache Misses Per Instruction']:
            Y_tmp = df[columns_j].mul(100)
            Y = Y_tmp.values.tolist()
            val.append(Y)
            label.append(f'{info[1]} {info[5]} {info[2]} {label_j}')
        elif columns_j in ['Package Joules Consumed Socket0 Energy Consumption', 'Package Joules Consumed Socket1 Energy Consumption']:
            #Y_tmp = df[columns_j] - 40
            Y_tmp = df[columns_j]
            Y = Y_tmp.values.tolist()
            val.append(Y)
            label.append(f'{info[1]} {info[5]} {info[2]} {label_j}')  
        elif columns_j in ['IRA Socket0', 'IRA Socket1']:
            Y_tmp = df['Utilization (%) Socket1'].mul(0)
            Y = Y_tmp.values.tolist()
            val.append(Y)
            label.append(f'{info[1]} {info[5]} {info[2]} {label_j}') 
        else:
            Y = df[columns_j].values.tolist()
            val.append(Y)
            label.append(f'{info[1]} {info[5]} {info[2]} {label_j}')
    
    return val, label

def json_info(file_daqconf, file_core, parent_folder_dir, input_dir, var, pdf, if_pdf=False, repin_threads_file=False):   
    emu_mode = None
    with open(f'{parent_folder_dir}/daqconfs/{file_daqconf}.json', 'r') as f:
        data_daqconf = json.load(f)
        
        info_boot = json.dumps(data_daqconf['boot'], skipkeys = True, allow_nan = True)
        data_boot_list = json.loads(info_boot)
        data_boot = convert(data_boot_list)
        info_hsi = json.dumps(data_daqconf['hsi'], skipkeys = True, allow_nan = True)
        data_hsi_list = json.loads(info_hsi)
        data_hsi = convert(data_hsi_list)
        info_trigger = json.dumps(data_daqconf['trigger'], skipkeys = True, allow_nan = True)
        data_trigger_list = json.loads(info_trigger)
        data_trigger = convert(data_trigger_list)
        info_readout = json.dumps(data_daqconf['readout'], skipkeys = True, allow_nan = True)
        data_readout_list = json.loads(info_readout)
        data_readout = convert(data_readout_list)

        for m, value_m in enumerate(data_readout):
            if value_m in ['thread_pinning_files']: 
                file_cpupins = data_readout_list[value_m][2]['file']
                
        if repin_threads_file:
            file_cpupins = repin_threads_file
    
    if if_pdf:
        pdf.set_font('Times', '', 10)
        pdf.write(5, f'daqconf file: {file_daqconf} \n')
        for i, value_i in enumerate(data_boot):
            if value_i in ['use_connectivity_service']:
                pdf.write(5, f'    * {value_i}: {data_boot_list[value_i]} \n')
            else:
                pass

        for j, value_j in enumerate(data_hsi):
            if value_j in ['random_trigger_rate_hz']: 
                pdf.write(5, f'    * {value_j}: {data_hsi_list[value_j]} \n')
            else:
                pass

        for l, value_l in enumerate(data_readout):
            if value_l in ['latency_buffer_size','generate_periodic_adc_pattern','use_fake_cards','enable_raw_recording', 'raw_recording_output_dir','enable_tpg','tpg_threshold','tpg_algorithm']: 
                pdf.write(5, f'    * {value_l}: {data_readout_list[value_l]} \n')
            else:
                pass
        for m, value_m in enumerate(data_readout):
            if value_m in ['thread_pinning_file']: 
                if repin_threads_file:
                    pdf.write(5, f'    * {value_m}: {repin_threads_file} \n')
                else:
                    pdf.write(5, f'    * {value_m}: {data_readout_list[value_m]} \n')

            else:
                pass

    emu_mode = True if data_readout_list['generate_periodic_adc_pattern'] else False
    
    for var_i in var:
        data_list = cpupining_info(parent_folder_dir, file_cpupins, var_i)
        pinning_table, cpu_core_table, cpu_utilization_maximum_table = extract_table_data(input_dir, file_core, data_list, emu_mode=emu_mode)
        pdf.ln(5)
        table_cpupins(columns_data=[pinning_table, cpu_core_table, cpu_utilization_maximum_table], pdf=pdf, if_pdf=if_pdf)
        pdf.cell(0, 10, f'Table of CPU core pins information of {var_i}.')
        pdf.ln(10) 

def cpupining_info(input_dir, file, var):
    file_name=file.split('/')
    with open(f'{input_dir}/cpupins/{file_name[-1]}', 'r') as ff:
        data_cpupins = json.load(ff)
        info_daq_application = json.dumps(data_cpupins['daq_application'][f'--name {var}'], skipkeys = True, allow_nan = True)
        data_list = json.loads(info_daq_application)
        
    return data_list

def core_utilization(input_dir, file):
    CPU_plot, User_plot = [], []
    
    info = break_file_name(file)
    data_frame = pd.read_csv(f'{input_dir}/{file}.csv')

    maxV = data_frame['CPU'].max()
    minV = data_frame['CPU'].min()

    for j in range(minV, maxV + 1):
        CPU_plot.append(j)
        df = data_frame.loc[data_frame['CPU'] == j]
        User_max = df['user (%)'].max()
        User_plot.append(User_max)

    return CPU_plot, User_plot

def parse_cpu_cores(cpu_cores_i):
    ranges = re.split(r',|-', cpu_cores_i)
    cpu_cores = []
    for item in ranges:
        if '-' in item:
            start, end = map(int, item.split('-'))
            cpu_cores.extend(range(start, end + 1))
        else:
            cpu_cores.append(int(item))
    return cpu_cores

def extract_table_data(input_dir, file_core, data_list, emu_mode=False): 
    pinning_table, cpu_core_table, cpu_core_table_format, cpu_utilization_table, cpu_utilization_maximum_table, max_tmp = [], [], [], [], [], []
    cpu_core, cpu_utilization = core_utilization(input_dir, file_core)
    denominator, sum_utilization = 0, 0

    # Process data_list, and extract 'threads' sub-dictionary, and other data entries
    for data_i, value_i in data_list.items():
        if data_i == 'threads': 
            for threads_i, cpu_cores_i in value_i.items():
                    if emu_mode:
                        if threads_i in ['fakeprod-1..', 'fakeprod-2..', 'consumer-1..', 'consumer-2..', 'recording-1..', 'recording-2..', 'consumer-0', 'tpset-0', 'cleanup-0', 'recording-0', 'postproc-0-1..', 'postproc-0-2..']:
                            pinning_table.append(threads_i)
                            cpu_core_table.append(cpu_cores_i)
                        else:
                            pass

                    else:
                        if threads_i in ['fakeprod-1..', 'fakeprod-2..']:
                            pass
                        else:
                            pinning_table.append(threads_i)
                            cpu_core_table.append(cpu_cores_i)                  
        
        else:
            pinning_table.append(data_i)
            cpu_core_table.append(value_i)

    # Calculate averages for each CPU core configuration
    for cpu_cores_i in cpu_core_table:
        try:
            cpu_cores = parse_cpu_cores(cpu_cores_i)
            cpu_core_table_format.append(cpu_cores)
        except ValueError:
            print(f'Check the format of the cpu pinning file. The [#,#] will not work.')

        for core_i in cpu_cores:
            denominator += 1
            sum_utilization += cpu_utilization[core_i] 
            max_tmp.append(cpu_utilization[core_i])
        
        utilization_average = round((sum_utilization / denominator), 2)
        cpu_utilization_table.append(utilization_average)
        cpu_utilization_maximum_table.append(max(max_tmp))
        denominator, sum_utilization = 0, 0   # Reset variables for the next iteration

    return pinning_table, cpu_core_table, cpu_utilization_maximum_table

def table_cpupins(columns_data, pdf, if_pdf=False):
    if not columns_data:
        print('you are missing the table data')
        return

    rows_data = []
    headers = ['Pinning', 'CPU cores', 'CPU max use (%)']
    rows_data.append(headers)
    
    # Transpose the data to convert columns to rows
    line = list(map(list, zip(*columns_data)))
    rows_data = rows_data + line
    
    line_height = pdf.font_size * 2.1
    col_width = [pdf.epw/3.25, pdf.epw/2, pdf.epw/6.8]
    
    lh_list = [] #list with proper line_height for each row

    if if_pdf:
        pdf.set_font('Times', '', 10)

        # Determine line heights based on the number of words in each cell
        for row in rows_data:
            max_lines = 1  # Initialize with a minimum of 1 line
            for datum in row:
                if isinstance(datum, int):
                    datum = str(datum)
                elif not isinstance(datum, str):
                    datum = str(datum)
                
                lines_needed = len(str(datum).split('\n'))  # Count the number of lines
                max_lines = max(max_lines, lines_needed)

            lh_list.append(line_height * max_lines)
        
        # Add table rows with word wrapping and dynamic line heights
        for j, row in enumerate(rows_data):
            line_height_table = lh_list[j] 
            for k, datum in enumerate(row):
                pdf.multi_cell(col_width[k], line_height_table, str(datum), border=1, align='L', new_x=XPos.RIGHT, new_y=YPos.TOP, max_line_height=pdf.font_size)

            pdf.ln(line_height_table)
        
        pdf.set_font('Times', '', 10)
        
    else:
        print(rows_data)

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

