#!/bin/bash
# need to source the environment file first

if [ $# -ne 3 ]; then
  echo "Usage: ./AMD_callback_test.sh <output_path> <cpupin_file> <test_name>"
  echo "Ex: ./AMD_callback_test.sh callbacktest_results/ cpupins/cpupin-eth-mockdlh-np02srv003-1.json"
  exit 2
fi

# Script parameters
test_time=90
output_path=$1
cpupin_file=$2
test_name=$3

# NUMA0 cores
cpu_affinity=("1-111:2")

## Callbacks
echo "> consumer_mode : callback"
#test_name=v4_2_1-np02srv003-1-eth-callback_Intel
sar -P ALL 5 18 >> $output_path/core_utilization-v4_2_1-np02srv003-1-eth-callback_${test_name}.csv &
		
taskset -c $cpu_affinity rubberdaq_test_mock_dlh --run_secs $test_time -n 10 --cb &
sleep 4
readout-affinity.py --pinfile $cpupin_file
sleep 120


## Queues
echo "> consumer_mode : queue"
#test_name=v4_2_1-np02srv003-1-eth-queue_Intel
sar -P ALL 5 18 >> $output_path/core_utilization-v4_2_1-np02srv003-1-eth-queue_${test_name}.csv &

taskset -c $cpu_affinity rubberdaq_test_mock_dlh --run_secs $test_time -n 10 --ct &
sleep 4
readout-affinity.py --pinfile $cpupin_file
sleep 120


echo "Finished !"
