import numpy as np
import os
import matplotlib.pyplot as plt
import csv
import sys
import re

# Parameters
lines_to_save_iostat = (0, 8, 11, 22)
save_freq_test_buffer_ms = 100
#iostat_legend = {"md127":"nvm_raid0", "nvme0n1":"nvm_raid0", "nvme1n1":"nvm_raid0", "nvme2n1":"nvm_raid0", "nvme3n1":"nvm_raid0",
#        "md126":"nvm_raid1", "nvme4n1":"nvm_raid1", "nvme5n1":"nvm_raid1", "nvme6n1":"nvm_raid1", "nvme7n1":"nvm_raid1"}
iostat_legend = {"nvme10n1":"singledisk"}

# Natural sorting function
def atoi(text):
    return int(text) if text.isdigit() else text

# Natural sorting files 
def natural_keys(text):
    return [ atoi(c) for c in re.split(r'(\d+)', text) ]

def fstrim_time_reader(file):
    f = open(file, 'r')
    output = []
    pattern_text = r'(?P<minutes>\d+)m(?P<seconds>\d+)\.(?P<ms>\d+)s'
    pattern_fstrim = re.compile(pattern_text)
    
    for line in f.readlines():
        if line.split('\t')[0] != 'real':
            continue
            
        real_time_str = line.split('\t')[1]
        groups = pattern_fstrim.match(real_time_str).groupdict()
        real_time = float(groups['minutes'])*60.0 + float(groups['seconds']) + float(groups['ms'])/1000.0
        output.append(round(real_time,3))
    
    return output

# Parse datafiles and add to data dict
def add_data(file, file_path, data):

    print("Reading "+file+" dataset")

    # Different data manipulation depending on the source
    if "iostat" in file:
        df = np.loadtxt(file_path, dtype=str, delimiter=';', skiprows=0, usecols=lines_to_save_iostat)
    elif "readout" in file:
        df = np.loadtxt(file_path, delimiter=';', skiprows=3, usecols=0)
    elif "time" in file:
        df = fstrim_time_reader(file_path)

    device_name = file.split('-')[0]

    # Create dictionary entry for current device
    if not device_name in data:
        data[device_name] = {'iostat': {}, 'thread': {}, 'fstrim': []}

    # Save data
    # types of data: iostat, thread, fstrim
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
    elif "readout" in file:
        # thread data, save all in one list
        data[device_name]['thread'][file.split('-')[2]] = df[:]
    elif "time" in file:
        data[device_name]['fstrim'] += df

# parse metric from iostat data in data dict, and plot on axs
def iostat_plotter(axs, axs_index, data, metric, device):
    for iostat_device in data[device]['iostat']:
        if iostat_device not in iostat_legend.keys():
            continue
        elif iostat_legend[iostat_device] != device:
            continue
        elif "nvme" in iostat_device:
            axs[axs_index].plot(np.arange(0, len(data[device]['iostat'][iostat_device][metric])-1, 1), data[device]['iostat'][iostat_device][metric][1:], '--', label=iostat_device)
        else:
            axs[axs_index].plot(np.arange(0, len(data[device]['iostat'][iostat_device][metric])-1, 1), data[device]['iostat'][iostat_device][metric][1:], '-', label=iostat_device)

# List all subfolders
def compute_folder(test_results_dir, data):
    test_name = test_results_dir.split('/')[-1]
    top_level = '/'.join(test_results_dir.split('/')[0:-2])
    plot_output_dir = os.path.join(top_level, 'plots')
    print("looking at test: ", test_name)

    for file in sorted(os.listdir(test_results_dir), key=natural_keys):
        file_path = os.path.join(test_results_dir, file)
        
        if os.path.isdir(file_path):
            print("WARNING directory structure is wierd, at ", file_path)
        # checking if it is a file
        elif os.path.isfile(file_path) and (file.endswith('.csv') or file.endswith('.time')):
            add_data(file,file_path,data)
                    
    # Generating summary plots after reading all files in folder
    print(data.keys())
    for device in data:
        
        fig, axs = plt.subplots(2, figsize=(17,20))
        max_threads = 0
                        
        # thread summary figure
        print("starting thread summary figure", device)
        for thread in data[device]['thread']:
            axs[0].plot(np.arange(0, len(data[device]['thread'][thread])*save_freq_test_buffer_ms/1000.0, save_freq_test_buffer_ms/1000.0), data[device]['thread'][thread][:], '-', label=thread)
            if len(data[device]['thread'][thread]) > max_threads:
                max_threads = max(data[device]['thread'][thread])

        axs[0].set_xlabel('time (s)')
        axs[0].set_ylabel('write speed (MiB/s)')
        axs[0].set_ylim([0, max_threads*1.1])
        axs[0].tick_params(axis='x', labelrotation=45)
        axs[0].legend(loc='lower right')
        axs[0].set_title(device+' individual tasks write speed')

        # write speed summary figure
        iostat_plotter(axs, 1, data, 'wMB/s', device)
        
        axs[1].set_xlabel('time (s)')
        axs[1].set_ylabel('write speed (MB/s)')
        axs[1].tick_params(axis='x', labelrotation=45)
        axs[1].legend(loc='upper right')
        axs[1].set_title(device+' Device write speed')
        
        plt.savefig(os.path.join(plot_output_dir, device+'_'+test_name+'_resume.png'))
        plt.close()
        
        
        
        
        fig, axs = plt.subplots(2, figsize=(17,20))

        # Device utilization summary figure 
        iostat_plotter(axs, 0, data, 'util', device)

        axs[0].set_xlabel('time (s)')
        axs[0].set_ylabel('device utilization (%)')
        axs[0].tick_params(axis='x', labelrotation=45)
        axs[0].legend(loc='upper right')
        axs[0].set_title(device+' Device utilization')
        
        
        # write await summary figure
        iostat_plotter(axs, 1, data, 'w_await', device)
        
        axs[1].set_xlabel('time (s)')
        axs[1].set_ylabel('w_await (ms)')
        axs[1].tick_params(axis='x', labelrotation=45)
        axs[1].legend(loc='upper right')
        axs[1].set_title(device+' average write request latency')
        
        plt.savefig(os.path.join(plot_output_dir, device+'_'+test_name+'_detail.png'))
        plt.close()


if __name__ == '__main__':
    # Check if input folder is given
    if len(sys.argv) != 2:
        print("Usage: python3 generate_graph_rate_limited_test.py <data_folder>")
        sys.exit(1)

    input_folder = sys.argv[1]
    output_folder = input_folder
    plot_output_dir = os.path.join(output_folder, 'plots')
    if not os.path.exists(plot_output_dir):
        os.makedirs(plot_output_dir)

    # loop through each results dir structure. Each test for each device
    for device_folder in sorted(os.listdir(input_folder), key=natural_keys):
        device_dir = os.path.join(input_folder, device_folder)
        if device_folder == 'plots':
            continue

        trim_times = []

        if os.path.isdir(device_dir):
            for test_folder in sorted(os.listdir(device_dir), key=natural_keys):
                test_results_dir = os.path.join(device_dir, test_folder)
                data = {}
                compute_folder(test_results_dir, data)

                trim_times += data[device_folder]['fstrim']
        #print(device_folder, "trim time max: ", np.max(trim_times), ", trim time median: ", np.median(trim_times))
        trim_times = [str(i)+',' for i in trim_times]
        fstrim_output_file = os.path.join(plot_output_dir, device_folder+'_fstrim_times.txt')
        with open(fstrim_output_file, 'w') as f:
            f.writelines(trim_times)



