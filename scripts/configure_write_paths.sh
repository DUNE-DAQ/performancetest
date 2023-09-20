#!/bin/bash

for i in {8..48..8}
do
	for j in {1..6}
	do
		pattern=s/nvm_raid0_0.output_0_${j}.out/nvm_raid0_1.output_0_${j}.out/
		sed -i $pattern snb_write_no_tpg_superdune_n${i}/data/ruemu0_conf.json
	done
done
