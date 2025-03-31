
  
# InfluxDB Tools 

We are using InfluxDB for archiving our performance testing of the np04 servers. The database is set up so that each run is a separate bucket which so far have been named *run-RUN_NUMBER* all of these are intended to be retained forever so that we can retrieve the data at any future time for analysis. This will be documentation on setting up an InfluxDB and using the tools which I have made to process the hdf5 files from the output of the performance test tools. 

## Setting up the Database

First one needs to have an InfluxDB setup instructions for doing this (better than I could write) are here https://docs.influxdata.com/influxdb/v2/install/?t=Linux. These pages also contain several pieces of useful information for using InfluxDB including configuring the ports and ip and authentication. Once finished the setup in the link you can start the daemon using the command `influxd` and from there you can access  the GUI (by default on `localhost:8086`) but you can change this in the configuration. 

## Using the Performance Test Tools

When you run the performance test tools they will output hdf5 files. In order to upload these to an InfluxDB the data needs to be in the form of line protocols. Since we already have all of the data stored in hdf5 files for now instead of formatting the output of the http request in the form of line protocols we instead format the hdf5 files in the form of annotated csv files. These are essentially several line protocols strung together. You can view some documentation here https://docs.influxdata.com/influxdb/v2/reference/syntax/annotated-csv/. In order to do this quickly there is a python script which will format the hdf5 file into an annotated csv file the usage is the following. 

    python hdf5_to_annocsv.py -i <input_hdf5_file> -o <output_csv_file> -t <table_number> -f <field_name>
The table number is an integer which is used to add multiple tables to the database so far I have been using table 0 for the Intel-PCM metrics 1 for the frontend ethernet table 2 for the DAQ overview table and 3  for the trigger primitives metrics. The field name is just a string which I am currently using to give a plane English description of the data contained in the table currently these are "DAQ-Overview", "Intel-PCM-DB", "Trigger-Primitives" and "Frontend-Ethernet". These can be modified as needed in the future but for my proof of concept this is the current way things have been setup. If the structure of this is okay then you can simply run the bash script. 

    make_all_csvs.sh <directory_with_all_hdf5_files>
Which will run the python script over all of the hdf5 files in the directory and fill in the details based on the file names. One can then upload these csv files to the InfluxDB.

## Uploading to the InfluxDB

In order to upload things to the database one needs to first install the influx cli. The influx cli can be installed from the instructions here https://docs.influxdata.com/influxdb/cloud/reference/cli/influx/?t=Linux. Once this is done you can set up a configuration the organization is called *np04-perftest* and you can create an api token using the cli following the instructions here https://docs.influxdata.com/influxdb/cloud/admin/tokens/create-token/. Once this is done you can activate the configuration and simply run the `upload_all_csvs.sh` script to upload all of the files of the directory to the database. Note that the name of the directory must be of the form `run-run_number` since the run number is taken from the directory name. 

## Querying The Database and  the GUI

First make sure that the port 8086 on `np04-srv-019` (if this port is a problem we can change it in the configuration) is being forwarded to your machine. Then simply type `localhost:8086` and you will see the browser window with a sign in screen you can use the username `np04-daq`. Then go to the data explorer page then select a time range and on the leftmost filter select the field you want and then on the rightmost filter select a measurement (or a set of measurements to view) you can then use the mouse to select a specific time range to see the data better.

