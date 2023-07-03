#!/bin/bash

if [ $# -ne 4 ]; then
  echo "Usage: ./config_recording_run.sh <test_name> <envir_name> <run_number> <path>"
  echo "path to performancetest"
  exit 2
fi

test_name=$1
envir_name=$2
run_num=$3
path=$4

iostat -m -t 1 120 > iostat_$test_name.txt &
nanorc $test_name $envir_name boot conf start_run $run_num  expert_command $test_name/$test_name/runp02srv00* $path/tests/record-cmd.json wait 600 stop_run shutdown

# move log files
mkdir RunConf_$run_num/logs
mv log_*.txt RunConf_$run_num/logs
grep -R "ERROR" RunConf_$run_num/logs >> error_summary.txt

# move output files
mkdir RunConf_$run_num/output
mv *.hdf5 RunConf_$run_num/output
mv logbook_*.txt RunConf_$run_num/output

echo "wait for 120s for resources to return to baseline"
sleep 120
