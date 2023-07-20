#!/bin/bash

if [ $# -ne 3 ]; then
  echo "Usage: ./config_recording_run.sh <test_names> <envir_name> <run_number_init>"
  exit 2
fi

test_names=$1
envir_name=$2
run_num_init=$3

#test_names=('us-east-2a' 'us-west-1a' 'eu-central-1a')

for test_name_i in "${test_names[@]}"
do
    run_num=$(($run_num_init+(counter++)))
    echo "$test_name_i"
    iostat -m -t 1 120 > iostat_$test_name_i.txt &
    nanorc $test_name_i $envir_name boot conf start_run $run_num wait 600 stop_run shutdown

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
