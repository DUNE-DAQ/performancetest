#!/bin/bash

if [ $# -ne 3 ]; then
  echo "Usage: ./config_run.sh <test_name> <envir_name> <run_number>"
  exit 2
fi

test_name=$1
envir_name=$2
run_num=$3

nanorc $test_name  $envir_name boot conf start_run $run_num wait 600 stop_run shutdown sleep 120
	


