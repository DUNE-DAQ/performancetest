#!/bin/bash
# need to source the environment file first

if [ $# -ne 6 ]; then
  echo "Usage: ./benchmark_rate_limiter.sh <frequency> <device(s)_to_test> <test_time> <num_applications> <buffer_sizes> <output_folder>"
  echo "Ex: ./benchmark_rate_limiter.sh 30.5 'nvm_raid0 nvm_raid1' 100 12 8388608 results_test_rate"
  exit 2
fi

# Script parameters
# freqs="166"
# devices="md0 md1 md2"
# test_time=100
# num_applic=10
# RESULTS_FOLDER="results_rate"
freqs=$1
devices=($2)
test_time=$3
num_applic=$4
RESULTS_FOLDER=$6
mkdir -p $RESULTS_FOLDER
USER=$(whoami)

#cpu_affinity=("0" "1")
device_count=$((${#devices[@]}-1))

if [ $num_applic -lt 9 ]
then
	cpu_affinity=("0" "1")
elif [ $num_applic -lt 17 ]
then
	cpu_affinity=("0,56" "1,57")
elif [ $num_applic -lt 25 ]
then

	cpu_affinity=("0,2,56" "1,3,57")
elif [ $num_applic -lt 33 ]
then
	cpu_affinity=("0,2,4,56,58" "1,3,5,57,59")
elif [ $num_applic -lt 41 ]
then
	cpu_affinity=("0,2,4,56,58,60" "1,3,5,57,59,61")
elif [ $num_applic -lt 49 ]
then
	cpu_affinity=("0,2,4,6,56,58,60" "1,3,5,7,57,59,61")
else
	cpu_affinity=("0-111")
fi


for ((device_num=0; device_num<=$device_count; device_num++)); do
    device=${devices[$device_num]}
    echo "Starting tests for $device"
    mkdir -p "$RESULTS_FOLDER/$device"

    for buffer_size in $5; do
        for freq in $freqs; do
            CURRENT_FOLDER="$RESULTS_FOLDER/$device/results-f$freq-t$test_time-n$num_applic-b$buffer_size"
            mkdir -p "$CURRENT_FOLDER"

	    echo "pre-trimming device $device"
            { time sudo fstrim -v /mnt/$device; } 2> $CURRENT_FOLDER/fstrim_${device}.time

	    echo "> number of applications : $num_applic - freq : $freq kHz - buffer size : $buffer_size"
            
            # Start iostat for devices individual data results
            iostat -x -m 1 $(($test_time+1)) | grep 'nvme\|md' > $CURRENT_FOLDER/$device-$freq-iostat.tmp &

            sleep 1

            # Start a certain number of rate limited tests simultanously
            for ((n=0;n<$num_applic;n++)); do
                fdreadoutlibs_test_bufferedfilewriter /mnt/$device/$USER/filetest_$n $buffer_size -L $freq > $CURRENT_FOLDER/$device-$freq-$n-readout.tmp &
            done;

            # Control CPU affinity
            for pid in $(pgrep fdreadoutlibs); do
                taskset --all-tasks -cp ${cpu_affinity[$device_num]} ${pid}
            done

            # Wait
            sleep $test_time

            # Clean process
            pkill -P $$
            killall fdreadoutlibs_test_bufferedfilewriter
            killall iostat

            # Clean data
            for ((n=0;n<$num_applic;n++)); do
                sed -e 's/.*\(Throughput: \)//g;s/ MiB\/s//g' $CURRENT_FOLDER/$device-$freq-$n-readout.tmp > $CURRENT_FOLDER/$device-$freq-$n-readout.csv
                rm $CURRENT_FOLDER/$device-$freq-$n-readout.tmp
                rm -f /mnt/$device/$USER/filetest_$n
            done;
            sed -e 's/\s\{1,\}/;/g' $CURRENT_FOLDER/$device-$freq-iostat.tmp > $CURRENT_FOLDER/$device-$freq-iostat.csv
            rm $CURRENT_FOLDER/$device-$freq-iostat.tmp

            # sync
            sync

            echo "post-trimming device $device"
            { time sudo fstrim -v /mnt/$device; } 2>> $CURRENT_FOLDER/fstrim_${device}.time

        done;
    done;
done;

echo "Finished !"
