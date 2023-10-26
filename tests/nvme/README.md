# NVME tests

## Setup
Check status of auto trim
```
sudo systemctl status fstrim.timer
```
If not already, disable auto-trim
```
sudo systemctl disable fstrim.timer
```
Make directories on NVMe drives
```
mkdir /mnt/nvm_raid0/$USER /mnt/nvm_raid1/$USER
```

## Benchmark NVMEs with WIBEth and stream scaling
To run the nvme benchmark test using WiBEth frame sizes and rates, with stream scaling from 8 to 48 :
```
./benchmark_wibeth_recording_rate_limiter_scaling.sh <output_folder>
```
---
Then create graphs from generated data with output sent to `<data_folder>/plots`:
```
python generate_graph_rate_limited_test.py <data_folder>
```
Ex :
```
python3 generate_graph_rate_limited_test.py results_test_rate/
```


## Rate limited test with multiple writing threads

Run `benchmark_rate_limiter.sh` script standalone on host to test :

```
./benchmark_rate_limiter.sh <frequency> <device(s)_to_test> <test_time> <num_applications> <buffer_sizes> <output_folder> <cpu_affinity>
```
Ex :
```
./benchmark_rate_limiter.sh 30.5 'nvm_raid0 nvm_raid1' 100 8 8388608 results_test_rate '0,56 1,57'
```
---
Then create graphs from generated data with output sent to `<data_folder>/plots`:
```
python generate_graph_rate_limited_test.py <data_folder>
```
Ex :
```
python3 generate_graph_rate_limited_test.py results_test_rate/
```
