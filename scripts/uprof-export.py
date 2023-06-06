#import the modules, def variables, and funtions
import os
import sys
import csv
import time
import glob
import fnmatch
import shutil
import numpy as np
import pickle as pkl
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib
import matplotlib.pyplot as plt 
import matplotlib.cm as cm
import matplotlib.colors as mcolors
from scipy.stats import chisquare
from sklearn.cluster import DBSCAN
from pathlib import Path
from datetime import datetime as dt

#import the modules, def variables, and funtions
import os
import sys
import csv
import time
import glob
import fnmatch
import shutil
import numpy as np
import pickle as pkl
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib
import matplotlib.pyplot as plt 
import matplotlib.cm as cm
import matplotlib.colors as mcolors
from scipy.stats import chisquare
from sklearn.cluster import DBSCAN
from pathlib import Path
from datetime import datetime as dt

color_list = [' ', ' ', 'red', 'blue', 'green', 'cyan', 'orange', 'yellow', 'magenta', 'lime', 'purple', 'navy', 'hotpink', 'olive', 'coral', 
              'salmon', 'teal', 'darkblue', 'darkgreen', 'darkcyan', 'darkorange', 'deepskyblue', 'darkmagenta', 'sienna', 'chocolate', 
              'orangered', 'gray', 'royalblue', 'gold', 'peru', 'seagreen', 'violet', 'tomato', 'lightsalmon', 'crimson', 'lightblue', 
              'lightgreen', 'lightpink', 'black']
linestyle_list = ['solid', 'dotted', 'dashed', 'dashdot']
    
def is_hidden(input_dir):
    name = os.path.basename(os.path.abspath(input_dir))
    if name.startswith('.'):
        return 'true'
    else:
        return 'false'

def make_file_list(input_dir):
    file_list =  []
    for root, dirs, files in os.walk(input_dir):
        for name in files:
            if is_hidden(name) == 'true':  
                print (name, ' is hidden, trying to delete it')
                os.remove(os.path.join(input_dir, name))
            else:
                file_list.append(os.path.join(input_dir, name))
    
    return file_list

def make_name_list(input_dir):
    l=os.listdir(input_dir)
    name_list=[x.split('.')[0] for x in l]

    return name_list

def make_column_list(file, input_dir):
    data_frame = pd.read_pickle('{}/{}.pkl'.format(input_dir, file))
    columns_list = list(data_frame.columns) 
    ncoln=len(columns_list)
    
    return columns_list

def remove_spaces_in_filename(input_dir):
    files = make_file_list(input_dir)
    for index, file_name in enumerate(files):
        if ' ' in file_name:
            new_file_name = file_name.replace(' ', '_')
            os.rename(file_name, new_file_name )  

def remove_date_in_filename_0(input_dir):
    files = make_file_list(input_dir)
    for index, file_name in enumerate(files):
        if '-seriestocolumns-' in file_name:
            os.rename(file_name, file_name[:-48]+'.csv' )
            
def remove_date_in_filename_1(input_dir):
    files = make_file_list(input_dir)
    for index, file_name in enumerate(files):
        if '-joinbyfield-' in file_name:
            os.rename(file_name, file_name[:-44]+'.csv' )
            
def remove_date_in_filename_2(input_dir):
    files = make_file_list(input_dir)
    for index, file_name in enumerate(files):
        if '-data-' in file_name:
            os.rename(file_name, file_name[:-29]+'.csv' )

def remove_underlines_in_filename_0(input_dir):
    files = make_file_list(input_dir)
    for index, file_name in enumerate(files):
        if '___' in file_name:
            new_file_name = file_name.replace('___', '_')
            os.rename(file_name, new_file_name ) 
            
def remove_underlines_in_filename_1(input_dir):
    files = make_file_list(input_dir)
    for index, file_name in enumerate(files):
        if '_.' in file_name:
            new_file_name = file_name.replace('_.', '.')
            os.rename(file_name, new_file_name ) 
            
def change_name_grafana_files(input_dir):
    remove_spaces_in_filename(input_dir=input_dir)
    remove_date_in_filename_0(input_dir=input_dir)
    remove_date_in_filename_1(input_dir=input_dir)
    remove_date_in_filename_2(input_dir=input_dir)
    remove_underlines_in_filename_0(input_dir=input_dir)
    remove_underlines_in_filename_1(input_dir=input_dir)
    
def csv_to_pkl(file, input_dir, output_dir):
    input_file = '{}/{}.csv'.format(input_dir, file)
    df = pd.read_csv(input_file)  
    df.to_pickle('{}/{}.pkl'.format(output_dir, file))
    
def datenum(d, d_base):
    t_0 = d_base.toordinal() 
    t_1 = dt.fromordinal(t_0)
    T = (d - t_1).total_seconds()
    #print('d =', d, 't_0 = ', t_0,'  t_1 = ', t_1, '  T =', T)
    
    return T

def add_column_to_pkl(file, input_dir, output_dir, variable_x):
    data_frame = pd.read_pickle('{}/{}.pkl'.format(input_dir, file))
    # Add new time format
    newtime=[]
    x_0 = data_frame[variable_x][0]
    d_0 = dt.strptime(x_0,'%Y-%m-%d %H:%M:%S')
    for index, value in enumerate(data_frame[variable_x]):   
        d = dt.strptime(value,'%Y-%m-%d %H:%M:%S')
        d_new = (datenum(d, d_0)-datenum(d_0, d_0))/60.
        #print('d_new = ', d_new)
        newtime.append(d_new) 

    data_frame.insert(0, 'NewTime', newtime, True)
    picklefile = open('{}/{}.pkl'.format(output_dir, file), 'wb')
    pkl.dump(data_frame, picklefile)
    picklefile.close()
    #print('{}/{}.pkl saved'.format(output_dir, file))

def units_selection(name):
    set0 = ['Memory_Bandwidth', 'Socket0_Memory_Bandwidth', 'Socket1_Memory_Bandwidth', 'Network_I_O', 
            'Network_Traffic', 'Total_Mem', 'Mem_RdBw_PKG0', 'Mem_WrBw_PKG0', 'Mem_RdBw_PKG1', 'Mem_WrBw_PKG1', 
            'Socket0_UPI_Incoming_Data_Traffic', 'Socket0_UPI_Outgoing_Data_And_Non-Data_Traffic', 
            'Socket1_UPI_Incoming_Data_Traffic', 'Socket1_UPI_Outgoing_Data_And_Non-Data_Traffic', 
            'Data_Writers_Information', 'Memory_Active_Inactive']
    set1 = ['Socket0_UPI_Utilization_Incoming_Data_Traffic', 'Socket0_UPI_Utilization_Outgoing_Data_And_Non-Data_Traffic', 
            'Socket1_UPI_Utilization_Incoming_Data_Traffic', 'Socket1_UPI_Utilization_Outgoing_Data_And_Non-Data_Traffic', 
            'L3_Miss_porcent', 'Utilization', 'DFO_time', 'CPU', 'L3_Cache_Hit_Ratio', 'L2_Cache_Hit_Ratio']
    set2 = ['L2_Access', 'L2_Miss', 'L2_Hit', 'L3_Access', 'IC_Access', 'IC_Miss', 'DC_Access']

    set_nothings = ['Eff_Freq', 'Instructions_Retired_Any', 'Clock_Unhalted_Thread', 'CPI', 'Branch_Misprediction_Ratio', 
                    'Op_Cache_Fetch_Miss_Ratio', 'IC_Fetch_Miss_Ratio', 'Context_Switches_Interrupts']
    
    if name in set0:
        unit = '(MByte/sec)'
    elif name in set1:
        unit = '(%)'
    elif name in ['Package_C-state_residency', 'Core_C-state_residency']:
        unit = '(stacked %)'
    elif name in ['Trigger_Rate']:
        unit = '(Hz)'
    elif name in ['Socket0_Energy_Consumption', 'Socket1_Energy_Consumption']:
        unit = '(Watt)'
    elif name in ['Instructions_Per_Cycle', 'IPC']:
        unit = '(IPC)'
    elif name in ['L2_Cache_Misses_Per_Instruction', 'L3_Cache_Misses_Per_Instruction']:
        unit = '(MPI)'
    elif name in set2:
        unit = '(pti)'
    elif name in ['Disk_occupancy', 'Disk_Space_Used']:
        unit = '(Tib)'
    elif name in ['Memory_Stack']:
        unit = '(bytes)'
    elif name in ['Process_schedule_stats_Running_Waiting']:
        unit = '(sec)'
    elif name in ['Hardware_temperature_monitor']:
        unit = '(degrees Celcius)'
    elif name in ['Active_Frequency_Ratio']:
        unit = '(AFREQ)'
    elif name in ['L3_Miss_Latency']:
        unit = '(core cycles)'
    else:
        unit = ''

    return unit

def plot_vars_uprof(file, input_dir, variable_x, variable_y, ylabel, figure_name, figure_dir):
    data_frame = pd.read_pickle('{}/{}.pkl'.format(input_dir, file))
    columns_list = list(data_frame.columns) 
    X = data_frame['NewTime']
    Y_tmp = []
    color_tmp = []
    label_tmp = []
    k = 1
    
    for i, columns_i in enumerate(columns_list):
        if columns_i in ['NewTime', variable_x]:
            pass
        else: 
            Y = data_frame[columns_i]
            if columns_i in variable_y:
                k += 1
                Y_tmp.append(Y)
                color_tmp.append(color_list[k])
                label_tmp.append(columns_i)
            else:
                pass

    # Here we make the plot:
    matplotlib.rcParams['font.family'] = 'DejaVu Serif'
    fig = plt.figure(figsize=(14,6))
    plt.style.use('default')
    plt.title(figure_name)
    plt.xlabel('Time (min)')
    unit = units_selection(ylabel)
    plt.ylabel('{} {}'.format(ylabel, unit))
    plt.grid() 
    
    for i in range(len(Y_tmp)):
        plt.plot(X, Y_tmp[i], color=color_tmp[i], label=label_tmp[i])

    plt.legend(loc='upper left')
    plt.tight_layout()
    
    plt.savefig('{}/pdf/{}_{}.pdf'.format(figure_dir, figure_name, ylabel), dpi=400)
    plt.savefig('{}/{}_{}.png'.format(figure_dir, figure_name, ylabel), dpi=200)
    print('Saved {}_{} to figures.'.format(figure_name, ylabel))
    plt.close()
    
def plot_vars_uprof_comparison(file, input_dir, comparison_names, variable_x, variable_y, ylabel, figure_name, figure_dir):
    linestyle_new = []
    X_new = []
    Y_new = [] 
    color_new = []
    label_new = []
    
    for i, directory in enumerate(input_dir):
        data_frame = pd.read_pickle('{}/{}.pkl'.format(input_dir[i], file))
        columns_list = list(data_frame.columns)
        X_new.append(data_frame['NewTime'].values.tolist())
        linestyle_new.append(linestyle_list[i])
        Y_tmp = [] 
        color_tmp = []
        label_tmp = []
        k = 1
    
        for j, columns_j in enumerate(columns_list):
            if columns_j in ['NewTime', variable_x]:
                pass
            else: 
                if columns_j in variable_y:
                    k += 1
                    Y_tmp.append(data_frame[columns_j].values.tolist())
                    color_tmp.append(color_list[k])
                    label_tmp.append('{} {}'.format(comparison_names[i], columns_j))
                else:
                    pass

        Y_new.append(Y_tmp)
        color_new.append(color_tmp)
        label_new.append(label_tmp)
    
    # Here we make the plot:
    matplotlib.rcParams['font.family'] = 'DejaVu Serif'
    fig = plt.figure(figsize=(14,6))
    plt.style.use('default')
    plt.title(figure_name)
    plt.xlabel('Time (min)')
    unit = units_selection(file)
    plt.ylabel('{} {}'.format(file, unit))
    plt.grid() 
    
    for i in range(len(input_dir)):
        for j in range(len(Y_new[i])):
            plt.plot(X_new[i], Y_new[i][j], color=color_new[i][j], label=label_new[i][j], linestyle=linestyle_new[i])
    
    plt.legend(loc='upper left')
    plt.tight_layout()
    
    plt.savefig('{}/pdf/Comparison_{}_{}.pdf'.format(figure_dir, figure_name, file), dpi=400)
    plt.savefig('{}/Comparison_{}_{}.png'.format(figure_dir, figure_name, file), dpi=200)
    print('Saved Comparison_{}_{} to figures.'.format(figure_name, file))
    plt.close()
    
def main():
    args = sys.argv
    if(len(sys.argv) != 10):
        print_usage()
        sys.exit(1)

    input_dir_csv = args[1]
    input_dir_pkl = args[2]
    output_dir = args[3]
    variable_y = args[4]
    ylabel = args[5]
    figure_name = args[6]
    figure_dir = args[7]
    comparison_names = args[8]
    do_comparison = args[9]
    variable_x='Timestamp'
    
    # Create output directory (if it doesn't exist yet):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    if not os.path.exists(figure_dir):
        os.makedirs(figure_dir)
        
    if not os.path.exists('{}/pdf'.format(figure_dir)):
        os.makedirs('{}/pdf'.format(figure_dir))
    
    if do_comparison:
        name_list = []
        name_list_0 = make_name_list(input_dir=output_dir[0])
        name_list_1 = make_name_list(input_dir=output_dir[1])

        for i, name_i in enumerate(name_list_1):
            if name_i in name_list_0:
                name_list.append(name_i)
            else:
                pass

        for file_list in name_list:
            for y_list, ylabel_list  in zip(variable_y, ylabel):
                try:
                    plot_vars_uprof_comparison(file=file_list, input_dir=output_dir, comparison_names=comparison_names, variable_x=variable_x, variable_y=y_list, ylabel=ylabel_list, figure_name=figure_name, figure_dir=figure_dir)
                except:
                    pass

    else:
        change_name_grafana_files(input_dir=input_dir_csv)
        name_list = make_name_list(input_dir=input_dir_csv)

        for file_list in name_list:
            csv_to_pkl(file=file_list, input_dir=input_dir_csv, output_dir=input_dir_pkl)
            add_column_to_pkl(file=file_list, input_dir=input_dir_pkl, output_dir=output_dir, variable_x=variable_x)
            for y_list, ylabel_list  in zip(variable_y, ylabel):
                try:
                    plot_vars_uprof(file=file_list, input_dir=output_dir, variable_x=variable_x, variable_y=y_list, ylabel=ylabel_list, figure_name=figure_name, figure_dir=figure_dir)
                except:
                    pass

def print_usage():
    print("Usage: uprof-export.py <input_dir_csv> <input_dir_pkl> <output_dir> <variable_y> <ylabel> <figure_name> <figure_dir> <comparison_names> <do_comparison>")
    print('input_dir_csv: path to csv files.')
    print('input_dir_pkl: path to folder to store basic pkl file.')
    print('output_dir: path to folder to store pkl files with reformated time. In the case of comparison list of paths.')
    print('variable_y: list of columns to plot together.')
    print('ylabel: list of y label.')
    print('figure_name: list of figure names.')
    print('figure_dir: path where figures will be stored.')
    print('comparison_names: list of names of two servers or tests for comparison.')
    print('do_comparison: True or False')
    
# Driver Code
if __name__ == '__main__':
	# Calling main() function
	main()
 