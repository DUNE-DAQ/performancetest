import argparse 
import h5py 
import numpy as np 
import datetime

def configure():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input-file', type=str, required=True, help='Path of hdf5 file to convert.')
    parser.add_argument('-o', '--output-file', type=str, required=True, help='Output annotated csv file.' )
    parser.add_argument('-t', '--table-number', type=int, required=True, help='The table number this should be different for each file processed.')
    parser.add_argument('-f', '--field-name', type=str, required=True, help='The name of the feild which should describe the type of data uploded.')
    return parser.parse_args()

def convert_hdf5_to_annocsv(args):

    value_key = 'block0_values'
    value_name_key = 'block0_items'
    times_key = 'axis1'

    f = h5py.File(args.input_file)
    table_number = args.table_number
    field_name = args.field_name
    key_list = list(f.keys())
    out_file = open(args.output_file, 'w')
    print("Converting hdf5 file to annotated csv ...")
    out_file.write("#group,false,false,false,false,true,true\n")
    out_file.write("#datatype,string,long,dateTime:RFC3339,double,string,string\n")
    out_file.write("#default, _result,,,,,\n")
    out_file.write(",result,table,_time,_value,_field,_measurement\n")       

    for k1 in key_list:
        print("Writing key: " + str((k1)))
        times = list(f[k1][times_key])
        time_length = len(times)
        times = [int(time) for time in times]
        times = [datetime.datetime.fromtimestamp(time) for time in times]
        if(value_name_key in list(f[k1].keys())):  #Check that there is actually data for the key and if not we don't write the key to the csv 
            values = np.array(f[k1][value_key],dtype=str)
            for i in range(time_length):
                for j in range(len(list(np.array(f[k1][value_name_key],dtype = str)))):
                    k2 = f[k1][value_name_key][j]
                    out_file.write(",," + str(table_number) + "," + str(times[i].date()) + "T" + str(times[i].time()) + "Z" + "," + values[i,j] + "," + field_name + "," + str(k1) + "-" + str(k2.decode('utf-8')).replace(",", "-") + "\n")
#We make the measurement field the two keys sperated by a dash also sometimes the keys have a comma so we replace those with dashes before writing to the csv
    out_file.close()


if __name__ == '__main__':
    args = configure()
    convert_hdf5_to_annocsv(args)


            

