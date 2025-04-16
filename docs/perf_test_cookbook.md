# Performance test cookbook
This document describes how to install the daqperformancetest tools and goes through the procedure of generating a peformance test report for a given DAQ run (using an enulated system).

## Prerequisites

- Work must be done on one of the CERN servers e.g. `np04-srv-013`
- Install a version of DUNEDAQ v5.2.1+ following the instructions [here](https://github.com/DUNE-DAQ/daqconf/wiki) Note that mileage with the nightly releases will vary due to the active devlepment.


## 1. Install performance test code
Following the prequisites you should have the daq software installed. You should be in your workarea directory. If not, switch to this directory. Check with `ls` you should see something like:

```[bash]
build  cache  dbt-workarea-constants.sh  env.sh  install  log  sourcecode
```

If you have not already, run:
`source env.sh`

Now install the performance test repo:

```
cd sourcecode
git clone https://github.com/DUNE-DAQ/performancetest.git
cd performancetest
source ~np04daq/bin/web_proxy.sh
pip install -r requirements.txt
source ~np04daq/bin/web_proxy.sh -u
source setup.sh
cd ../../
```

Now, each time you want to do performance testing:

```
cd <your_dunedaq_workarea>
source env.sh
source sourcecode/performancetest/setup.sh
```

## 2. Install daqsystemtest
In order to take a run with an emulated DAQ system, clone daqsystemtest:

```
cd sourcecode
git clone https://github.com/DUNE-DAQ/daqsystemtest.git
cd ..
dbt-workarea-env
dbt-build
```

## 3. Take a run
The performancetest tools collect data through the operational monitoring infastructure, so you need to take a run with the monitoring data being published to opmon. Thus we run with `ehn1-local-1x1-config`.

To take the run:

```
drunc-unified-shell ssh-CERN-kafka config/daqsystemtest/example-configs.data.xml ehn1-local-1x1-config $USER-local-test

# Within the drunc shell
conf
start --run-number <run_number> # run number should be unique
enable-triggers
# wait for a few seconds
disable-triggers
drain-dataflow
stop-trigger-sources
stop
scrap
terminate
exit

```

or with one command:

```
drunc-unified-shell ssh-CERN-kafka config/daqsystemtest/example-configs.data.xml ehn1-local-1x1-config $USER-local-test boot wait 5 conf wait 3 start --run-number <run_number> enable-triggers wait 60 disable-triggers drain-dataflow stop-trigger-sources stop scrap terminate
```

If you check the monitoring dashboard: http://np04-srv-017.cern.ch:31023/d/v5_3_0-overview, you should be able to find your session name (should contain your CERN username if you followed the above commands), you should see monitoring data from your run.

### For AMD machines only:
To get detailed CPU information you need to run AMD uProf. In a new terminal ssh into the machine you are testing and setup the same dunedaq environment i.e.

```
cd <your_dunedaq_workarea>
source env.sh
source sourcecode/performancetest/setup.sh
```

Now, with root privaleges, run

```
sudo $PERFORMANCE_TEST_PATH/scripts/start_uprof.sh <test_name> <duration_seconds>
```

The test name can be anything, and generally ensure the duration is long enough for the run to start and finish e.g. if you plan to run for 60 s, then run `start_uprof` for 120 s.

## 4. Generate the performance report

To generate the performance report:

1. Generate the json file:
    ```
    generate_test_config.py -n perf_example.json
    ```
2. The json file should look like
    ```
    {
        "dunedaq_version": "version of DUNEDAQ used to perform tests e.g. v4.4.8",
        "time_range": [
            0,
            -1
        ],
        "host": "server being tested e.g. np02-srv-003",
        "data_source": "source of the data, crp, apa or emu",
        "test_name": "short test name",
        "run_number": "run number of the test",
        "session": "grafana partition name for the given test",
        "workarea": "path to dunedaq directory, can be left as null",
        "config_repo": "v5 configuration repo used in this test e.g. ehn1-daqconfigs",
        "out_path": "/nfs/rscratch/sbhuller/perftest/",
        "data_path": null,
        "plot_path": null,
        "documentation": {
            "purpose": null,
            "goals": null,
            "method": null,
            "control_plane": null,
            "configuration": null,
            "concurrancy": null,
            "summary": null
        }
    }
    ```
    and edit the file to look like (replacing the values encased in <> with the relavent information)
    ```
    {
        "dunedaq_version": "v5.3.0",
        "time_range": [
            0,
            -1
        ],
        "host": <host_name_of_server_tested>,
        "data_source": "emu",
        "test_name": "exmaple_perf_test",
        "run_number": <your_run_number>,
        "session": <your_session_name>,
        "workarea": <absolute_path_to_your_dunedaq_workarea>,
        "config_repo": null,
        "out_path": "./",
        "data_path": null,
        "plot_path": null,
        "documentation": {
            "purpose": null,
            "goals": null,
            "method": null,
            "control_plane": null,
            "configuration": null,
            "concurrancy": null,
            "summary": null
        }
    }
    ```
    *Note: if you ran on an AMD system you would need to provide the path of the uprof csv data as:*
    ```[json]
    "uprof_file": <path_to_your_uprof_csv_file>,
    ```
3. Generate the performance report:
    ```
    generate_performance_report.py -f perf_example.json
    ```

if succussful you should see a directory starting with `perftest-`, checking the directory you should see:

```
data  performance_report-run<your_run_number>-<host_name>.pdf  plots
```

In addition to the report document, the data collected to generate the report is located in `data/`, and the plots generated from the testing are located under `plots`.

## Caveats
Note that there are a few things to bear in mind:
- For Intel machines, specific CPU information is published to the Intel PCM dashboard, So for AMD machines the plots will be empty. For AND machines you would need to the run AMD uprof tool **in parallel to taking the run** To generate the equivalent plots.
- The hyperlinks in the performance report document will not work, as this requires uploading the reports to the CERNbox (only possible by the CERNbox owner (Shyam)).