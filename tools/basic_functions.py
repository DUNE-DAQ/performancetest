import os
import sys
import csv
import time
import glob
import json
import requests
import re
import shutil
import subprocess
import matplotlib
import matplotlib.pyplot as plt 
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import matplotlib.dates as mdates
import numpy as np
import pickle as pkl
import pandas as pd
from pathlib import Path
from datetime import datetime as dt
from fpdf import FPDF 
from fpdf.enums import XPos, YPos

cs8_os = ['np04srv001', 'np04srv002', 'np04srv003', 'np04srv008', 'np04srv010', 'np04srv014', 'np04srv023', 'np04onl003']
c7_os = ['np04srv007', 'np04srv009', 'np04crt001']

def directory(input_dir):
    # Create directory (if it doesn't exist yet):
    for dir_path in input_dir:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            
def get_unix_timestamp(time_str):
    formats = ['%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S']
    for fmt in formats:
        try:
            timestamp = dt.strptime(time_str, fmt).timestamp()
            return int(timestamp * 1000) if '.' in time_str else int(timestamp)
        except ValueError:
            pass
    raise ValueError('Invalid time format: {}'.format(time_str))

def make_column_list(file, input_dir):
    data_frame = pd.read_csv('{}/{}.csv'.format(input_dir, file))
    columns_list = list(data_frame.columns) 
    ncoln=len(columns_list) 
    return columns_list

def datenum(d, d_base):
    t_0 = d_base.toordinal() 
    t_1 = dt.fromordinal(t_0)
    T = (d - t_1).total_seconds()
    return T

def is_hidden(input_dir):
    name = os.path.basename(os.path.abspath(input_dir))
    if name.startswith('.'):
        return 'true'
    else:
        return 'false'

def make_file_list(input_dir):
    file_list =  []
    for root, dirs, files in os.walk(input_dir):
        for name in files:
            if is_hidden(name) == 'true':  
                print (name, ' is hidden, trying to delete it')
                os.remove(os.path.join(input_dir, name))
            else:
                file_list.append(os.path.join(input_dir, name))
                
    return file_list

def make_name_list(input_dir):
    l=os.listdir(input_dir)
    name_list=[x.split('.')[0] for x in l]
    
    all_list = []
    all_plots_list = []
    pcm_list = []
    uprof_list = []
    time_list = []
    reformated_uprof_list = []
    reformated_time_list = []
    
    for i, name_i in enumerate(name_list):
        if 'reformatter_uprof-' in name_i:
            reformated_uprof_list.append(name_i)
            all_plots_list.append(name_i)
            
        elif 'reformatter_timechart-' in name_i:
            reformated_time_list.append(name_i)
            
        elif 'uprof-' in name_i:
            uprof_list.append(name_i)
            all_list.append(name_i)
            
        elif 'timechart-' in name_i:
            time_list.append(name_i)
            
        elif 'grafana-' in name_i:
            pcm_list.append(name_i)
            all_list.append(name_i)
            all_plots_list.append(name_i)
            
        else:
            pass

    return pcm_list, uprof_list, time_list, reformated_uprof_list, reformated_time_list, all_list, all_plots_list

def create_var_list(file_list, var_list):
    files_srv_list = [] 
    for var_j in  var_list:
        tmp = []
        for name_i in file_list:
            if '{}'.format(var_j) in name_i:
                tmp.append(name_i)
              
        files_srv_list.append(tmp)
        
    return files_srv_list

def fetch_grafana_panels(grafana_url, dashboard_uid):
    panels = []
    # Get dashboard configuration
    dashboard_url = '{}/api/dashboards/uid/{}'.format(grafana_url, dashboard_uid)     
    try:
        response = requests.get(dashboard_url)
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type')

            if content_type and 'application/json' in content_type:
                dashboard_data = response.json()  
                # Extract panels data
                panels = dashboard_data['dashboard']['panels']
                return panels
            else:
                print('Warning: Response is not in JSON format. Content-Type:', content_type)
                html_content = response.text
                
        else:
            print('Error: Failed to fetch dashboard data. Status code:', response.status_code)
        
    except requests.exceptions.RequestException as e:
        print('Error: Request failed with the following exception:', e)

def get_query_urls(panel, host):
    targets = panel.get('targets', [])
    queries = []
    queries_label = []
    for target in targets:
        if 'expr' in target:
            query = target['expr'].replace('${host}', host)
            queries.append(query)
            queries_label.append(target['legendFormat'])
    
    if queries:
        return queries, queries_label
    else:
        return None

def extract_data_and_stats_from_panel(grafana_url, dashboard_uid, delta_time, host, input_dir, output_csv_file):
    for dashboard_uid_to_use in dashboard_uid:
        panels_data = fetch_grafana_panels(grafana_url, dashboard_uid_to_use)
        if not panels_data:
            print('Error in extract_data_and_stats_from_panel: Failed to fetch dashboard panels data.')
            return
        
        url = '{}/api/datasources/proxy/1/api/v1/query_range'.format(grafana_url)
        start_timestamp = get_unix_timestamp(delta_time[0])
        end_timestamp = get_unix_timestamp(delta_time[1])
        all_dataframes = []
        
        for panel_i, panel in enumerate(panels_data):
            if 'targets' not in panel:
                print('Skipping panel ', panel['title'], ' with no targets.')
                continue
            
            query_urls, queries_label = get_query_urls(panel, host)
            if not query_urls:
                print('Skipping panel ', panel['title'], ' with no valid query URL.')
                continue
            
            for i, query_url in enumerate(query_urls):
                column_name = '{} {}'.format(queries_label[i], panel['title'])
                data = {
                    'query': query_url,
                    'start': start_timestamp,
                    'end': end_timestamp,
                    'step': 2
                }

                response = requests.post(url, data=data)
                response_data = response.json()
                
                if response.status_code != 200:
                    print('Error: Failed to fetch dashboard data. Status code:content ', response.status_code, ':', response.content)
                    print('Response panel:data:content for panel ', panel['title'], ':', response_data, ':', response.content)
                    return None

                if 'data' not in response_data or 'resultType' not in response_data['data'] or response_data['data']['resultType'] != 'matrix':
                    print('Skipping query with no valid response in panel: ', panel['title'])
                    continue

                result = response_data['data']['result'][0]
                metric = result['metric']
                values = result.get('values', [])
                values_without_first_column = [row[1:] for row in values]

                if not values:
                    print('Skipping query with no valid response in panel: ', panel['title'])
                    continue

                timestamps = [val[0] for val in values]
                df_first = pd.DataFrame(values, columns=['Timestamp', column_name])
                df_first['Timestamp'] = pd.to_datetime(df_first['Timestamp'], unit='s')
                df = pd.DataFrame(values_without_first_column, columns=[column_name])
                
                if panel_i == 0 and i == 0: 
                    df_tmp = df_first
                else:
                    df_tmp = df
                
                all_dataframes.append(df_tmp)

        # Combine all dataframes into a single dataframe
        combined_df = pd.concat(all_dataframes, axis=1)

        # Save the combined dataframe as a CSV file
        output = '{}/grafana-{}.csv'.format(input_dir, output_csv_file)
        try:
            combined_df.to_csv(output, index=False)
            print('Data saved to CSV successfully:', output)
        except Exception as e:
            print('Exception Error: Failed to save data to CSV:', str(e))

def uprof_pcm_formatter(input_dir, file):
    #data_frame = pd.read_csv('{}/{}.csv'.format(input_dir, file), skiprows=[1, 47], error_bad_lines=False) 

    newfile = 'reformatter_{}'.format(file)
    f = open('{}/{}.csv'.format(input_dir, file),'r')
    f_new = open('{}/{}.csv'.format(input_dir, newfile),'w')
    
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
        # and add headers for l2 cache hit ratio
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
            date_n = '{year_month}-{day:02d} {hour:02d}:{min:02d}:{sec:02d}'.format(year_month=full_date[0:7], day=day_n, hour=hour_n, min=min_n, sec=sec_n)
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
    newfile = 'reformatter_{}'.format(file)
    f = open('{}/{}.csv'.format(input_dir, file),'r')
    f_new = open('{}/{}.csv'.format(input_dir, newfile),'w')

    header = True
    for line in f:
        # get & reformat full date
        if 'Profile Start Time:' in line:
            full_date = line.split(',')[1]
            month = month2num(full_date[0:3])
            date = int(full_date[4:6])
            year = int(full_date[7:11])
            full_date_new = '{year}-{month:02d}-{date:02d}'.format(year=year, month=month, date=date)

        # Reformat timestamps
        if not header:
            timestamp_n = line.split(',')[1]
            timestamp_n = timestamp_n.split(':')
            hour_n = int(timestamp_n[0])
            min_n = int(timestamp_n[1])
            sec_n = int(timestamp_n[2])
            date_n = ',{year_month_day} {hour:02d}:{min:02d}:{sec:02d},'.format(year_month_day=full_date_new, hour=hour_n, min=min_n, sec=sec_n)

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
    if month_str in months:
        return months[month_str]
    else:
        print('Warning: invalid month')
        
def combine_time_and_uprof_files(input_dir, time_file, uprof_file):
    input_file0 = '{}/reformatter_{}.csv'.format(input_dir, time_file)
    input_file1 = '{}/reformatter_{}.csv'.format(input_dir, uprof_file)
        
    data_frame0 = pd.read_csv(input_file0) 
    data_frame1 = pd.read_csv(input_file1) 
    df_merged = data_frame0.merge(data_frame1, how='outer')
    
    # Save the combined dataframe as a CSV file
    output = '{}/reformatter_{}.csv'.format(input_dir, uprof_file)
    try:
        df_merged.to_csv(output, index=False)
        print('Data saved to CSV successfully:', output)
    except Exception as e:
        print('Error in combine_time_and_uprof_files: Failed to save data to CSV:', str(e))

def break_file_name(file):
    info=file.split('-')
    return info

def check_OS(server):
    if server in cs8_os:
        return 'CS8'
    elif server in c7_os:
        return 'C7'
    return 'Alma9'

def add_new_time_format(input_dir, file):
    data_frame = pd.read_csv('{}/{}.csv'.format(input_dir, file))  

    # Add new time format
    newtime=[]
    x_0 = data_frame['Timestamp'][0]
    d_0 = dt.strptime(x_0,'%Y-%m-%d %H:%M:%S')
    for index, value in enumerate(data_frame['Timestamp']):   
        d = dt.strptime(value,'%Y-%m-%d %H:%M:%S')
        d_new = (datenum(d, d_0)-datenum(d_0, d_0))/60.
        newtime.append(d_new) 

    data_frame.insert(0, 'NewTime', newtime, True)
    data_frame.to_csv('{}/{}.csv'.format(input_dir, file), index=False)

def convert(s):
    return list(map(lambda x: x, s))

def get_column_val(df, columns, labels, file):
    val = []
    label = []
    info = break_file_name(file)
    
    for j, (columns_j, label_j) in enumerate(zip(columns, labels)):
        if columns_j in ['NewTime', 'Timestamp']:
            continue
        elif columns_j in ['C0 Core C-state residency', 'CPU Utilization', 'Socket0 Instructions Per Cycle', 'Socket0 Instructions Retired Any (Million)']:
            Y_tmp = df[columns_j].mul(1)
            Y = Y_tmp.values.tolist()
            val.append(Y)
            label.append('{} {}'.format(info[5], info[2]))
        elif columns_j in ['Socket0 L3 Cache Misses Per Instruction', 'Socket1 L3 Cache Misses Per Instruction', 'L2 Miss (pti) Socket0', 'L2 Miss (pti) Socket1']:
            Y_tmp = df[columns_j].mul(1)
            Y = Y_tmp.values.tolist()
            val.append(Y)
            label.append('{} {} {}'.format(info[5], info[2] , label_j))
        elif columns_j in ['Socket0 L2 Cache Misses', 'Socket1 L2 Cache Misses', 'Socket0 L3 Cache Misses', 'Socket1 L3 Cache Misses']:
            Y_tmp = df[columns_j].mul(1)
            Y = Y_tmp.values.tolist()
            val.append(Y)
            label.append('{} {} {}'.format(info[5], info[2] , label_j))
        elif columns_j in ['L3 Miss Socket0', 'L3 Miss Socket1']:
            Y_tmp = df[columns_j].div(1000000000)
            Y = Y_tmp.values.tolist()
            val.append(Y)
            label.append('{} {} {}'.format(info[5], info[2] , label_j))
        elif columns_j in ['Socket0 Memory Bandwidth', 'Socket1 Memory Bandwidth']:
            Y_tmp = df[columns_j].div(1000)
            Y = Y_tmp.values.tolist()
            val.append(Y)
            label.append('{} {} {}'.format(info[5], info[2] , label_j))
        elif columns_j in ['L2 Hit Ratio Socket0', 'L2 Hit Ratio Socket1']:
            Y_tmp = df[columns_j].div(1)
            Y = Y_tmp.values.tolist()
            val.append(Y)
            label.append('{} {} {}'.format(info[5], info[2] , label_j))
        elif columns_j in ['Socket0 L2 Cache Misses Per Instruction', 'Socket1 L2 Cache Misses Per Instruction']:
            Y_tmp = df[columns_j].mul(100)
            Y = Y_tmp.values.tolist()
            val.append(Y)
            label.append('{} {} {}'.format(info[5], info[2] , label_j))
            
        elif columns_j in ['Package Joules Consumed Socket0 Energy Consumption', 'Package Joules Consumed Socket1 Energy Consumption']:
            #Y_tmp = df[columns_j] - 40
            Y_tmp = df[columns_j]
            Y = Y_tmp.values.tolist()
            val.append(Y)
            label.append('{} {} {}'.format(info[5], info[2] , label_j))    
        else:
            Y = df[columns_j].values.tolist()
            val.append(Y)
            label.append('{} {} {}'.format(info[5], info[2] , label_j))
    
    return val, label

def json_info(file_daqconf, file_cpupins, input_dir, var, pdf, if_pdf=False):  
    with open('{}/cpupins/{}.json'.format(input_dir, file_cpupins), 'r') as ff:
        data_cpupins = json.load(ff)
        
        info_daq_application = json.dumps(data_cpupins['daq_application']['--name {}'.format(var)], skipkeys = True, allow_nan = True)
        data_list = json.loads(info_daq_application)
        data_threads = convert(data_list['threads'])
        max_file = int(len(data_threads)/3)
       
    with open('{}/daqconfs/{}.json'.format(input_dir, file_daqconf), 'r') as f:
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
        
        if if_pdf:
            pdf.set_font('Times', '', 10)
            pdf.write(5, 'daqconf file: {} \n'.format(file_daqconf))
            for i, value_i in enumerate(data_boot):
                if value_i in ['use_connectivity_service']:
                    pdf.write(5, '    * {}: {} \n'.format(value_i, data_boot_list[value_i]))
                else:
                    pass
                
            for j, value_j in enumerate(data_hsi):
                if value_j in ['random_trigger_rate_hz']: 
                    pdf.write(5, '    * {}: {} \n'.format(value_j, data_hsi_list[value_j]))
                else:
                    pass
                
            for k, value_k in enumerate(data_trigger):
                if value_k in ['trigger_activity_config']: 
                    pdf.write(5, '    * {}: prescale: {} \n'.format(value_k, data_trigger_list[value_k]['prescale']))
                else:
                    pass
            
            for l, value_l in enumerate(data_readout):
                if value_l in ['latency_buffer_size','generate_periodic_adc_pattern','use_fake_cards','enable_raw_recording','raw_recording_output_dir','enable_tpg','tpg_threshold','tpg_algorithm']: 
                    pdf.write(5, '    * {}: {} \n'.format(value_l, data_readout_list[value_l]))
                else:
                    pass
            for m, value_m in enumerate(data_readout):
                if value_m in ['thread_pinning_file']: 
                    pdf.write(5, '    * {}: {} \n'.format(value_m, data_readout_list[value_m]))
                    pdf.set_font('Times', '', 8)
                    pdf.write(5, '        - {} \n'.format(var))
                    pdf.write(5, '        - "parent": "{}" \n'.format(data_list['parent']))
                    pdf.write(5, '        - "threads": \n')
                    for i in range(0, max_file):
                        pdf.write(5, '                "{}": {}    "{}": {}     "{}": {} \n'.format(data_threads[i], data_list['threads'][data_threads[i]], data_threads[i+max_file], data_list['threads'][data_threads[i+max_file]], data_threads[i+2*max_file], data_list['threads'][data_threads[i+2*max_file]]))
                else:
                    pass
            pdf.write(5,'\n')

def append_lists(list1, list2):
    for i in list2:
        list1.append(i)
    return list1

def readoutmap_change_var(file, input_dir, var):
    with open('{}/{}.json'.format(input_dir, file), 'r') as ff:
        data = json.load(ff)
        info = json.dumps(data, skipkeys = True, allow_nan = True, indent=4)
    
    print(len(data))
    print(info)

    for value_i in data[0]:
        if value_i == var:
            print(value_i, ': ', data[0][value_i])
            data[0][value_i]=int(data[0][value_i])+1
            print(value_i, ': ', data[0][value_i])
        else:
            pass
