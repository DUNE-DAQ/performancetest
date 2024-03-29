#!/bin/bash

if [ $# -ne 3 ]; then
  echo "Usage: ./start_uprof.sh <output_directory> <test_name> <duration in seconds>"
  exit 2
fi

output_dir=$1
test_name=$2
duration=$3

# cpu core utilization monitoring at 60 second intervals
sar -P ALL 60 75 >> $output_dir/$test_name/core_utilization-${test_name}.csv &

echo "start uprof monitoring"
/opt/AMDuProf_*/bin/AMDuProfPcm -a -s -d $duration -t 2500 -m memory,ipc,l1,l2,l3 -A package -k -o $output_dir/$test_name/uprof-${test_name}.csv &
/opt/AMDuProf_*/bin/AMDuProfCLI-bin timechart --event power --interval 15000 --duration $duration -o $output_dir/$test_name 

cd $output_dir/$test_name/AMDuProf-SWP-Timechart_*/
mv timechart.csv ../timechart-${test_name}.csv

cd ../
