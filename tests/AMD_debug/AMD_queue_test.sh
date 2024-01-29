#!/bin/bash
# need to source the environment file first

if [ $# -ne 1 ]; then
  echo "Usage: ./AMD_queue_test.sh <test_time>"
  echo "Ex: ./AMD_queue_test.sh 100000 1 60"
  exit 2
fi

# Script parameters
#queue_size=$1
#queue_type_i=$2
test_time=60
output_path="/nfs/home/mman/DUNE-SW/dunedaq-fddaq-v4.2.0/sourcecode/performancetest/tests/AMD_debug"

cpu_affinity=("0,128")

# Start uProf monitoring
sudo /opt/AMDuProf_4.0-341/bin/AMDuProfPcm -a -s -d 420 -t 250 -m memory,ipc,l1,l2,l3 -A package,ccd -k -o $output_path/uprof-$queue_size-$queue_type.csv &
sleep 2

# queue pusher-puller
for queue_type_i in 1 0
do
	for queue_size in 100000 10000 1000
	do
		if [ "$queue_type_i" == 1 ]; then
        		queue_type="pc"
		else
        		queue_type="dub"
		fi
		echo "> queue_size : $queue_size - queue_type : $queue_type"
		
		dpdklibs_test_queueperf_app -s $queue_size -t $test_time -q $queue_type &
		pid=$(pidof dpdklibs_test_queueperf_app)
		taskset --all-tasks -cp ${cpu_affinity} $pid
		sleep 70
	done
done


echo "Finished !"
