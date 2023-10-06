# performancetest/docs


## DAQ performance tests

The performance test suite has the following dependencies to install:

```
yum install numactl
yum install hwloc-gui
yum install htop
yum install sysstat

git clone https://github.com/DUNE-DAQ/performancetest.git
git clone https://github.com/DUNE-DAQ/nanorc.git
cd nanorc/; pip install .
```

### PCM Grafana

To monitor the performance of an Intel CPU server while running DAQ apps, we use PCM (For AMD machines, see next section). This can then be displayed on a grafana dashboard. This will actively monitor metrics such as memory bandwidth, CPU utilization, energy consumption, cache hit ratio, inter-socket data rates, and others. This can be used to measure KPIs such as readout server memory bandwidth performance as number of DAQ data links is scaled.

First you need to clone PCM here https://github.com/intel/pcm. Then instructions to build it, and scripts to run PCM-Grafana, which have been modified for Centos 8 to use podman containers instead of docker containers, are given here https://github.com/DUNE-DAQ/performancetest/tree/develop/grafana#readme

For an older OS or if you use docker instead of podman, the original scripts and instructions are here https://github.com/intel/pcm/tree/master/scripts/grafana.

To configure the PCM-Grafana dashboard:
1. Ensure that the data source is configured to prometheus at the correct host address and port (default port is 9090). Note that this is the host address of prometheus and grafana, not PCM.
2. Go to dashboards and import https://github.com/DUNE-DAQ/performancetest/blob/develop/grafana/PCM_Dashboard-1665067579560.json

### uProf Grafana

To monitor the performance of an AMD CPU server while running DAQ apps, we use uProf. Since a grafana integration is not yet supported by AMD, the process is less smooth than for the Intel case. Nonetheless, installing and running the tool, as well as monitoring with grafana, will all be described in this section.

The uProf tool rpm can be downloaded from here https://developer.amd.com/amd-uprof/#download

And then with root privileges, uProf is installed and NMI watchdog is disabled (required for uProf to run) as follows: 
```
yum install amduprof-x.y-z.x86_64.rpm
echo  > 0 /proc/sys/kernel/nmi_watchdog 
```

The uProfPcm tool is used to monitor most cpu metrics (eg. memory bandwidth, cpu utilization, cache hits, ...), however to monitor power consumption we need to add the uProfCLI timechart tool. Some other disadvantages are uProf requires a run duration and the output needs to be reformatted so grafana can parse it, meaning the process requires more attention and doesn't support live monitoring. 

Monitoring a link scaling test with this tool is done as follows (after running the script to generate the configurations described [below](https://github.com/DUNE-DAQ/performancetest#link-scaling-performance-tests)):

```
sudo ./scripts/start_uprof.sh <output_dir>

# Once test is complete, run this script to reformat the uprof output
# Input uprof files (check output_dir) and reformatted file names
python3 grafana/uprof_csv_formatter.py <pcm_file> <pcm_file_reformatted> <timechart_file> <timechart_file_reformatted>
```

Then configure grafana to plot the metrics. The same grafana instance can be used as for the Intel case. In the grafana browser, go to Configuration->Plugins and install the CSV plugin. Configure two CSV datasources in local mode, one for the reformatted uProfPcm file, and one for the timechart. For local access, the data files should be saved to either `/var/lib/grafana/csv` or the volume mount `grafana/grafana_volume/csv`. Then upload the [uProfPcm dashboard](https://github.com/DUNE-DAQ/performancetest/blob/develop/grafana/uProf_PCM_Dashboard.json). 

### CPU pinning

In order to optimize the server for a high performance use case such as this, we must use CPU pinning, which binds processes to a CPU thread to prevent the latency involved in moving the process to a different thread and re-caching the data. First there are some tools to explore the hardware topology to determine the appropriate pinning configuration. 

```
# For CPU pinning to work, the NUMA daemon needs to be disabled. Check its status:
service numad status
# And run this if it's enabled
sudo service numad stop  

# To list the NUMA nodes and their associated CPU numbers
numactl -H

# To get a graphical representation of NUMA nodes and hardware topology (opens a pop-up window)
lstopo

# To determine the NUMA node of felix card in PCIE
lspci | grep CERN  # outputs a hardware address of the form <aa:bb.c> 
lspci -s <hw-address> -vvv | grep NUMA

# This next tool may or may not be useful
# To monitor cpu utilization by core, to diagnose if the pinning is working
htop
```

Since cpu pinning configurations are fully dependent on hardware topology, different servers may need different configs. The important thing to look for is how cores/threads are distributed across NUMA nodes. Example configurations can be found [here](https://github.com/DUNE-DAQ/performancetest/tree/develop/cpupins) and [here](https://github.com/DUNE-DAQ/readoutlibs/blob/develop/config/cpupins).

### Stream scaling performance tests

The readout app performance test for a particular system configuration will be described here, with scaling for 8, 16, 24, 32, 40, and 48 streams. This will produce configurations for these streams, hosting readout locally, and all other apps at a given host. At 12 minutes per run (10m run, 2m cooldown), this full test is expected to take just under 2 hours. Ensure first that PCM monitoring is active so that results can be exported from Grafana. The stream scaling tests were run with fddaq-v4.1.0.

```
# Run this only once to disable higher-level core sleep states
sudo ./scripts/cpu-perf-mode.sh
```

### Stream scaling SNB recording performance test

This is a performance test for the SNB recording, with scaling for 8, 16, 24, 32, 40, and 48 streams. It is configured with software TPG enabled, CPU pinning, non-local hosting for non-readout apps, and raw recording enabled. The recording is run for the first 100s of the 10 minute run per stream, and requires ~1TB of space in the recording directory. The results can be exported from the grafana monitoring as usual. And it will again take about 5 hours to complete.

### RAID throughput

Recording to RAID disks should have a throughput of about 880 MB/s per data link. The throughput can be plotted, scaled down by the number of data links, for each run in the test. After running the performance test with recording to disk, view the RAID throughput with: `./analysis/iostat_plotter.py <test_directory>`

