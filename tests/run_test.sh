#!/bin/bash

if [ $# -ne 3 ]; then
  echo "Usage: ./run_link_scaling.sh <envir_name> <run_num> <test_name>"
  exit 2
fi

envir_name=$1
run_num=$2
test_name=$3

nanorc $test_name $envir_name boot conf start_run $run_num wait 900 stop_run shutdown
	
# move log files
mkdir RunConf_$run_num/logs
mv log_*.txt RunConf_$run_num/logs
grep -R "ERROR" RunConf_$run_num/logs >> error_summary.txt

# move output files
mkdir RunConf_$run_num/output
mv *.hdf5 RunConf_$run_num/output
mv logbook_*.txt RunConf_$run_num/output
mv error_summary.txt RunConf_$run_num/output
mv RunConf_$run_num $test_name/

echo "wait for 100s for resources to return to baseline"
sleep 100
