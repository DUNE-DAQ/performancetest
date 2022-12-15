#!/bin/bash



if [ $# -ne 1 ]; then
  echo "Usage: source link_scaling_run.sh <run_number>"
  echo "All run numbers up to run_number+23 must be unused."
  exit 2
fi

run_num_init=$1

for i in {1..24}
do
	echo "scaling to ${i} links"
	run_num=$(($run_num_init + ${i} - 1))
	#echo $run_num
	nanorc snb_write_no_tpg_n${i} centos-test boot conf start_run ${run_num} expert_command snb_write_no_tpg_n${i}/snb_write_no_tpg_n${i}/ruemu0 record-cmd.json wait 600 stop_run shutdown
	echo "wait for 120s for resources to return to baseline"
	sleep 120

done
