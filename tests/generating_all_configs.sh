#./config_gen.sh <server_readout> <NUMA_node_num> <data_format> <test> <dunedaq_version>
#------------------- np02srv001 -----------------
#./config_gen.sh np02srv001 0 eth Emu_stream_scaling NFDT_PROD4_240306
#./config_gen.sh np02srv001 0 eth Emu_stream_scaling_swtpg NFDT_PROD4_240306

#------------------- np02srv003 -----------------
#./config_gen.sh np02srv003 0 eth Emu_stream_scaling NFDT_PROD4_240306
#./config_gen.sh np02srv003 0 eth Emu_stream_scaling_swtpg NFDT_PROD4_240306
#./config_gen.sh np02srv003 0 eth Emu_stream_scaling_recording NFDT_PROD4_240306
#./config_gen.sh np02srv003 0 eth Emu_stream_scaling_recording_swtpg NFDT_PROD4_240306
#./config_gen_dualread.sh np02srv003 01 eth Emu_stream_scaling NFDT_PROD4_240306
./config_gen_dualread.sh np02srv003 01 eth Emu_stream_scaling_swtpg NFDT_PROD4_240306

#------------------- np02srv004 -----------------
#./config_gen.sh np02srv004 0 eth Emu_stream_scaling NFDT_PROD4_240306
#./config_gen.sh np02srv004 0 eth Emu_stream_scaling_swtpg NFDT_PROD4_240306
#./config_gen.sh np02srv004 0 eth Emu_stream_scaling_recording NFDT_PROD4_240306
#./config_gen.sh np02srv004 0 eth Emu_stream_scaling_recording_swtpg NFDT_PROD4_240306
#./config_gen_dualread.sh np02srv004 01 eth Emu_stream_scaling NFDT_PROD4_240306
./config_gen_dualread.sh np02srv004 01 eth Emu_stream_scaling_swtpg NFDT_PROD4_240306


