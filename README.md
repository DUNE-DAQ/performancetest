# performancetest

Link to CERNBox with reports, data and plots: https://cernbox.cern.ch/s/gEl6XmzXbW8OffB

In `performancetest` users can find all the resources to conduct benchmark and performance tests. Moreover, to process and present the results. In the `docs` folder users will find detailed test explanations, comprehensive instructions on how to execute these tests, and a comprehensive guide on how to effectively process the gathered data. In the `tools` folder the user can find the python3 notebooks and Python file with the basic functions needed for creating the reports.   

## Installation
For the performance reports to work with dunedaq v5, you must add conffwk and confmodel in the sourcecode. From the main dunedaq directory:

```[bash]
cd sourcecode
git clone https://github.com/DUNE-DAQ/conffwk.git
git clone https://github.com/DUNE-DAQ/confmodel.git
cd ..
dbt-workarea-env
dbt-build
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
    "host": "server being tested e.g. np02-srv-003",
    "data_source": "source of the data, crp, apa or emu",
    "socket_num": "socket number tested on the host machine, 0, 1 or 01 for both",
    "test_name": "short test name",
    "run_number": "run number of the test",
    "session": "grafana partition name for the given test",
    "out_path": "override this if you want to save data and reports locally.",
    "readout_name": [
        "readouthost names in daqconf file, for each test"
    ],
    "documentation": {
        "purpose": "state the purpose of your test, if not provided, default text will be added instead",
        "goals": "state the goals of this sepcific test, if not provided, default text will be added instead",
        "method": "state how you will attempt to reach the goal, if not provided, default text will be added instead",
        "control plane": "how was the system controlled during the test i.e. proceess manager configuration",
        "configuration": "path to configuration or git commit hash from ehn1configs",
        "concurrancy": "active users on the readout machine during the time of the run, what applications were run in parallel on the machine"
    }
}
```
Each key has a description of what it is and what value can be added. Note that for `documentation`, the values can be set to `null` and boilerplate text is inserted into the report instead. Also note that `out_path` can be removed if you are saving reports to the shared cernbox.

Below is an example configuration file with the minimal information required:
```[json]
{
    "dunedaq_version": "v5.2.0",
    "host": "np02-srv-003",
    "data_source": "2xCRP",
    "socket_num": "01",
    "test_name": "example",
    "run_number": 29641,
    "session": "np02-session",
    "documentation": {
        "purpose": null,
        "goals": null,
        "method": null,
        "control_plane": null,
        "configuration": null,
        "concurrancy": null,
        "summary": null
    },
}
```

Once you fill in all the values, run the following command:

```[bash]
generate_performance_report.py -f <path of your json file>
```
which should create a directory where all the data and pdfs are stored (notified in the command line output).


To run each step by hand, you can run:

```[bash]
collect_metrics.py -f <path of your json file>

frontend_ethernet.py -f <path of your json file>
resource_utlization.py -f <path of your json file>
tp_metrics.py -f <path of your json file>
```

The first command retrives data from the grafana dashboards (daq_overview, frontent_ethernet, trigger_primitives, intel PCM) and stores the data to hdf5 files. In addition, the a new entry is added to the json file called the `data_path` that is the path all files produced are kept. The last three generate relavent plots from the stored data and writes them to file (in `data_path`). Finally, to generate the report:

```[bash]
performance_report.py -f <path of your json file>
```

which creates a pdf document of the performance report, based off the template design.

Note that when you are done you shold also move the json file to the `data_path` **TODO: automatically copy the configuration to the data_path**

### Micro Service

**TODO: Implement service through jupyter notebook or equivalent to provide and easier user interface.**


## Setup software area:

Mount cernbox for file transfers

add public viewer link, keep uploader link hidden