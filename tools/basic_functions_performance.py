import os
import json
import re

from warnings import warn

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

from fpdf import FPDF 
from fpdf.enums import XPos, YPos

import conffwk
import confmodel

from basic_functions import break_file_name, current_time, load_json

from rich import print

color_list = ['red', 'blue', 'green', 'cyan', 'orange', 'navy', 'magenta', 'lime', 'purple', 'hotpink', 'olive', 'salmon', 'teal', 'darkblue', 'darkgreen', 'darkcyan', 'darkorange', 'deepskyblue', 'darkmagenta', 'sienna', 'chocolate']
linestyle_list = ['solid', 'dotted', 'dashed', 'dashdot','solid', 'dotted', 'dashed', 'dashdot']
marker_list = ['s','o','.','p','P','^','<','>','*','+','x','X','d','D','h','H']

def pcm_columns_list(socket : int) -> dict:
    """ Map of metric name (y axes label) to the column name in the grafana dataframe for the pcm metrics.

    Args:
        socket (int): Socket number (0 or 1)

    Returns:
        dict: map for given socket.
    """
    return {
        'CPU Utilization (%)'                : 'C0 Core C-state residency',
        'Memory Bandwidth (GB/sec)'          : f'Socket{socket} Memory Bandwidth',
        'Instructions Per Cycle'             : f'Socket{socket} Instructions Per Cycle',
        'Instructions Retired Any (Million)' : f'Socket{socket} Instructions Retired Any (Million)',
        'L2 Cache Misses (Million)'          : f'Socket{socket} L2 Cache Misses',
        'L2 Cache [Misses/Accesses] (%)'     : f'Socket{socket} L2 Cache Hits',
        'L3 Cache Misses (Million)'          : f'Socket{socket} L3 Cache Misses',
        'L3 Cache [Misses/Accesses] (%)'     : f'Socket{socket} L3 Cache Hits'
    }


def uprof_columns_list(socket : int) -> dict:
    """ Map of metric name (y axes label) to the column name in the grafana dataframe for the uprof metrics.

    Args:
        socket (int): Socket number (0 or 1)

    Returns:
        dict: map for given socket.
    """
    return {
        'CPU Utilization (%)'                : f' Utilization (%) Socket{socket}',
        'Memory Bandwidth (GB/sec)'          : f'Total Mem Bw (GB/s) Socket{socket}',
        'Instructions Per Cycle'             : f'IPC (Sys + User) Socket{socket}',
        'Instructions Retired Any (Million)' : f'IRA Socket{socket}',   #<------------- we don't have this (IRA) data 
        'L2 Cache Misses (Million)'          : f'L2 Miss (pti) Socket{socket}',
        'L2 Cache [Misses/Accesses] (%)'     : f'L2 Access (pti) Socket{socket}',
        'L3 Cache Misses (Million)'          : f'L3 Miss Socket{socket}',
        'L3 Cache [Misses/Accesses] (%)'     : f'L3 Miss % Socket{socket}'
    }

label_columns = ['Socket0','Socket1']

def percentage(num : float, den : float) -> float:
    return 100 * num / den


def dict_rev(d : dict) -> dict:
    return {v : k for k , v in d.items()}


def get_column_val(df, columns, labels, file):
    val = []
    label = []
    info = break_file_name(file)
    
    for (columns_j, label_j) in zip(columns, labels):
        if columns_j in ['NewTime', 'Timestamp']:
            continue
        elif columns_j in ['Socket0 L2 Cache Hits', 'Socket0 L3 Cache Hits', 'Socket1 L2 Cache Hits', 'Socket1 L3 Cache Hits']:
            socket = columns_j.split("Socket")[1][0]
            cache = columns_j.split(" Cache")[0][-1]
            Y = percentage(df[f"Socket{socket} L{cache} Cache Misses"], df[f"Socket{socket} L{cache} Cache Hits"] + df[f"Socket{socket} L{cache} Cache Misses"])
        elif columns_j in ['L2 Access (pti) Socket0', 'L2 Access (pti) Socket1', 'L2 Access (pti) Socket1.1']:
            socket = columns_j.split("L")[1][0]
            cache = columns_j.split("Socket")[1]
            Y = percentage(df[f'L{cache} Miss (pti) Socket{socket}'], df[f'L{cache} Access (pti) Socket{socket}'])
        elif columns_j in ['Socket0 L2 Cache Misses', 'Socket1 L2 Cache Misses', 'L2 Miss (pti) Socket0', 'L2 Miss (pti) Socket1', 'Socket0 L3 Cache Misses', 'Socket1 L3 Cache Misses', 'L3 Miss % Socket0', 'L3 Miss % Socket1', 'Ave L3 Miss Latency Socket0', 'Ave L3 Miss Latency Socket1']:
            Y = df[columns_j]
        elif columns_j in ['L3 Miss Socket0', 'L3 Miss Socket1', 'L3 Miss Socket1.1']:
            Y = df[columns_j].div(1_000_000_000)
        elif columns_j in ['Socket0 Memory Bandwidth', 'Socket1 Memory Bandwidth']:
            Y = df[columns_j].div(1000)
        elif columns_j in ['Socket0 L2 Cache Misses Per Instruction', 'Socket1 L2 Cache Misses Per Instruction']:
            Y = df[columns_j].mul(100)
        elif columns_j in ['Package Joules Consumed Socket0 Energy Consumption', 'Package Joules Consumed Socket1 Energy Consumption']:
            Y = df[columns_j]
        elif columns_j in ['IRA Socket0', 'IRA Socket1']:
            Y = df['Utilization (%) Socket1'].mul(0)
        else:
            Y = df[columns_j]
        val.append(Y.values)
        label.append(f'{info[1]} {info[5]} {info[2]} {label_j}')
    
    return val, label


def plot(ax : plt.Axes, x : list, y : list, x_label : str, y_label : str, colour : str, label : str, linestyle : str):
    ax.plot(x, y, color=colour, label=label, linestyle=linestyle)
    ax.set_ylabel(y_label)
    ax.set_xlabel(x_label)

    ax.grid(which='major', color='gray', linestyle='dashed')
    ax.legend(loc='upper left')
    return


def find_attribute(dal_obj : any, targets : list) -> dict:
    """Iterates through all attributes in a dal object, returning those which were targeted.

    Args:
        dal_obj (any): dal representation of an ocject in the configuration.
        targets (list): List of attributes to be found.

    Returns:
        dict: information about targeted attributes.
    """
    found_attrs = {}
    for k in dal_obj.__schema__["attribute"]: # get a list of all attributes this object has
        if k in targets:
            found_attrs[k] = getattr(dal_obj, k)
    return found_attrs


def find_relation(dal_obj : any, targets : list, found : dict = {}) -> dict:
    """Search a dal object, retrieving information about any relations or attributes which were targeted. Search is recursive.

    Args:
        dal_obj (any): dal representation of an ocject in the configuration.
        targets (list): List of attributes or relations to be found.
        found_attrs (dict, optional): dictionary of found targets. Defaults to {}.

    Returns:
        dict: Found targets.
    """
    found[dal_obj.id] = find_attribute(dal_obj, targets) # search for attributes this object may have


    if len(dal_obj.__schema__["relation"]) > 0:
        for k in dal_obj.__schema__["relation"]: # search for relations this object has
            obj = getattr(dal_obj, k) # get inforation about the relations
            if hasattr(obj, "__schema__"): # check this is an object, and not something else e.g. and attribute
                if k in targets:
                    found[k] = list(obj) # store information about targeted relations (who they are relationships with)
                find_relation(obj, targets, found[dal_obj.id]) # search relations in obj
    else:
        pass # no relations
    return found


def prune_attrs(found_targets : dict):
    """Remove any empty dictionaries in the found targets produced from find_relations.

    Args:
        attrs (dict): found targets.
    """
    for i in list(found_targets.keys()):
        if type(found_targets[i]) == dict:
            if len(found_targets[i]) > 0: # if dictionary is not empty, search it contents for more dictionaries
                prune_attrs(found_targets[i])
                prune_attrs(found_targets[i]) # search again to remove i if it is empty
            else:
                found_targets.pop(i) # if empty, remove this dict
        else:
            pass # not a dictionary, so keep
    return found_targets


def plot_vars_comparison(output_dir, grafana_data : list[str], pdf_name):
    X_plot = []
    
    y_plot = {}
    for file_i in grafana_data:    
        info = break_file_name(file_i)
        data_frame = pd.read_csv(file_i)
        X_plot.append(data_frame['NewTime'].values)

        if info[0] == "grafana":
            column_generator = pcm_columns_list
        else:
            column_generator = uprof_columns_list

        y = {}
        for s in range(2):
            y_tmp = {}
            for c in column_generator(s).values():
                v, _ = get_column_val(data_frame, [c], [label_columns[s]], file_i)
                y_tmp[c] = v
            plot_label = f"{info[2]} Socket{s}"
            y[plot_label] = y_tmp
        y_plot[f"{info[1]} {info[5]}"] = y

    # Here we make the plot:
    matplotlib.rcParams['font.family'] = 'DejaVu Serif'
    rows=cols=2
    rows_cols = rows*cols
    fig_num = 0

    for s in range(2):
        y_labels = {**dict_rev(pcm_columns_list(s)), **dict_rev(uprof_columns_list(s))}
        _, axs = plt.subplots(rows, cols, figsize=(18, 8))
        plt.style.use('default')
        axs = axs.flatten()
        for i, (test, data) in enumerate(y_plot.items()):
            for k in data:
                if f"Socket{s}" in k: break
            for j, (name, metric) in enumerate(data[k].items()):
                if j < rows_cols:
                    plot(axs[j], X_plot[i], metric[0], "Time (min)", y_labels[name], color_list[i], (test + " " + k).replace("_", " "), linestyle_list[0])
                else:
                    pass

        plt.tight_layout()
        out = f'{output_dir}/Fig{fig_num}_{pdf_name}_results_socket{s}.png'
        plt.savefig(out)
        print(out)
        plt.close()
        fig_num += 1

    for s in range(2):
        y_labels = {**dict_rev(pcm_columns_list(s)), **dict_rev(uprof_columns_list(s))}
        _, axs = plt.subplots(rows, cols, figsize=(18, 8))
        plt.style.use('default')
        axs = axs.flatten()
        for i, (test, data) in enumerate(y_plot.items()):
            for k in data:
                if f"Socket{s}" in k: break
            for j, (name, metric) in enumerate(data[k].items()):
                if j < rows_cols:
                    pass
                else:
                    plot(axs[j - rows_cols], X_plot[i], metric[0], "Time (min)", y_labels[name], color_list[i], (test + " " + k).replace("_", " "), linestyle_list[0])

        plt.tight_layout()
        out = f'{output_dir}/Fig{fig_num}_{pdf_name}_results_cache_socket{s}.png'
        plt.savefig(out)
        print(out)
        plt.close()
        fig_num += 1
    return


def create_report_performance(input_dir, output_dir, all_files, times : list[list], readout_name, daqconf_files, core_utilization_files, parent_folder_dir, print_info=True, pdf_name='performance_report', repin_threads_file=[None], comment=['TBA']):

    # Open pdf file
    pdf = FPDF()
    pdf.add_page()
    pdf.ln(1)
    pdf.image(f'{parent_folder_dir}/tools/dune_logo.jpg', w=180)
    pdf.ln(2)
    pdf.set_font('Times', 'B', 16)
    pdf.cell(40,10,'Performance Report')
    pdf.ln(10)
    
    # creating report
    pdf.set_font('Times', '', 10)
    pdf.write(5, 'The tests were run for the WIBEth data format. The Figures 1 and 2 show the results of the tests ran (Table1) using the different metrics. \n')
    pdf.write(5, '    * L2-hits is the fraction of requests that make it to L2 at all. Similar for L3. \n')
    pdf.write(5, '    * L2-misses is the fraction of requests that make it to L2 at all and then miss in L2. Similar for L3. \n')
    pdf.ln(10)
    
    #-------------------------------------------TABLE-----------------------------------------------
    # Data to tabular
    rows_data = []
    headers = ['Test', 'Time start', 'Time end', 'Readout SRV', 'dunedaq', 'Socket', 'General comments']
    rows_data.append(headers)
    
    line_height = pdf.font_size * 3
    col_width = [pdf.epw/6, pdf.epw/8, pdf.epw/8, pdf.epw/8, pdf.epw/10, pdf.epw/15, pdf.epw/4]  
    lh_list = [] #list with proper line_height for each row

    for i, file_i in enumerate(all_files):
        info = break_file_name(file_i)
        test_info = re.sub('_', ' ', info[5]).split(".")[0]
        line = [test_info, times[i][0], times[i][1], info[2], info[1], info[3], comment[i]]
        rows_data.append(line)
    
    # Determine line heights based on the number of words in each cell
    for row in rows_data:
        max_lines = 1  # Initialize with a minimum of 1 line
        for datum in row:
            lines_needed = len(str(datum).split('\n'))  # Count the number of lines
            max_lines = max(max_lines, lines_needed)

        lh_list.append(line_height * max_lines)
        
    # Add table rows with word wrapping and dynamic line heights
    for j, row in enumerate(rows_data):
        line_height_table = lh_list[j] 
        for k, datum in enumerate(row):
            pdf.multi_cell(col_width[k], line_height_table, datum, border=1, align='L', new_x=XPos.RIGHT, new_y=YPos.TOP, max_line_height=pdf.font_size)
            
        pdf.ln(line_height_table)
        
    pdf.write(5, 'Table. Summary of the tests ran. \n')    
    pdf.ln(10)

    
    #-------------------------------------------- FIGURES START ------------------------------------------------
    plot_vars_comparison(output_dir, all_files, pdf_name)
    
    if info[3] == '0' or info[3] == '01':
        pdf.image(f'{output_dir}/Fig0_{pdf_name}_results_socket0.png', w=180)
        pdf.write(5, 'Figure. Socket0 results of the tests ran using the metrics CPU Utilization (%), Memory Bandwidth (GB/sec), Instructions Per Cycle, Instructions Retired Any (Million).')
        pdf.ln(10)
        pdf.image(f'{output_dir}/Fig2_{pdf_name}_results_cache_socket0.png', w=180)
        pdf.write(5, 'Figure. Socket0 results of the tests ran using the metrics L2 Cache Misses (Million), L2 Cache [Misses/Hits] (%), L3 Cache Misses (Million), and L3 Cache [Misses/Hits] (%).')
        pdf.ln(10)
        
    if info[3] == '1' or info[3] == '01':
        pdf.image(f'{output_dir}/Fig1_{pdf_name}_results_socket1.png', w=180)
        pdf.write(5, 'Figure. Socket1 results of the tests ran using the metrics CPU Utilization (%), Memory Bandwidth (GB/sec), Instructions Per Cycle, Instructions Retired Any (Million).')
        pdf.ln(10)
        pdf.image(f'{output_dir}/Fig3_{pdf_name}_results_cache_socket1.png', w=180)
        pdf.write(5, 'Figure. Socket1 results of the tests ran using the metrics L2 Cache Misses (Million), L2 Cache [Misses/Hits] (%), L3 Cache Misses (Million), and L3 Cache [Misses/Hits] (%).')
        pdf.ln(10)
    #-------------------------------------------- FIGURES END ------------------------------------------------

    #---------------------------------------- CONFIGURATIONS START ---------------------------------------------
    if print_info:
        pdf.write(5, 'Configurations: \n', 'B')

        for r, d, c, t in zip(readout_name, daqconf_files, core_utilization_files, repin_threads_file):
            if ".json" in d:
                daqconf_info(file_daqconf=d, file_core=c, input_dir=input_dir, var=r, pdf=pdf, if_pdf=print_info, repin_threads_file=t)
            elif ".data.xml" in d:
                oks_info(d, pdf)
            else:
                raise Exception("Not a valid file format for DAQ configurations.")

    pdf.ln(20)
    pdf.set_font('Times', '', 10)
    pdf.write(5, f'The End, made on {current_time()}')
    pdf.output(f'{output_dir}/{pdf_name}_report.pdf')
    #---------------------------------------- CONFIGURATIONS END ---------------------------------------------
    
    print(f'The report was create and saved to {output_dir}/{pdf_name}.pdf')


def oks_info(xml_file : str, pdf : FPDF):
    """Get important information from the OKS configuration and write it to the pdf.

    Args:
        xml_file (str): OKS data file for configuration.
        pdf (FPDF): pdf to write to.
    """
    conf = conffwk.Configuration(f"oksconflibs:{xml_file}") # load OKS data file

    session = conf.get_dals("Session")[0] # grab session id

    apps = {i.id : i.class_name for i in confmodel.session_get_all_applications(conf._obj, session.id)} # list all applications run in the session
    apps[session.id] = "Session"

    target_info = {
        "Session" : ["use_connectivity_server"],
        "ReadoutApplication" : ["tp_generation_enabled", "ta_generation_enabled", "emulation_mode", "size", "processing_steps"],
        "FakeHSIApplication" : ["trigger_rate"]
    }

    found = {}
    # search the values of the attributes or relations specified iin target info for each app
    for uid, cls in apps.items():
        if cls in target_info:
            found = found | prune_attrs(find_relation(conf.get_dal(cls, uid), target_info[cls]))

    pdf.set_font("Times", "", 10)
    pdf.write(6, f"configuration file: {xml_file} \n")
    pdf.write(6, f"specific information:\n")
    write_oks_info(found, pdf)
    return


def write_oks_info(info : dict, pdf : FPDF, indent : str = ""):
    """Write contents of the found oks info into the pdf.

    Args:
        info (dict): Information from the configuration.
        pdf (FPDF): pdf file to write to.
        indent (str, optional): Indentation amount, allows bullet point style text. Defaults to "".
    """
    for k, v in info.items():
        if type(v) == dict:
            pdf.write(6, indent + "- " + k + "\n")
            indent += "    "
            write_oks_info(v, pdf, indent)

        else:
            pdf.write(6, indent + "- " + f"{k} : {v}" + "\n")
    return


def cpupining_info(file, var):
    with open(file, 'r') as f:
        data_cpupins = json.load(f)
        info_daq_application = json.dumps(data_cpupins['daq_application'][f'--name {var}'], skipkeys = True, allow_nan = True)
        data_list = json.loads(info_daq_application)
        
    return data_list


def core_utilization(input_dir, file):
    CPU_plot, User_plot = [], []
    
    data_frame = pd.read_csv(f'{input_dir}{file}')

    print(data_frame)

    maxV = data_frame['CPU'].max()
    minV = data_frame['CPU'].min()

    for j in range(minV, maxV + 1):
        CPU_plot.append(j)
        df = data_frame.loc[data_frame['CPU'] == j]
        User_max = df['user (%)'].max()
        User_plot.append(User_max)

    return CPU_plot, User_plot


def parse_cpu_cores(cpu_cores_i):
    ranges = re.split(r',|-', cpu_cores_i)
    cpu_cores = []
    for item in ranges:
        if '-' in item:
            start, end = map(int, item.split('-'))
            cpu_cores.extend(range(start, end + 1))
        else:
            cpu_cores.append(int(item))
    return cpu_cores


def extract_table_data(input_dir, file_core, data_list, emu_mode=False): 
    pinning_table, cpu_core_table, cpu_core_table_format, cpu_utilization_table, cpu_utilization_maximum_table, max_tmp = [], [], [], [], [], []
    cpu_core, cpu_utilization = core_utilization(input_dir, file_core)
    denominator, sum_utilization = 0, 0

    # Process data_list, and extract 'threads' sub-dictionary, and other data entries
    for data_i, value_i in data_list.items():
        if data_i == 'threads': 
            for threads_i, cpu_cores_i in value_i.items():
                    if emu_mode:
                        if threads_i in ['fakeprod-1..', 'fakeprod-2..', 'consumer-1..', 'consumer-2..', 'recording-1..', 'recording-2..', 'consumer-0', 'tpset-0', 'cleanup-0', 'recording-0', 'postproc-0-1..', 'postproc-0-2..']:
                            pinning_table.append(threads_i)
                            cpu_core_table.append(cpu_cores_i)
                        else:
                            pass

                    else:
                        if threads_i in ['fakeprod-1..', 'fakeprod-2..']:
                            pass
                        else:
                            pinning_table.append(threads_i)
                            cpu_core_table.append(cpu_cores_i)                  
        
        else:
            pinning_table.append(data_i)
            cpu_core_table.append(value_i)

    # Calculate averages for each CPU core configuration
    for cpu_cores_i in cpu_core_table:
        try:
            cpu_cores = parse_cpu_cores(cpu_cores_i)
            cpu_core_table_format.append(cpu_cores)
        except ValueError:
            print(f'Check the format of the cpu pinning file. The [#,#] will not work.')

        for core_i in cpu_cores:
            denominator += 1
            sum_utilization += cpu_utilization[core_i] 
            max_tmp.append(cpu_utilization[core_i])
        
        utilization_average = round((sum_utilization / denominator), 2)
        cpu_utilization_table.append(utilization_average)
        cpu_utilization_maximum_table.append(max(max_tmp))
        denominator, sum_utilization = 0, 0   # Reset variables for the next iteration

    return pinning_table, cpu_core_table, cpu_utilization_maximum_table


def daqconf_info(file_daqconf, file_core, input_dir, var, pdf, if_pdf=False, repin_threads_file=False):
    applist = load_json(file_daqconf)

    emu_mode = True if applist["readout"]['generate_periodic_adc_pattern'] else False

    if repin_threads_file:
        file_cpupins = repin_threads_file
    else:
        if "thread_pinning_files" in applist["readout"]:
            file_cpupins = applist["readout"]["thread_pinning_files"][2]["file"]

    info_to_print = {
        "boot" : ['use_connectivity_service'],
        "hsi" : ['random_trigger_rate_hz'],
        "readout" : ['latency_buffer_size','generate_periodic_adc_pattern','use_fake_cards','enable_raw_recording', 'raw_recording_output_dir','enable_tpg','tpg_threshold','tpg_algorithm']
    }

    if if_pdf:
        pdf.set_font('Times', '', 10)
        pdf.write(5, f'daqconf file: {file_daqconf} \n')

        for name, info in applist.items():
            if name in info_to_print:
                for k, v in info.items():
                    if k in info_to_print[name]:
                        pdf.write(5, f'    * {k}: {v} \n')
    
    for var_i in var:
        if os.path.isabs(file_cpupins):
            data_list = cpupining_info(file_cpupins, var_i)
            pinning_table, cpu_core_table, cpu_utilization_maximum_table = extract_table_data(input_dir, file_core, data_list, emu_mode=emu_mode)
            pdf.ln(5)
            table_cpupins(columns_data=[pinning_table, cpu_core_table, cpu_utilization_maximum_table], pdf=pdf, if_pdf=if_pdf)
            pdf.cell(0, 10, f'Table of CPU core pins information of {var_i}.')
            pdf.ln(10)
        else:
            warn("Cannot parse cpu pinning file, path must be absolute")


def table_cpupins(columns_data, pdf, if_pdf=False):
    if not columns_data:
        print('you are missing the table data')
        return

    rows_data = []
    headers = ['Pinning', 'CPU cores', 'CPU max use (%)']
    rows_data.append(headers)
    
    # Transpose the data to convert columns to rows
    line = list(map(list, zip(*columns_data)))
    rows_data = rows_data + line
    
    line_height = pdf.font_size * 2.1
    col_width = [pdf.epw/3.25, pdf.epw/2, pdf.epw/6.8]
    
    lh_list = [] #list with proper line_height for each row

    if if_pdf:
        pdf.set_font('Times', '', 10)

        # Determine line heights based on the number of words in each cell
        for row in rows_data:
            max_lines = 1  # Initialize with a minimum of 1 line
            for datum in row:
                if isinstance(datum, int):
                    datum = str(datum)
                elif not isinstance(datum, str):
                    datum = str(datum)
                
                lines_needed = len(str(datum).split('\n'))  # Count the number of lines
                max_lines = max(max_lines, lines_needed)

            lh_list.append(line_height * max_lines)
        
        # Add table rows with word wrapping and dynamic line heights
        for j, row in enumerate(rows_data):
            line_height_table = lh_list[j] 
            for k, datum in enumerate(row):
                pdf.multi_cell(col_width[k], line_height_table, str(datum), border=1, align='L', new_x=XPos.RIGHT, new_y=YPos.TOP, max_line_height=pdf.font_size)

            pdf.ln(line_height_table)
        
        pdf.set_font('Times', '', 10)
        
    else:
        print(rows_data)

