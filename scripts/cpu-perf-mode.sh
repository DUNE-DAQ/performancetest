#!/bin/bash

echo "Disabling Idle-State level 6-2 on all cores..."
cpupower -c all idle-set -d 6
cpupower -c all idle-set -d 5
cpupower -c all idle-set -d 4
cpupower -c all idle-set -d 3
cpupower -c all idle-set -d 2
cpupower idle-info

echo " "
echo "Set frequency governor to performance (if available)..."
cpupower -c all frequency-set --governor performance
cpupower frequency-info

echo " "
echo "Set performance bias to max performance..."
cpupower -c all set --perf-bias 0
cpupower -c all info

echo " "
echo "Monitor current Idle-States..."
cpupower monitor

echo " "
echo "#########################################"
echo "# Cross-check current idle states above #"
echo "#      All cores should idle in C1      #"
echo "#########################################"

