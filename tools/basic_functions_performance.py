from basic_functions import *
from fpdf import FPDF 
from fpdf.enums import XPos, YPos
from PIL import Image

pcm_columns_list_0 = ['C0 Core C-state residency', 'Socket0 Memory Bandwidth',
                    'Socket0 Instructions Per Cycle', 'Socket0 Instructions Retired Any (Million)',
                    'Socket0 L2 Cache Misses', 'Socket0 L2 Cache Hits',
                    'Socket0 L3 Cache Misses', 'Socket0 L3 Cache Hits']
pcm_columns_list_1 = ['C0 Core C-state residency', 'Socket1 Memory Bandwidth',
                    'Socket1 Instructions Per Cycle', 'Socket1 Instructions Retired Any (Million)',
                    'Socket1 L2 Cache Misses', 'Socket1 L2 Cache Hits',
                    'Socket1 L3 Cache Misses', 'Socket1 L3 Cache Hits']
uprof_columns_list_0 = [' Utilization (%) Socket0', 'Total Mem Bw (GB/s) Socket0',
                        'IPC (Sys + User) Socket0', 'IRA Socket0',   #<------------- we don't have this (IRA) data 
                        'L2 Miss (pti) Socket0', 'L2 Access (pti) Socket0',
                        'L3 Miss Socket0', 'L3 Miss % Socket0']
uprof_columns_list_1 = ['Utilization (%) Socket1', 'Total Mem Bw (GB/s) Socket1',
                        'IPC (Sys + User) Socket1', 'IRA Socket1',   #<------------- we don't have this (IRA) data 
                        'L2 Miss (pti) Socket1', 'L2 Access (pti) Socket1',
                        'L3 Miss Socket1', 'L3 Miss % Socket1']
label_names = ['CPU Utilization (%)', 'Memory Bandwidth (GB/sec)',
            'Instructions Per Cycle', 'Instructions Retired Any (Million)',
            'L2 Cache Misses (Million)', 'L2 Cache [Misses/Accesses] (%)',
            'L3 Cache Misses (Million)', 'L3 Cache [Misses/Accesses] (%)']
label_columns = ['Socket0','Socket1']

def plot_vars_comparison(input_dir, output_dir, all_files, pdf_name):
    X_plot, Y_plot_0, Y_plot_1, label_plot_0, label_plot_1 = [], [], [], [], []
    
    for i, file_i in enumerate(all_files):    
        info = break_file_name(file_i)
        data_frame = pd.read_csv(f'{input_dir}/{file_i}.csv')
        X_plot.append(data_frame['NewTime'].values.tolist())
                
        Y_tmp_0, Y_tmp_1, label_tmp_0, label_tmp_1 = [], [], [], []
        
        if info[0]=='grafana':
            for k, (columns_pcm_0, columns_pcm_1) in enumerate(zip(pcm_columns_list_0, pcm_columns_list_1)):
                Y_0, label_0 = get_column_val(data_frame, [columns_pcm_0], [label_columns[0]], file_i)  
                Y_1, label_1 = get_column_val(data_frame, [columns_pcm_1], [label_columns[1]], file_i)  
                Y_tmp_0.append(Y_0)
                label_tmp_0.append(label_0)
                Y_tmp_1.append(Y_1)
                label_tmp_1.append(label_1)
        else:
            for k, (columns_uprof_0, columns_uprof_1) in enumerate(zip(uprof_columns_list_0, uprof_columns_list_1)):
                Y_0, label_0 = get_column_val(data_frame, [columns_uprof_0], [label_columns[0]], file_i)
                Y_1, label_1 = get_column_val(data_frame, [columns_uprof_1], [label_columns[1]], file_i)
                Y_tmp_0.append(Y_0)
                label_tmp_0.append(label_0)
                Y_tmp_1.append(Y_1)
                label_tmp_1.append(label_1)
    
        Y_plot_0.append(Y_tmp_0)
        label_plot_0.append(label_tmp_0)
        Y_plot_1.append(Y_tmp_1)
        label_plot_1.append(label_tmp_1)
    
    # Here we make the plot:
    matplotlib.rcParams['font.family'] = 'DejaVu Serif'
    rows=cols=2
    rows_cols = rows*cols
    fig, axs = plt.subplots(rows, cols, figsize=(18, 8))
    plt.style.use('default')
    axs = axs.flatten()
    #axs[3].axis('off')
    
    for i in range(len(Y_plot_0)):  #number of files or tests
        for j in range(len(Y_plot_0[i])):  #number of metrix
            if j < rows_cols:
                label0_ij0 = re.sub('_', ' ', label_plot_0[i][j][0])
                axs[j].plot(X_plot[i], Y_plot_0[i][j][0], color=color_list[i], label=label0_ij0, linestyle=linestyle_list[0])
                axs[j].set_ylabel(f'{label_names[j]}')
                axs[j].set_xlabel('Time (min)')
                axs[j].grid(which='major', color='gray', linestyle='dashed')
                axs[j].legend(loc='upper left')
            else:
                pass
                
    plt.tight_layout()
    plt.savefig(f'{output_dir}/Fig0_{pdf_name}_results_socket0.png')
    print(f'{output_dir}/Fig0_{pdf_name}_results_socket0.png')
    plt.close() 
    
    fig, axs = plt.subplots(rows, cols, figsize=(18, 8))
    plt.style.use('default')
    axs = axs.flatten()   
    
    for i in range(len(Y_plot_0)):  
        for j in range(len(Y_plot_0[i])):
            if j < rows_cols:
                pass
            else:
                label0_ij0 = re.sub('_', ' ', label_plot_0[i][j][0])
                axs[j-rows_cols].plot(X_plot[i], Y_plot_0[i][j][0], color=color_list[i], label=label0_ij0, linestyle=linestyle_list[0])
                axs[j-rows_cols].set_ylabel(f'{label_names[j]}')
                axs[j-rows_cols].set_xlabel('Time (min)')
                axs[j-rows_cols].grid(which='major', color='gray', linestyle='dashed')
                axs[j-rows_cols].legend(loc='upper left')
                
    plt.tight_layout()
    plt.savefig(f'{output_dir}/Fig1_{pdf_name}_results_cache_socket0.png')
    print(f'{output_dir}/Fig1_{pdf_name}_results_cache_socket0.png')
    plt.close() 
    
    fig, axs = plt.subplots(rows, cols, figsize=(18, 8))
    plt.style.use('default')
    axs = axs.flatten()
    
    for i in range(len(Y_plot_1)):  
        for j in range(len(Y_plot_1[i])):
            if j < rows_cols:
                label1_ij0 = re.sub('_', ' ', label_plot_1[i][j][0])
                axs[j].plot(X_plot[i], Y_plot_1[i][j][0], color=color_list[i], label=label1_ij0, linestyle=linestyle_list[0])
                axs[j].set_ylabel(f'{label_names[j]}')
                axs[j].set_xlabel('Time (min)')
                axs[j].grid(which='major', color='gray', linestyle='dashed')
                axs[j].legend(loc='upper left')
            else:
                pass
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/Fig2_{pdf_name}_results_socket1.png')
    print(f'{output_dir}/Fig2_{pdf_name}_results_socket1.png')
    plt.close() 
    
    fig, axs = plt.subplots(rows, cols, figsize=(18, 8))
    plt.style.use('default')
    axs = axs.flatten()
    
    for i in range(len(Y_plot_1)):  
        for j in range(len(Y_plot_1[i])):
            if j < rows_cols:
                pass
            else:
                label1_ij0 = re.sub('_', ' ', label_plot_1[i][j][0])
                axs[j-rows_cols].plot(X_plot[i], Y_plot_1[i][j][0], color=color_list[i], label=label1_ij0, linestyle=linestyle_list[0])
                axs[j-rows_cols].set_ylabel(f'{label_names[j]}')
                axs[j-rows_cols].set_xlabel('Time (min)')
                axs[j-rows_cols].grid(which='major', color='gray', linestyle='dashed')
                axs[j-rows_cols].legend(loc='upper left')
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/Fig3_{pdf_name}_results_cache_socket1.png')
    print(f'{output_dir}/Fig3_{pdf_name}_results_cache_socket1.png')
    plt.close() 

def create_report_performance(input_dir, output_dir, all_files, readout_name, daqconf_files, core_utilization_files, parent_folder_dir, print_info=True, pdf_name='performance_report', repin_threads_file=[None], comment=['TBA']):    
    directory([input_dir, output_dir])

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
    headers = ['Test', 'Readout SRV', 'dunedaq', 'Socket', 'General comments']
    rows_data.append(headers)
    
    line_height = pdf.font_size * 2
    col_width = [pdf.epw/3.8, pdf.epw/8, pdf.epw/7, pdf.epw/12, pdf.epw/4]  
    lh_list = [] #list with proper line_height for each row
    
    for i, file_i in enumerate(all_files):
        info = break_file_name(file_i)
        test_info = re.sub('_', ' ', info[5])
        line = [test_info, info[2], info[1], info[3], comment[i]]
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
    plot_vars_comparison(input_dir, output_dir, all_files, pdf_name)
    
    if info[3] == '0' or info[3] == '01':
        pdf.image(f'{output_dir}/Fig0_{pdf_name}_results_socket0.png', w=180)
        pdf.write(5, 'Figure. Socket0 results of the tests ran using the metrics CPU Utilization (%), Memory Bandwidth (GB/sec), Instructions Per Cycle, Instructions Retired Any (Million).')
        pdf.ln(10)
        pdf.image(f'{output_dir}/Fig1_{pdf_name}_results_cache_socket0.png', w=180)
        pdf.write(5, 'Figure. Socket0 results of the tests ran using the metrics L2 Cache Misses (Million), L2 Cache [Misses/Hits] (%), L3 Cache Misses (Million), and L3 Cache [Misses/Hits] (%).')
        pdf.ln(10)
        
    if info[3] == '1' or info[3] == '01':
        pdf.image(f'{output_dir}/Fig2_{pdf_name}_results_socket1.png', w=180)
        pdf.write(5, 'Figure. Socket1 results of the tests ran using the metrics CPU Utilization (%), Memory Bandwidth (GB/sec), Instructions Per Cycle, Instructions Retired Any (Million).')
        pdf.ln(10)
        pdf.image(f'{output_dir}/Fig3_{pdf_name}_results_cache_socket1.png', w=180)
        pdf.write(5, 'Figure. Socket1 results of the tests ran using the metrics L2 Cache Misses (Million), L2 Cache [Misses/Hits] (%), L3 Cache Misses (Million), and L3 Cache [Misses/Hits] (%).')
        pdf.ln(10)
    #-------------------------------------------- FIGURES END ------------------------------------------------
    
    #---------------------------------------- CONFIGURATIONS START ---------------------------------------------
    if print_info:
        pdf.write(5, 'Configurations: \n', 'B')
        for i in range(len(all_files)):
            info = break_file_name(all_files[i])
            var_i = readout_name[i]
            file_daqconf_i = daqconf_files[i]
            file_core_i = core_utilization_files[i]
            repin_threads_file_i = repin_threads_file[i]
            
            json_info(file_daqconf=file_daqconf_i, file_core=file_core_i, parent_folder_dir=parent_folder_dir, input_dir=input_dir, var=var_i, pdf=pdf, if_pdf=print_info, repin_threads_file=repin_threads_file_i)           

    pdf.ln(20)
    pdf.set_font('Times', '', 10)
    pdf.write(5, f'The End, made on {current_time()}')
    pdf.output(f'{output_dir}/{pdf_name}_report.pdf')
    #---------------------------------------- CONFIGURATIONS END ---------------------------------------------
    
    print(f'The report was create and saved to {output_dir}/{pdf_name}.pdf')

def json_info(file_daqconf, file_core, parent_folder_dir, input_dir, var, pdf, if_pdf=False, repin_threads_file=False):   
    emu_mode = None
    with open(f'{parent_folder_dir}/daqconfs/{file_daqconf}.json', 'r') as f:
        data_daqconf = json.load(f)
        
        info_boot = json.dumps(data_daqconf['boot'], skipkeys = True, allow_nan = True)
        data_boot_list = json.loads(info_boot)
        data_boot = convert(data_boot_list)
        info_hsi = json.dumps(data_daqconf['hsi'], skipkeys = True, allow_nan = True)
        data_hsi_list = json.loads(info_hsi)
        data_hsi = convert(data_hsi_list)
        info_trigger = json.dumps(data_daqconf['trigger'], skipkeys = True, allow_nan = True)
        data_trigger_list = json.loads(info_trigger)
        data_trigger = convert(data_trigger_list)
        info_readout = json.dumps(data_daqconf['readout'], skipkeys = True, allow_nan = True)
        data_readout_list = json.loads(info_readout)
        data_readout = convert(data_readout_list)

        for m, value_m in enumerate(data_readout):
            if value_m in ['thread_pinning_files']: 
                file_cpupins = data_readout_list[value_m][2]['file']
                
        if repin_threads_file:
            file_cpupins = repin_threads_file
    
    if if_pdf:
        pdf.set_font('Times', '', 10)
        pdf.write(5, f'daqconf file: {file_daqconf} \n')
        for i, value_i in enumerate(data_boot):
            if value_i in ['use_connectivity_service']:
                pdf.write(5, f'    * {value_i}: {data_boot_list[value_i]} \n')
            else:
                pass

        for j, value_j in enumerate(data_hsi):
            if value_j in ['random_trigger_rate_hz']: 
                pdf.write(5, f'    * {value_j}: {data_hsi_list[value_j]} \n')
            else:
                pass

        for l, value_l in enumerate(data_readout):
            if value_l in ['latency_buffer_size','generate_periodic_adc_pattern','use_fake_cards','enable_raw_recording', 'raw_recording_output_dir','enable_tpg','tpg_threshold','tpg_algorithm']: 
                pdf.write(5, f'    * {value_l}: {data_readout_list[value_l]} \n')
            else:
                pass
        for m, value_m in enumerate(data_readout):
            if value_m in ['thread_pinning_file']: 
                if repin_threads_file:
                    pdf.write(5, f'    * {value_m}: {repin_threads_file} \n')
                else:
                    pdf.write(5, f'    * {value_m}: {data_readout_list[value_m]} \n')

            else:
                pass

    emu_mode = True if data_readout_list['generate_periodic_adc_pattern'] else False
    
    for var_i in var:
        data_list = cpupining_info(parent_folder_dir, file_cpupins, var_i)
        pinning_table, cpu_core_table, cpu_utilization_maximum_table = extract_table_data(input_dir, file_core, data_list, emu_mode=emu_mode)
        pdf.ln(5)
        table_cpupins(columns_data=[pinning_table, cpu_core_table, cpu_utilization_maximum_table], pdf=pdf, if_pdf=if_pdf)
        test_info = break_file_name(file_core)
        # test = re.sub('_', ' ', test_info[5])
        # pdf.cell(0, 10, f'Table of CPU core pins information of {var_i} from {test}.')
        pdf.cell(0, 10, f'Table of CPU core pins information of {var_i}.')
        pdf.ln(10) 

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
