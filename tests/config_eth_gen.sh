#!/bin/bash

if [ $# -ne 4 ]; then
echo "Usage: ./config_eth_gen.sh <path> <daqconf_file> <hwmap_file> <test_name>"
ecjo "path to performancetest"
exit 2
fi

path=$1
daqconf_file=$2
hwmap_file=$3
test_name=$4

daqconf_multiru_gen -c ./$path/daqconfs/$daqconf_file --detector-readout-map-file ./$path/readoutmaps/$hwmap_file $test_name