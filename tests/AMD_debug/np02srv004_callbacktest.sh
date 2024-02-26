#!/bin/bash
# need to source the environment file first

if [ $# -ne 2 ]; then
  echo "Usage: ./AMD_callback_test.sh <output_path> <cpupin_file>"
  echo "Ex: ./AMD_callback_test.sh 60"
  exit 2
fi

# Script parameters
test_time=90
output_path=$1
cpupin_file=$2

# NUMA0 cores
cpu_affinity=("64-127,192-255")

## Callbacks
echo "> consumer_mode : callback"
test_name=v4_2_1-np02srv004-1-eth-callback_AMD
# Start uProf monitoring
sudo /opt/AMDuProf_4.0-341/bin/AMDuProfPcm -a -s -d 95 -t 250 -m memory,ipc,l1,l2,l3 -A package,ccd -k -o $output_path/uprof-$test_name.csv &

# cpu core utilization monitoring at 5 second intervals
sar -P ALL 5 18 >> $output_path/core_utilization-${test_name}.txt &

taskset -c $cpu_affinity rubberdaq_test_mock_dlh --run_secs $test_time -n 10 --cb &
sleep 4
readout-affinity.py --pinfile $cpupin_file
sleep 120


## Queues
echo "> consumer_mode : queue"
test_name=v4_2_1-np02srv004-1-eth-queue_AMD
sudo /opt/AMDuProf_4.0-341/bin/AMDuProfPcm -a -s -d 95 -t 250 -m memory,ipc,l1,l2,l3 -A package,ccd -k -o $output_path/uprof-$test_name.csv &

sar -P ALL 5 18 >> $output_path/core_utilization-${test_name}.txt &

taskset -c $cpu_affinity rubberdaq_test_mock_dlh --run_secs $test_time -n 10 --ct &
sleep 4
readout-affinity.py --pinfile $cpupin_file
sleep 120


echo "Finished !"
