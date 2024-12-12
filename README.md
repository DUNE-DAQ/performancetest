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

then

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
Each key has a description of what it is and what value can be added. Note that the `plot_path` and `data_path` are values which you can override, otherwise they are automaically filled so they can be left as is. In addition, the `out_path` is the location where the directory for the test report is created. This should not be changed unless you want to keep the data and reports locally (note the urls in the report will not work in this case). Also, the workarea value is the absolute path to the dunedaq directory, if provided the reports will contain information about the software and configuration, otherwise it can be left as null Finally, note that for `documentation`, the values can be set to `null` and boilerplate text is inserted into the report instead. Also note that `out_path` can be removed if you are saving reports to the shared cernbox. The time range specifies the range plots are made for the reports.

Below is an example configuration file with the minimal information required:
```[json]
{
    "dunedaq_version": "v5.3.0",
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
    "workarea": "/nfs/home/sbhuller/NFD_DEV_241126_A9",
    "out_path": ".",
    "data_path": "perftest-run32852-v5_3_0-np04srv031-test_fixes/data/",
    "plot_path": "plots/",
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
collect_metrics.py -f <path of your json file>

frontend_ethernet.py -f <path of your json file>
resource_utlization.py -f <path of your json file>
tp_metrics.py -f <path of your json file>
analyze_data.py -f <path of your json file>
```

The first command retrives data from the grafana dashboards (daq_overview, frontent_ethernet, trigger_primitives, intel PCM) and stores the data to hdf5 files. In addition, the a new entry is added to the json file called the `data_path` that is the path all files produced are kept. The others generate relavent plots from the stored data and writes them to file (in `data_path`). Finally, to generate the report:

```[bash]
performance_report.py -f <path of your json file>
```

which creates a pdf document of the performance report, based off the template design.

Note that when you are done you shold also move the json file to the `data_path` **TODO: automatically copy the configuration to the data_path**

### Micro Service

**Note that this should only be run on np0x machines which are seldom used, for example np04-srv-013.**

The shared work area is setup on `/nfs/sw/dunedaq_performance_test/`. To setup, simply run
```[bash]
source env.sh
```

all work should be done in the `work` directory which any user can read/write from.

In this environment, the above instructions can be run to produce performance reports, but in addition, a jupyter notebook has been setup for a more interactive experience.

To start the notebook session run the following command

```[bash]
jupyter lab $PERFORMANCE_TEST_PATH/app/ --no-browser --port=8080
```

and note that if the port is being used then another 4 digit number should be used in place of `8080`. You should see a url which looks like
```[bash]
http://localhost:8080/tree?token=...
```

Now, on your local machine tunnel to the server running the service:

```[bash]
ssh -L 8080:localhost:8080 <user-name>@<server-name>
```

Then, in your browser open the above url and you should be able to see the jupyter file explorer and you can open `performance_report.ipynb`

The notebook should look something like this:

![image](docs/screenshots/notebook_1.png)

The first cell shows infmormation in the json file, so fill these out as appropriate. The cells below are markdown text with a heading corresponding to each one in the performance report. in the cells called `insert text here` you can add your comments and notes to the performance report.

![image](docs/screenshots/notebook_2.png)

Note that is the text is not modified or is left blank, the boilerplate text is added to the notebook instead. Once all the comments are made and the test info is supplied, save the notebook (Ctrl-S) and then on the tab click Run -> Run All Cells.

![image](docs/screenshots/notebook_3.png)

Once complete, you should be able to see plots of the metrics for the given run:

![image](docs/screenshots/notebook_4.png)

and the final cell should also create the pdf version of the performance report written to `out_path`.

### extra information

 - When using either the notebook or `generate_performance_report.py`, you can manually supply the `data_path` and the `plot_path` if you want to skip the metrics collection or plotting steps.
 - For the urls to work, you need to upload the files to the public cernbox (url provided), this sohuld be done periodically anyway if your performance reports are written to `/nfs/rscratch/sbhuller/perftest`
