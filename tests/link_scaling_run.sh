#!/bin/bash

if [ $# -ne 1 ]; then
  echo "Usage: ./link_scaling_run.sh <run_number>"
  echo "All run numbers up to run_number+23 must be unused."
  exit 2
fi

run_num_init=$1

for i in {1..24}
do
	echo "Scaling to ${i} links"
	run_num=$(($run_num_init + ${i} - 1))
	nanorc daq_fake_cpupin_n${i} centos-test boot conf start_run ${run_num} wait 600 stop_run shutdown
	echo "wait for 120s for resources to return to baseline"
	sleep 120

done
