#!/bin/bash
# need to source the environment file first

if [ $# -ne 2 ]; then
  echo "Usage: ./AMD_callback_test.sh <output_path> <cpupin_file>"
  echo "Ex: ./AMD_callback_test.sh callbacktest_results/ cpupins/cpupin-eth-mockdlh-np02srv003-1.json"
  exit 2
fi

# Script parameters
test_time=90
output_path=$1
cpupin_file=$2

# NUMA0 cores
cpu_affinity=("1-111:2")

## Callbacks
echo "> consumer_mode : callback"
		
taskset -c $cpu_affinity rubberdaq_test_mock_dlh --run_secs $test_time -n 10 --cb &
sleep 4
readout-affinity.py --pinfile $cpupin_file
sleep 120


## Queues
echo "> consumer_mode : queue"

taskset -c $cpu_affinity rubberdaq_test_mock_dlh --run_secs $test_time -n 10 --ct &
sleep 4
readout-affinity.py --pinfile $cpupin_file
sleep 120


echo "Finished !"
