#------------------- np02srv003 -----------------
#./config_gen.sh <server_readout> <NUMA_node_num> <data_format> <test> <dunedaq_version>
./config_gen.sh np02srv003 0 eth stream_scaling v4_2_0
./config_gen.sh np02srv003 0 eth stream_scaling_swtpg v4_2_0
./config_gen.sh np02srv003 0 eth stream_scaling_recording v4_2_0
./config_gen.sh np02srv003 0 eth stream_scaling_recording_swtpg v4_2_0

fddaqconf_gen -c ../daqconfs/daqconf-eth-basic_swtpg-np02srv003-0.json --detector-readout-map-file ../readoutmaps/RM-np02srv003-0-streams48.json v4_2_0-np02srv003-0-eth-basic_swtpg-np04srv025
fddaqconf_gen -c ../daqconfs/daqconf-eth-basic_swtpg-np02srv003-1.json --detector-readout-map-file ../readoutmaps/RM-np02srv003-1-streams48.json v4_2_0-np02srv003-1-eth-basic_swtpg-np04srv025
fddaqconf_gen -c ../daqconfs/daqconf-eth-basic_recording_swtpg-np02srv003-0.json --detector-readout-map-file ../readoutmaps/RM-np02srv003-0-streams48.json v4_2_0-np02srv003-0-eth-basic_recording_swtpg-np04srv025
fddaqconf_gen -c ../daqconfs/daqconf-eth-basic_recording_swtpg-np02srv003-1.json --detector-readout-map-file ../readoutmaps/RM-np02srv003-1-streams48.json v4_2_0-np02srv003-1-eth-basic_recording_swtpg-np04srv025
fddaqconf_gen -c ../daqconfs/daqconf-eth-basic_recording_swtpg_multinode-np02srv003-1.json --detector-readout-map-file ../readoutmaps/RM-np02srv003-1-streams48.json v4_2_0-np02srv003-1-eth-basic_recording_swtpg_multinode-np04srv025

#------------------- np02srv004 -----------------
#./config_gen.sh <server_readout> <NUMA_node_num> <data_format> <test> <dunedaq_version>
./config_gen.sh np02srv004 0 eth stream_scaling v4_2_0
./config_gen.sh np02srv004 0 eth stream_scaling_swtpg v4_2_0
./config_gen.sh np02srv004 0 eth stream_scaling_recording v4_2_0
./config_gen.sh np02srv004 0 eth stream_scaling_recording_swtpg v4_2_0

fddaqconf_gen -c ../daqconfs/daqconf-eth-basic_swtpg-np02srv004-0.json --detector-readout-map-file ../readoutmaps/RM-np02srv004-0-streams48.json v4_2_0-np02srv004-0-eth-basic_swtpg-np04srv025
fddaqconf_gen -c ../daqconfs/daqconf-eth-basic_swtpg-np02srv004-1.json --detector-readout-map-file ../readoutmaps/RM-np02srv004-1-streams48.json v4_2_0-np02srv004-1-eth-basic_swtpg-np04srv025
fddaqconf_gen -c ../daqconfs/daqconf-eth-basic_recording_swtpg-np02srv004-0.json --detector-readout-map-file ../readoutmaps/RM-np02srv004-0-streams48.json v4_2_0-np02srv004-0-eth-basic_recording_swtpg-np04srv025
fddaqconf_gen -c ../daqconfs/daqconf-eth-basic_recording_swtpg-np02srv004-1.json --detector-readout-map-file ../readoutmaps/RM-np02srv004-1-streams48.json v4_2_0-np02srv004-1-eth-basic_recording_swtpg-np04srv025
fddaqconf_gen -c ../daqconfs/daqconf-eth-1stream_recording_swtpg_oneL3-np02srv004-0.json --detector-readout-map-file ../readoutmaps/RM-np02srv004-0-stream1.json v4_2_0-np02srv004-0-eth-1stream_recording_swtpg_oneL3-np04srv025
