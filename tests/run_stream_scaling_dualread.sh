#!/bin/bash

if [ $# -ne 4 ]; then
  echo "Usage: ./run_link_scaling_dualread.sh <envir_name> <run_num_init> <test_name> <partition>"
  echo "All run numbers up to run_num_init+2 must be unused."
  exit 2
fi

envir_name=$1
run_num_init=$2
test_name=$3
partition=$4

cd $test_name

for i in {16..48..16}
do
	echo "Scaling to ${i} streams"
	run_num_increment=${i}/16
	run_num=$(($run_num_init + $run_num_increment -1))

	nanorc --partition-number ${partition} ${i} $envir_name boot conf start_run $run_num wait 600 stop_run shutdown
		
	# move log files
	mkdir RunConf_$run_num/logs
	mv log_*.txt RunConf_$run_num/logs
	grep -R "ERROR" RunConf_$run_num/logs >> error_summary.txt

	# move output files
	mkdir RunConf_$run_num/output
	mv *.hdf5 RunConf_$run_num/output
	mv logbook_*.txt RunConf_$run_num/output
	mv error_summary.txt RunConf_$run_num/output
	#mv iostat_*.txt RunConf_$run_num/output

	echo "wait for 120s for resources to return to baseline"
	sleep 120

done