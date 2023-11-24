#!/bin/bash

if [ $# -ne 7 ]; then
  echo "Usage: ./config_gen.sh <path_to_performancetest> <server_readout> <NUMA_node_num> <data_format> <test> <dunedaq_version> <server_others>"
  echo "<NUMA_node_num>: 0, 1 or 01 (when using both)"
  echo "<data_format>: eth of wib2"
  echo "<test>: ex. stream_scaling"
  echo "<dunedaq_version>: v4_1_1" 
  echo "<server_others>: local server that runs all the apps except the readout"
  exit 2
fi

path=$1
server_readout=$2
NUMA_node_num=$3
data_format=$4
test=$5
dunedaq_version=$6
server_others=$7

test_name=$dunedaq_version-$server_readout-$NUMA_node_num-$data_format-$test-$server_others
mkdir $test_name
cd $test_name

for i in {8..48..8}
do
  fddaqconf_gen -c $path/daqconfs/daqconf-$data_format-$test-$server_readout-$NUMA_node_num.json --detector-readout-map-file $path/readoutmaps/RM-$server_readout-$NUMA_node_num-streams${i}.json ${i}
done
