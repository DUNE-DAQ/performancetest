#!/bin/bash

if [ $# -ne 3 ]; then
  echo "Usage: ./link_scaling_run.sh <partition_number> <op_env_name> <run_number>"
  echo "All run numbers up to run_number+23 must be unused."
  exit 2
fi

partition_num=$1
op_env_name=$2
run_num_init=$3

for i in {1..24}
do
	echo "Scaling to ${i} links"
	run_num=$(($run_num_init + ${i} - 1))
	#nanorc --partition-number ${partition_num} daq_fake_cpupin_n${i} centos-test boot conf start_run ${run_num} wait 600 stop_run shutdown
	nanorc --partition-number ${partition_num} daq_fake_cpupin_n${i} ${op_env_name} boot conf start_run ${run_num} wait 600 stop_run shutdown
	
	# move log files
	mkdir -p RunConf_${run_num}/logs
        mv log_*.txt RunConf_${run_num}/logs
        grep -R "ERROR" RunConf_${run_num}/logs >> error_summary.txt

	echo "wait for 120s for resources to return to baseline"
	sleep 120

done
