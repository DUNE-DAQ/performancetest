# NVME tests

## Rate limited test with multiple writting threads

Run benchmark-rate_limiter.sh script on host to test :

```
./benchmark_rate_limiter.sh <frequency> <device(s)_to_test> <test_time> <num_applications> <buffer_sizes> <output_folder>
```
Ex :
```
./benchmark_rate_limiter.sh 166 'md0 md1 md2' 100 10 4096 results_test_rate
```
---
Then create graphs from generated data :
```
python3 compile_benchmark_results.py <data_folder>
```
Ex :
```
python3 compile_benchmark_results.py results_test_rate/
```