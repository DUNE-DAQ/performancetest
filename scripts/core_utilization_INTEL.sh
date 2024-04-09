#!/bin/bash

if [ $# -ne 3 ]; then
  echo "Usage: ./core_utilization_INTEL.sh <output_directory> <test_name> <duration_min>"
  exit 2
fi

output_dir=$1
test_name=$2
duration_min=$3

sar -P ALL 60 ${duration_min} >> ${output_dir}/${test_name}/core_utilization-${test_name}.csv &
