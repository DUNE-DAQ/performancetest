#!/bin/bash

for i in {8..48..8}
do
	pattern=s/nvm_raid0_0.output_0_${i}.out/nvm_raid0_0.output_0_${i}.out/
	sed -i $pattern snb_write_no_tpg_superdune_n${i}/data/ruemu0_conf.json
done
