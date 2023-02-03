#!/bin/bash

if [ $# -ne 4 ]; then
  echo "Usage: ./link_scaling_gen.sh <test_name> <host_address> <pin_file> <output_path>"
  echo "host_address is the address to host all processes except readout (run locally)"
  echo "pin_file is the full path to the cpu pinning config file"
  echo "output path for raw recording"
  exit 2
fi

test_name=$1
host_address=$2
pin_file=$3
output_path=$4

mkdir $test_name
cp tests/record-cmd.json $test_name/
cd $test_name
curl -o frames.bin -O https://cernbox.cern.ch/index.php/s/0XzhExSIMQJUsp0/download

for i in {1..24}
do
        daqconf_multiru_gen -d frames.bin -o . -n $i --thread-pinning-file $pin_file --host-df $host_address --host-dfo $host_address --host-trigger $host_address --host-hsi $host_address --enable-raw-recording --raw-recording-output-dir $ouput_path snb_write_no_tpg_n${i}

done


