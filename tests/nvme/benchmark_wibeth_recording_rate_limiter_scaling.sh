#!/bin/bash

if [ $# -ne 1 ]; then
  echo "Usage: ./benchmark_wibeth_recording_rate_limiter_scaling.sh <output_folder>"
  echo "Ex: ./benchmark_wibeth_recording_rate_limiter_scaling.sh results_benchmark_rate_limiter"
  exit 2
fi

# Parameters
#rate=30.5
#targets='nvm_raid0 nvm_raid1'
#duration=100
#buffer_size=8388608

output_dir=$1

# initialize analysis output dir
mkdir -p $output_dir/plots

for i in {8..48..8}
do
  echo "Scaling to ${i} streams"
  ./benchmark_rate_limiter.sh 30.5 'nvm_raid0 nvm_raid1' 100 ${i} 8388608 $output_dir
  echo "${i} streams done"
done
