import numpy as np
import os
import matplotlib.pyplot as plt
import csv
import sys

data = {}

lines_to_save_iostat = (0, 4, 10, 15)
save_freq_test_buffer_ms = 100

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
def compute_folder(ifolder, data):
    for file in sorted(os.listdir(ifolder), key=natural_keys):
        file_path = os.path.join(ifolder, file)
        
        # For all files in subfolder
        if os.path.isdir(file_path):
            compute_folder(file_path, data)
            
            
        # checking if it is a file
        if os.path.isfile(file_path) and file.endswith('.csv'):
            
            print("Reading "+file+" dataset")
            
            # Different data manipulation depending on the source
            if "iostat" in file:
                df = np.loadtxt(file_path, dtype=str, delimiter=';', skiprows=0, usecols=lines_to_save_iostat)
            else:
                df = np.loadtxt(file_path, delimiter=';', skiprows=2, usecols=0)

            device_name = file.split('-')[0]
            
            # Create dictionary entry for current device
            if not device_name in data:
                data[device_name] = {'iostat': {}, 'thread': {}}
            
            # Save data
            # 2 types of data: iostat and thread
            if "iostat" in file:
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
                data[device_name]['thread'][file.split('-')[2]] = df[:]
                    
    # Generating summary plots after reading all files in folder
    for device in data:
        
        fig, axs = plt.subplots(2, figsize=(17,20))
        max_threads = 0
        
        # replace extremes values if inferior to threshold
        # for thread in data[device]['thread']:
        #     old_val = max(data[device]['thread'][thread])
        #     for i in range(len(data[device]['thread'][thread])):
        #         if data[device]['thread'][thread][i] < max(data[device]['thread'][thread])/1.1:
        #             data[device]['thread'][thread][i] = old_val
        #         if i > 1:
        #             old_val = sum(data[device]['thread'][thread][:i]) / len(data[device]['thread'][thread][:i])
        #         else: 
        #             old_val = max(data[device]['thread'][thread])
                            
                        
        # thread summary figure
        for thread in data[device]['thread']:
            axs[0].plot(np.arange(0, len(data[device]['thread'][thread])*save_freq_test_buffer_ms/1000, save_freq_test_buffer_ms/1000), data[device]['thread'][thread][:], '-', label=thread)
            if len(data[device]['thread'][thread]) > max_threads:
                max_threads = max(data[device]['thread'][thread])

        axs[0].set_xlabel('time (s)')
        axs[0].set_ylabel('write MiB/s')
        axs[0].set_ylim([0, max_threads*1.1])
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
        
        plt.savefig(os.path.join(ifolder, '_rate_limited_threads_resume'+'.png'))
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
        plt.savefig(os.path.join(ifolder,'_rate_limited_threads_detail'+'.png'))
        plt.close()

        data = {}


compute_folder(input_folder, data)