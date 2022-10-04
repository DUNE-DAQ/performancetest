# performancetest

## Benchmark testing suite

The various benchmark tests can be run through the Phoronix Test Suite (pts). It automates installing and executing tests, and uploads results to https://openbenchmarking.org/

To install pts (in CentOS Stream 8):
`yum install phoronix-test-suite`

To install and run a test:
```
phoronix-test-suite install <test>
phoronix-test-suite run <test>
```

Or do both install and run:
`phoronix-test-suite benchmark <test>`

TODO: Documentation for either batch testing or generating a custom test suite will come shortly. Making a custom test suite allows testing options and prompts to be preset for full automation.

### Memory bandwidth test

To benchmark the memory bandwidth (in MB/s) of the system , we use STREAM. The details of the STREAM test can be found here https://www.cs.virginia.edu/stream/ref.html

To install the test, you first must set the CFLAGS env var:
```
export CFLAGS='mcmodel=medium'
phoronix-test-suite benchmark pts/stream
```

Follow the prompts, and when prompted for memory test configuration, select 'test all options'. Once the test is complete, results can be uploaded with a given link to https://openbenchmarking.org/

### Disk I/O speed test

To benchmark the read and write performance of storage disks, we use fio. Ensure first that the disks are mounted and have a filesystem on them (eg. xfs). Then to run the test:

`phoronix-test-suite benchmark pts/fio`

Options here are: 
* Disk Test Configuration - test all options
* Engine - Linux AIO
* Buffered - no
* Direct - yes
* Block Size - 4, 8, 16, 32, 64, 128 KB (multiple options can be selected, delimited by commas)
* Disk Target - mounted targets should appear

TODO: rebuild fio with libaio engine

## DAQ performance tests

To monitor the performance of the server while running DAQ apps, we use PCM https://github.com/intel/pcm. This can then be displayed on a grafana dashboard. This will actively monitor metrics such as memory bandwidth, CPU utilization, energy consumption, cache hit ratio, inter-socket data rates, and others. This can be used to measure KPIs such as readout server memory bandwidth performance as number of DAQ data links is scaled.

Instructions to run PCM Grafana is given here on Centos 7 https://github.com/intel/pcm/tree/master/scripts/grafana#readme. On Centos 8 the scripts needed to be updated to use podman containers instead of docker containers. 

TODO: upload grafana scripts.
