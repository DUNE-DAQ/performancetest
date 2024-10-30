import os
import queries, files
import utils
import pathlib
import numpy as np
import pandas as pd

import harvester

from rich import print

def parse_prometheus_generic(response : dict):
    metrics = {}
    values = []

    # get the metrics and values for each smaple
    for r in response["data"]["result"]:
        for k in r["metric"]:
            if k not in metrics:
                metrics[k] = [r["metric"][k]]
            else:
                metrics[k].append(r["metric"][k])
        values.append(np.array(r["values"]))

    # construct a sample name from the metrics
    tags = {}
    for k in metrics:
        if len(np.unique(metrics[k])) > 1:
            tags[k] = metrics[k]

    sample_label = None
    name = None
    for k, v in tags.items():
        if sample_label is None:
            sample_label = np.array(v)
            name = k
        else:
            sample_label = np.char.add(np.char.add(sample_label, "_"), np.array(v))
            name = name + "_" + k

    if sample_label is None: sample_label = ["total"]

    # construct the dataframe
    parsed = {}
    for s, v in zip(sample_label, values):
        parsed["time"] = v[:, 0]
        parsed[s] = v[:, 1]

    return name, pd.DataFrame(parsed).set_index("time").astype(float)

config = files.load_json(f"{os.environ['PERFORMANCE_TEST_PATH']}/config/dashboard_info.json")

host = "np04-srv-031"

datasources = queries.get_datasources(config["grafana_url"])

prometheus_url =  harvester.get_valid_datasources(datasources, dunedaq_version = "v5.2.0")["prometheus"]["url"]

time = queries.time_range(start = 1730308076, end = 1730308136)

query_dict = {
    "CPU Usage (%)" : f"100 * (1 - irate(node_cpu_seconds_total{{nodename=\"{host}\", mode=\"idle\"}}[10m]))",
    "CPU Idle (s)" : f"node_cpu_seconds_total{{nodename=\"{host}\", mode=\"idle\"}}",

    "Total Memory (B)" : f"node_memory_MemTotal_bytes{{nodename=\"{host}\"}}",
    "Available Memory (B)" : f"node_memory_MemAvailable_bytes{{nodename=\"{host}\"}}",
    "Memory Usage (%)" : f"(node_memory_MemTotal_bytes{{nodename=\"{host}\"}} - node_memory_MemAvailable_bytes{{nodename=\"{host}\"}}) / node_memory_MemTotal_bytes{{nodename=\"{host}\"}}",
}

dfs = {}
sample_desc = {}
for query in query_dict:
    name, df = parse_prometheus_generic(queries.query_prometheus(prometheus_url, query_str = query_dict[query], time_range = time))
    dfs[query] = df
    sample_desc[query] = name

print(dfs)
print(sample_desc)

# response = queries.query_prometheus(prometheus_url, query_str = query_str, time_range = time)
# print(parse_prometheus_generic(response))