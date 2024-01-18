# CPU Pinning
18-January-2024 - Work in progress, feedback is welcome - Danaisis Vargas

The following instructions are aimed at users who want to create cpupinnig files or use the ones in this package. 

## Using cpupinning existing files
In this package you can find a folder called `cpupins` contening several files used for previus tests. The naming squeme of this files is: cpupin-<data_format>-<test_name>-<readout_server>-<numa_node>.json
NOTE: each information is separated by `-` while each word inside each information is separated by `_`. You can always add information at the end (after <numa_node>) but this order should not vary. 
- <data_format>: eth of wib2
- <test_name>: ex. basic_recording_swtpg
- <readout_server>: np02srv003
- <numa_node>: 0, 1 or 01 (when using both)

Here is a list of the cpupining files available.

| CPU pinning file name | Used for: |
| --- | --- |
| cpupin-eth-basic-np02srv003-0.json | 48 streams test without recording or TPG on server np02srv003 pining only to numa node 0 |
| cpupin-eth-basic-np02srv004-0.json | 48 streams test without recording or TPG on server np02srv004 pining only to numa node 0 |
| cpupin-eth-basic_swtpg-np02srv003-0.json | 48 streams test without recording but with TPG on server np02srv003 pining only to numa node 0 |
| cpupin-eth-basic_swtpg-np02srv004-0.json | 48 streams test without recording but with TPG on server np02srv004 pining only to numa node 0 |
| cpupin-eth-basic_swtpg-np02srv003-1.json | 48 streams test without recording but with TPG on server np02srv003 pining only to numa node 1 |
| cpupin-eth-basic_swtpg-np02srv004-1.json | 48 streams test without recording but with TPG on server np02srv004 pining only to numa node 1 |
| cpupin-eth-basic_recording-np02srv003-0.json | 48 streams test with recording but without TPG on server np02srv003 pining only to numa node 0 |
| cpupin-eth-basic_recording-np02srv004-0.json | 48 streams test with recording but without TPG on server np02srv004 pining only to numa node 0 |
| cpupin-eth-basic_recording_swtpg-np02srv003-0.json | 48 streams test with recording and TPG on server np02srv003 pining only to numa node 0 |
| cpupin-eth-basic_recording_swtpg-np02srv004-0.json | 48 streams test with recording and TPG on server np02srv004 pining only to numa node 0 |
| cpupin-eth-basic_recording_swtpg-np02srv003-1.json | 48 streams test with recording and TPG on server np02srv003 pining only to numa node 1 |
| cpupin-eth-basic_recording_swtpg-np02srv004-1.json | 48 streams test with recording and TPG on server np02srv004 pining only to numa node 1 |
| cpupin-eth-basic_recording_swtpg_multinode-np02srv003-1.json | 48 streams test with recording and TPG on server np02srv003 pining to both numa nodes |
| cpupin-eth-1stream_recording_swtpg_oneL3-np02srv004-0.json | 1 stream test with recording and TPG on server np02srv004 pining only the first L3 of numa node 0 |

## Creating cpupinning
In the tools of this package there is a python3 notebook (`Cpupins.ipynb`) that when feed the cpu pin distribution of the server it will create a basic cpupin file. 

- "readout_app" is related to the server and the node you will to use for readout (ex. 'runp02srv003eth0')
    * for now regardless of the node being use the name will alway use node 0
- "node" is the node being use (ex. 1 or 0) # working in adding multinode use 
- "cpus" is the cpu nodes distribution to be used base on the server you want to use for readout (ex. np02srv003_node0_cpus)
- "tops" is the number of pins pars to dedicate to each pin_type (ex. [8, 8, 21, 18, 18, 1, 1]):
    * pin_type=["rte-worker", "fakeprod", "postproc-0", "consumer", "recording", "tpset", "cleanup"]
    * If tops = 0, that mean to not use that type
    * So for the example is producing a basic distribution with raw recording and tpg distribution
- "steps" is ....

```
#CPUPINING FILE for np02srv003
np02srv003_node1_cpus = [[ 1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31, 33, 35, 37, 39, 
                            41, 43, 45, 47, 49, 51, 53, 55], [57, 59, 61, 63, 65, 67, 69, 71, 73, 75, 
                            77, 79, 81, 83, 85, 87, 89, 91, 93, 95, 97, 99, 101, 103, 105, 107, 109, 111]]

#CPUPINING FILE for np02srv004
np02srv004_node0_cpus = [[ 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 
                            21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 
                            40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 
                            59,  60, 61, 62, 63], [128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 
                            139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154,
                            155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 
                            171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 
                            187, 188, 189, 190, 191]]

All_readout_app = ['runp02srv003eth0', 'runp02srv004eth0']
All_node = [1, 0]
All_steps = [2, 1]
All_cpus = [np02srv003_node1_cpus, np02srv004_node0_cpus]
All_tops = [[[8, 8, 21, 18, 18, 1, 1]],[[8, 8, 36, 36, 36, 1, 1]]]

for RO_list, node_list, cpus_list, tops_list, steps_list in zip(All_readout_app, All_node, All_cpus, All_tops, All_steps):
    for tops_list_i, tops_name in zip(tops_list, All_tops_names):
        cpupins_files(readout_app=RO_list, node=node_list, cpus=cpus_list, tops=tops_list_i, steps=steps_list)

#Output

{
    "daq_application": {
        "--name runp02srv003eth0": {
            "parent": "3, 5, 59, 61",
            "threads": {
                "rte-worker-7": "7",
                "rte-worker-9": "9",
                "rte-worker-63": "63",
                "rte-worker-65": "65",
      
                "fakeprod-2..": "7,9,11,13,63,65,67,69",
      
                "consumer-2..": "15,17,19,21,23,25,27,29,31,71,73,75,77,79,81,83,85,87",
      
                "recording-2..": "15,17,19,21,23,25,27,29,31,71,73,75,77,79,81,83,85,87",
      
                "consumer-0": "33,89",
                "tpset-0": "33,89",
                "cleanup-0": "33,89",
                "recording-0": "33,89",
      
                "postproc-0-2..": "35,37,39,41,43,45,47,49,51,53,55,91,93,95,97,99,101,103,105,107,109,111",
            }
        }
    }
}

{
    "daq_application": {
        "--name runp02srv004eth0": {
            "parent": "1, 2, 129, 130",
            "threads": {
                "rte-worker-3": "3",
                "rte-worker-4": "4",
                "rte-worker-5": "5",
                "rte-worker-6": "6",
                "rte-worker-131": "131",
                "rte-worker-132": "132",
                "rte-worker-133": "133",
                "rte-worker-134": "134",
      
                "fakeprod-1..": "3,4,5,6,131,132,133,134",
      
                "consumer-1..": "7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152",
      
                "recording-1..": "7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152",
      
                "consumer-0": "25,153",
                "tpset-0": "25,153",
                "cleanup-0": "25,153",
                "recording-0": "25,153",
      
                "postproc-0-1..": "26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,170,171",
            }
        }
    }
}
```