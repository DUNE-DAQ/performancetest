import argparse 
import h5py 
import numpy as np 
import datetime
import glob
import re
import sys
import os

def configure():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--directories', type=str, required=True, help='Comma delimited list of directories with hdf5 data.')
    parser.add_argument('-v', '--verbose', type=bool, required=False, help="For debugging print which keys are being written to the annotated csvs.")
    return parser.parse_args()

def infer_field_from_fname(fname):
    field = None
    if("node-exporter" in fname):
        field = "Node-Exporter"
    elif("grafana-A_CvwTCWk" in fname):
        field = "Intel-PCM-DB"
    elif("uprof-pcm" in fname):
        field = "uProf-PCM-DB"
    elif("frontend_ethernet" in fname):
        field = "Frontend-Ethernet"
    elif("readout" in fname):
        field = "Readout"
    elif("overview" in fname):
        field = "DAQ-Overview"
    elif("trigger_primitives" in fname):
        field = "Trigger-Primitives"
    elif("uprof-power" in fname):
        field = "uProf-Power"

    return field


def convert_hdf5_to_annocsv(in_file, table_num, field_name, verbose):

    value_key = 'block0_values'
    value_name_key = 'block0_items'
    times_key = 'axis1'
    f = h5py.File(in_file)
    key_list = list(f.keys())
    of_name = in_file.replace(".hdf5", ".csv")
    out_file = open(of_name, 'w')
    print("Converting hdf5 file to annotated csv ...")
    out_file.write("#group,false,false,false,false,true,true\n")
    out_file.write("#datatype,string,long,dateTime:RFC3339,double,string,string\n")
    out_file.write("#default, _result,,,,,\n")
    out_file.write(",result,table,_time,_value,_field,_measurement\n")       

    for k1 in key_list:
        if(verbose==True):
            print("Writing key: " + str((k1)))
        times = list(f[k1][times_key])
        time_length = len(times)
        times = [int(time) for time in times]
        times = [datetime.datetime.fromtimestamp(time, tz=datetime.timezone(datetime.timedelta(0))) for time in times]
        if(value_name_key in list(f[k1].keys())):  #Check that there is actually data for the key and if not we don't write the key to the csv 
            values = np.array(f[k1][value_key],dtype=str)
            for i in range(time_length):
                for j in range(len(list(np.array(f[k1][value_name_key],dtype = str)))):
                    k2 = f[k1][value_name_key][j]
                    out_file.write(",," + str(table_num) + "," + str(times[i].date()) + "T" + str(times[i].time()) + "Z" + "," + values[i,j] + "," + field_name + "," + str(k1) + "-" + str(k2.decode('utf-8')).replace(",", "-") + "\n")
#We make the measurement field the two keys sperated by a dash also sometimes the keys have a comma so we replace those with dashes before writing to the csv
    out_file.close()



def convert_hdf5_and_upload(args):
    directories = args.directories
    verbose=args.verbose
    dir_list = directories.split(",")
    for dir in dir_list:
        run_num = re.search(r'run\d\d*', dir)[0] 
        print("Processing and uploading all hdf5 files for " + str(run_num))
        #try a dry run of an influx command to check if the service is running
        if(os.system("influx user list > /dev/null")==256):
            print("The influx db is not running or there were other problems connecting check your port forwarding and that the service is running")
        else:
            os.system("influx bucket create -n " + str(run_num))


        hdf5_files = glob.glob(dir + "/*.hdf5") 
        for h5 in hdf5_files:
            field_name = infer_field_from_fname(h5)
            table_num = 0
            convert_hdf5_to_annocsv(h5, table_num, field_name, False)
            if(os.system("influx user list > /dev/null")==256):
                print("The influx db is not running or there were other problems connecting check your port forwarding and that the service is running")
            else:
                os.system("influx write -b " + str(run_num)  + " --file " + h5.replace(".hdf5", ".csv"))
    
         
    


if __name__ == '__main__':
    args = configure()
    convert_hdf5_and_upload(args)



            

