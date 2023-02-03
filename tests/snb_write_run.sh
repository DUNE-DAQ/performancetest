#!/bin/bash

if [ $# -ne 1 ]; then
  echo "Usage: ./link_scaling_run.sh <run_number>"
  echo "All run numbers up to run_number+23 must be unused."
  exit 2
fi

run_num_init=$1

for i in {1..24}
do
	# disk throughput
        iostat -m -t 1 120 > iostat_n${i}.txt &

	echo "scaling to ${i} links"
	run_num=$(($run_num_init + ${i} - 1))
	#echo $run_num
	nanorc snb_write_n${i} centos-test boot conf start_run ${run_num} expert_command snb_write_n${i}/snb_write_n${i}/ruemu0 record-cmd.json wait 600 stop_run shutdown
	
	# move log files
        mkdir RunConf_${run_num}/logs
        mv log_*.txt RunConf_${run_num}/logs
        grep -R "ERROR" RunConf_${run_num}/logs >> error_summary.txt
	
	echo "wait for 120s for resources to return to baseline"
	sleep 120

done
