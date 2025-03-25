#!/bin/bash

INTEL_PCM_KEY="A_CvwTCWk"
FEE_KEY="frontend_ethernet"
DAQ_OVERVIEW_KEY="overview"
TP_KEY="trigger_primitives"

echo "Processing all hdf5 files in $1 ..."

for file in $1/*.hdf5
do
	fname=$(basename $file)
	field=$(echo ${fname%.*} | cut -d'-' -f3)
	field1=$(echo ${fname%.*} | cut -d'-' -f2) #The intel pcm file is special and doesn't match the naming of the other three so this is an exception for that 

	if [[ $field1 == $INTEL_PCM_KEY ]]; then

	       echo "Convering Intel-PCM file ..."	
	       python hdf5_to_annocsv_test.py -i $file -o "$1/"${fname%.*}"-csv.csv" -t 0 -f "Intel-PCM-DB" >> $1/hdf5_conv_out.txt

	fi

	if [[ $field == $FEE_KEY ]]; then

		echo "Convering Frontend Ethernet file ..."
		python hdf5_to_annocsv_test.py -i $file -o "$1/"${fname%.*}"-csv.csv" -t 1 -f "Frontend-Ethernet" >> $1/hdf5_conv_out.txt

	fi 

	if [[ $field == $DAQ_OVERVIEW_KEY ]]; then

		echo "Convering DAQ-Overview file ..."
		python hdf5_to_annocsv_test.py -i $file -o "$1/"${fname%.*}"-csv.csv" -t 2 -f "DAQ-Overview" >> $1/hdf5_conv_out.txt

	fi 

	if [[ $field == $TP_KEY ]]; then
		
		echo "Convering Trigger Primitive file ..."
		python hdf5_to_annocsv_test.py -i $file -o "$1/"${fname%.*}"-csv.csv" -t 3 -f "Trigger-Primitives" >> $1/hdf5_conv_out.txt

	fi

done

echo "Conversion is done check the file $1/hdf5_conv_out.txt for errors if nothing bad is there go ahead and delete it the csv files will be OK."

