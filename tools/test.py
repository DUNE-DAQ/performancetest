from basic_functions import fetch_grafana_panels, extract_grafana_data, get_query_urls, get_unix_timestamp, process_files
from basic_functions_performance import create_report_performance
from rich import print
import copy
import requests


def main():

    # "grafana-v4_4_6-np02srv003-1-eth-singlenic_tp_recording_numa1"

    args = {
        "datasource_url" : "http://np04-srv-016.cern.ch:31093",
        "grafana_url" : "http://np04-srv-017.cern.ch:31023",
        "dashboard_uid" : ["A_CvwTCWk"],
        "delta_time" : ["2024-09-17 17:37:00", "2024-09-17 18:15:00"],
        "host" : "np02-srv-003",
        "partition" : "np04-daq",
        "input_dir" : "/nfs/home/sbhuller/fddaq_v4_4_8/work/v4_4_8-np02srv003-1-eth-Emu_stream_scaling/",
        "output_csv_file" : "v4_4_8-np02srv003-1-eth-emu_stream_scale",
    }

    extract_grafana_data(**args)
    process_files(input_dir=args["input_dir"], process_pcm_files=True, process_uprof_files=False, process_core_files=True)
    process_files(input_dir=args["input_dir"] + "/Emu_stream_scaling/", process_pcm_files=False, process_uprof_files=False, process_core_files=True)

    args = {
            "input_dir" : "/nfs/home/sbhuller/fddaq_v4_4_8/work/v4_4_8-np02srv003-1-eth-Emu_stream_scaling/",
            "output_dir" : "/nfs/home/sbhuller/fddaq_v4_4_8/work/v4_4_8-np02srv003-1-eth-Emu_stream_scaling/",
            "all_files" : ["grafana-v4_4_8-np02srv003-1-eth-emu_stream_scale"],
            "readout_name" : [["runp02srv003eth0"]],
            "daqconf_files" : ["daqconf-eth-Emu_stream_scaling-np02srv003-1"],
            "core_utilization_files" : ["Emu_stream_scaling/reformatted_core_utilization-Emu_stream_scaling"],
            "parent_folder_dir" : '/nfs/home/sbhuller/fddaq_v4_4_8/sourcecode/performancetest/',
            "print_info" : True,
            "pdf_name" : "stream_scale_test_np02srv003_1_emu",
            "repin_threads_file" : [None],
            "comment" : ["Test report for the stream scale test, performed using np02-srv-003 and fddaq-v4.4.8."]

        }
    create_report_performance(**args)

if __name__ == "__main__":
    main()