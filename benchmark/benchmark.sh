#!/bin/sh

if [ $# -ne 2 ]; then
  echo "Usage: ./benchmark.sh <path> <output_path>"
  echo "<path>: path to performancetest"
  exit 2
fi

path=$1
output_path=$2

cp $path/benchmark/user-config.xml ~/.phoronix-test-suite/
cp -r $path/benchmark/local/ ~/.phoronix-test-suite/test-suites/

export CFLAGS='-mcmodel=medium'

phoronix-test-suite batch-benchmark dunedaq-srv-benchmark

results=$(ls -t ~/.phoronix-test-suite/test-results/ | head -n1)

phoronix-test-suite result-file-to-csv $results

mv ~/$results.csv $output_path

echo "Moved Output To: $output_path"

