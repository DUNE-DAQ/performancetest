import utils
import pathlib

cernbox_upload_url = "https://cernbox.cern.ch/remote.php/dav/public-files/v8xXXMvFx6Dvyuq/"
response = utils.transfer(cernbox_upload_url, {"grafana-v5_2_0-frontend_ethernet-v5_2_0-np02srv003-01-eth-example.hdf5" : pathlib.Path("/nfs/sw/dunedaq_performance_test/work/2xCRP/grafana-v5_2_0-frontend_ethernet-v5_2_0-np02srv003-01-eth-example.hdf5")})

print(response.text)

# print(utils.make_public_link("grafana-v5_2_0-frontend_ethernet-v5_2_0-np02srv003-01-eth-example.hdf5"))

#! create ssh key for perftest (requires the person knows the account password)
#! create mount point in work
# - mkdir perftest
# - sshfs username@remote-server:/path/to/remote-directory ~/remote-mount