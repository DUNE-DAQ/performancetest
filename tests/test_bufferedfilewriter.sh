#!/bin/bash

if [ $# -ne 1 ]; then
  echo "Usage: ./test_bufferedfilewriter.sh <filename>"
  echo "Give path to file to write to, to benchmark write performance of RAID disks."
  exit 2
fi

filename=$1

# disk throughput
iostat -m -t 1 140 > bufferedfilewriter_throughput.txt &

timeout 120 readoutlibs_test_bufferedfilewriter $filename
