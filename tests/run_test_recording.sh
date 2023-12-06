#!/bin/bash

if [ $# -ne 5 ]; then
  echo "Usage: ./run_stream_scaling_recording.sh <envir_name> <run_num> <test_name> <server> <NUMA_node_num>"
  exit 2
fi

envir_name=$1
run_num=$2
test_name=$3
server=$4
NUMA_node_num=$5

nanorc $test_name $envir_name boot conf start_run $run_num expert_command --timeout 10 $test_name/$test_name/ru${server}eth${NUMA_node_num} record-cmd.json wait 900 stop_run shutdown

mkdir RunConf_$run_num/output
mv log_*.txt RunConf_$run_num/output
grep -R "ERROR" RunConf_$run_num/output >> error_summary.txt
rm *.hdf5 
mv logbook_*.txt RunConf_$run_num/output
mv RunConf_$run_num $test_name/

echo "wait for 100s for resources to return to baseline"
sleep 100
