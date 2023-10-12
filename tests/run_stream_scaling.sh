#!/bin/bash

if [ $# -ne 3 ]; then
  echo "Usage: ./run_link_scaling.sh <envir_name> <run_num_init> <test_name>"
  echo "All run numbers up to run_num_init+5 must be unused."
  exit 2
fi

envir_name=$1
run_num_init=$2
test_name=$3

cd $test_name

for i in {8..48..8}
do
	# disk throughput
    #iostat -m -t 1 120 > iostat_${i}.txt &
	
	echo "Scaling to ${i} streams"
	run_num_increment=${i}/8 
	run_num=$(($run_num_init + $run_num_increment -1))

	nanorc ${i} $envir_name boot conf start_run $run_num wait 300 stop_run shutdown
		
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
