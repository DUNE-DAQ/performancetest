#!/bin/bash
###
# Created on: 2023
#
# Author: Matthew Man
# Affiliation: University of Toronto
#
# Description: Run AMD uProf monitoring
###

if [ $# -ne 2 ]; then
  echo "Usage: ./start_uprof.sh <test_name> <duration in seconds>"
  exit 2
fi

test_name=$1
duration=$2

echo "start uprof monitoring"
/opt/AMDuProf_*/bin/AMDuProfPcm -a -s -d $duration -t 1000 -m memory,ipc,l1,l2,l3 -A package -k -q -o uprof-${test_name}.csv &
PCM_ID=$(echo $!)

/opt/AMDuProf_*/bin/AMDuProfCLI-bin timechart --event power --interval 1000 --duration $duration -o /tmp/$test_name
CLI_ID=$(echo $!)

wait $PCM_ID
wait $CLI_ID

echo "done."

cat uprof-${test_name}.csv /tmp/$test_name/AMDuProf-SWP-Timechart_*/timechart.csv > uprof-${test_name}-merged.csv

# clean up files
rm -rf uprof-${test_name}.csv
rm -rf /tmp/$test_name

echo "uprof outputs located in" uprof-${test_name}.csv