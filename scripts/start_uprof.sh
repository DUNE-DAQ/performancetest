#!/bin/bash

echo "start uprof monitoring"
/home/centos/Downloads/AMDuProf_Linux_x64_4.0.341/bin/AMDuProfPcm -a -s -d 18000 -t 2500 -m memory,ipc,l1,l2,l3 -A package -k -o /home/centos/Desktop/uprof_data/uprof_pcm_record.csv &
/home/centos/Downloads/AMDuProf_Linux_x64_4.0.341/bin/AMDuProfCLI timechart --event power --interval 15000 --duration 18000 -o /home/centos/Desktop/uprof_data &

