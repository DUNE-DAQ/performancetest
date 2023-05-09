#!/bin/bash

if [ $# -ne 1 ]; then
  echo "Usage: ./start_uprof.sh <output_directory>"
  exit 2
fi

output_dir=$1

echo "start uprof monitoring"
/opt/AMDuProf_4.0-341/bin/AMDuProfPcm -a -s -d 18000 -t 2500 -m memory,ipc,l1,l2,l3 -A package -k -o ${output_dir}/uprof_pcm.csv &
#/opt/AMDuProf_4.0-341/bin/bin/AMDuProfCLI timechart --event power --interval 15000 --duration 18000 -o ${output_dir} &
/opt/AMDuProf_4.0-341/bin/AMDuProfCLI-bin timechart --event power --interval 15000 --dur\
ation 18000 -o ${output_dir} &
