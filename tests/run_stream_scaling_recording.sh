#!/bin/bash

if [ $# -ne 4 ]; then
  echo "Usage: ./run_link_scaling_recording.sh <envir_name> <run_num_init> <test_name> <server_readout>"
  echo "All run numbers up to run_num_init+7 must be unused."
  exit 2
fi

envir_name=$1
run_num_init=$2
test_name=$3
server_readout=$4

readout={$server_readout}eth1
cd $test_name

for i in {8..48..8}
do
    # disk throughput
    iostat -m -t 1 120 > iostat_${i}.txt &
	
    echo "Scaling to ${i} streams"
    run_num_increment=${i}/8 
    run_num=$(($run_num_init + $run_num_increment))

    nanorc ${i} $envir_name boot conf start_run $run_num expert_command --timeout 10 $test_name_${i}/$test_name_${i}/$readout record-cmd.json wait 600 stop_run shutdown
	
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