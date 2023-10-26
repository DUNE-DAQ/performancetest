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

# CPU affinity mapping from physical cores to threads, on np02-srv-003
# 'device0_threads,... device1_threads,...'
physical_cores_1='0,56 1,57'
physical_cores_2='0,2,56,58 1,3,57,59'
physical_cores_3='0,2,4,56,58,60 1,3,5,57,59,61'
physical_cores_4='0,2,4,6,56,58,60,62 1,3,5,7,57,59,61,63'
physical_cores_all='0-111 0-111'

# initialize analysis output dir
mkdir -p $output_dir/plots

for i in {8..48..8}
do
  echo "Scaling to ${i} streams"

  # select cpu pinning
  if [ $i -lt 9 ]
  then
        cpu_affinity=$physical_cores_1
  elif [ $i -lt 17 ]
  then
        cpu_affinity=$physical_cores_1
  elif [ $i -lt 25 ]
  then
        cpu_affinity=$physical_cores_2
  elif [ $i -lt 33 ]
  then
        cpu_affinity=$physical_cores_3
  elif [ $i -lt 41 ]
  then
        cpu_affinity=$physical_cores_3
  elif [ $i -lt 49 ]
  then
        cpu_affinity=$physical_cores_4
  else
        cpu_affinity=$physical_cores_all
  fi

  echo $cpu_affinity

  ./benchmark_rate_limiter.sh 30.5 "nvm_raid0 nvm_raid1" 100 ${i} 8388608 $output_dir "${cpu_affinity}"
  echo "${i} streams done"
done
