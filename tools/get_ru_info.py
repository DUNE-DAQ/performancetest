#!/usr/bin/env python
import argparse
import json
import os
import subprocess

from rich import print


def run_command(host : str, cmd : str) -> subprocess.CompletedProcess:
    return subprocess.run(['ssh', f'{os.environ["USER"]}@{host}', f'{cmd}'], capture_output = True)


def parse_output(output: subprocess.CompletedProcess, separator : str = None) -> list | dict:
    output_lines = str(output.stdout)[2:].split("\\n")

    if separator:
        parsed = {}
        for i in output_lines:
            info = i.split(separator)
            if len(info) > 1:
                parsed[info[0]] = info[1].replace("  ", "")

        return parsed
    else:
        return output_lines


def get_cpu_info(host : str) -> dict:
    return parse_output(run_command(host, "lscpu"), ":")


def get_pci_info(host : str) -> dict:
    output = parse_output(run_command(host, "lspci | grep -E -i 'network|ethernet'"))

    parsed = {}
    for i in output:
        info = i.split(":")
        if len(info) > 1:
            parsed[info[0]+info[1]] = info[-1].replace("  ", "")
    return parsed


def get_os_info(host : str) -> dict:
    return parse_output(run_command(host, "cat /etc/os-release"), separator = "=")


def get_dpdk_info(host : str) -> dict:
    output = run_command(host, "dpdk-testpmd -v -h | grep EAL:")
    lines = str(output.stderr)[2:].split("\\n")

    parsed = {}
    for l in lines:
        if "EAL:" in l:
            info = l.split(": ")
            parsed[info[1]] = info[2]
    return parsed


def get_disk_info(host : str):
    return json.loads(run_command(host, "lsblk -o NAME,MODEL,SIZE -d --json").stdout)


def create_list_dict(dictionary : dict):
    l = "<ul>\n"
    for k, v in dictionary.items():
        l += f"<li> {k} : {v} </li>\n"
    l += "</ul>"
    return l

def get_ru_info(host : str) -> list[str]:
    cpu = get_cpu_info(host)
    pci = get_pci_info(host)
    op = get_os_info(host)
    dpdk = get_dpdk_info(host)
    disk = get_disk_info(host)

    cpu_info = [
    "Architecture",
    "CPU(s)",
    "Model name",
    "Thread(s) per core",
    "Core(s) per socket",
    "Socket(s)",
    "CPU max MHz",
    "CPU min MHz",
    'L1d cache',
    'L1i cache',
    'L2 cache',
    'L3 cache',
    'NUMA node(s)'
    ]


    op_info = [
        "NAME",
        "VERSION",
        "ID",
    ]

    lines = ["<p> CPU: </p>"]
    
    lines.append(create_list_dict({k : v for k, v in cpu.items() if k in cpu_info}))

    lines.append("<p> PCI: </p>")

    lines.append(create_list_dict({k.split(".0 ")[-1] : v for k, v in pci.items() if ".0" in k}))

    lines.append("<p> OS: </p>")
    lines.append(create_list_dict({k : v for k, v in op.items() if k in op_info}))

    lines.append("<p> DPDK: </p>")
    lines.append(create_list_dict({k : v for k, v in dpdk.items() if k in dpdk}))

    lines.append("<p> DISK: </p>")
    for i in disk["blockdevices"]:
        lines.append(create_list_dict({k : v for k, v in i.items()}))
    return lines

def main(args : argparse.Namespace):
    host = args.host
    file_path = f"{host}_specs.html"
    with open(file_path, "w") as file:
        file.writelines(get_ru_info(host))

    print(f"specifications written to {file_path}")
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Collect system information for readout host.")

    parser.add_argument("-r", "--readout-server", type = str, dest = "host", help = "server name e.g. np02-srv-003", required = True)


    args = parser.parse_args()

    print(args)
    main(args)