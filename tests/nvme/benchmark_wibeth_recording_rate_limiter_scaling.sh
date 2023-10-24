#!/bin/bash

# Parameters
#rate=30.5
#targets='nvm_raid0 nvm_raid1'
#duration=100
#buffer_size=8388608

output_dir=results_benchmark_rate_limiter

# initialize analysis output dir
mkdir -p $output_dir/plots

for i in {8..48..8}
do
  echo "Scaling to ${i} streams"
  ./benchmark_rate_limiter.sh 30.5 'nvm_raid0 nvm_raid1' 100 ${i} 8388608 $output_dir
  echo "${i} streams done"
done
