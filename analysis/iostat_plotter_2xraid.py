# input directory to iostat files, output plot of disk throughput
# Notes: we assume sampling rate of 1s for 120s, and data is in MB/s. Consider moving to JSON for clarity

import glob
import sys
import re
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

filename = '/mnt/dunedaq/dunedaq-v3.1.0/readout_test/superdune_write_2xraid/'
n=24

def file_parser(filename, device='nvme'):
    iostat_file = open(filename, 'r')
    lines = iostat_file.readlines()

    disk_throughput = []
    working_sum = 0.0
    for line in lines:
        if 'Device' in line:
            disk_throughput += [working_sum]
            working_sum = 0.0
        #if device in line:
        if ('nvme0' in line) or ('nvme1' in line) or ('nvme2' in line) or ('nvme3' in line):
            line = re.split('\s+', line)
            working_sum += float(line[3])
    
    iostat_file.close()

    # remove first two elements and any leading zeroes
    #print(len(disk_throughput))
    disk_throughput = disk_throughput[2:]
    #while disk_throughput[0]<100:
    #    tmp = disk_throughput.pop(0)

    return np.array(disk_throughput)

def dir_parser(directoryname):
    #colours1 = mpl.colormaps['Blues'].resampled(n)
    #colours2 = mpl.colormaps['Reds'].resampled(n)
    #colour_i = np.linspace(0,1,n)
    colours = plt.cm.jet(np.linspace(0,1,n))

    # loop over first raid device
    div = 1
    for i in range(1,n+1): 
        if i < 13:
            continue
        filename = 'iostat_n{}.txt'.format(i)
        filepath = directoryname + filename
        disk_throughput = file_parser(filepath, 'md127')
        disk_throughput_scaled = disk_throughput / div
        label = 'link ' + str(i)
        plt.plot(disk_throughput_scaled, label=label, color=colours[i-1])
        div += 1
    
    # loop over second raid device
    #for i in range(13,n+13):
    #    filename = 'iostat_n{}.txt'.format(i)
    #    filepath = directoryname + filename
    #    disk_throughput = file_parser(filepath, 'md126')
    #    disk_throughput_scaled = disk_throughput / (i-13)
    #    label = 'link ' + str(i) + ' (samsung)'
    #    plt.plot(disk_throughput_scaled, label=label, color=colours2(colour_i[i-13]))
    
    plt.legend(bbox_to_anchor=(1.25,0.6), loc='center right')
    plt.grid(axis='y')
    plt.title('Throughput to RAID0 *4 drives (samsung on links 13-24), scaled down by number of data links')
    plt.xlabel('time (s)')
    plt.ylabel('disk throughput (MB/s)')
    plt.tight_layout()
    plt.savefig('superdune_disk_throughput_2xraid.png')


def main():
    args=sys.argv

    dir_parser(filename)

if __name__ == "__main__":
    main()

