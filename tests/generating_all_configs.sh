#------------------- np02srv003 -----------------
#./config_gen.sh <server_readout> <NUMA_node_num> <data_format> <test> <dunedaq_version>
./config_gen.sh np02srv003 1 eth Emu_stream_scaling v4_3_0
./config_gen.sh np02srv003 1 eth Emu_stream_scaling_swtpg v4_3_0
./config_gen.sh np02srv003 1 eth Emu_stream_scaling_recording v4_3_0
./config_gen.sh np02srv003 1 eth Emu_stream_scaling_recording_swtpg v4_3_0

#------------------- np02srv004 -----------------
#./config_gen.sh <server_readout> <NUMA_node_num> <data_format> <test> <dunedaq_version>
./config_gen.sh np02srv004 0 eth Emu_stream_scaling v4_3_0
./config_gen.sh np02srv004 0 eth Emu_stream_scaling_swtpg v4_3_0
./config_gen.sh np02srv004 0 eth Emu_stream_scaling_recording v4_3_0
./config_gen.sh np02srv004 0 eth Emu_stream_scaling_recording_swtpg v4_3_0

#------------------- np02srv004 -----------------
#./config_gen.sh <server_readout> <NUMA_node_num> <data_format> <test> <dunedaq_version>
./config_gen.sh np02srv001 0 eth Emu_stream_scaling v4_3_0
./config_gen.sh np02srv001 0 eth Emu_stream_scaling_swtpg v4_3_0
