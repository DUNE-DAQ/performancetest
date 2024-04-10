#!/bin/bash

if [ $# -ne 4 ]; then
  echo "Usage: ./run_link_scaling_dualread.sh <partition> <test_name> <user> <envir_name>"
  exit 2
fi

partition=$1
test_name=$2
user=$3
envir_name=$4

cd $test_name

for i in {16..48..16}
do
	echo "Scaling to ${i} streams"
	nano04rc --partition-number $partition --timeout 120 $test_name/$i/conf.json $user $envir_name boot start_run --message "$i streams" wait 600 stop_run shutdown exit
	
	echo "wait for 120s for resources to return to baseline"
	sleep 120

done
