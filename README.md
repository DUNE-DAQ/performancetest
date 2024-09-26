# performancetest


In `performancetest` users can find all the resources to conduct benchmark and performance tests. Moreover, to process and present the results. In the `docs` folder users will find detailed test explanations, comprehensive instructions on how to execute these tests, and a comprehensive guide on how to effectively process the gathered data. In the `tools` folder the user can find the python3 notebooks and Python file with the basic functions needed for creating the reports.   

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

Guide on using performance report tools TBD.