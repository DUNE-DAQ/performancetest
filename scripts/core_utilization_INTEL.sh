#!/bin/bash

if [ $# -ne 2 ]; then
  echo "Usage: ./core_utilization_INTEL.sh <output_directory> <test_name>"
  exit 2
fi

output_dir=$1
test_name=$2

sar -P ALL 60 75 >> ${output_dir}/${test_name}/core_utilization-${test_name}.csv &
