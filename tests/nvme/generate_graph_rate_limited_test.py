import numpy as np
import os
import matplotlib.pyplot as plt
import csv
import sys

data = {}

lines_to_save_iostat = (0, 4, 10, 15)

import re

# Natural sorting function
def atoi(text):
    return int(text) if text.isdigit() else text

# Natural sorting files 
def natural_keys(text):
    return [ atoi(c) for c in re.split(r'(\d+)', text) ]

# Check if input folder is given
if len(sys.argv) != 2:
    print("Usage: python3 compile_benchmark_results.py <data_folder>")
    sys.exit(1)

input_folder = sys.argv[1]
output_folder = input_folder

# List all subfolders
for folder in os.listdir(input_folder):
    folder_path = os.path.join(input_folder, folder)
    
    # For all files in subfolder
    if os.path.isdir(folder_path):
        for f in sorted(os.listdir(input_folder+folder+"/"), key=natural_keys):
            f_path = os.path.join(folder_path, f)
        
            # checking if it is a file
            if os.path.isfile(f_path) and f.endswith('.csv'):
                
                print("Reading "+f+" dataset")
                
                # Different data manipulation depending on the source
                if "iostat" in f:
                    df = np.loadtxt(f_path, dtype=str, delimiter=';', skiprows=0, usecols=lines_to_save_iostat)
                else:
                    df = np.loadtxt(f_path, delimiter=';', skiprows=1, usecols=0)

                device_name = f.split('-')[0]
                
                # Create dictionary entry for current device
                if not device_name in data:
                    data[device_name] = {'iostat': {}, 'thread': {}}
                
                # Save data
                # 2 types of data: iostat and thread
                if "iostat" in f:
                    # line by line to save differents disks data
                    for line in df:
                        # Initialize list if not already done
                        if not line[0] in data[device_name]['iostat']:
                            data[device_name]['iostat'][line[0]] = {'wMB/s': [], 'w_await': [], 'util': []}
                        # Save data
                        data[device_name]['iostat'][line[0]]['wMB/s'].append(float(line[1]))
                        data[device_name]['iostat'][line[0]]['w_await'].append(float(line[2]))
                        data[device_name]['iostat'][line[0]]['util'].append(float(line[3]))
                else:
                    # thread data, save all in one list
                    data[device_name]['thread'][f.split('-')[2]] = df[:]


# Generating summary plots
for device in data:
    
    fig, axs = plt.subplots(2, figsize=(17,20))
    
    # thread summary figure
    for thread in data[device]['thread']:
        axs[0].plot(np.arange(0, len(data[device]['thread'][thread])/10, 0.1), data[device]['thread'][thread][:], '-', label=thread)
        
    axs[0].set_xlabel('time (s)')
    axs[0].set_ylabel('write MiB/s')
    axs[0].tick_params(axis='x', labelrotation=45)
    axs[0].legend(loc='lower right')
    axs[0].set_title(device+' individual tasks write speed')
    
    for iostat in data[device]['iostat']:
        if "nvme" in iostat:
            # full line for raid
            axs[1].plot(np.arange(0, len(data[device]['iostat'][iostat]['wMB/s'])-1, 1), data[device]['iostat'][iostat]['wMB/s'][1:], '--', label=iostat)
        else:
            axs[1].plot(np.arange(0, len(data[device]['iostat'][iostat]['wMB/s'])-1, 1), data[device]['iostat'][iostat]['wMB/s'][1:], '-', label=iostat)
    
    # write speed summary figure
    axs[1].set_xlabel('time (s)')
    axs[1].set_ylabel('wMB/s')
    axs[1].tick_params(axis='x', labelrotation=45)
    axs[1].legend(loc='upper right')
    axs[1].set_title(device+' Write speed (individual and total raid)')
    
    plt.savefig(os.path.join(output_folder, '_'+device+'_rate_limited_threads_resume'+'.png'))
    plt.close()
    
    
    
    
    fig, axs = plt.subplots(2, figsize=(17,20))

    # Device utilization summary figure    
    for iostat in data[device]['iostat']:
        if "nvme" in iostat:
            axs[0].plot(np.arange(0, len(data[device]['iostat'][iostat]['util'])-1, 1), data[device]['iostat'][iostat]['util'][1:], '--', label=iostat)
        else:
            axs[0].plot(np.arange(0, len(data[device]['iostat'][iostat]['util'])-1, 1), data[device]['iostat'][iostat]['util'][1:], '-', label=iostat)
    
    axs[0].set_xlabel('time (s)')
    axs[0].set_ylabel('% util')
    axs[0].tick_params(axis='x', labelrotation=45)
    axs[0].legend(loc='upper right')
    axs[0].set_title(device+' Device utilization (individual and total raid)')
    
    for iostat in data[device]['iostat']:
        if "nvme" in iostat:
            axs[1].plot(np.arange(0, len(data[device]['iostat'][iostat]['w_await'])-1, 1), data[device]['iostat'][iostat]['w_await'][1:], '--', label=iostat)
        else:
            axs[1].plot(np.arange(0, len(data[device]['iostat'][iostat]['w_await'])-1, 1), data[device]['iostat'][iostat]['w_await'][1:], '-', label=iostat)
    
    # write await summary figure
    axs[1].set_xlabel('time (s)')
    axs[1].set_ylabel('w_await')
    axs[1].tick_params(axis='x', labelrotation=45)
    axs[1].legend(loc='upper right')
    axs[1].set_title(device+' Write await (individual and total raid)')
    
    plt.title(device+' resume')
    plt.savefig(os.path.join(output_folder,'_'+device+'_rate_limited_threads_detail'+'.png'))
    plt.close()