# performancetest

Link to CERNBox with reports, data and plots: https://cernbox.cern.ch/files/link/public/ceg2IUASsNrHSvn

path to performance test work area: `/nfs/sw/dunedaq_performance_test/`. Use a low usage server for running the tools e.g. np04-srv-013.

In `performancetest` users can find all the resources to conduct benchmark and performance tests. Moreover, to process and present the results. In the `docs` folder users will find detailed test explanations, comprehensive instructions on how to execute these tests, and a comprehensive guide on how to effectively process the gathered data. In the `tools` folder the user can find the python3 notebooks and Python file with the basic functions needed for creating the reports.   

## Installation
For the performance reports to work with dunedaq v5, you must add conffwk and confmodel in the sourcecode.

Once the dunedaq directory is created, or each time you login, from the main dunedaq directory run
```[bash]
source env.sh
```

In order to setup your environment, run

```[bash]
pip install -r requirements.txt
```

to install the necessary Python packages. Everytime you login, run

```[bash]
source setup.sh
```

or add this to `env.sh` in your dunedaq workspace.

## Generating Performance reports

### Command line
First generate a json file describing all the necessary information for the test:

```[bash]
generate_test_config.py -n <json filep path>
```

which should create a configuration which looks like:
```[json]
{
    "dunedaq_version": "version of DUNEDAQ used to perform tests e.g. v4.4.8",
    "time_range": [
        0,
        -1
    ],
    "host": "server being tested e.g. np02-srv-003",
    "data_source": "source of the data, crp, apa or emu",
    "socket_num": "socket number tested on the host machine, 0, 1 or 01 for both",
    "test_name": "short test name",
    "run_number": "run number of the test",
    "session": "grafana partition name for the given test",
    "workarea": "path to dunedaq directory, can be left as null",
    "out_path": "/nfs/rscratch/sbhuller/perftest/",
    "data_path": null,
    "plot_path": null,
    "documentation": {
        "purpose": "state the purpose of your test, if not provided, default text will be added instead",
        "goals": "state the goals of this sepcific test, if not provided, default text will be added instead",
        "method": "state how you will attempt to reach the goal, if not provided, default text will be added instead",
        "control plane": "how was the system controlled during the test i.e. proceess manager configuration",
        "configuration": "path to configuration or git commit hash from ehn1configs",
        "concurrancy": "active users on the readout machine during the time of the run, what applications were run in parallel on the machine",
        "summary": "summary/conclusions of the test"
    }
}
```
Each key has a description of what it is and what value can be added. Note that the `plot_path` and `data_path` are values which you can override, otherwise they are automaically filled so they can be left as is. In addition, the `out_path` is the location where the directory for the test report is created. This should not be changed unless you want to keep the data and reports locally (note the urls in the report will not work in this case). Also, the workarea value is the absolute path to the dunedaq directory, if provided the reports will contain information about the software and configuration, otherwise it can be left as `null` Finally, note that for `documentation`, the values can be set to `null` and boilerplate text is inserted into the report instead. Also note that `out_path` can be removed if you are saving reports to the shared cernbox. The time range specifies the range plots are made for the reports.

Below is an example configuration file with the minimal information required:
```[json]
{
    "dunedaq_version": "v5.2.0",
    "time_range": [
        0,
        60
    ],
    "host": "np04-srv-031",
    "data_source": "4xAPA",
    "socket_num": "01",
    "test_name": "test_fixes",
    "run_number": 32852,
    "session": "np04-session",
    "workarea": "/nfs/home/sbhuller/fddaq-v5.2.0-a9-1/",
    "config_repo": "ehn1-daqconfigs",
    "out_path": ".",
    "data_path": null,
    "plot_path": null,
    "documentation": {
        "purpose": "High trigger rate at 132us readout window",
        "goals": "readout data requested in a 132us readout window at the highest Trigger rate posible.",
        "method": "change the trigger rate using the set_rate command during the run",
        "control plane": "how was the system controlled during the test i.e. proceess manager configuration",
        "configuration": "path to configuration or git commit hash from ehn1configs",
        "concurrancy": "active users on the readout machine during the time of the run, what applications were run in parallel on the machine",
        "summary": "DAQ Fails at trigger rate of 20 Hz (trigger inhibited)."
    }
}
```

Once you fill in all the values, run the following command:

```[bash]
generate_performance_report.py -f <path of your json file>
```
which should create a directory where all the data and pdfs are stored (notified in the command line output).


To run each step by hand, you can run:

```[bash]
collect_metrics.py -f <path of your json file> # harvest data from grafana dashboards or raw data files from PCM counters.
workarea_info.py -f <path to your json file> # get DAQ software and configuration information (optional).
get_server_info -f <path to your json file> # get hardware information about the server tested.
basic_plotter.py -f <path of your json file>  # make basic plots of all harvested data.
analyze_data.py -f <path of your json file> # analyse data and plot KPIs.
```

The first command retrives data from the grafana dashboards (daq_overview, frontent_ethernet, trigger_primitives, intel PCM) and stores the data to hdf5 files. In addition, the a new entry is added to the json file called the `data_path` that is the path all files produced are kept. The second will make simple plots of the metrics captured intended for initial assessment, while the final script performs more detailed analysis and makes more comprehensive plots. All the created files and data is kept in `out_path`.

Finally, to generate the report:

```[bash]
performance_report.py -f <path of your json file>
```

which creates a pdf document of the performance report, based off the template design.

Note that when you are done you shold also move the json file to the `data_path` **TODO: automatically copy the configuration to the data_path**

### Custom pinning file

It is possible to use a different the pinning file passed in the workarea config if you pass

```[json]
"pinning": "path to your pinning file",
```

### AMD hardware counters

To add AMD hardware counters to the performance test workflow, first one must run the uprof software **during** a given test, by running the following:

```
sudo $PERFORMANCE_TEST_PATH/scripts/start_uprof.sh <test_name> <duration_seconds>
```

to run the pcm and power profiling tools for a set time. Next in the test configuration json file the optional parameter:

```[json]
"uprof_file": "path to your uprof csv file",
```

can be added. Then, the performance test tools above can be re-ran to process this csv file along with the dashboard data, which is included in the performance report. Note if not running the tools from scratch, you can add the `--regen` option to redo the data harvesting (required if you add the uprof csv file to an existing test workflow.)

## Gathering available hardware resources
[Gathering available hardware resources](docs/device_information_tools.md)

## Micro service
[Micro service](docs/microservice.md)

## Instructions for generating a performance test with an emulated system
[performance test cookbook](docs/perf_test_cookbook.md)
