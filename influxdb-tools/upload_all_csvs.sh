#!/bin/bash
BUCKET_NAME=$(basename $1)
echo $BUCKET_NAME
influx bucket create -n $BUCKET_NAME

for f in $1/*.csv
do

        influx write -b $BUCKET_NAME --file $f 

done