#!/bin/bash

if [ $# -ne 2 ]; then
  echo "Usage: ./start_uprof.sh <output_directory> <duration in seconds>"
  exit 2
fi

output_dir=$1
duration=$2

echo "start uprof monitoring"
/opt/AMDuProf_4.0-341/bin/AMDuProfPcm -a -s -d $duration -t 2500 -m memory,ipc,l1,l2,l3 -A package -k -o $output_dir/uprof-$output_dir.csv &
/opt/AMDuProf_4.0-341/bin/AMDuProfCLI-bin timechart --event power --interval 15000 --duration $duration -o $output_dir 

cd $output_dir/AMDuProf-SWP-Timechart_*/
mv timechart.csv ../timechart-$output_dir.csv

cd ../
