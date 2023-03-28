#!/bin/sh
# need to source the environment file first

if [ $# -ne 5 ]; then
  echo "Usage: ./benchmark_rate_limiter.sh <frequency> <device(s)_to_test> <test_time> <num_applications> <output_folder>"
  echo "Ex: ./benchmark_rate_limiter.sh 166 'md0 md1 md2' 100 10 results_test_rate"
  exit 2
fi

# Script parameters
# freqs="166"
# devices="md0 md1 md2"
# test_time=100
# num_applic=10
# RESULTS_FOLDER="results_rate"
freqs=$1
devices=$2
test_time=$3
num_applic=$4
RESULTS_FOLDER=$5


mkdir $RESULTS_FOLDER

for device in $devices; do
    echo "Starting tests for $device"
    mkdir "$RESULTS_FOLDER/$device"

        for freq in $freqs; do
            echo "> freq : $freq"

            CURRENT_FOLDER="$RESULTS_FOLDER/$device"
            
            # Start iostat for devices individual data results
            iostat -x -m 1 $(($test_time+1)) | grep 'nvme\|md' > $CURRENT_FOLDER/$device-$freq-iostat.tmp &

            sleep 1

            # Start a certain number of rate limited tests simultanously
            for ((n=0;n<$num_applic;n++)); do
                readoutlibs_test_bufferedfilewriter /mnt/$device/filetest_$n -L $freq > $CURRENT_FOLDER/$device-$freq-$n-readout.tmp &
            done;

            # Wait
            sleep $test_time

            # Clean process
            pkill -P $$
            killall readoutlibs_test_bufferedfilewriter
            killall iostat

            # Clean data
            for ((n=0;n<$num_applic;n++)); do
                sed -e 's/.*\(Throughput: \)//g;s/ MiB\/s//g' $CURRENT_FOLDER/$device-$freq-$n-readout.tmp > $CURRENT_FOLDER/$device-$freq-$n-readout.csv
                rm $CURRENT_FOLDER/$device-$freq-$n-readout.tmp
                rm -f /mnt/$device/filetest_$n
            done;
            sed -e 's/\s\{1,\}/;/g' $CURRENT_FOLDER/$device-$freq-iostat.tmp > $CURRENT_FOLDER/$device-$freq-iostat.csv
            rm $CURRENT_FOLDER/$device-$freq-iostat.tmp        
    done
done

echo "Finished !"