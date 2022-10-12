# performancetest

## Benchmark testing suite

The various benchmark tests can be run through the Phoronix Test Suite (pts). It automates installing and executing tests, and uploads results to https://openbenchmarking.org/

To install pts (in CentOS Stream 8):
`yum install phoronix-test-suite`

Phoronix should be run in a clean shell, where `dbt-workarea-env` hasn't been run. You can skip to the [Automating benchmark tests](https://github.com/DUNE-DAQ/performancetest#automating-benchmark-tests) section, which describes how to run all the benchmark tests. Otherwise, the tool and the tests are described in the following sections. To install and run a test:
```
phoronix-test-suite install <test>
phoronix-test-suite run <test>
```

Or do both install and run:
`phoronix-test-suite benchmark <test>`

### Memory bandwidth test

To benchmark the memory bandwidth (in MB/s) of the system , we use STREAM. The details of the STREAM test can be found here https://www.cs.virginia.edu/stream/ref.html

To install the test, you first must set the CFLAGS env var:
```
export CFLAGS='-mcmodel=medium'
phoronix-test-suite benchmark pts/stream
```

Follow the prompts, and when prompted for memory test configuration, select 'test all options'. Once the test is complete, results can be uploaded with a given link to https://openbenchmarking.org/

### Disk I/O speed test

To benchmark the read and write performance of storage disks, we use fio. Ensure first that the disks to be tested are mounted and have a filesystem on them (eg. xfs). Then to run the test:

`phoronix-test-suite benchmark pts/fio`

Options here are: 
* Disk Test Configuration - test all options
* Engine - Linux AIO
* Buffered - no
* Direct - yes
* Block Size - 4, 8, 16, 32, 64, 128 KB (multiple options can be selected, delimited by commas)
* Disk Target - mounted targets should appear

## Automating benchmark tests

To automate the tests you should build a test suite with preselected test options. In this way, users are only prompted before and after all tests have run. To do so, run this:
`phoronix-test-suite build-suite pts/stream pts/fio`

Follow the prompts and select the options for each test given above. The test suite can then be installed and run like this:
```
export CFLAGS='-mcmodel=medium'
phoronix-test-suite install <suite-name>
phoronix-test-suite run <suite-name>
```

Optionally you can run in batch mode, which also lets you configure pre and post test prompt responses. To set this up, run: `phoronix-test-suite batch-setup`. Then configure options like this, for example:

* Save test results when in batch mode (Y/n): y
* Open the web browser automatically when in batch mode (y/N): n
* Auto upload the results to OpenBenchmarking.org (Y/n): y
* Prompt for test identifier (Y/n): y
* Prompt for test description (Y/n): y
* Prompt for saved results file-name (Y/n): y
* Run all test options (Y/n): y

Then run the test suite in batch mode like this `phoronix-test-suite batch-benchmark <suite-name>`. You will only be prompted for what you selected, and results will be uploaded to OpenBenchmarking at the link given.

## DAQ performance tests

### PCM Grafana

To monitor the performance of the server while running DAQ apps, we use PCM. This can then be displayed on a grafana dashboard. This will actively monitor metrics such as memory bandwidth, CPU utilization, energy consumption, cache hit ratio, inter-socket data rates, and others. This can be used to measure KPIs such as readout server memory bandwidth performance as number of DAQ data links is scaled.

First you need to clone PCM here https://github.com/intel/pcm. Then instructions to build it, and scripts to run PCM-Grafana, which have been modified for Centos 8 to use podman containers instead of docker containers, are given here https://github.com/DUNE-DAQ/performancetest/tree/develop/grafana#readme

For an older OS or if you use docker instead of podman, the original scripts and instructions are here https://github.com/intel/pcm/tree/master/scripts/grafana.

To configure the PCM-Grafana dashboard:
1. Ensure that the data source is configured to prometheus at the correct host address and port (default port is 9090). Note that this is the host address of prometheus and grafana, not PCM.
2. Go to dashboards and import https://github.com/DUNE-DAQ/performancetest/blob/develop/grafana/PCM_Dashboard-1665067579560.json

### CPU pinning

In order to optimize the server for a high performance use case such as this, we must use CPU pinning, which binds processes to a CPU thread to prevent the latency involved in moving the process to a different thread and re-caching the data. First there are some tools to explore the hardware topology to determine the appropriate pinning configuration. 

```
yum install numactl
yum install hwloc-gui
yum install htop

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

Since cpu pinning configurations are fully dependent on hardware topology, different servers may need different configs. The important thing to look for is how cores/threads are distributed across NUMA nodes. Example configurations can be found here:
https://github.com/DUNE-DAQ/performancetest/tree/develop/cpupins
https://github.com/DUNE-DAQ/readoutlibs/blob/develop/config/cpupins


### Link scaling performance tests

The readout app performance test for a particular system configuration, with scaling from 1-24 data links, will be described here. This will produce configurations for 1-24 data links, hosting readout locally and all other apps at a given host. At 12 minutes per run, this full test is expected to take just under 5 hours. Ensure first that PCM monitoring is active, so that results can be exported from grafana. 

```
# Run this only once to disable higher level core sleep states
./scripts/cpu-perf-mode.sh

# Run this only once to generate config files for each run at n=1-24 links, giving it the address to host non-readout apps, and the full path to the cpu pin file
curl -o frames.bin -O https://cernbox.cern.ch/index.php/s/0XzhExSIMQJUsp0/download
./tests/link_scaling_gen.sh <host_address> <pin_file>

# To run the test, give it a run number and ensure all run numbers up to run_number+23 are unused
./tests/link_scaling_run.sh <run_number>
```

Details will follow for changing the configuration between tests.

