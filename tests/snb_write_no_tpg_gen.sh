#!/bin/bash

if [ $# -ne 3 ]; then
  echo "Usage: ./link_scaling_gen.sh <host_address> <pin_file> <output_path>"
  echo "host_address is the address to host all processes except readout (run locally)"
  echo "pin_file is the full path to the cpu pinning config file"
  echo "output path for raw recording"
  exit 2
fi

host_address=$1
pin_file=$2
output_path=$3

for i in {1..24}
do
        daqconf_multiru_gen -d frames.bin -o . -n $i --thread-pinning-file $pin_file --host-df $host_address --host-dfo $host_address --host-trigger $host_address --host-hsi $host_address --enable-raw-recording --raw-recording-output-dir $ouput_path snb_write_no_tpg_n${i}

done


