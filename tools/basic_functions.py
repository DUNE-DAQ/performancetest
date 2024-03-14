#This Python file contains imports and variable definitions to support data analysis and visualization tasks. This would allow another script to easily generate plots, tables, PDFs etc for data analysis without having to redefine these each time. The file provides some reusable variables and utilities to build on. Overall these provide some common utility functions for working with files, directories, times, and data in Python.

#* It imports common Python packages like os, sys, csv, time, json, re, shutil, subprocess, requests, matplotlib, numpy, pickle, pandas, pathlib, datetime, fpdf, dateutil, tabulate, getpass, flask. These provide functionality for system calls, file I/O, data manipulation, plotting, PDF generation, date parsing, formatting tables, getting passwords, and web apps.

#* It defines some lists:
#    * color_list - a list of color names for plotting/visualization
#    * linestyle_list - a list of line style names (solid, dotted, etc) for plotting
#    * marker_list - a list of marker symbols (circles, squares, etc) for plotting
#    * not_alma9_os - a list of hostnames, possibly for some filtering logic
#    * list_py_package - a list of the imported Python package names

#This is a collection of utility functions in Python:
#* debug_missing_module - This checks if a module is installed and prints an error message if not. It takes a module name as input and returns a bool indicating if the module is installed. This is useful for debugging missing dependencies before running a script.
#* get_access - This securely gets a username and password from the user, without echoing the password typed. It uses the getpass module. The input is the prompt strings, and the output is the username and password variables.
#* directory - This creates directories if they don't already exist. It takes a list of directory paths as input. The output is the directories being created if needed.
#* current_time - This returns a string with the current date and time formatted a certain way. There are no inputs. The output is the formatted time string.
#* get_unix_timestamp - This converts a time string to a unix timestamp integer. It takes a time string as input and tries different formats until one works. The output is the integer timestamp.
#* make_column_list - This reads a CSV file and returns a list of the column names. It takes the filename and directory as input and outputs the column name list.
#* datenum - This calculates the elapsed time in seconds between two datetime objects. It takes the two datetimes as input and outputs the time difference as a float.
#* is_hidden - This checks if a filename indicates a hidden file. It takes a filename/path as input and returns a bool.
#* make_file_list - This builds a list of files in a directory, omitting hidden files. It takes the directory path as input and outputs a list of file paths.
#* make_name_list_benchmark - This extracts the base filenames from a directory into a list. It takes the directory path as input and outputs a list of base filenames without extensions.
#* make_name_list - This categorizes filenames in a directory into different lists based on patterns in the names. It takes the directory path as input and outputs several lists of filenames grouped by the patterns found.
#* create_var_list - This filters a list of filenames based on a list of substrings. It takes a file list and string list as input and outputs a list of lists of filenames containing each substring. 

import os
import sys
import csv
import time
import glob
import json
import re
import shutil
import subprocess
import requests
import getpass
import matplotlib
import matplotlib.pyplot as plt 
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import matplotlib.dates as mdates
import numpy as np
import pickle as pkl
import pandas as pd
from flask import Flask, request
from pathlib import Path
from datetime import datetime as dt
from fpdf import FPDF 
from fpdf.enums import XPos, YPos
from dateutil.parser import parse
from tabulate import tabulate

color_list = ['red', 'blue', 'green', 'cyan', 'orange', 'navy', 'magenta', 'lime', 'purple', 'hotpink', 
              'olive', 'salmon', 'teal', 'darkblue', 'darkgreen', 'darkcyan', 'darkorange', 'deepskyblue', 
              'darkmagenta', 'sienna', 'chocolate', 'orangered', 'gray', 'royalblue', 'gold', 'peru', 
              'seagreen', 'violet', 'tomato', 'lightsalmon', 'crimson', 'lightblue', 'lightgreen', 'linen', 
              'lightpink', 'black', 'darkgray', 'lightgray', 'saddlebrown', 'brown', 'khaki', 'tan']

linestyle_list = ['solid', 'dotted', 'dashed', 'dashdot','solid', 'dotted', 'dashed', 'dashdot']

marker_list = ['s','o','.','p','P','^','<','>','*','+','x','X','d','D','h','H'] 

not_alma9_os = ['np04srv008', 'np04srv010', 'np04srv014', 'np04srv023', 'np04onl003', 'np04srv007', 'np04srv009', 'np04crt001']
list_py_package = ['os', 'sys', 'csv', 'time', 'glob', 'json', 'requests', 're', 'shutil', 'subprocess', 'matplotlib', 
                   'numpy', 'pickle', 'pandas', 'pathlib', 'datetime', 'fpdf', 'dateutil', 'tabulate', 'getpass', 'flask']

# Function to debug missing modules before starting.
def debug_missing_module(module_name):
    try:
        __import__(module_name) 
    except ImportError:
        print(f"Error: {module_name} is not installed.")
        print(f"To install it, run: pip install {module_name}")
        return False
    return True

# Function to ask hidden password
def get_access():
    username = input("Enter username :")
    password = getpass("Enter password :")

# Function to create directory (if it doesn't exist yet).
def directory(input_dir):
    for dir_path in input_dir:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

# Function to return the current time.
def current_time():
    now = dt.now()
    current_dnt = now.strftime('%Y-%m-%d %H:%M:%S')
    return current_dnt

# Function to 
def get_unix_timestamp(time_str):
    formats = ['%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S']
    for fmt in formats:
        try:
            timestamp = dt.strptime(time_str, fmt).timestamp()
            return int(timestamp * 1000) if '.' in time_str else int(timestamp)
        except ValueError:
            pass
    raise ValueError('Invalid time format: {}'.format(time_str))

# Function to 
def make_column_list(file, input_dir):
    data_frame = pd.read_csv('{}/{}.csv'.format(input_dir, file))
    columns_list = list(data_frame.columns) 
    ncoln=len(columns_list) 
    return columns_list

# Function to return a deltaT from the start of the test.
def datenum(d, d_base): 
    t_0 = d_base.toordinal() 
    t_1 = dt.fromordinal(t_0)
    T = (d - t_1).total_seconds()
    return T

# Function to
def is_hidden(input_dir): 
    name = os.path.basename(os.path.abspath(input_dir))
    return True if name.startswith('.') else False

# Function to 
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

# Function to 
def make_name_list_benchmark(input_dir):
    l=os.listdir(input_dir)
    benchmark_list=[x.split('.')[0] for x in l]

    return benchmark_list

# Function to 
def make_name_list(input_dir):
    l=os.listdir(input_dir)
    name_list=[x.split('.')[0] for x in l]
    
    pcm_list, uprof_list, core_utilization_list, reformated_uprof_list, reformated_core_utilization_list , all_list, all_plots_list = [], [], [], [], [], [], []
    
    for i, name_i in enumerate(name_list):
        if 'reformatter_uprof-' in name_i:
            reformated_uprof_list.append(name_i)
            all_plots_list.append(name_i)
        
        elif 'reformatter_core_utilization-' in name_i:
            reformated_core_utilization_list.append(name_i)
            
        elif 'core_utilization-' in name_i: 
            core_utilization_list.append(name_i)
            
        elif 'uprof-' in name_i:
            uprof_list.append(name_i)
            all_list.append(name_i)
            
        elif 'grafana-' in name_i:
            pcm_list.append(name_i)
            all_list.append(name_i)
            all_plots_list.append(name_i)
            
        else:
            pass

    return pcm_list, uprof_list, core_utilization_list, reformated_uprof_list, reformated_core_utilization_list , all_list, all_plots_list

# Function to 
def create_var_list(file_list, var_list):
    files_srv_list = [] 
    for var_j in  var_list:
        tmp = []
        for name_i in file_list:
            tmp.append(name_i) if '{}'.format(var_j) in name_i else print(var_j, 'not in ', name_i )

        files_srv_list.append(tmp)
        
    return files_srv_list

# Function to 
def cpupins_utilazation_reformatter(input_dir):
    pcm_file, uprof_file, core_utilization_file, reformated_uprof_file, reformatter_core_utilization_file, all_file, all_plots_file = make_name_list(input_dir)
    
    for file in core_utilization_file:
        newfile = 'reformatter_{}'.format(file)
        f = open('{}/{}.csv'.format(input_dir, file),'r')
        f_new = open('{}/{}.csv'.format(input_dir, newfile),'w')
        header = 'Timestamp,CPU,user (%),nice (%),system (%),iowait (%),steal (%),idle (%)'
        f_new.write(header)   
        
        for i, line in enumerate(f):
            if 'Average:'in line or 'all' in line or 'CPU' in line or '                      ' in line or i < 3:
                pass
            else:
                list_new = list(line.split("    "))
                formatted_line = ','.join(list_new)
                f_new.write(formatted_line)   

        print(f"New CSV file saved as: {newfile}.csv ")   

# Function to 
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
                panels = dashboard_data['dashboard']['panels']        # Extract panels data
                return panels
            else:
                print('Warning: Response is not in JSON format. Content-Type:', content_type)
                html_content = response.text
                
        else:
            print('Error: Failed to fetch dashboard data. Status code:', response.status_code)
        
    except requests.exceptions.RequestException as e:
        print('Error: Request failed with the following exception:', e)

# Function to 
def get_query_urls(panel, host, partition):
    targets = panel.get('targets', [])
    
    queries = []
    queries_label = []
    for target in targets:
        if 'expr' in target:
            query = target['expr'].replace('${host}', host)
            queries.append(query)
            queries_label.append(target['legendFormat'])
        elif 'query' in target:
            query = target['query'].replace('${partition}', partition)
            queries.append(query)
            queries_label.append(target['refId'])
        else:
            print('Missing expr or query in targets.')

    return queries, queries_label if queries else None
    
# Function to 
def extract_data_and_stats_from_panel(grafana_url, dashboard_uid, delta_time, host, partition=None, input_dir='', output_csv_file=''):
    for dashboard_uid_to_use in dashboard_uid:
        panels_data = fetch_grafana_panels(grafana_url, dashboard_uid_to_use)
        if not panels_data:
            print('Error in extract_data_and_stats_from_panel: Failed to fetch dashboard panels data.')
            return
        
        #url = http://np04-srv-009.cern.ch:3000/d/91zWmJEVk/intel-r-performance-counter-monitor-intel-r-pcm-dashboard?orgId=1&refresh=5s&var-host=np04-squery_rangerv-021
        url = '{}/api/datasources/proxy/1/api/v1/query_range'.format(grafana_url)
        
        if partition:
            #url = 'http://np04-srv-017.cern.ch:31023/d/v4_3_0-frontend_ethernet/frontend-ethernet?from=1710261229606&to=1710273051890&var-influxdb=ffedc550-6555-4a16-a113-aabf2b980c30&var-postgresql=c7e9e333-25c9-49e7-b209-b9492f70d419&var-partition=np04hddev&var-hsi_series=&var-hsi_field=&var-run_time=0&orgId=1'
            #url = '{}/api/datasources/proxy/v1/{}/api/1/query_range'.format(grafana_url, partition)
            url = '{}/api/datasources/proxy/v1/query_range'.format(grafana_url)
            
        start_timestamp = get_unix_timestamp(delta_time[0])
        end_timestamp = get_unix_timestamp(delta_time[1])
        all_dataframes = []
        
        for panel_i, panel in enumerate(panels_data):
            if 'targets' not in panel:
                print('Skipping panel ', panel['title'], ' with no targets.')
                continue
            
            query_urls, queries_label = get_query_urls(panel, host, partition)
            if not query_urls:
                print('Skipping panel ', panel['title'], ' with no valid query URL')
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
                
                print('response_data = ', response_data)
                
                if response.status_code != 200:
                    print('Error: Failed to fetch dashboard data. Status code: content ', response.status_code, ':', response.content)
                    print('Response panel:data:content for panel ', panel['title'], ':', response_data, ':', response.content)
                    return None

                if 'data' not in response_data or 'resultType' not in response_data['data'] or response_data['data']['resultType'] != 'matrix' or response_data['data']['result']==[]:
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
                
                df_tmp = df_first if panel_i == 0 and i == 0 else df
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

# Function to 
def uprof_pcm_formatter(input_dir, file):
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

# Function to 
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

# Function to reformat uprof time data.
def month2num(month_str):
    months = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
    return months[month_str] if month_str in months else print('Warning: invalid month')

# Function to combine time and uprof data into one CSV file.
def combine_time_and_uprof_files(input_dir, time_file, uprof_file):
    input_file0 = '{}/reformatter_{}.csv'.format(input_dir, time_file)
    input_file1 = '{}/reformatter_{}.csv'.format(input_dir, uprof_file)
        
    data_frame0 = pd.read_csv(input_file0) 
    data_frame1 = pd.read_csv(input_file1) 
    df_merged = data_frame0.merge(data_frame1, how='outer')
    
    output = '{}/reformatter_{}.csv'.format(input_dir, uprof_file)
    try:
        df_merged.to_csv(output, index=False)
        print('Data saved to CSV successfully:', output)
    except Exception as e:
        print('Error in combine_time_and_uprof_files: Failed to save data to CSV:', str(e))

# Function to break file name using "-" as divider.
def break_file_name(file):
    return file.split('-')

# Function to check the server Os
def check_OS(server):
    return 'CS8/C7' if server in not_alma9_os else 'Alma9'

# Function to add new time format for data.s
def add_new_time_format(input_dir, file):
    data_frame = pd.read_csv('{}/{}.csv'.format(input_dir, file))  

    newtime=[]
    x_0 = data_frame['Timestamp'][0]
    d_0 = dt.strptime(x_0,'%Y-%m-%d %H:%M:%S')
    for index, value in enumerate(data_frame['Timestamp']):   
        d = dt.strptime(value,'%Y-%m-%d %H:%M:%S')
        d_new = (datenum(d, d_0)-datenum(d_0, d_0))/60.
        newtime.append(d_new) 

    data_frame.insert(0, 'NewTime', newtime, True)
    data_frame.to_csv('{}/{}.csv'.format(input_dir, file), index=False)

# Function to add new time format for cpu pinning utilization.
def add_new_time_format_utilization(input_dir, file): 
    data_frame = pd.read_csv('{}/{}.csv'.format(input_dir, file))  

    newtime=[]
    x_0_tmp = data_frame['Timestamp'][0]
    x_0 = convert_to_24_hour_format(x_0_tmp)
    d_0 = dt.strptime(x_0,'%H:%M:%S')
    for index, value_tmp in enumerate(data_frame['Timestamp']):  
        value = convert_to_24_hour_format(value_tmp)
        d = dt.strptime(value,'%H:%M:%S')
        d_new = (datenum(d, d_0)-datenum(d_0, d_0))/60.
        newtime.append(d_new) 

    data_frame.insert(0, 'NewTime', newtime, True)
    data_frame.to_csv('{}/{}.csv'.format(input_dir, file), index=False)   

# Function to convert a AM/PM format to a 24 hour format.
def convert_to_24_hour_format(time_str):
    dt_object = dt.strptime(time_str, "%I:%M:%S %p")
    time_24_hour = dt_object.strftime("%H:%M:%S")
    
    return time_24_hour

# Function to convert the _______ to list.
def convert(s):
    return list(map(lambda x: x, s))

# Function to get the values in a given column of the CSV file and weith it if need it.
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
            label.append('{} {} {} {}'.format(info[1], info[5], info[2], label_j))
        elif columns_j in ['Socket0 L3 Cache Hits']:
            Y_tmp =  df['Socket0 L3 Cache Misses'].div(df[columns_j]+df['Socket0 L3 Cache Misses']).mul(100)
            Y = Y_tmp.values.tolist()
            val.append(Y)
            label.append('{} {} {} {}'.format(info[1], info[5], info[2], label_j))  
        elif columns_j in ['Socket1 L2 Cache Hits']:
            Y_tmp = df['Socket1 L2 Cache Misses'].div(df[columns_j]+df['Socket1 L2 Cache Misses']).mul(100)
            Y = Y_tmp.values.tolist()
            val.append(Y)
            label.append('{} {} {} {}'.format(info[1], info[5], info[2], label_j))  
        elif columns_j in ['Socket1 L3 Cache Hits']:
            Y_tmp = df['Socket1 L3 Cache Misses'].div(df[columns_j]+df['Socket1 L3 Cache Misses']).mul(100)
            Y = Y_tmp.values.tolist()
            val.append(Y)
            label.append('{} {} {} {}'.format(info[1], info[5], info[2], label_j))  
        elif columns_j in ['L2 Access (pti) Socket0']:
            Y_tmp = df['L2 Miss (pti) Socket0'].div(df[columns_j]).mul(100)
            Y = Y_tmp.values.tolist()
            val.append(Y)
            label.append('{} {} {} {}'.format(info[1], info[5], info[2], label_j))  
        elif columns_j in ['L2 Access (pti) Socket1']:
            Y_tmp = df['L2 Miss (pti) Socket1'].div(df[columns_j]).mul(100)
            Y = Y_tmp.values.tolist()
            val.append(Y)
            label.append('{} {} {} {}'.format(info[1], info[5], info[2], label_j))
        elif columns_j in ['L2 Access (pti) Socket1.1']:
            Y_tmp = df['L2 Miss (pti) Socket1.1'].div(df[columns_j]).mul(100)
            Y = Y_tmp.values.tolist()
            val.append(Y)
            label.append('{} {} {} {}'.format(info[1], info[5], info[2], label_j))  
        elif columns_j in ['Socket0 L2 Cache Misses', 'Socket1 L2 Cache Misses', 'L2 Miss (pti) Socket0', 'L2 Miss (pti) Socket1', 'Socket0 L3 Cache Misses', 'Socket1 L3 Cache Misses', 'L3 Miss % Socket0', 'L3 Miss % Socket1', 'Ave L3 Miss Latency Socket0', 'Ave L3 Miss Latency Socket1']:
            Y_tmp = df[columns_j].div(1)
            Y = Y_tmp.values.tolist()
            val.append(Y)
            label.append('{} {} {} {}'.format(info[1], info[5], info[2], label_j))
        elif columns_j in ['L3 Miss Socket0', 'L3 Miss Socket1', 'L3 Miss Socket1.1']:
            Y_tmp = df[columns_j].div(1000000000)
            Y = Y_tmp.values.tolist()
            val.append(Y)
            label.append('{} {} {} {}'.format(info[1], info[5], info[2], label_j))
        elif columns_j in ['Socket0 Memory Bandwidth', 'Socket1 Memory Bandwidth']:
            Y_tmp = df[columns_j].div(1000)
            Y = Y_tmp.values.tolist()
            val.append(Y)
            label.append('{} {} {} {}'.format(info[1], info[5], info[2], label_j))
        elif columns_j in ['Socket0 L2 Cache Misses Per Instruction', 'Socket1 L2 Cache Misses Per Instruction']:
            Y_tmp = df[columns_j].mul(100)
            Y = Y_tmp.values.tolist()
            val.append(Y)
            label.append('{} {} {} {}'.format(info[1], info[5], info[2], label_j))
        elif columns_j in ['Package Joules Consumed Socket0 Energy Consumption', 'Package Joules Consumed Socket1 Energy Consumption']:
            #Y_tmp = df[columns_j] - 40
            Y_tmp = df[columns_j]
            Y = Y_tmp.values.tolist()
            val.append(Y)
            label.append('{} {} {} {}'.format(info[1], info[5], info[2], label_j))    
        else:
            Y = df[columns_j].values.tolist()
            val.append(Y)
            label.append('{} {} {} {}'.format(info[1], info[5], info[2], label_j))
    
    return val, label

# Function to extract the information of the daqconf file and print daqconf, and cpupinning info.
def json_info(file_daqconf, file_core, input_directory, input_dir, var, pdf, if_pdf=False, repin_threads_file=None):   
    emu_mode = None
    with open('{}/daqconfs/{}.json'.format(input_directory, file_daqconf), 'r') as f:
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

    data_list = cpupining_info(input_directory, file_cpupins, var)
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

        for l, value_l in enumerate(data_readout):
            if value_l in ['latency_buffer_size','generate_periodic_adc_pattern','use_fake_cards','enable_raw_recording', 'raw_recording_output_dir','enable_tpg','tpg_threshold','tpg_algorithm']: 
                pdf.write(5, '    * {}: {} \n'.format(value_l, data_readout_list[value_l]))
            else:
                pass
        for m, value_m in enumerate(data_readout):
            if value_m in ['thread_pinning_file']: 
                if repin_threads_file:
                    pdf.write(5, '    * {}: {} \n'.format(value_m, repin_threads_file))
                else:
                    pdf.write(5, '    * {}: {} \n'.format(value_m, data_readout_list[value_m]))

            else:
                pass
            
    emu_mode = True if data_readout_list['generate_periodic_adc_pattern'] else False
    pinning_table, cpu_core_table, cpu_utilization_table, cpu_utilization_maximum_table = extract_table_data(input_dir, file_core, data_list, emu_mode=emu_mode)
    pdf.ln(5)
    table_cpupins(columns_data=[pinning_table, cpu_core_table, cpu_utilization_table, cpu_utilization_maximum_table], pdf=pdf, if_pdf=if_pdf)

# Function to extract the information of the cpupinning file.
def cpupining_info(input_dir, file, var):
    with open('{}/cpupins/{}'.format(input_dir, file), 'r') as ff:
        data_cpupins = json.load(ff)
        info_daq_application = json.dumps(data_cpupins['daq_application']['--name {}'.format(var)], skipkeys = True, allow_nan = True)
        data_list = json.loads(info_daq_application)
        
    return data_list

# Function to extract the "CPU" and "Utilization" of the pins from the CSV file.
def core_utilization(input_dir, file):
    CPU_plot, User_plot = [], []
    
    info = break_file_name(file)
    data_frame = pd.read_csv('{}/{}.csv'.format(input_dir, file))

    maxV = data_frame['CPU'].max()
    minV = data_frame['CPU'].min()

    for j in range(minV, maxV + 1):
        CPU_plot.append(j)
        df = data_frame.loc[data_frame['CPU'] == j]
        User_max = df['user (%)'].max()
        User_plot.append(User_max)

    return CPU_plot, User_plot

# Function to format, combine and calculate the data to be printed in the table.
def extract_table_data(input_dir, file_core, data_list, emu_mode):
    pinning_table, cpu_core_table, cpu_utilization_table, cpu_utilization_maximum_table, max_tmp = [], [], [], [], []
    cpu_core, cpu_utilization = core_utilization(input_dir, file_core)
    deno, sum_utilization = 0, 0

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
            cpu_cores = [int(num) for num in cpu_cores_i.split(',')]
        except ValueError:
            print('Check the format of the cpu pinning file. The ["#,#"] or "#-#" will not work.')

        for core_i in cpu_cores:
            deno += 1
            sum_utilization += cpu_utilization[core_i] 
            max_tmp.append(cpu_utilization[core_i])
        
        utilization_average = round((sum_utilization / deno), 2)
        #print('utilization_average, sum_utilization, deno = ', utilization_average, sum_utilization, deno)
        #print('max_tmpo = ', max_tmp)
        #print('max(max_tmp) = ', max(max_tmp))
        cpu_utilization_table.append(utilization_average)
        cpu_utilization_maximum_table.append(max(max_tmp))
        deno, sum_utilization = 0, 0                # Reset variables for the next iteration

    return pinning_table, cpu_core_table, cpu_utilization_table, cpu_utilization_maximum_table

# Function to create the cpupins utilization table base in the data suplied as input. The input "columns_data" comes from the extract_table_data funtion.
def table_cpupins(columns_data, pdf, if_pdf=False):
    if not columns_data:
        print('you are missing the table data')
        return

    rows_data = []
    headers = ['Pinning', 'CPU cores', 'CPU ave (%)', 'CPU max (%)']
    rows_data.append(headers)
    
    # Transpose the data to convert columns to rows
    line = list(map(list, zip(*columns_data)))
    rows_data = rows_data + line
    
    line_height = pdf.font_size * 2.1
    col_width = [pdf.epw/7.2, pdf.epw/2., pdf.epw/7.5, pdf.epw/7.5]
    
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

# Function to append two or more givelists, the input is a list of lists to append to the first list on the input.
def append_lists(list_of_lists):
    for i, list_i in enumerate(list_of_lists):
        if not i == 0:
            for j in list_i:
                list_of_lists[0].append(j) 
        
    return list_of_lists[0]

def get_parents(cpus_node):
    parents0_tmp = cpus_node[0]
    parents1_tmp = cpus_node[1]
    parents0 = parents0_tmp[1:3]
    parents1 = parents1_tmp[1:3]
    #parents = append_lists(parents0, parents1)
    parents = parents0 + parents1
    
    return parents 

def pins_couple(node, cpus, pin_type, top):
    l = cpus[0]
    m = cpus[1]
    minimum = 100 if node != 1 else 148

    if top[0] != 0:
        for i in range(minimum, minimum + top[0]):
            j = 3+i-minimum
            if top[0] == 24:
                pin_str = f'"{pin_type[0]}-({i}|{i+top[0]})":'
            elif top[0] == 12:
                pin_str = f'"{pin_type[0]}-({i}|{i+top[0]}|{i+top[0]*2}|{i+top[0]*3})":'
            elif top[0] == 8:
                pin_str = f'"{pin_type[0]}-({i}|{i+top[0]}|{i+top[0]*2}|{i+top[0]*3}|{i+top[0]*4}|{i+top[0]*5})":'
            elif top[0] == 6:
                pin_str = f'"{pin_type[0]}-({i}|{i+top[0]}|{i+top[0]*2}|{i+top[0]*3}|{i+top[0]*4}|{i+top[0]*5}|{i+top[0]*6}|{i+top[0]*7})":'
            elif top[0] == 4:
                pin_str = f'"{pin_type[0]}-({i}|{i+top[0]}|{i+top[0]*2}|{i+top[0]*3}|{i+top[0]*4}|{i+top[0]*5}|{i+top[0]*6}|{i+top[0]*7}|{i+top[0]*8}|{i+top[0]*9}|{i+top[0]*10}|{i+top[0]*11})":'
            elif top[0] == 3:
                pin_str = f'"{pin_type[0]}-({i}|{i+top[0]}|{i+top[0]*2}|{i+top[0]*3}|{i+top[0]*4}|{i+top[0]*5}|{i+top[0]*6}|{i+top[0]*7}|{i+top[0]*8}|{i+top[0]*9}|{i+top[0]*10}|{i+top[0]*11}|{i+top[0]*12}|{i+top[0]*13}|{i+top[0]*14}|{i+top[0]*15})":'
            else:
                print('ERROR in {}', pin_type[0])
                pass

            print(f'{pin_str} "{l[j]},{m[j]}",')

    if top[1] != 0:
        print('      ')
        for i in range(minimum, minimum + top[1]):
            j = 3+i-minimum
            if top[1] == 24:
                pin_str = f'"{pin_type[1]}-({i}|{i+top[1]})":'
            elif top[1] == 12:
                pin_str = f'"{pin_type[1]}-({i}|{i+top[1]}|{i+top[1]*2}|{i+top[1]*3})":'
            elif top[1] == 8:
                pin_str = f'"{pin_type[1]}-({i}|{i+top[1]}|{i+top[1]*2}|{i+top[1]*3}|{i+top[1]*4}|{i+top[1]*5})":'
            elif top[1] == 6:
                pin_str = f'"{pin_type[1]}-({i}|{i+top[1]}|{i+top[1]*2}|{i+top[1]*3}|{i+top[1]*4}|{i+top[1]*5}|{i+top[1]*6}|{i+top[1]*7})":'
            else:
                print('ERROR in {}', pin_type[1])
                pass

            print(f'{pin_str} "{l[top[0]+j]},{m[top[0]+j]}",')

    if top[2] != 0:
        print('      ')
        for i in range(minimum, minimum + top[1]):
            j = 3+i-minimum
            if top[1] == 24:
                pin_str = f'"{pin_type[2]}-({i}|{i+top[1]})":'
            elif top[1] == 12:
                pin_str = f'"{pin_type[2]}-({i}|{i+top[1]}|{i+top[1]*2}|{i+top[1]*3})":'
            elif top[1] == 8:
                pin_str = f'"{pin_type[2]}-({i}|{i+top[1]}|{i+top[1]*2}|{i+top[1]*3}|{i+top[1]*4}|{i+top[1]*5})":'
            elif top[1] == 6:
                pin_str = f'"{pin_type[2]}-({i}|{i+top[1]}|{i+top[1]*2}|{i+top[1]*3}|{i+top[1]*4}|{i+top[1]*5}|{i+top[1]*6}|{i+top[1]*7})":'
            else:
                print('ERROR in {}', pin_type[1])
                pass

            print(f'{pin_str} "{l[top[0]+j]},{m[top[0]+j]}",')   

    if top[3] != 0:      
        print('      ')
        for i in range(minimum, minimum + 1):    
            j = 3+i-minimum
            pin_str = f'"{pin_type[1]}-0":'
            pin_str_record = f'"{pin_type[2]}-0":'
            print(f'{pin_str} [{l[top[0]+top[1]+j]},{m[top[0]+top[1]+j]}],')
            if top[2] != 0:
                print(f'{pin_str_record} [{l[top[0]+top[1]+j]},{m[top[0]+top[1]+j]}],')

        print('      ')
        for i in range(minimum, minimum + top[3]):
            j = 3+i-minimum
            if top[3] == 24:
                pin_str = f'"{pin_type[3]}-{i}":'
            elif top[3] == 12:
                pin_str = f'"{pin_type[3]}-({i}|{i+top[3]*2})":'
            elif top[3] == 8:
                pin_str = f'"{pin_type[3]}-({i}|{i+top[3]*2}|{i+top[3]*4})":'
            elif top[3] == 6:
                pin_str = f'"{pin_type[3]}-({i}|{i+top[3]*2}|{i+top[3]*4}|{i+top[3]*6})":'
            elif top[3] == 4:
                pin_str = f'"{pin_type[3]}-({i}|{i+top[0]*2}|{i+top[0]*4}|{i+top[0]*6}|{i+top[0]*8}|{i+top[0]*10})":'
            else:
                print('ERROR in {}', pin_type[3])
                pass

            print(f'{pin_str} "{l[top[0]+top[1]+1+j]}",')

        for i in range(minimum, minimum + top[3]):
            j = 3+i-minimum   
            k = i+top[3]
            if top[3] == 24:
                pin_str = f'"{pin_type[3]}-{k}":'
            elif top[3] == 12:
                pin_str = f'"{pin_type[3]}-({k}|{k+top[3]*2})":'
            elif top[3] == 8:
                pin_str = f'"{pin_type[3]}-({k}|{k+top[3]*2}|{k+top[3]*4})":'
            elif top[3] == 6:
                pin_str = f'"{pin_type[3]}-({k}|{k+top[3]*2}|{k+top[3]*4}|{k+top[3]*6})":'
            elif top[3] == 4:
                pin_str = f'"{pin_type[3]}-({i}|{i+top[0]*2}|{i+top[0]*4}|{i+top[0]*6}|{i+top[0]*8}|{i+top[0]*10})":'
            else:
                print('ERROR in {}', pin_type[3])
                pass

            print(f'{pin_str} "{m[top[0]+top[1]+1+j]}",')

def pins_type_list(node, cpus, pin_type, top, step):
    a = cpus[0]
    b = cpus[1]
    x1, x2, y1, y2 = parents = get_parents(cpus)

    j = 3
    k = j+int(top[0]/2) if top[3] != 0 else j

    if top[4] != 0:
        l = k+int(top[3]/2) if top[2] != 0 else k
        m = l+1 if top[2] != 0 else k

    else:
        l = k+int(top[3]/2)
        m = l+1

    for i in range(x2+step, x2+step + int(top[0]/2), step):
        pin_str = f'"{pin_type[0]}-{i}":'
        print(f'                {pin_str} "{i}",')  

    for i in range(y2+step, y2+step + int(top[0]/2), step):
        pin_str = f'"{pin_type[0]}-{i}":'
        print(f'                {pin_str} "{i}",') 

    print('      ')
    if node == 0:
        pin_str_fakeprod = f'"{pin_type[1]}-1..":'
    else: 
        pin_str_fakeprod = f'"{pin_type[1]}-2..":'

    pin_num_fakeprod = f'"{a[j]},{a[j+1]},{a[j+2]},{a[j+3]},{b[j]},{b[j+1]},{b[j+2]},{b[j+3]}"'
    print(f'                {pin_str_fakeprod} {pin_num_fakeprod},')

    if top[3] != 0:
        print('      ')
        if node == 0:
            pin_str_consumer = f'"{pin_type[3]}-1..":'
        else:
            pin_str_consumer = f'"{pin_type[3]}-2..":'

        if top[3] == 12:
            pin_num_consumer = f'"{a[k]},{a[k+1]},{a[k+2]},{a[k+3]},{a[k+4]},{a[k+5]},{b[k]},{b[k+1]},{b[k+2]},{b[k+3]},{b[k+4]},{b[k+5]}"'
        elif top[3] == 14:
            pin_num_consumer = f'"{a[k]},{a[k+1]},{a[k+2]},{a[k+3]},{a[k+4]},{a[k+5]},{a[k+6]},{b[k]},{b[k+1]},{b[k+2]},{b[k+3]},{b[k+4]},{b[k+5]},{b[k+6]}"'
        elif top[3] == 18:
            pin_num_consumer = f'"{a[k]},{a[k+1]},{a[k+2]},{a[k+3]},{a[k+4]},{a[k+5]},{a[k+6]},{a[k+7]},{a[k+8]},{b[k]},{b[k+1]},{b[k+2]},{b[k+3]},{b[k+4]},{b[k+5]},{b[k+6]},{b[k+7]},{b[k+8]}"'
        elif top[3] == 24:
            pin_num_consumer = f'"{a[k]},{a[k+1]},{a[k+2]},{a[k+3]},{a[k+4]},{a[k+5]},{a[k+6]},{a[k+7]},{a[k+8]},{a[k+9]},{a[k+10]},{a[k+11]},{b[k]},{b[k+1]},{b[k+2]},{b[k+3]},{b[k+4]},{b[k+5]},{b[k+6]},{b[k+7]},{b[k+8]},{b[k+9]},{b[k+10]},{b[k+11]}"'
        elif top[3] == 30:
            pin_num_consumer = f'"{a[k]},{a[k+1]},{a[k+2]},{a[k+3]},{a[k+4]},{a[k+5]},{a[k+6]},{a[k+7]},{a[k+8]},{a[k+9]},{a[k+10]},{a[k+11]},{a[k+12]},{a[k+13]},{a[k+14]},{b[k]},{b[k+1]},{b[k+2]},{b[k+3]},{b[k+4]},{b[k+5]},{b[k+6]},{b[k+7]},{b[k+8]},{b[k+9]},{b[k+10]},{b[k+11]},{b[k+12]},{b[k+13]},{b[k+14]}"'
        elif top[3] == 36:
            pin_num_consumer = f'"{a[k]},{a[k+1]},{a[k+2]},{a[k+3]},{a[k+4]},{a[k+5]},{a[k+6]},{a[k+7]},{a[k+8]},{a[k+9]},{a[k+10]},{a[k+11]},{a[k+12]},{a[k+13]},{a[k+14]},{a[k+15]},{a[k+16]},{a[k+17]},{b[k]},{b[k+1]},{b[k+2]},{b[k+3]},{b[k+4]},{b[k+5]},{b[k+6]},{b[k+7]},{b[k+8]},{b[k+9]},{b[k+10]},{b[k+11]},{b[k+12]},{b[k+13]},{b[k+14]},{b[k+15]},{b[k+16]},{b[k+17]}"'
        elif top[3] == 42:
            pin_num_consumer = f'"{a[k]},{a[k+1]},{a[k+2]},{a[k+3]},{a[k+4]},{a[k+5]},{a[k+6]},{a[k+7]},{a[k+8]},{a[k+9]},{a[k+10]},{a[k+11]},{a[k+12]},{a[k+13]},{a[k+14]},{a[k+15]},{a[k+16]},{a[k+17]},{a[k+18]},{a[k+19]},{a[k+20]},{b[k]},{b[k+1]},{b[k+2]},{b[k+3]},{b[k+4]},{b[k+5]},{b[k+6]},{b[k+7]},{b[k+8]},{b[k+9]},{b[k+10]},{b[k+11]},{b[k+12]},{b[k+13]},{b[k+14]},{b[k+15]},{b[k+16]},{b[k+17]},{b[k+18]},{b[k+19]},{b[k+20]}"'
        else:
            pass

        print(f'                {pin_str_consumer} {pin_num_consumer},')

    if top[4] != 0:
        print('      ')
        if node == 0:
            pin_str_recording = f'"{pin_type[4]}-1..":'
        else:
            pin_str_recording = f'"{pin_type[4]}-2..":'

        if top[3] == 12:
            pin_num_recording = f'"{a[k]},{a[k+1]},{a[k+2]},{a[k+3]},{a[k+4]},{a[k+5]},{b[k]},{b[k+1]},{b[k+2]},{b[k+3]},{b[k+4]},{b[k+5]}"'
        elif top[3] == 14:
            pin_num_recording = f'"{a[k]},{a[k+1]},{a[k+2]},{a[k+3]},{a[k+4]},{a[k+5]},{a[k+6]},{b[k]},{b[k+1]},{b[k+2]},{b[k+3]},{b[k+4]},{b[k+5]},{b[k+6]}"'
        elif top[3] == 18:
            pin_num_recording = f'"{a[k]},{a[k+1]},{a[k+2]},{a[k+3]},{a[k+4]},{a[k+5]},{a[k+6]},{a[k+7]},{a[k+8]},{b[k]},{b[k+1]},{b[k+2]},{b[k+3]},{b[k+4]},{b[k+5]},{b[k+6]},{b[k+7]},{b[k+8]}"'
        elif top[3] == 24:
            pin_num_recording = f'"{a[k]},{a[k+1]},{a[k+2]},{a[k+3]},{a[k+4]},{a[k+5]},{a[k+6]},{a[k+7]},{a[k+8]},{a[k+9]},{a[k+10]},{a[k+11]},{b[k]},{b[k+1]},{b[k+2]},{b[k+3]},{b[k+4]},{b[k+5]},{b[k+6]},{b[k+7]},{b[k+8]},{b[k+9]},{b[k+10]},{b[k+11]}"'
        elif top[3] == 30:
            pin_num_recording = f'"{a[k]},{a[k+1]},{a[k+2]},{a[k+3]},{a[k+4]},{a[k+5]},{a[k+6]},{a[k+7]},{a[k+8]},{a[k+9]},{a[k+10]},{a[k+11]},{a[k+12]},{a[k+13]},{a[k+14]},{b[k]},{b[k+1]},{b[k+2]},{b[k+3]},{b[k+4]},{b[k+5]},{b[k+6]},{b[k+7]},{b[k+8]},{b[k+9]},{b[k+10]},{b[k+11]},{b[k+12]},{b[k+13]},{b[k+14]}"'
        elif top[3] == 36:
            pin_num_recording = f'"{a[k]},{a[k+1]},{a[k+2]},{a[k+3]},{a[k+4]},{a[k+5]},{a[k+6]},{a[k+7]},{a[k+8]},{a[k+9]},{a[k+10]},{a[k+11]},{a[k+12]},{a[k+13]},{a[k+14]},{a[k+15]},{a[k+16]},{a[k+17]},{b[k]},{b[k+1]},{b[k+2]},{b[k+3]},{b[k+4]},{b[k+5]},{b[k+6]},{b[k+7]},{b[k+8]},{b[k+9]},{b[k+10]},{b[k+11]},{b[k+12]},{b[k+13]},{b[k+14]},{b[k+15]},{b[k+16]},{b[k+17]}"'
        elif top[3] == 42:
            pin_num_recording = f'"{a[k]},{a[k+1]},{a[k+2]},{a[k+3]},{a[k+4]},{a[k+5]},{a[k+6]},{a[k+7]},{a[k+8]},{a[k+9]},{a[k+10]},{a[k+11]},{a[k+12]},{a[k+13]},{a[k+14]},{a[k+15]},{a[k+16]},{a[k+17]},{a[k+18]},{a[k+19]},{a[k+20]},{b[k]},{b[k+1]},{b[k+2]},{b[k+3]},{b[k+4]},{b[k+5]},{b[k+6]},{b[k+7]},{b[k+8]},{b[k+9]},{b[k+10]},{b[k+11]},{b[k+12]},{b[k+13]},{b[k+14]},{b[k+15]},{b[k+16]},{b[k+17]},{b[k+18]},{b[k+19]},{b[k+20]}"'
        else:
            pass

        print(f'                {pin_str_recording} {pin_num_recording},')

    if top[2] != 0:   
        print('      ')
        pin_str_consumer0 = f'"{pin_type[3]}-0":'
        pin_str_recording0 = f'"{pin_type[4]}-0":'
        pin_str_tpset0 = f'"{pin_type[5]}-0":'
        pin_str_cleanup0 = f'"{pin_type[6]}-0":'
        pin_num0 = f'"{a[l]},{b[l]}"'

        print(f'                {pin_str_consumer0} {pin_num0},')
        print(f'                {pin_str_tpset0} {pin_num0},')
        print(f'                {pin_str_cleanup0} {pin_num0},')
        if top[4] != 0:
            print(f'                {pin_str_recording0} {pin_num0},')

    if top[2] != 0:
        print('      ')
        if node == 0:
            pin_str_postproc = f'"{pin_type[2]}-1..":'
        else:
            pin_str_postproc = f'"{pin_type[2]}-2..":'

        if top[2] == 12:
            pin_num_postproc = f'"{a[m]},{a[m+1]},{a[m+2]},{a[m+3]},{a[m+4]},{a[m+5]},{b[m]},{b[m+1]},{b[m+2]},{b[m+3]},{b[m+4]},{b[m+5]}"'
        elif top[2] == 14:
            pin_num_postproc = f'"{a[m]},{a[m+1]},{a[m+2]},{a[m+3]},{a[m+4]},{a[m+5]},{a[m+6]},{b[m]},{b[m+1]},{b[m+2]},{b[m+3]},{b[m+4]},{b[m+5]},{b[m+6]}"'
        elif top[2] == 18:
            pin_num_postproc = f'"{a[m]},{a[m+1]},{a[m+2]},{a[m+3]},{a[m+4]},{a[m+5]},{a[m+6]},{a[m+7]},{a[m+8]},{b[m]},{b[m+1]},{b[m+2]},{b[m+3]},{b[m+4]},{b[m+5]},{b[m+6]},{b[m+7]},{b[m+8]}"'
        elif top[2] == 21:
            pin_num_postproc = f'"{a[m]},{a[m+1]},{a[m+2]},{a[m+3]},{a[m+4]},{a[m+5]},{a[m+6]},{a[m+7]},{a[m+8]},{a[m+9]},{a[m+10]},{b[m]},{b[m+1]},{b[m+2]},{b[m+3]},{b[m+4]},{b[m+5]},{b[m+6]},{b[m+7]},{b[m+8]},{b[m+9]},{b[m+10]}"'
        elif top[2] == 24:
            pin_num_postproc = f'"{a[m]},{a[m+1]},{a[m+2]},{a[m+3]},{a[m+4]},{a[m+5]},{a[m+6]},{a[m+7]},{a[m+8]},{a[m+9]},{a[m+10]},{a[m+11]},{b[m]},{b[m+1]},{b[m+2]},{b[m+3]},{b[m+4]},{b[m+5]},{b[m+6]},{b[m+7]},{b[m+8]},{b[m+9]},{b[m+10]},{b[m+11]}"'
        elif top[2] == 30:
            pin_num_postproc = f'"{a[m]},{a[m+1]},{a[m+2]},{a[m+3]},{a[m+4]},{a[m+5]},{a[m+6]},{a[m+7]},{a[m+8]},{a[m+9]},{a[m+10]},{a[m+11]},{a[m+12]},{a[m+13]},{a[m+14]},{b[m]},{b[m+1]},{b[m+2]},{b[m+3]},{b[m+4]},{b[m+5]},{b[m+6]},{b[m+7]},{b[m+8]},{b[m+9]},{b[m+10]},{b[m+11]},{b[m+12]},{b[m+13]},{b[m+14]}"'
        elif top[2] == 36:
            pin_num_postproc = f'"{a[m]},{a[m+1]},{a[m+2]},{a[m+3]},{a[m+4]},{a[m+5]},{a[m+6]},{a[m+7]},{a[m+8]},{a[m+9]},{a[m+10]},{a[m+11]},{a[m+12]},{a[m+13]},{a[m+14]},{a[m+15]},{a[m+16]},{a[m+17]},{b[m]},{b[m+1]},{b[m+2]},{b[m+3]},{b[m+4]},{b[m+5]},{b[m+6]},{b[m+7]},{b[m+8]},{b[m+9]},{b[m+10]},{b[m+11]},{b[m+12]},{b[m+13]},{b[m+14]},{b[m+15]},{b[m+16]},{b[m+17]}"'
        elif top[2] == 42:
            pin_num_postproc = f'"{a[m]},{a[m+1]},{a[m+2]},{a[m+3]},{a[m+4]},{a[m+5]},{a[m+6]},{a[m+7]},{a[m+8]},{a[m+9]},{a[m+10]},{a[m+11]},{a[m+12]},{a[m+13]},{a[m+14]},{a[m+15]},{a[m+16]},{a[m+17]},{a[m+18]},{a[m+19]},{a[m+20]},{b[m]},{b[m+1]},{b[m+2]},{b[m+3]},{b[m+4]},{b[m+5]},{b[m+6]},{b[m+7]},{b[m+8]},{b[m+9]},{b[m+10]},{b[m+11]},{b[m+12]},{b[m+13]},{b[m+14]},{b[m+15]},{b[m+16]},{b[m+17]},{b[m+18]},{b[m+19]},{b[m+20]}"'
        else:
            pass

        print(f'                {pin_str_postproc} {pin_num_postproc},')


    