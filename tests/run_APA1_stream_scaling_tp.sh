#!/bin/bash

if [ $# -ne 3 ]; then
  echo "Usage: ./run_link_scaling.sh <envir_name> <run_num_init> <test_name>"
  echo "All run numbers up to run_num_init+5 must be unused."
  exit 2
fi

envir_name=$1
run_num_init=$2
test_name=$3

mkdir -p $test_name
#cd $test_name

# cpu utilization
sar -P ALL 60 65 >> $test_name/cpupins_utilization_${test_name}.txt &

for i in {8..40..8}
do
	global_cfg=global_configs/stream_scaling/np04_APA1_WIB_${i}_tp_perftest.json
        cpupin_file=np04daq-configs/cpupin_files/cpupin-all-running.json

	echo "Scaling to ${i} streams"
	run_num_increment=${i}/8 
	run_num=$(($run_num_init + $run_num_increment -1))

	nanorc $global_cfg $envir_name boot conf start $run_num pin_threads --pin-thread-file $cpupin_file enable_triggers wait 600 stop_run shutdown
		
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
        mv RunConf_$run_num $test_name

	echo "wait for 120s for resources to return to baseline"
	sleep 120

done
