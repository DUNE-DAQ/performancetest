# performancetest


In `performancetest` users can find all the resources to conduct benchmark and performance tests. Moreover, to process and present the results. In the `docs` folder users will find detailed test explanations, comprehensive instructions on how to execute these tests, and a comprehensive guide on how to effectively process the gathered data. In the `tools` folder the user can find the python3 notebooks and Python file with the basic functions needed for creating the reports.   

## Installation
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

To generate a performance report the tools `collect_metrics.py` and `generate_performance_report.py` are used. Both tools require a json file as input, which provides metrics about the test and necessary information requiret to retrieve the data. To generate a template json file, run

```[bash]
collect_metrics.py -g
```

which should produce a file called `template_report.json` in your current directory. In this configuration file lists all the information needed and a brief decsription describing each entry. Note that Entries with `None` are optional. Once all the information is filled run

```[bash]
collect_metrics.py -f <name of your json file>
```

to collect the dashboard information and format the core utilisation output. The output of this script are csv files for each test and core utilisation file, which are automatically added to your json file under the entries `grafana_data_files` and `core_utilisation_files`, respectively.

Generate the performance report by running

```[bash]
generate_performance_report.py -f <name of your json file>
```