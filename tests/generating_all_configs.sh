#./config_gen.sh <server_readout> <NUMA_node_num> <data_format> <test> <dunedaq_version>
#------------------- np02srv001 -----------------
#./config_gen.sh np02srv001 0 eth Emu_stream_scaling NFDT_PROD4_240306
#./config_gen.sh np02srv001 0 eth Emu_stream_scaling_swtpg NFDT_PROD4_240306

#------------------- np02srv003 -----------------
#./config_gen.sh np02srv003 0 eth Emu_stream_scaling NFDT_PROD4_240306
#./config_gen.sh np02srv003 0 eth Emu_stream_scaling_swtpg NFDT_PROD4_240306
#./config_gen.sh np02srv003 0 eth Emu_stream_scaling_recording NFDT_PROD4_240306
#./config_gen.sh np02srv003 0 eth Emu_stream_scaling_recording_swtpg NFDT_PROD4_240306

#------------------- np02srv004 -----------------
#./config_gen.sh np02srv004 0 eth Emu_stream_scaling NFDT_PROD4_240306
#./config_gen.sh np02srv004 0 eth Emu_stream_scaling_swtpg NFDT_PROD4_240306
#./config_gen.sh np02srv004 0 eth Emu_stream_scaling_recording NFDT_PROD4_240306
#./config_gen.sh np02srv004 0 eth Emu_stream_scaling_recording_swtpg NFDT_PROD4_240306
fddaqconf_gen -c ../daqconfs/daqconf-eth-Emu_stream_scaling-np02srv004-01.json --detector-readout-map-file ../readoutmaps/RM-np02srv004-01-streams96.json NFDT_PROD4_240306-np02srv004-01-eth-Emu_96_streams
fddaqconf_gen -c ../daqconfs/daqconf-eth-Emu_stream_scaling_swtpg-np02srv004-01.json --detector-readout-map-file ../readoutmaps/RM-np02srv004-01-streams96.json NFDT_PROD4_240306-np02srv004-01-eth-Emu_96_streams_swtpg
fddaqconf_gen -c ../daqconfs/daqconf-eth-Emu_stream_scaling-np02srv004-01.json --detector-readout-map-file ../readoutmaps/RM-np02srv004-01-streams80.json NFDT_PROD4_240306-np02srv004-01-eth-Emu_80_streams
fddaqconf_gen -c ../daqconfs/daqconf-eth-Emu_stream_scaling_swtpg-np02srv004-01.json --detector-readout-map-file ../readoutmaps/RM-np02srv004-01-streams80.json NFDT_PROD4_240306-np02srv004-01-eth-Emu_80_streams_swtpg

