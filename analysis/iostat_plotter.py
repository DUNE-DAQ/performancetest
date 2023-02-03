# input directory to iostat files, output plot of disk throughput
# Notes: we assume sampling rate of 1s for 120s, and data is in MB/s. Consider moving to JSON for clarity

import glob
import sys
import re
import matplotlib.pyplot as plt
import numpy as np

filename = '/mnt/dunedaq/dunedaq-v3.1.0/readout_test/snb_write_superdune/'
n=24

def file_parser(filename):
    iostat_file = open(filename, 'r')
    lines = iostat_file.readlines()

    disk_throughput = []
    working_sum = 0.0
    for line in lines:
        if 'Device' in line:
            disk_throughput += [working_sum]
            working_sum = 0.0
        if 'nvme' in line:
            line = re.split('\s+', line)
            working_sum += float(line[3])
    
    iostat_file.close()

    # remove first two elements and any leading zeroes
    #disk_throughput = disk_throughput[2:]
    while disk_throughput[0]<100:
        tmp = disk_throughput.pop(0)

    return np.array(disk_throughput)

def dir_parser(directoryname):
    colours = plt.cm.jet(np.linspace(0,1,n))
    for i in range(1,n+1):
        filename = 'iostat_n{}.txt'.format(i)
        filepath = directoryname + filename
        disk_throughput = file_parser(filepath)
        disk_throughput_scaled = disk_throughput / i
        #print(disk_throughput_scaled)
        
        label = str(i) + ' links'
        plt.plot(disk_throughput_scaled, label=label, color=colours[i-1])
    plt.legend(bbox_to_anchor=(1.25,0.6), loc='center right')
    plt.grid(axis='y')
    plt.title('Throughput to RAID0 *8 drives, scaled down by number of data links')
    plt.xlabel('time (s)')
    plt.ylabel('disk throughput (MB/s)')
    plt.tight_layout()
    plt.savefig('record_disk_throughput.png')


def main():
    args=sys.argv

    dir_parser(filename)

if __name__ == "__main__":
    main()

