# Benchmark testing suite
18-January-2024 - Work in progress, feedback is welcome - Matthew Man and Danaisis Vargas

The following instructions are aimed at users who want to run and create a benchmark report. The various benchmark tests can be run through the Phoronix Test Suite (pts). It automates installing and executing tests, and uploads results to https://openbenchmarking.org/

To install pts (in CentOS Stream 8):
`yum install phoronix-test-suite`

Phoronix should be run in a clean shell, where `dbt-workarea-env` hasn't been run. You can skip to the [Automating benchmark tests](https://github.com/DUNE-DAQ/performancetest#automating-benchmark-tests) section, which describes how to run all the benchmark tests. Otherwise, the tool and the tests are described in the following sections. To install and run a test:
```
phoronix-test-suite install <test>
phoronix-test-suite run <test>
```

Or do both install and run:
`phoronix-test-suite benchmark <test>`

## Memory bandwidth test
To benchmark the memory bandwidth (in MB/s) of the system , we use STREAM. The details of the STREAM test can be found here https://www.cs.virginia.edu/stream/ref.html

To install the test, you first must set the CFLAGS env var:
```
export CFLAGS='-mcmodel=medium'
phoronix-test-suite benchmark pts/stream
```

Follow the prompts, and when prompted for memory test configuration, select 'test all options'. Once the test is complete, results can be uploaded with a given link to https://openbenchmarking.org/

## Disk I/O speed test
To benchmark the read and write performance of storage disks, we use fio. Ensure first that the disks to be tested are mounted and have a filesystem on them (eg. xfs). Then to run the test:

`phoronix-test-suite benchmark pts/fio`

Options here are: 
* Disk Test Configuration - test all options
* Engine - Linux AIO
* Buffered - no
* Direct - yes
* Block Size - 4, 8, 16, 32, 64, 128 KB (multiple options can be selected, delimited by commas)
* Disk Target - mounted targets should appear

# Automating benchmark tests

To automate the tests you should build a test suite with preselected test options. In this way, users are only prompted before and after all tests have run. To do so, run this:
`phoronix-test-suite build-suite pts/stream pts/fio`

Follow the prompts and select the options for each test given above. The test suite can then be installed  and run like this:
```
export CFLAGS='-mcmodel=medium'
phoronix-test-suite install <suite-name>
phoronix-test-suite run <suite-name>
```

Optionally you can run in batch mode, which also lets you configure pre and post test prompt responses. To  set this up, run: `phoronix-test-suite batch-setup`. Then configure options like this, for example:

* Save test results when in batch mode (Y/n): y
* Open the web browser automatically when in batch mode (y/N): n
* Auto upload the results to OpenBenchmarking.org (Y/n): y
* Prompt for test identifier (Y/n): n
* Prompt for test description (Y/n): n
* Prompt for saved results file-name (Y/n): n
* Run all test options (Y/n): y

Then run the test suite in batch mode like this `phoronix-test-suite batch-benchmark <suite-name>`. You  will only be prompted for what you selected, and results will be uploaded to OpenBenchmarking at the link given.

# Automating benchmark tests
To automate the tests you should build a test suite and run it. All is done buy running this:
```
benchmark_path = '../results'
./benchmark.sh <path_to_performancetest> <benchmark_path>
```

# Benchmark report
The report can be created using the python3 notebook `Benchmark_report.ipynb` Important to have all the output_files in one foder and give the correct path to them (`benchmark_path`). Also, is necesary to expecify the path to the forder where the report will be store (`report_path`). This pahts should be diferents.

## Creating the report
```
# Phoronix data 
report_path = '../reports'
create_report_benchmark(benchmark_path, report_path)
```
