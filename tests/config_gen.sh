#!/bin/bash

if [ $# -ne 4 ]; then
  echo "Usage: ./config_gen.sh <path> <server> <NUMA_node_num> <daqconf_file>"
  echo "<path>: path to performancetest"
  exit 2
fi

path=$1
server=$2
NUMA_node_num=$3
daqconf_file=$4

test_name=perf-$server-$NUMA_node_num
mkdir $test_name
cd $test_name

for i in {8..48..8}
do
  daqconf_multiru_gen -c $path/daqconfs/$daqconf_file --detector-readout-map-file $path/readoutmaps/RM-$server-$NUMA_node_num-stream${i}.json ${i}
done

