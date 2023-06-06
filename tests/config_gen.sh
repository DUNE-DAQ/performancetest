#!/bin/bash

if [ $# -ne 4 ]; then
  echo "Usage: ./config_gen.sh <daqconf_file> <hwmap_file> <test_name>"
  exit 2
fi

daqconf_file=$1
hwmap_file=$2
test_name=$3

daqconf_multiru_gen -c ./../dunedaq-v4.0.0/sourcecode/performancetest/daqconfs/$daqconf_file --hardware-map-file ./../dunedaq-v4.0.0/sourcecode/performancetest/hwmaps/$hwmap_file $test_name
