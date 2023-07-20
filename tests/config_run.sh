#!/bin/bash

if [ $# -ne 4 ]; then
  echo "Usage: ./config_run.sh <path> <envir_name> <run_num_init> <test_type>"
  echo "<path>: path to performancetest"
  echo "<test_type>: options amd, intel, amd_recording_wib2, amd_recording_wibeth, intel_recording_wib2, intel_recording_wibeth"
  exit 2
fi

path=$1
envir_name=$2
run_num_init=$3
test_type=$4

if [ "$test_type" = "amd" ]; then
    test_names=("perf_12link_amd_node0" "perf_12link_amd_node1" "perf_12link_amd_node1_swtpg'  'perf_24link_amd_node0" "perf_24link_amd_node1" "perf_24link_amd_node1_swtpg" "perf_eth_48link_amd_node0" "perf_eth_48link_amd_node1" "perf_eth_48link_amd_node1_swtpg" "perf_eth_96link_amd_node0" "perf_eth_96link_amd_node1" "perf_eth_96link_amd_node1_swtpg")
elif [ "$test_type" = "intel" ]; then
    test_names=("perf_12link_intel_node0" "perf_12link_intel_node1" "perf_12link_intel_node1_swtpg" "perf_24link_intel_node0" "perf_24link_intel_node1" "perf_24link_intel_node1_swtpg" "perf_eth_48link_intel_node0" "perf_eth_48link_intel_node1" "perf_eth_48link_intel_node1_swtpg" "perf_eth_96link_intel_node0" "perf_eth_96link_intel_node1" "perf_eth_96link_intel_node1_swtpg")
elif [ "$test_type" = "amd_recording_wib2" ]; then
    test_names=("perf_12link_amd_node1_recording" "perf_12link_amd_node1_recording_swtpg" "perf_24link_amd_node1_recording" "perf_24link_amd_node1_recording_swtpg")
elif [ "$test_type" = "amd_recording_wibeth" ]; then
    test_names=("perf_eth_48link_amd_node1_recording" "perf_eth_48link_amd_node1_recording_swtpg" "perf_eth_96link_amd_node1_recording" "perf_eth_96link_amd_node1_recording_swtpg")
elif [ "$test_type" = "intel_recording_wib2" ]; then
    test_names=("perf_12link_intel_node1_recording" "perf_12link_intel_node1_recording_swtpg" "perf_24link_intel_node1_recording" "perf_24link_intel_node1_recording_swtpg")
else
    test_names=("perf_eth_48link_intel_node1_recording" "perf_eth_48link_intel_node1_recording_swtpg" "perf_eth_96link_intel_node1_recording" "perf_eth_96link_intel_node1_recording_swtpg")
fi

for test_name_i in "${test_names[@]}"
do
    run_num=$(($run_num_init+(counter++)))
    echo "running tests $test_name_i"
    iostat -m -t 1 120 > iostat_$test_name_i.txt &
    if [ "$test_type" = "amd" ] || [ "$test_type" = "intel" ]; then
	nanorc $test_name_i $envir_name boot conf start_run $run_num wait 600 stop_run shutdown
    elif [ "$test_type" = "amd_recording_wib2" ]; then
        nanorc $test_name_i $envir_name boot conf start_run $run_num expert_command --timeout 10 $test_name_i/$test_name_i/runp02srv004flx1 $path/tests/record-cmd.json wait 600 stop_run shutdown
    elif [ "$test_type" = "amd_recording_wibeth" ]; then
        nanorc $test_name_i $envir_name boot conf start_run $run_num expert_command --timeout 10 $test_name_i/$test_name_i/runp02srv004eth1 $path/tests/record-cmd.json wait 600 stop_run shutdown
    elif [ "$test_type" = "intel_recording_wib2" ]; then
        nanorc $test_name_i $envir_name boot conf start_run $run_num expert_command --timeout 10 $test_name_i/$test_name_i/runp02srv003flx1 $path/tests/record-cmd.json wait 600 stop_run shutdown
    else
        nanorc $test_name_i $envir_name boot conf start_run $run_num expert_command --timeout 10 $test_name_i/$test_name_i/runp02srv003eth1 $path/tests/record-cmd.json wait 600 stop_run shutdown     
    fi
    
    # move log files
    mkdir RunConf_$run_num/logs
    mv log_*.txt RunConf_$run_num/logs
    grep -R "ERROR" RunConf_$run_num/logs >> error_summary.txt

    # move output files
    mkdir RunConf_$run_num/output
    mv *.hdf5 RunConf_$run_num/output
    mv logbook_*.txt RunConf_$run_num/output
    mv error_summary.txt RunConf_$run_num/output
    mv iostat_*.txt RunConf_$run_num/output

    echo "wait for 120s for resources to return to baseline"
    sleep 120
done
