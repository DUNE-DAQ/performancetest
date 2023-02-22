#!/bin/bash

for i in {1..24}
do
	for j in {12..23}
	do
		pattern=s/nvm_raid0_0.output_0_${j}.out/nvm_raid0_1.output_0_${j}.out/
		sed -i $pattern snb_write_no_tpg_superdune_n${i}/data/ruemu0_conf.json
	done
done
