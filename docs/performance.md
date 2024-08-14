# Pre-checks
18-January-2024 - Work in progress, feedback is welcome - Danaisis Vargas and Matthew Man

The following instructions are aimed at users who want to run and create a performance report. 
- **Server configuration:**
    - cpu-perf-mode script doesn’t work because the intel-pstate driver isn’t loaded
        - cause: BIOS Speedselect mode enable/disable (basically retest what we did with OTHER perf. governors.)
- **After booting:**
    - Is the cpu-perf-mode script automatically run?
        - C1 Idle_Stats
        - Frequency is super low
        - Run this only once to disable higher-level core sleep states:
            - `cd dunedaq-v*/sourcecode/performancetest/scripts/`
            - `sudo ./cpu-perf-mode.sh`
    - Inventory: CPU core count, RAM, NUMA locality, etc.
- **Services:**
    - Install or check that they are installed:
        
        ```
        sudo yum install numactl
        sudo yum install hwloc-gui
        sudo yum install htop
        sudo yum install sysstat

        git clone https://github.com/DUNE-DAQ/performancetest.git
        git clone https://github.com/DUNE-DAQ/nanorc.git
        cd nanorc/; pip install .
        ```

    - NUMA daemon needs to be disabled.
        - Check its status: `service numad status`
        - And run this if it's enabled: `sudo service numad stop`
        - in np02/np04 this is not installed
- **Mounting RAIDs devices:**
    - `lsblk -f`
    - `lspci | grep memory`
        
        ```
        sudo mdadm -D /dev/md127
        sudo mdadm --create --verbose /dev/md127 --level=0 --raid-devices=4 /dev/nvme0n1 /dev/nvme1n1 /dev/nvme2n1 /dev/nvme3n1
        sudo mkfs.xfs /dev/md127
        sudo mkdir /mnt/nvm_raid0
        sudo mount -t xfs /dev/md127 /mnt/nvm_raid0
        ls -l /mnt/
        sudo chown <user> /mnt/nvm_raid0
        ls -l /mnt/nvm_raid0
        sudo chown <user> /mnt/nvm_raid0/fiofile
        ```

    - Make sure np04daq user has write access to the directory
    - Modify `/etc/fstab` to mount on boot up.
        - Note: this didn't work, the device file `/dev/md0` was forgotten on reboot so it crashed
    - Also, to query drive info you can use: `sudo smartctl -a /dev/nvme0n1`
- **CPU pinning:**

    In order to optimize the server for a high-performance use case such as this, we must use CPU pinning, which binds processes to a CPU thread to prevent the latency involved in moving the process to a different thread and re-caching the data. First there are some tools to explore the hardware topology to determine the appropriate pinning configuration.
    
    - Problems encountered: Parent used any cores -> allocation of LBs is undeterministic
    - To list the NUMA nodes and their associated CPU numbers: `numactl -H`
    - To determine the NUMA node of felix card in PCIE (outputs a hardware address of the form `<aa:bb.c>`):
        - `lspci | grep CERN`
            - Intel: `<b3:00.0>, <b4:00.0>`
        - `lspci -s <hw-address> -vvv | grep NUMA`
    - To get a graphical representation of NUMA nodes and hardware topology (opens a pop-up window): `lstopo`
    - This next tool may or may not be useful. To monitor cpu utilization by core, to diagnose if the pinning is working, needs to be used before sourcing dunedaq.
        - `htop`

## uProf Grafana
To monitor the performance of an AMD CPU server while running DAQ apps, we use uProf. Since a grafana integration is not yet supported by AMD, the process is less smooth than for the Intel case. Nonetheless, installing and running the tool, as well as monitoring with grafana, will all be described in this section.

The uProf tool rpm can be downloaded from here https://developer.amd.com/amd-uprof/#download

And then with root privileges, uProf is installed and NMI watchdog is disabled (required for uProf to run) as follows: 
```
yum install amduprof-x.y-z.x86_64.rpm
echo  > 0 /proc/sys/kernel/nmi_watchdog 
```

The uProfPcm tool is used to monitor most cpu metrics (eg. memory bandwidth, cpu utilization, cache hits, ...), however to monitor power consumption we need to add the uProfCLI timechart tool. Some other disadvantages are uProf requires a run duration and the output needs to be reformatted so grafana can parse it, meaning the process requires more attention and doesn't support live monitoring. 

Monitoring a link scaling test with this tool is done as follows (after running the script to generate the configurations described [below](https://github.com/DUNE-DAQ/performancetest#link-scaling-performance-tests)):

Then configure grafana to plot the metrics. The same grafana instance can be used as for the Intel case. In the grafana browser, go to Configuration->Plugins and install the CSV plugin. Configure two CSV datasources in local mode, one for the reformatted uProfPcm file, and one for the timechart. For local access, the data files should be saved to either `/var/lib/grafana/csv` or the volume mount `grafana/grafana_volume/csv`. Then upload the [uProfPcm dashboard](https://github.com/DUNE-DAQ/performancetest/blob/develop/grafana/uProf_PCM_Dashboard.json). 

# DAQ Performance Tests
- DAQ configuration generation:
    - needed files for each run: `daqconf.json`, `hrdware-map-file.txt`, and `cpupin.json`
    
- Tests:
    - **Stream scaling performance tests:** The readout app performance test for a particular system configuration will be described here, with scaling for 8, 16, 24, 32, 40, and 48 streams. This will produce configurations for these streams, hosting readout locally, and all other apps at a given host. At 12 minutes per run (10m run, 2m cooldown), this full test is expected to take just under 2 hours. Ensure first that PCM monitoring is active so that results can be exported from Grafana.
    - **Stream scaling SNB recording performance test:** This is a performance test for the SNB recording, with scaling for 8, 16, 24, 32, 40, and 48 streams. It is configured with software TPG enabled, CPU pinning, non-local hosting for non-readout apps, and raw recording enabled. The recording is run for the first 100s of the 10 minute run per stream, and requires ~1TB of space in the recording directory. The results can be exported from the grafana monitoring as usual. And it will again take about 2 hours to complete.
    - **RAID throughput:** Recording to RAID disks should have a throughput of about 880 MB/s per data link. The throughput can be plotted, scaled down by the number of data links, for each run in the test. After running the performance test with recording to disk, view the RAID throughput with:
        - `cd ../dunedaq-*/sourcecode/performancetest/analysis/`
        - `sudo ./iostat_plotter.py /mnt/nvm_raid0/iostat_plotter/`
    - **Buffered file writer:**
        - `cd ../dunedaq-*/sourcecode/performancetest/tests/`
        - `sudo ./test_bufferedfilewriter.sh /mnt/nvm_raid0/results_bufferedfilewriter_<server>`

# How to run tests
NOTE: First do the pre-checks. Not sure if cpu-perf-mode.sh is automaticlly run. 

We have 2 cases, we can run the automatic scaling or a single test at a time. Important, in the case of an INTEL server skip step 2 (it is only for AMD servers).

- The single test:
    1. Generate config file: `fddaqconf_gen -c <daqconf_file.json> --detector-readout-map-file <readoutmap.json> <test_name>`
    2. Start monitoring and CPU utilization recording (this is run on the readout server in use): 
    - for INTEL do:
        - `cd sourcecode/performancetest/scripts/; ./core_utilization_INTEL.sh <test_path> <test_name>`
    - for AMD do:
        - `cd sourcecode/performancetest/scripts/; sudo ./start_uprof.sh <test_path> <test_name> <duration_seconds>`
        - If there is an error in Power monitoring do: `cd /opt/AMDuProf_*/bin/; sudo ./AMDPowerProfilerDriver.sh install`
    3. Run the test: `nanorc <test_name> test-perf` 
        - `boot; conf; start_run <run_num>;`
        - for recording: `expert_command --timeout 10 <test_name>/<test_name>/<readout_app> ../record-cmd.json`
        - `stop_run; exit`
    
- The automatic scaling:
    1. Generate config files for streams [8, 16, 24, 32, 40, 48]:
        - `./config_gen.sh <server_readout> <NUMA_node_num> <data_format> <test> <dunedaq_version> `
            - `<server_readout>`: ex. server that will run the readout app, ex. np02srv004
            - `<NUMA_node_num>`: 0, 1, or 2 (when using both)
            - `<data_format>`: eth of wib2
            - `<test>`: ex. stream_scaling
            - `<dunedaq_version>`: ex. v4_1_1 or NFD23_09_28
    2. Start monitoring and CPU utilization recording (this is run on the readout server in use): 
    - for INTEL do:
        - `cd sourcecode/performancetest/scripts/; ./core_utilization_INTEL.sh <test_path> <test_name> <duration_minutes>`
    - for AMD do:
        - `cd sourcecode/performancetest/scripts/; sudo ./start_uprof.sh <test_path> <test_name> <duration_seconds>`
        - If there is an error in Power monitoring do: `cd /opt/AMDuProf_4.0-341/bin/; sudo ./AMDPowerProfilerDriver.sh install`
    3. Run the test: 
        - without recording: `./run_stream_scaling.sh <envir_name> <run_num_init> <test_name>`
            - Move output files from raw recording: `cd sourcecode/performancetest/scripts/; sudo ./move_raw_data.sh <test_name>/<streams>`
        - with recording: `./run_scaling_scaling_recording.sh <envir_name> <run_num_init> <test_name> <server>`

# Performance report
The report can be created using the python3 notebook `Performance_report.ipynb` Important to have all the output_files in one foder and give the correct path to them (`results_path`). Also, is necesary to expecify the path to the forder where the report will be store (`report_path`). This pahts should be diferents.

## Proccesing data from Grafana and creating the report
Note: change the paths to fit yours

To extract the data from a given dashboard in grafana:
* 'grafana_url' is:
    * 'http://np04-srv-009.cern.ch:3000'  (legacy)
    * 'http://np04-srv-017.cern.ch:31023' (new) not working for now use legacy
* 'dashboard_uid' is the unic dashboard identifiyer, you can find this information on the link of the dashboard. The dashboard_uid code is in the web link after/d/.../ 
    * for intel-r-performance-counter-monitor-intel-r-pcm dashboard dashboard_uid = '91zWmJEVk' 
* delta_time is [start, end] given in the format '%Y-%m-%d %H:%M:%S'
* host is the name of the server in study for example: "np02-srv-003"     

file_name (for performance tests): [version]-[server_app_tested]-[numa node]-[data format]-[tests_name]
* example of name: v4_1_1-np02srv003-0-eth-stream_scaling
```
grafana_url = 'http://np04-srv-009.cern.ch:3000' 
dashboard_uid = ['91zWmJEVk']
host_used = 'np02-srv-003'  
delta_time = [['2023-10-01 01:42:30', '2023-10-01 02:54:35'], 
              ['2023-10-06 10:31:52', '2023-10-06 11:42:41']]
output_csv_file = ['NFD23_09_28-np02srv003-0-eth-stream_scaling-np04srv003', 
                   'NFD23_09_28-np02srv003-0-eth-stream_scaling_swtpg-np04srv003']
results_path = '../performance_results'
report_path = '../reports'
performancetest_path = '../sourcecode/performancetest'

for delta_time_list, output_csv_file_list in zip(delta_time, output_csv_file):
    extract_data_and_stats_from_panel(grafana_url, dashboard_uid, delta_time=delta_time_list, host=host_used, 
                                      input_dir=results_path, output_csv_file=output_csv_file_list)

create_report_performance(input_dir=results_path, output_dir=report_path,
                          daqconfs_cpupins_folder_parent_dir=performancetest_path, 
                          process_pcm_files=False, process_uprof_files=False, 
                          print_info=True, streams='8, 16, 24, 32, 40, and 48', 
                          pdf_name='performancetest_without_recording', 
                          elog_message=['0.1 Hz', '0.1 Hz second'])

```
