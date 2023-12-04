#!/bin/bash

if [ $# -ne 1 ]; then
  echo "Usage: ./move_raw_data.sh <test_name>"
  exit 2
fi

test_name=$1

cd /mnt/nvm_raid0/

mv output_* $test_name
