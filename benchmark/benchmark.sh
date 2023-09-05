#!/bin/sh

if [ $# -ne 3 ]; then
  echo "Usage: ./benchmark.sh <path> <output_path> <test_name>"
  echo "<path>: path to performancetest"
  exit 2
fi

path=$1
output_path=$2
test_name=$3
test_suite=dunedaq-srv-benchmark

cp $path/benchmark/user-config.xml ~/.phoronix-test-suite/
cp -r $path/benchmark/local/ ~/.phoronix-test-suite/test-suites/

export CFLAGS='-mcmodel=medium'

phoronix-test-suite batch-benchmark $test_suite

results=$(ls -t ~/.phoronix-test-suite/test-results/ | head -n1)

phoronix-test-suite result-file-to-csv $results

mv ~/$results.csv $output_path/$test_name.csv

echo "Moved Output To: $output_path/$test_name.csv"

