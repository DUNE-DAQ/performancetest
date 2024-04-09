#!/bin/bash

if [ $# -ne 5 ]; then
  echo "Usage: ./config_gen_dualread.sh <server_readout> <NUMA_node_num> <data_format> <test> <dunedaq_version>"
  echo "<NUMA_node_num>: 0, 1 or 01 (when using both)"
  echo "<data_format>: eth of wib2"
  echo "<test>: ex. stream_scaling"
  echo "<dunedaq_version>: v4_1_1" 
  exit 2
fi

server_readout=$1
NUMA_node_num=$2
data_format=$3
test=$4
dunedaq_version=$5

test_name=$dunedaq_version-$server_readout-$NUMA_node_num-$data_format-$test
mkdir $test_name
cd $test_name

for i in {16..48..16}
do
  fddaqconf_gen -c ../../daqconfs/daqconf-$data_format-$test-$server_readout-$NUMA_node_num.json --detector-readout-map-file ../../readoutmaps/RM-$server_readout-$NUMA_node_num-streams${i}.json ${i}
done
