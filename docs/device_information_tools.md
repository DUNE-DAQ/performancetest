# Getting Hardware Information
This document lists the current tools that can be used to acquire hardware information about a given server using tools such as lshw under the hood.

You can see how to use all these tools by using the `--help` option

## auto_discovery.py

Will parse the output of numactl, `lshw`, `lspci`, `nvme` and `mdadm`, and pretty print the information. Example output from np04-srv-017:

```[bash]
(dbt) [sbhuller@np04-srv-017 scripts]$ auto_discovery.py 
Error running 'nvme list-subsys': b'Failed to scan topology: No such file or directory\n'
Error running 'nvme list': b'Failed to scan topology: No such file or directory\n'
Error running 'ls /dev/md/': b"ls: cannot access '/dev/md/': No such file or directory\n"
Error running 'lshw -C Network -C Storage -json': b'WARNING: you should run this program as super-user.\nWARNING: output may be incomplete or inaccurate, you should run this program as super-user.\n'
#### Hardware info...
  -> Logical CPU count: 32
  -> Physical CPU count: 16
  -> NUMA nodes: 2
   * CPUs node 0 0 2 4 6 8 10 12 14 16 18 20 22 24 26 28 30
   * size node 0 32284672
   * free node 0 22690816
   * devs node 0 [
    [
        "0000:01:00.0",
        {
            "id": "network:0",
            "class": "network",
            "claimed": true,
            "handle": "PCI:0000:01:00.0",
            "description": "Ethernet interface",
            "product": "Ethernet Controller X710 for 10GbE SFP+",
            "vendor": "Intel Corporation",
            "physid": "0",
            "businfo": "pci@0000:01:00.0",
            "logicalname": "eno1",
            "version": "01",
            "serial": "24:6e:96:45:25:8c",
            "units": "bit/s",
            "size": 10000000000,
            "capacity": 10000000000,
            "width": 64,
            "clock": 33000000,
            "configuration": {
                "autonegotiation": "off",
                "broadcast": "yes",
                "driver": "i40e",
                "driverversion": "5.14.0-362.8.1.el9_3.x86_64",
                "duplex": "full",
                "firmware": "5.05 0x80002885 17.5.12",
                "ip": "10.73.136.40",
                "latency": "0",
                "link": "yes",
                "multicast": "yes",
                "speed": "10Gbit/s"
            },
            "capabilities": {
                "bus_master": "bus mastering",
                "cap_list": "PCI capabilities listing",
                "rom": "extension ROM",
                "ethernet": true,
                "physical": "Physical interface",
                "fibre": "optical fibre",
                "10000bt-fd": "10Gbit/s (full duplex)"
            }
        }
    ],
    [
        "0000:01:00.1",
        {
            "id": "network:1",
            "class": "network",
            "claimed": true,
            "handle": "PCI:0000:01:00.1",
            "description": "Ethernet interface",
            "product": "Ethernet Controller X710 for 10GbE SFP+",
            "vendor": "Intel Corporation",
            "physid": "0.1",
            "businfo": "pci@0000:01:00.1",
            "logicalname": "eno2",
            "version": "01",
            "serial": "24:6e:96:45:25:8e",
            "units": "bit/s",
            "capacity": 10000000000,
            "width": 64,
            "clock": 33000000,
            "configuration": {
                "autonegotiation": "off",
                "broadcast": "yes",
                "driver": "i40e",
                "driverversion": "5.14.0-362.8.1.el9_3.x86_64",
                "firmware": "5.05 0x80002885 17.5.12",
                "latency": "0",
                "link": "no",
                "multicast": "yes"
            },
            "capabilities": {
                "bus_master": "bus mastering",
                "cap_list": "PCI capabilities listing",
                "rom": "extension ROM",
                "ethernet": true,
                "physical": "Physical interface",
                "1000bt-fd": "1Gbit/s (full duplex)",
                "1000bx-fd": "1Gbit/s (full duplex)",
                "10000bt-fd": "10Gbit/s (full duplex)",
                "10000bx-fd": "10Gbit/s (full duplex)",
                "autonegotiation": "Auto-negotiation"
            }
        }
    ],
    [
        "0000:06:00.0",
        {
            "id": "network:0",
            "class": "network",
            "claimed": true,
            "handle": "PCI:0000:06:00.0",
            "description": "Ethernet interface",
            "product": "I350 Gigabit Network Connection",
            "vendor": "Intel Corporation",
            "physid": "0",
            "businfo": "pci@0000:06:00.0",
            "logicalname": "eno3",
            "version": "01",
            "serial": "24:6e:96:45:25:ac",
            "units": "bit/s",
            "capacity": 1000000000,
            "width": 32,
            "clock": 33000000,
            "configuration": {
                "autonegotiation": "on",
                "broadcast": "yes",
                "driver": "igb",
                "driverversion": "5.14.0-362.8.1.el9_3.x86_64",
                "firmware": "1.67, 0x80000d6b, 17.5.12",
                "latency": "0",
                "link": "no",
                "multicast": "yes",
                "port": "twisted pair"
            },
            "capabilities": {
                "bus_master": "bus mastering",
                "cap_list": "PCI capabilities listing",
                "rom": "extension ROM",
                "ethernet": true,
                "physical": "Physical interface",
                "tp": "twisted pair",
                "10bt": "10Mbit/s",
                "10bt-fd": "10Mbit/s (full duplex)",
                "100bt": "100Mbit/s",
                "100bt-fd": "100Mbit/s (full duplex)",
                "1000bt-fd": "1Gbit/s (full duplex)",
                "autonegotiation": "Auto-negotiation"
            }
        }
    ],
    [
        "0000:06:00.1",
        {
            "id": "network:1",
            "class": "network",
            "claimed": true,
            "handle": "PCI:0000:06:00.1",
            "description": "Ethernet interface",
            "product": "I350 Gigabit Network Connection",
            "vendor": "Intel Corporation",
            "physid": "0.1",
            "businfo": "pci@0000:06:00.1",
            "logicalname": "eno4",
            "version": "01",
            "serial": "24:6e:96:45:25:ad",
            "units": "bit/s",
            "capacity": 1000000000,
            "width": 32,
            "clock": 33000000,
            "configuration": {
                "autonegotiation": "on",
                "broadcast": "yes",
                "driver": "igb",
                "driverversion": "5.14.0-362.8.1.el9_3.x86_64",
                "firmware": "1.67, 0x80000d6b, 17.5.12",
                "latency": "0",
                "link": "no",
                "multicast": "yes",
                "port": "twisted pair"
            },
            "capabilities": {
                "bus_master": "bus mastering",
                "cap_list": "PCI capabilities listing",
                "rom": "extension ROM",
                "ethernet": true,
                "physical": "Physical interface",
                "tp": "twisted pair",
                "10bt": "10Mbit/s",
                "10bt-fd": "10Mbit/s (full duplex)",
                "100bt": "100Mbit/s",
                "100bt-fd": "100Mbit/s (full duplex)",
                "1000bt-fd": "1Gbit/s (full duplex)",
                "autonegotiation": "Auto-negotiation"
            }
        }
    ]
]
   * CPUs node 1 1 3 5 7 9 11 13 15 17 19 21 23 25 27 29 31
   * size node 1 33021952
   * free node 1 19611648
   * devs node 1 []
#### Memory status:

svmem(total=66875097088, available=60712132608, percent=9.2, used=5454286848, free=43307429888, active=13014777856, inactive=8479129600, buffers=1982464, cached=18111397888, shared=20553728, slab=1126014976)
no RAID devices were found.
```

## auto_discovery_oks.py
Same as auto_discovery, but sorts the hardware information into python classes similar to objects one could define in the oks configuration. Meant as a devlepment tool only. Example output from np04-srv-017:

```[bash]
(dbt) [sbhuller@np04-srv-017 scripts]$ auto_discovery_oks.py 
Error running 'nvme list-subsys': b'Failed to scan topology: No such file or directory\n'
Error running 'nvme list': b'Failed to scan topology: No such file or directory\n'
Error running 'ls /dev/md/': b"ls: cannot access '/dev/md/': No such file or directory\n"
Error running 'lshw -C Network -C Storage -json': b'WARNING: you should run this program as super-user.\nWARNING: output may be incomplete or inaccurate, you should run this program as super-user.\n'
host.name='np04-srv-017'
node.numa=0
node.cpus=[0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30]
node.name='name'
node.size=32284672
node.devices=
[
    <class '__main__.NetworkDevice'>:{'mac': '24:6e:96:45:25:8c', 'ip': '10.73.136.40', 'pcie': '0000:01:00.0', 'numa': 0, 'product': 'Ethernet Controller X710 for 10GbE SFP+', 'name': 'eno1'},
    <class '__main__.NetworkDevice'>:{'mac': '24:6e:96:45:25:8e', 'ip': 'not found', 'pcie': '0000:01:00.1', 'numa': 0, 'product': 'Ethernet Controller X710 for 10GbE SFP+', 'name': 'eno2'},
    <class '__main__.NetworkDevice'>:{'mac': '24:6e:96:45:25:ac', 'ip': 'not found', 'pcie': '0000:06:00.0', 'numa': 0, 'product': 'I350 Gigabit Network Connection', 'name': 'eno3'},
    <class '__main__.NetworkDevice'>:{'mac': '24:6e:96:45:25:ad', 'ip': 'not found', 'pcie': '0000:06:00.1', 'numa': 0, 'product': 'I350 Gigabit Network Connection', 'name': 'eno4'}
]
node.numa=1
node.cpus=[1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31]
node.name='name'
node.size=33021952
node.devices=
[]
```

## llc_domain_parser.py

Parse the output of lstopo and create a heirarchical map of processing units per core, last level cache domain, numa and socket. Example with np04-srv-017:

```[bash]
(dbt) [sbhuller@np04-srv-017 scripts]$ llc_domain_parser.py np04-srv-017
Namespace(server='np04-srv-017')
Error running 'ssh sbhuller@np04-srv-017 lstopo -p --of xml': b'Warning: No xauth data; using fake authentication data for X11 forwarding.\r\n'
{0: {0: {8: {0: [0, 16], 1: [2, 18], 2: [4, 20], 3: [6, 22], 4: [8, 24], 5: [10, 26], 6: [12, 28], 7: [14, 30]}}}, 1: {1: {15: {0: [1, 17], 1: [3, 19], 2: [5, 21], 3: [7, 23], 4: [9, 25], 5: [11, 27], 6: [13, 29], 7: [15, 31]}}}}
```

## get_pcie_map.py

Get a map of the physical slots and the respective pcie devices. Example with np02-srv-004:

```[bash]
(dbt) [sbhuller@np04-srv-017 scripts]$ get_pcie_map.py -s np02-srv-004
Namespace(host='np02-srv-004')
Error running 'ssh sbhuller@np02-srv-004 sudo dmidecode -t slot | grep -e Designation -e "Bus Address" -e "Current Usage"': b'Warning: No xauth data; using fake authentication data for X11 forwarding.\r\n'
Error running 'ssh sbhuller@np02-srv-004 lspci -D': b'Warning: No xauth data; using fake authentication data for X11 forwarding.\r\n'
Error running 'ssh sbhuller@np02-srv-004 lspci -vv -m | grep -Ew "Device:|NUMANode:"': b'Warning: No xauth data; using fake authentication data for X11 forwarding.\r\n'
{
    'SLOT1 PCI-E 4.0 X16|In Use': {'deivce:': '0000:e1:00.0 Non-Volatile memory controller: Seagate Technology PLC FireCuda 530 SSD (rev 01)', 'NUMA:': '2'},
    'SLOT2 PCI-E 4.0 X16|In Use': {'deivce:': '0000:c1:00.0 Ethernet controller: Intel Corporation Ethernet Controller E810-C for QSFP (rev 02)', 'NUMA:': '2'},
    'SLOT3 PCI-E 4.0 X16|In Use': {'deivce:': '0000:81:00.0 Non-Volatile memory controller: Phison Electronics Corporation E16 PCIe4 NVMe Controller (rev 01)', 'NUMA:': '3'},
    'SLOT4 PCI-E 4.0 X16|In Use': {'deivce:': '0000:a1:00.0 Ethernet controller: Intel Corporation Ethernet Controller E810-C for QSFP (rev 02)', 'NUMA:': '3'},
    'SLOT5 PCI-E 4.0 X16|In Use': {'deivce:': '0000:c3:00.0 Non-Volatile memory controller: Samsung Electronics Co Ltd NVMe SSD Controller PM9A1/PM9A3/980PRO', 'NUMA:': '2'},
    'SLOT7 PCI-E 4.0 X16|In Use': {'deivce:': '0000:61:00.0 Ethernet controller: Intel Corporation Ethernet Controller E810-C for SFP (rev 02)', 'NUMA:': '0'},
    'SLOT8 PCI-E 4.0 X16|In Use': {'deivce:': '0000:41:00.0 Ethernet controller: Intel Corporation Ethernet Controller E810-C for QSFP (rev 02)', 'NUMA:': '0'},
    'SLOT9 PCI-E 4.0 X16|In Use': {'deivce:': '0000:01:00.0 Non-Volatile memory controller: Samsung Electronics Co Ltd NVMe SSD Controller PM9A1/PM9A3/980PRO', 'NUMA:': '1'},
    'SLOT10 PCI-E 4.0 X16|In Use': {'deivce:': '0000:25:00.0 Ethernet controller: Intel Corporation Ethernet Controller E810-C for QSFP (rev 02)', 'NUMA:': '1'}
}
```

## create_pinning_minimal.py

Create a cpu pinning file based on a template pinning file for a given readout host. Currently works for readout servers only as certain assignments are made based on the thread names. Example using np02-srv-004:

```[bash]
(dbt) [sbhuller@np04-srv-017 new_conf]$ create_pinning_minimal.py -r np02-srv-004 -t new_tempate.json
Namespace(template='new_tempate.json', readout_server='np02-srv-004', tpproc=None, ccp=None, recording=None, rawproc=None, rte=None)
──────────────────────────────────────────────────────────────────────────────────────────────────────── CPU map ─────────────────────────────────────────────────────────────────────────────────────────────────────────
[
    {
        'Socket:0': [
            {
                'NUMA:0': [
                    {
                        'Cache:8': [
                            {'Core:0': ['PU:0', 'PU:128']},
                            {'Core:1': ['PU:1', 'PU:129']},
                            {'Core:2': ['PU:2', 'PU:130']},
                            {'Core:3': ['PU:3', 'PU:131']},
                            {'Core:4': ['PU:4', 'PU:132']},
                            {'Core:5': ['PU:5', 'PU:133']},
                            {'Core:6': ['PU:6', 'PU:134']},
                            {'Core:7': ['PU:7', 'PU:135']}
                        ]
                    },
                    {
                        'Cache:49': [
                            {'Core:8': ['PU:8', 'PU:136']},
                            {'Core:9': ['PU:9', 'PU:137']},
                            {'Core:10': ['PU:10', 'PU:138']},
                            {'Core:11': ['PU:11', 'PU:139']},
                            {'Core:12': ['PU:12', 'PU:140']},
                            {'Core:13': ['PU:13', 'PU:141']},
                            {'Core:14': ['PU:14', 'PU:142']},
                            {'Core:15': ['PU:15', 'PU:143']}
                        ]
                    },
                    {
                        'Cache:90': [
                            {'Core:16': ['PU:16', 'PU:144']},
                            {'Core:17': ['PU:17', 'PU:145']},
                            {'Core:18': ['PU:18', 'PU:146']},
                            {'Core:19': ['PU:19', 'PU:147']},
                            {'Core:20': ['PU:20', 'PU:148']},
                            {'Core:21': ['PU:21', 'PU:149']},
                            {'Core:22': ['PU:22', 'PU:150']},
                            {'Core:23': ['PU:23', 'PU:151']}
                        ]
                    },
                    {
                        'Cache:131': [
                            {'Core:24': ['PU:24', 'PU:152']},
                            {'Core:25': ['PU:25', 'PU:153']},
                            {'Core:26': ['PU:26', 'PU:154']},
                            {'Core:27': ['PU:27', 'PU:155']},
                            {'Core:28': ['PU:28', 'PU:156']},
                            {'Core:29': ['PU:29', 'PU:157']},
                            {'Core:30': ['PU:30', 'PU:158']},
                            {'Core:31': ['PU:31', 'PU:159']}
                        ]
                    }
                ]
            },
            {
                'NUMA:1': [
                    {
                        'Cache:172': [
                            {'Core:32': ['PU:32', 'PU:160']},
                            {'Core:33': ['PU:33', 'PU:161']},
                            {'Core:34': ['PU:34', 'PU:162']},
                            {'Core:35': ['PU:35', 'PU:163']},
                            {'Core:36': ['PU:36', 'PU:164']},
                            {'Core:37': ['PU:37', 'PU:165']},
                            {'Core:38': ['PU:38', 'PU:166']},
                            {'Core:39': ['PU:39', 'PU:167']}
                        ]
                    },
                    {
                        'Cache:213': [
                            {'Core:40': ['PU:40', 'PU:168']},
                            {'Core:41': ['PU:41', 'PU:169']},
                            {'Core:42': ['PU:42', 'PU:170']},
                            {'Core:43': ['PU:43', 'PU:171']},
                            {'Core:44': ['PU:44', 'PU:172']},
                            {'Core:45': ['PU:45', 'PU:173']},
                            {'Core:46': ['PU:46', 'PU:174']},
                            {'Core:47': ['PU:47', 'PU:175']}
                        ]
                    },
                    {
                        'Cache:254': [
                            {'Core:48': ['PU:48', 'PU:176']},
                            {'Core:49': ['PU:49', 'PU:177']},
                            {'Core:50': ['PU:50', 'PU:178']},
                            {'Core:51': ['PU:51', 'PU:179']},
                            {'Core:52': ['PU:52', 'PU:180']},
                            {'Core:53': ['PU:53', 'PU:181']},
                            {'Core:54': ['PU:54', 'PU:182']},
                            {'Core:55': ['PU:55', 'PU:183']}
                        ]
                    },
                    {
                        'Cache:295': [
                            {'Core:56': ['PU:56', 'PU:184']},
                            {'Core:57': ['PU:57', 'PU:185']},
                            {'Core:58': ['PU:58', 'PU:186']},
                            {'Core:59': ['PU:59', 'PU:187']},
                            {'Core:60': ['PU:60', 'PU:188']},
                            {'Core:61': ['PU:61', 'PU:189']},
                            {'Core:62': ['PU:62', 'PU:190']},
                            {'Core:63': ['PU:63', 'PU:191']}
                        ]
                    }
                ]
            }
        ]
    },
    {
        'Socket:1': [
            {
                'NUMA:2': [
                    {
                        'Cache:337': [
                            {'Core:64': ['PU:64', 'PU:192']},
                            {'Core:65': ['PU:65', 'PU:193']},
                            {'Core:66': ['PU:66', 'PU:194']},
                            {'Core:67': ['PU:67', 'PU:195']},
                            {'Core:68': ['PU:68', 'PU:196']},
                            {'Core:69': ['PU:69', 'PU:197']},
                            {'Core:70': ['PU:70', 'PU:198']},
                            {'Core:71': ['PU:71', 'PU:199']}
                        ]
                    },
                    {
                        'Cache:378': [
                            {'Core:72': ['PU:72', 'PU:200']},
                            {'Core:73': ['PU:73', 'PU:201']},
                            {'Core:74': ['PU:74', 'PU:202']},
                            {'Core:75': ['PU:75', 'PU:203']},
                            {'Core:76': ['PU:76', 'PU:204']},
                            {'Core:77': ['PU:77', 'PU:205']},
                            {'Core:78': ['PU:78', 'PU:206']},
                            {'Core:79': ['PU:79', 'PU:207']}
                        ]
                    },
                    {
                        'Cache:419': [
                            {'Core:80': ['PU:80', 'PU:208']},
                            {'Core:81': ['PU:81', 'PU:209']},
                            {'Core:82': ['PU:82', 'PU:210']},
                            {'Core:83': ['PU:83', 'PU:211']},
                            {'Core:84': ['PU:84', 'PU:212']},
                            {'Core:85': ['PU:85', 'PU:213']},
                            {'Core:86': ['PU:86', 'PU:214']},
                            {'Core:87': ['PU:87', 'PU:215']}
                        ]
                    },
                    {
                        'Cache:460': [
                            {'Core:88': ['PU:88', 'PU:216']},
                            {'Core:89': ['PU:89', 'PU:217']},
                            {'Core:90': ['PU:90', 'PU:218']},
                            {'Core:91': ['PU:91', 'PU:219']},
                            {'Core:92': ['PU:92', 'PU:220']},
                            {'Core:93': ['PU:93', 'PU:221']},
                            {'Core:94': ['PU:94', 'PU:222']},
                            {'Core:95': ['PU:95', 'PU:223']}
                        ]
                    }
                ]
            },
            {
                'NUMA:3': [
                    {
                        'Cache:501': [
                            {'Core:96': ['PU:96', 'PU:224']},
                            {'Core:97': ['PU:97', 'PU:225']},
                            {'Core:98': ['PU:98', 'PU:226']},
                            {'Core:99': ['PU:99', 'PU:227']},
                            {'Core:100': ['PU:100', 'PU:228']},
                            {'Core:101': ['PU:101', 'PU:229']},
                            {'Core:102': ['PU:102', 'PU:230']},
                            {'Core:103': ['PU:103', 'PU:231']}
                        ]
                    },
                    {
                        'Cache:542': [
                            {'Core:104': ['PU:104', 'PU:232']},
                            {'Core:105': ['PU:105', 'PU:233']},
                            {'Core:106': ['PU:106', 'PU:234']},
                            {'Core:107': ['PU:107', 'PU:235']},
                            {'Core:108': ['PU:108', 'PU:236']},
                            {'Core:109': ['PU:109', 'PU:237']},
                            {'Core:110': ['PU:110', 'PU:238']},
                            {'Core:111': ['PU:111', 'PU:239']}
                        ]
                    },
                    {
                        'Cache:583': [
                            {'Core:112': ['PU:112', 'PU:240']},
                            {'Core:113': ['PU:113', 'PU:241']},
                            {'Core:114': ['PU:114', 'PU:242']},
                            {'Core:115': ['PU:115', 'PU:243']},
                            {'Core:116': ['PU:116', 'PU:244']},
                            {'Core:117': ['PU:117', 'PU:245']},
                            {'Core:118': ['PU:118', 'PU:246']},
                            {'Core:119': ['PU:119', 'PU:247']}
                        ]
                    },
                    {
                        'Cache:624': [
                            {'Core:120': ['PU:120', 'PU:248']},
                            {'Core:121': ['PU:121', 'PU:249']},
                            {'Core:122': ['PU:122', 'PU:250']},
                            {'Core:123': ['PU:123', 'PU:251']},
                            {'Core:124': ['PU:124', 'PU:252']},
                            {'Core:125': ['PU:125', 'PU:253']},
                            {'Core:126': ['PU:126', 'PU:254']},
                            {'Core:127': ['PU:127', 'PU:255']}
                        ]
                    }
                ]
            }
        ]
    }
]
cpu_resource_allocation=ChainMap({'rawproc': 26, 'rte': 1, 'recording': 16, 'tpproc': 4, 'ccp': 12})
Warning: CPU has multiple cache boundaries, but only one cache region was requested. Consider using the default resource allocation (remove "resource_allocation" from the template), or define multiple cache regions
{
    'runp02srv004eth0': {
        'numa': 0,
        'threads': ['rte-worker-2', 'rte-worker-3', 'rte-worker-4', 'rte-worker-5', 'rawproc-0-1..', 'tpproc-0-1..', 'cleanup-1..', 'consumer-1..', 'recording-1..', 'cleanup-1.', 'consumer-1.', 'periodic-1.']
    },
    'runp02srv004eth1': {
        'numa': 1,
        'threads': ['rte-worker-34', 'rte-worker-35', 'rte-worker-36', 'rte-worker-37', 'rawproc-0-2..', 'tpproc-0-2..', 'cleanup-2..', 'consumer-2..', 'recording-2..', 'cleanup-2.', 'consumer-2.', 'periodic-2.']
    },
    'runp02srv004eth2': {
        'numa': 2,
        'threads': ['rte-worker-66', 'rte-worker-67', 'rte-worker-68', 'rte-worker-69', 'rawproc-0-3..', 'tpproc-0-3..', 'cleanup-3..', 'consumer-3..', 'recording-3..', 'cleanup-3.', 'consumer-3.', 'periodic-3.']
    },
    'runp02srv004eth3': {
        'numa': 3,
        'threads': ['rte-worker-98', 'rte-worker-99', 'rte-worker-100', 'rte-worker-101', 'rawproc-0-4..', 'tpproc-0-4..', 'cleanup-4..', 'consumer-4..', 'recording-4..', 'cleanup-4.', 'consumer-4.', 'periodic-4.']
    }
}
total_requested_cores=62
requested_caches=4
total_requested_cores=62
requested_caches=4
total_requested_cores=62
requested_caches=4
total_requested_cores=62
requested_caches=4
────────────────────────────────────────────────────────────────────────────────────────────────── CPU pinning running ───────────────────────────────────────────────────────────────────────────────────────────────────
{
    'daq_application': {
        'runp02srv004eth0': {
            'threads': {
                'rte-worker-2': '2',
                'rte-worker-3': '3',
                'rte-worker-4': '4',
                'rte-worker-5': '5',
                'rawproc-0-1..': '1,129,130,131,132,133,6,134,7,135,8,136,9,137,10,138,11,139,12,140,13,141,14,142,15,143',
                'tpproc-0-1..': '16,144,17,145',
                'cleanup-1..': '18,146,19,147,20,148,21,149,22,150,23,151',
                'consumer-1..': '18,146,19,147,20,148,21,149,22,150,23,151',
                'recording-1..': '24,152,25,153,26,154,27,155,28,156,29,157,30,158,31,159',
                'cleanup-1.': '18,146,19,147,20,148,21,149,22,150,23,151',
                'consumer-1.': '18,146,19,147,20,148,21,149,22,150,23,151',
                'periodic-1.': '18,146,19,147,20,148,21,149,22,150,23,151'
            },
            'parent': '18,146,19,147,20,148,21,149,22,150,23,151'
        },
        'runp02srv004eth1': {
            'threads': {
                'rte-worker-34': '34',
                'rte-worker-35': '35',
                'rte-worker-36': '36',
                'rte-worker-37': '37',
                'rawproc-0-2..': '33,161,162,163,164,165,38,166,39,167,40,168,41,169,42,170,43,171,44,172,45,173,46,174,47,175',
                'tpproc-0-2..': '48,176,49,177',
                'cleanup-2..': '50,178,51,179,52,180,53,181,54,182,55,183',
                'consumer-2..': '50,178,51,179,52,180,53,181,54,182,55,183',
                'recording-2..': '56,184,57,185,58,186,59,187,60,188,61,189,62,190,63,191',
                'cleanup-2.': '50,178,51,179,52,180,53,181,54,182,55,183',
                'consumer-2.': '50,178,51,179,52,180,53,181,54,182,55,183',
                'periodic-2.': '50,178,51,179,52,180,53,181,54,182,55,183'
            },
            'parent': '50,178,51,179,52,180,53,181,54,182,55,183'
        },
        'runp02srv004eth2': {
            'threads': {
                'rte-worker-66': '66',
                'rte-worker-67': '67',
                'rte-worker-68': '68',
                'rte-worker-69': '69',
                'rawproc-0-3..': '65,193,194,195,196,197,70,198,71,199,72,200,73,201,74,202,75,203,76,204,77,205,78,206,79,207',
                'tpproc-0-3..': '80,208,81,209',
                'cleanup-3..': '82,210,83,211,84,212,85,213,86,214,87,215',
                'consumer-3..': '82,210,83,211,84,212,85,213,86,214,87,215',
                'recording-3..': '88,216,89,217,90,218,91,219,92,220,93,221,94,222,95,223',
                'cleanup-3.': '82,210,83,211,84,212,85,213,86,214,87,215',
                'consumer-3.': '82,210,83,211,84,212,85,213,86,214,87,215',
                'periodic-3.': '82,210,83,211,84,212,85,213,86,214,87,215'
            },
            'parent': '82,210,83,211,84,212,85,213,86,214,87,215'
        },
        'runp02srv004eth3': {
            'threads': {
                'rte-worker-98': '98',
                'rte-worker-99': '99',
                'rte-worker-100': '100',
                'rte-worker-101': '101',
                'rawproc-0-4..': '97,225,226,227,228,229,102,230,103,231,104,232,105,233,106,234,107,235,108,236,109,237,110,238,111,239',
                'tpproc-0-4..': '112,240,113,241',
                'cleanup-4..': '114,242,115,243,116,244,117,245,118,246,119,247',
                'consumer-4..': '114,242,115,243,116,244,117,245,118,246,119,247',
                'recording-4..': '120,248,121,249,122,250,123,251,124,252,125,253,126,254,127,255',
                'cleanup-4.': '114,242,115,243,116,244,117,245,118,246,119,247',
                'consumer-4.': '114,242,115,243,116,244,117,245,118,246,119,247',
                'periodic-4.': '114,242,115,243,116,244,117,245,118,246,119,247'
            },
            'parent': '114,242,115,243,116,244,117,245,118,246,119,247'
        }
    }
}
──────────────────────────────────────────────────────────────────────────────────────────────────── CPU pinning all ─────────────────────────────────────────────────────────────────────────────────────────────────────
{
    'daq_application': {
        'runp02srv004eth0': {
            'threads': {
                'rte-worker-2': '2',
                'rte-worker-3': '3',
                'rte-worker-4': '4',
                'rte-worker-5': '5',
                'rawproc-0-1..': '1,129,130,131,132,133,6,134,7,135,8,136,9,137,10,138,11,139,12,140,13,141,14,142,15,143',
                'tpproc-0-1..': '16,144,17,145',
                'cleanup-1..': '18,146,19,147,20,148,21,149,22,150,23,151',
                'consumer-1..': '18,146,19,147,20,148,21,149,22,150,23,151',
                'recording-1..': '24,152,25,153,26,154,27,155,28,156,29,157,30,158,31,159',
                'cleanup-1.': '18,146,19,147,20,148,21,149,22,150,23,151',
                'consumer-1.': '18,146,19,147,20,148,21,149,22,150,23,151',
                'periodic-1.': '18,146,19,147,20,148,21,149,22,150,23,151'
            },
            'parent': 
'0,128,1,129,2,130,3,131,4,132,5,133,6,134,7,135,8,136,9,137,10,138,11,139,12,140,13,141,14,142,15,143,16,144,17,145,18,146,19,147,20,148,21,149,22,150,23,151,24,152,25,153,26,154,27,155,28,156,29,157,30,158,31,159'
        },
        'runp02srv004eth1': {
            'threads': {
                'rte-worker-34': '34',
                'rte-worker-35': '35',
                'rte-worker-36': '36',
                'rte-worker-37': '37',
                'rawproc-0-2..': '33,161,162,163,164,165,38,166,39,167,40,168,41,169,42,170,43,171,44,172,45,173,46,174,47,175',
                'tpproc-0-2..': '48,176,49,177',
                'cleanup-2..': '50,178,51,179,52,180,53,181,54,182,55,183',
                'consumer-2..': '50,178,51,179,52,180,53,181,54,182,55,183',
                'recording-2..': '56,184,57,185,58,186,59,187,60,188,61,189,62,190,63,191',
                'cleanup-2.': '50,178,51,179,52,180,53,181,54,182,55,183',
                'consumer-2.': '50,178,51,179,52,180,53,181,54,182,55,183',
                'periodic-2.': '50,178,51,179,52,180,53,181,54,182,55,183'
            },
            'parent': 
'32,160,33,161,34,162,35,163,36,164,37,165,38,166,39,167,40,168,41,169,42,170,43,171,44,172,45,173,46,174,47,175,48,176,49,177,50,178,51,179,52,180,53,181,54,182,55,183,56,184,57,185,58,186,59,187,60,188,61,189,62,190,
63,191'
        },
        'runp02srv004eth2': {
            'threads': {
                'rte-worker-66': '66',
                'rte-worker-67': '67',
                'rte-worker-68': '68',
                'rte-worker-69': '69',
                'rawproc-0-3..': '65,193,194,195,196,197,70,198,71,199,72,200,73,201,74,202,75,203,76,204,77,205,78,206,79,207',
                'tpproc-0-3..': '80,208,81,209',
                'cleanup-3..': '82,210,83,211,84,212,85,213,86,214,87,215',
                'consumer-3..': '82,210,83,211,84,212,85,213,86,214,87,215',
                'recording-3..': '88,216,89,217,90,218,91,219,92,220,93,221,94,222,95,223',
                'cleanup-3.': '82,210,83,211,84,212,85,213,86,214,87,215',
                'consumer-3.': '82,210,83,211,84,212,85,213,86,214,87,215',
                'periodic-3.': '82,210,83,211,84,212,85,213,86,214,87,215'
            },
            'parent': 
'64,192,65,193,66,194,67,195,68,196,69,197,70,198,71,199,72,200,73,201,74,202,75,203,76,204,77,205,78,206,79,207,80,208,81,209,82,210,83,211,84,212,85,213,86,214,87,215,88,216,89,217,90,218,91,219,92,220,93,221,94,222,
95,223'
        },
        'runp02srv004eth3': {
            'threads': {
                'rte-worker-98': '98',
                'rte-worker-99': '99',
                'rte-worker-100': '100',
                'rte-worker-101': '101',
                'rawproc-0-4..': '97,225,226,227,228,229,102,230,103,231,104,232,105,233,106,234,107,235,108,236,109,237,110,238,111,239',
                'tpproc-0-4..': '112,240,113,241',
                'cleanup-4..': '114,242,115,243,116,244,117,245,118,246,119,247',
                'consumer-4..': '114,242,115,243,116,244,117,245,118,246,119,247',
                'recording-4..': '120,248,121,249,122,250,123,251,124,252,125,253,126,254,127,255',
                'cleanup-4.': '114,242,115,243,116,244,117,245,118,246,119,247',
                'consumer-4.': '114,242,115,243,116,244,117,245,118,246,119,247',
                'periodic-4.': '114,242,115,243,116,244,117,245,118,246,119,247'
            },
            'parent': 
'96,224,97,225,98,226,99,227,100,228,101,229,102,230,103,231,104,232,105,233,106,234,107,235,108,236,109,237,110,238,111,239,112,240,113,241,114,242,115,243,116,244,117,245,118,246,119,247,120,248,121,249,122,250,123,2
51,124,252,125,253,126,254,127,255'
        }
    }
}
─────────────────────────────────────────────────────────────────────────────────────────────── remaining CPUs in CPU map ────────────────────────────────────────────────────────────────────────────────────────────────
[]
pinning has been written to cpupin-all-running.json
pinning has been written to cpupin-all.json
```
and the template looks like:
```[json]
{
    "daq_application" : {
        "runp02srv004eth0" : {
            "numa" : 0,
            "threads" : [
                "rte-worker-2",
                "rte-worker-3",
                "rte-worker-4",
                "rte-worker-5",
        
                "rawproc-0-1..",
                "tpproc-0-1..",
        
                "cleanup-1..",
                "consumer-1..",
                "recording-1..",
        
                "cleanup-1.",
                "consumer-1.",
                "periodic-1."        
            ]
        },
        "runp02srv004eth1": {
            "numa" : 1,
            "threads": [
                "rte-worker-34",
                "rte-worker-35",
                "rte-worker-36",
                "rte-worker-37",
    
                "rawproc-0-2..",
                "tpproc-0-2..",
    
                "cleanup-2..",
                "consumer-2..",
                "recording-2..",
    
                "cleanup-2.",
                "consumer-2.",
                "periodic-2."  
            ]
        },
        "runp02srv004eth2": {
            "numa" : 2,
            "threads": [
                "rte-worker-66",
                "rte-worker-67",
                "rte-worker-68",
                "rte-worker-69",
    
                "rawproc-0-3..",
                "tpproc-0-3..",
    
                "cleanup-3..",
                "consumer-3..",
                "recording-3..",
    
                "cleanup-3.",
                "consumer-3.",
                "periodic-3."
            ]
        },
        "runp02srv004eth3": {
            "numa" : 3,
            "threads": [
                "rte-worker-98",
                "rte-worker-99",
                "rte-worker-100",
                "rte-worker-101",
    
                "rawproc-0-4..",
                "tpproc-0-4..",
    
                "cleanup-4..",
                "consumer-4..",
                "recording-4..",
    
                "cleanup-4.",
                "consumer-4.",
                "periodic-4."
            ]
        }
    },
    "resource_allocation" : [
        {
            "rawproc" : 26,
            "rte" : 1,
            "recording" : 16,
            "tpproc" : 4,
            "ccp" : 12
        }
    ]
}
```

## readout_affinity_oks.py

Create cpu pinning files used during configuring and running, but uses the oks session file to infer the thread names (in place of a less bloated template file). Note one must have the database path correctly set in order to work correctly. e.g. if you use `ehn1-daqconfigs` you need to run `source setup_db_path.sh`.

Example template file
```[json]
{
    "np02-srv-004" : [
        {
            "rawproc" : 26,
            "rte" : 1
        },
        {
            "recording" : 16
        },
        {
            "tpproc" : 4,
            "ccp" : 12
        }
    ]
}
```

Example output
```[bash]
(dbt) [sbhuller@np04-srv-017 pin]$ readout_affinity_oks.py -t new_template.json -o ehn1-daqconfigs/sessions/np04-session.data.xml 
Namespace(template='new_template.json', oks_session='ehn1-daqconfigs/sessions/np04-session.data.xml')
ehn1-daqconfigs/sessions/np04-session.data.xml
ResourceSetAND(id='apa1-senders',
  contains = ['<hds-np04-wib-101-10g-0@HermesDataSender>', '<hds-np04-wib-101-10g-1@HermesDataSender>', '<hds-np04-wib-102-10g-0@HermesDataSender>', '<hds-np04-wib-102-10g-1@HermesDataSender>', '<hds-np04-wib-103-10g-0@HermesDataSender>', '<hds-np04-wib-103-10g-1@HermesDataSender>', 
'<hds-np04-wib-104-10g-0@HermesDataSender>', '<hds-np04-wib-104-10g-1@HermesDataSender>', '<hds-np04-wib-105-10g-0@HermesDataSender>', '<hds-np04-wib-105-10g-1@HermesDataSender>']])
ResourceSetAND(id='apa2-senders',
  contains = ['<hds-np04-wib-201-10g-0@HermesDataSender>', '<hds-np04-wib-201-10g-1@HermesDataSender>', '<hds-np04-wib-202-10g-0@HermesDataSender>', '<hds-np04-wib-202-10g-1@HermesDataSender>', '<hds-np04-wib-203-10g-0@HermesDataSender>', '<hds-np04-wib-203-10g-1@HermesDataSender>', 
'<hds-np04-wib-204-10g-0@HermesDataSender>', '<hds-np04-wib-204-10g-1@HermesDataSender>', '<hds-np04-wib-205-10g-0@HermesDataSender>', '<hds-np04-wib-205-10g-1@HermesDataSender>']])
ResourceSetAND(id='apa3-senders',
  contains = ['<hds-np04-wib-301-10g-0@HermesDataSender>', '<hds-np04-wib-301-10g-1@HermesDataSender>', '<hds-np04-wib-302-10g-0@HermesDataSender>', '<hds-np04-wib-302-10g-1@HermesDataSender>', '<hds-np04-wib-303-10g-0@HermesDataSender>', '<hds-np04-wib-303-10g-1@HermesDataSender>', 
'<hds-np04-wib-304-10g-0@HermesDataSender>', '<hds-np04-wib-304-10g-1@HermesDataSender>', '<hds-np04-wib-305-10g-0@HermesDataSender>', '<hds-np04-wib-305-10g-1@HermesDataSender>']])
ResourceSetAND(id='apa4-senders',
  contains = ['<hds-np04-wib-401-10g-0@HermesDataSender>', '<hds-np04-wib-401-10g-1@HermesDataSender>', '<hds-np04-wib-402-10g-0@HermesDataSender>', '<hds-np04-wib-402-10g-1@HermesDataSender>', '<hds-np04-wib-403-10g-0@HermesDataSender>', '<hds-np04-wib-403-10g-1@HermesDataSender>', 
'<hds-np04-wib-404-10g-0@HermesDataSender>', '<hds-np04-wib-404-10g-1@HermesDataSender>', '<hds-np04-wib-405-10g-0@HermesDataSender>', '<hds-np04-wib-405-10g-1@HermesDataSender>']])
{
    'runp02srv004eth0': {
        'host': 'np02-srv-004',
        'numa': 0,
        'lcores': [2, 3, 4, 5],
        'tp_source_ids': [10, 11, 12],
        'detstream_source_ids': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139],
        'prefix': {'recording': 'recording-', 'cleanup': 'cleanup-', 'consumer': 'consumer-', 'periodic': 'periodic-', 'link': 'rawproc-', 'tp': 'tpproc-'}
    },
    'runp02srv004eth1': {
        'host': 'np02-srv-004',
        'numa': 1,
        'lcores': [34, 35, 36, 37],
        'tp_source_ids': [20, 21, 22],
        'detstream_source_ids': [200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239],
        'prefix': {'recording': 'recording-', 'cleanup': 'cleanup-', 'consumer': 'consumer-', 'periodic': 'periodic-', 'link': 'rawproc-', 'tp': 'tpproc-'}
    },
    'runp02srv004eth2': {
        'host': 'np02-srv-004',
        'numa': 2,
        'lcores': [66, 67, 68, 69],
        'tp_source_ids': [30, 31, 32],
        'detstream_source_ids': [300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 319, 320, 321, 322, 323, 324, 325, 326, 327, 328, 329, 330, 331, 332, 333, 334, 335, 336, 337, 338, 339],
        'prefix': {'recording': 'recording-', 'cleanup': 'cleanup-', 'consumer': 'consumer-', 'periodic': 'periodic-', 'link': 'rawproc-', 'tp': 'tpproc-'}
    },
    'runp02srv004eth3': {
        'host': 'np02-srv-004',
        'numa': 3,
        'lcores': [98, 99, 100, 101],
        'tp_source_ids': [40, 41, 42],
        'detstream_source_ids': [400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 416, 417, 418, 419, 420, 421, 422, 423, 424, 425, 426, 427, 428, 429, 430, 431, 432, 433, 434, 435, 436, 437, 438, 439],
        'prefix': {'recording': 'recording-', 'cleanup': 'cleanup-', 'consumer': 'consumer-', 'periodic': 'periodic-', 'link': 'rawproc-', 'tp': 'tpproc-'}
    }
}
{
    'np02-srv-004': {
        'runp02srv004eth0': {'numa': 0, 'threads': ['rawproc-0-1..', 'cleanup-1..', 'consumer-1..', 'periodic-1..', 'recording-1..', 'tpproc-0-1.', 'cleanup-1.', 'consumer-1.', 'periodic-1.', 'rte-worker-2', 'rte-worker-3', 'rte-worker-4', 'rte-worker-5']},
        'runp02srv004eth1': {'numa': 1, 'threads': ['rawproc-0-2..', 'cleanup-2..', 'consumer-2..', 'periodic-2..', 'recording-2..', 'tpproc-0-2.', 'cleanup-2.', 'consumer-2.', 'periodic-2.', 'rte-worker-34', 'rte-worker-35', 'rte-worker-36', 'rte-worker-37']},
        'runp02srv004eth2': {'numa': 2, 'threads': ['rawproc-0-3..', 'cleanup-3..', 'consumer-3..', 'periodic-3..', 'recording-3..', 'tpproc-0-3.', 'cleanup-3.', 'consumer-3.', 'periodic-3.', 'rte-worker-66', 'rte-worker-67', 'rte-worker-68', 'rte-worker-69']},
        'runp02srv004eth3': {'numa': 3, 'threads': ['rawproc-0-4..', 'cleanup-4..', 'consumer-4..', 'periodic-4..', 'recording-4..', 'tpproc-0-4.', 'cleanup-4.', 'consumer-4.', 'periodic-4.', 'rte-worker-98', 'rte-worker-99', 'rte-worker-100', 'rte-worker-101']}
    }
}
{'np02-srv-004': <resources.CoreMap object at 0x7f9026ea5930>}
{'np02-srv-004': ChainMap({'rawproc': 26, 'rte': 1}, {'recording': 16}, {'tpproc': 4, 'ccp': 12})}
validating resource allocation for host np02-srv-004
done!
creating pinning for readout applications on host np02-srv-004
────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── CPU map ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
[
    {
        'Socket:0': [
            {
                'NUMA:0': [
                    {'Cache:8': [{'Core:0': ['PU:0', 'PU:128']}, {'Core:1': ['PU:1', 'PU:129']}, {'Core:2': ['PU:2', 'PU:130']}, {'Core:3': ['PU:3', 'PU:131']}, {'Core:4': ['PU:4', 'PU:132']}, {'Core:5': ['PU:5', 'PU:133']}, {'Core:6': ['PU:6', 'PU:134']}, {'Core:7': ['PU:7', 'PU:135']}]},
                    {
                        'Cache:49': [
                            {'Core:8': ['PU:8', 'PU:136']},
                            {'Core:9': ['PU:9', 'PU:137']},
                            {'Core:10': ['PU:10', 'PU:138']},
                            {'Core:11': ['PU:11', 'PU:139']},
                            {'Core:12': ['PU:12', 'PU:140']},
                            {'Core:13': ['PU:13', 'PU:141']},
                            {'Core:14': ['PU:14', 'PU:142']},
                            {'Core:15': ['PU:15', 'PU:143']}
                        ]
                    },
                    {
                        'Cache:90': [
                            {'Core:16': ['PU:16', 'PU:144']},
                            {'Core:17': ['PU:17', 'PU:145']},
                            {'Core:18': ['PU:18', 'PU:146']},
                            {'Core:19': ['PU:19', 'PU:147']},
                            {'Core:20': ['PU:20', 'PU:148']},
                            {'Core:21': ['PU:21', 'PU:149']},
                            {'Core:22': ['PU:22', 'PU:150']},
                            {'Core:23': ['PU:23', 'PU:151']}
                        ]
                    },
                    {
                        'Cache:131': [
                            {'Core:24': ['PU:24', 'PU:152']},
                            {'Core:25': ['PU:25', 'PU:153']},
                            {'Core:26': ['PU:26', 'PU:154']},
                            {'Core:27': ['PU:27', 'PU:155']},
                            {'Core:28': ['PU:28', 'PU:156']},
                            {'Core:29': ['PU:29', 'PU:157']},
                            {'Core:30': ['PU:30', 'PU:158']},
                            {'Core:31': ['PU:31', 'PU:159']}
                        ]
                    }
                ]
            },
            {
                'NUMA:1': [
                    {
                        'Cache:172': [
                            {'Core:32': ['PU:32', 'PU:160']},
                            {'Core:33': ['PU:33', 'PU:161']},
                            {'Core:34': ['PU:34', 'PU:162']},
                            {'Core:35': ['PU:35', 'PU:163']},
                            {'Core:36': ['PU:36', 'PU:164']},
                            {'Core:37': ['PU:37', 'PU:165']},
                            {'Core:38': ['PU:38', 'PU:166']},
                            {'Core:39': ['PU:39', 'PU:167']}
                        ]
                    },
                    {
                        'Cache:213': [
                            {'Core:40': ['PU:40', 'PU:168']},
                            {'Core:41': ['PU:41', 'PU:169']},
                            {'Core:42': ['PU:42', 'PU:170']},
                            {'Core:43': ['PU:43', 'PU:171']},
                            {'Core:44': ['PU:44', 'PU:172']},
                            {'Core:45': ['PU:45', 'PU:173']},
                            {'Core:46': ['PU:46', 'PU:174']},
                            {'Core:47': ['PU:47', 'PU:175']}
                        ]
                    },
                    {
                        'Cache:254': [
                            {'Core:48': ['PU:48', 'PU:176']},
                            {'Core:49': ['PU:49', 'PU:177']},
                            {'Core:50': ['PU:50', 'PU:178']},
                            {'Core:51': ['PU:51', 'PU:179']},
                            {'Core:52': ['PU:52', 'PU:180']},
                            {'Core:53': ['PU:53', 'PU:181']},
                            {'Core:54': ['PU:54', 'PU:182']},
                            {'Core:55': ['PU:55', 'PU:183']}
                        ]
                    },
                    {
                        'Cache:295': [
                            {'Core:56': ['PU:56', 'PU:184']},
                            {'Core:57': ['PU:57', 'PU:185']},
                            {'Core:58': ['PU:58', 'PU:186']},
                            {'Core:59': ['PU:59', 'PU:187']},
                            {'Core:60': ['PU:60', 'PU:188']},
                            {'Core:61': ['PU:61', 'PU:189']},
                            {'Core:62': ['PU:62', 'PU:190']},
                            {'Core:63': ['PU:63', 'PU:191']}
                        ]
                    }
                ]
            }
        ]
    },
    {
        'Socket:1': [
            {
                'NUMA:2': [
                    {
                        'Cache:337': [
                            {'Core:64': ['PU:64', 'PU:192']},
                            {'Core:65': ['PU:65', 'PU:193']},
                            {'Core:66': ['PU:66', 'PU:194']},
                            {'Core:67': ['PU:67', 'PU:195']},
                            {'Core:68': ['PU:68', 'PU:196']},
                            {'Core:69': ['PU:69', 'PU:197']},
                            {'Core:70': ['PU:70', 'PU:198']},
                            {'Core:71': ['PU:71', 'PU:199']}
                        ]
                    },
                    {
                        'Cache:378': [
                            {'Core:72': ['PU:72', 'PU:200']},
                            {'Core:73': ['PU:73', 'PU:201']},
                            {'Core:74': ['PU:74', 'PU:202']},
                            {'Core:75': ['PU:75', 'PU:203']},
                            {'Core:76': ['PU:76', 'PU:204']},
                            {'Core:77': ['PU:77', 'PU:205']},
                            {'Core:78': ['PU:78', 'PU:206']},
                            {'Core:79': ['PU:79', 'PU:207']}
                        ]
                    },
                    {
                        'Cache:419': [
                            {'Core:80': ['PU:80', 'PU:208']},
                            {'Core:81': ['PU:81', 'PU:209']},
                            {'Core:82': ['PU:82', 'PU:210']},
                            {'Core:83': ['PU:83', 'PU:211']},
                            {'Core:84': ['PU:84', 'PU:212']},
                            {'Core:85': ['PU:85', 'PU:213']},
                            {'Core:86': ['PU:86', 'PU:214']},
                            {'Core:87': ['PU:87', 'PU:215']}
                        ]
                    },
                    {
                        'Cache:460': [
                            {'Core:88': ['PU:88', 'PU:216']},
                            {'Core:89': ['PU:89', 'PU:217']},
                            {'Core:90': ['PU:90', 'PU:218']},
                            {'Core:91': ['PU:91', 'PU:219']},
                            {'Core:92': ['PU:92', 'PU:220']},
                            {'Core:93': ['PU:93', 'PU:221']},
                            {'Core:94': ['PU:94', 'PU:222']},
                            {'Core:95': ['PU:95', 'PU:223']}
                        ]
                    }
                ]
            },
            {
                'NUMA:3': [
                    {
                        'Cache:501': [
                            {'Core:96': ['PU:96', 'PU:224']},
                            {'Core:97': ['PU:97', 'PU:225']},
                            {'Core:98': ['PU:98', 'PU:226']},
                            {'Core:99': ['PU:99', 'PU:227']},
                            {'Core:100': ['PU:100', 'PU:228']},
                            {'Core:101': ['PU:101', 'PU:229']},
                            {'Core:102': ['PU:102', 'PU:230']},
                            {'Core:103': ['PU:103', 'PU:231']}
                        ]
                    },
                    {
                        'Cache:542': [
                            {'Core:104': ['PU:104', 'PU:232']},
                            {'Core:105': ['PU:105', 'PU:233']},
                            {'Core:106': ['PU:106', 'PU:234']},
                            {'Core:107': ['PU:107', 'PU:235']},
                            {'Core:108': ['PU:108', 'PU:236']},
                            {'Core:109': ['PU:109', 'PU:237']},
                            {'Core:110': ['PU:110', 'PU:238']},
                            {'Core:111': ['PU:111', 'PU:239']}
                        ]
                    },
                    {
                        'Cache:583': [
                            {'Core:112': ['PU:112', 'PU:240']},
                            {'Core:113': ['PU:113', 'PU:241']},
                            {'Core:114': ['PU:114', 'PU:242']},
                            {'Core:115': ['PU:115', 'PU:243']},
                            {'Core:116': ['PU:116', 'PU:244']},
                            {'Core:117': ['PU:117', 'PU:245']},
                            {'Core:118': ['PU:118', 'PU:246']},
                            {'Core:119': ['PU:119', 'PU:247']}
                        ]
                    },
                    {
                        'Cache:624': [
                            {'Core:120': ['PU:120', 'PU:248']},
                            {'Core:121': ['PU:121', 'PU:249']},
                            {'Core:122': ['PU:122', 'PU:250']},
                            {'Core:123': ['PU:123', 'PU:251']},
                            {'Core:124': ['PU:124', 'PU:252']},
                            {'Core:125': ['PU:125', 'PU:253']},
                            {'Core:126': ['PU:126', 'PU:254']},
                            {'Core:127': ['PU:127', 'PU:255']}
                        ]
                    }
                ]
            }
        ]
    }
]
total_requested_cores=62
requested_caches=4
total_requested_cores=62
requested_caches=4
total_requested_cores=62
requested_caches=4
total_requested_cores=62
requested_caches=4
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── CPU pinning running ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
{
    'daq_application': {
        'runp02srv004eth0': {
            'threads': {
                'rte-worker-2': '2',
                'rte-worker-3': '3',
                'rte-worker-4': '4',
                'rte-worker-5': '5',
                'rawproc-0-1..': '1,129,130,131,132,133,6,134,7,135,8,136,9,137,10,138,11,139,12,140,13,141,14,142,15,143',
                'cleanup-1..': '24,152,25,153,26,154,27,155,28,156,29,157',
                'consumer-1..': '24,152,25,153,26,154,27,155,28,156,29,157',
                'periodic-1..': '24,152,25,153,26,154,27,155,28,156,29,157',
                'recording-1..': '16,144,17,145,18,146,19,147,20,148,21,149,22,150,23,151',
                'tpproc-0-1.': '30,158,31,159',
                'cleanup-1.': '24,152,25,153,26,154,27,155,28,156,29,157',
                'consumer-1.': '24,152,25,153,26,154,27,155,28,156,29,157',
                'periodic-1.': '24,152,25,153,26,154,27,155,28,156,29,157'
            },
            'parent': '24,152,25,153,26,154,27,155,28,156,29,157'
        },
        'runp02srv004eth1': {
            'threads': {
                'rte-worker-34': '34',
                'rte-worker-35': '35',
                'rte-worker-36': '36',
                'rte-worker-37': '37',
                'rawproc-0-2..': '33,161,162,163,164,165,38,166,39,167,40,168,41,169,42,170,43,171,44,172,45,173,46,174,47,175',
                'cleanup-2..': '56,184,57,185,58,186,59,187,60,188,61,189',
                'consumer-2..': '56,184,57,185,58,186,59,187,60,188,61,189',
                'periodic-2..': '56,184,57,185,58,186,59,187,60,188,61,189',
                'recording-2..': '48,176,49,177,50,178,51,179,52,180,53,181,54,182,55,183',
                'tpproc-0-2.': '62,190,63,191',
                'cleanup-2.': '56,184,57,185,58,186,59,187,60,188,61,189',
                'consumer-2.': '56,184,57,185,58,186,59,187,60,188,61,189',
                'periodic-2.': '56,184,57,185,58,186,59,187,60,188,61,189'
            },
            'parent': '56,184,57,185,58,186,59,187,60,188,61,189'
        },
        'runp02srv004eth2': {
            'threads': {
                'rte-worker-66': '66',
                'rte-worker-67': '67',
                'rte-worker-68': '68',
                'rte-worker-69': '69',
                'rawproc-0-3..': '65,193,194,195,196,197,70,198,71,199,72,200,73,201,74,202,75,203,76,204,77,205,78,206,79,207',
                'cleanup-3..': '88,216,89,217,90,218,91,219,92,220,93,221',
                'consumer-3..': '88,216,89,217,90,218,91,219,92,220,93,221',
                'periodic-3..': '88,216,89,217,90,218,91,219,92,220,93,221',
                'recording-3..': '80,208,81,209,82,210,83,211,84,212,85,213,86,214,87,215',
                'tpproc-0-3.': '94,222,95,223',
                'cleanup-3.': '88,216,89,217,90,218,91,219,92,220,93,221',
                'consumer-3.': '88,216,89,217,90,218,91,219,92,220,93,221',
                'periodic-3.': '88,216,89,217,90,218,91,219,92,220,93,221'
            },
            'parent': '88,216,89,217,90,218,91,219,92,220,93,221'
        },
        'runp02srv004eth3': {
            'threads': {
                'rte-worker-98': '98',
                'rte-worker-99': '99',
                'rte-worker-100': '100',
                'rte-worker-101': '101',
                'rawproc-0-4..': '97,225,226,227,228,229,102,230,103,231,104,232,105,233,106,234,107,235,108,236,109,237,110,238,111,239',
                'cleanup-4..': '120,248,121,249,122,250,123,251,124,252,125,253',
                'consumer-4..': '120,248,121,249,122,250,123,251,124,252,125,253',
                'periodic-4..': '120,248,121,249,122,250,123,251,124,252,125,253',
                'recording-4..': '112,240,113,241,114,242,115,243,116,244,117,245,118,246,119,247',
                'tpproc-0-4.': '126,254,127,255',
                'cleanup-4.': '120,248,121,249,122,250,123,251,124,252,125,253',
                'consumer-4.': '120,248,121,249,122,250,123,251,124,252,125,253',
                'periodic-4.': '120,248,121,249,122,250,123,251,124,252,125,253'
            },
            'parent': '120,248,121,249,122,250,123,251,124,252,125,253'
        }
    }
}
────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── CPU pinning all ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
{
    'daq_application': {
        'runp02srv004eth0': {
            'threads': {
                'rte-worker-2': '2',
                'rte-worker-3': '3',
                'rte-worker-4': '4',
                'rte-worker-5': '5',
                'rawproc-0-1..': '1,129,130,131,132,133,6,134,7,135,8,136,9,137,10,138,11,139,12,140,13,141,14,142,15,143',
                'cleanup-1..': '24,152,25,153,26,154,27,155,28,156,29,157',
                'consumer-1..': '24,152,25,153,26,154,27,155,28,156,29,157',
                'periodic-1..': '24,152,25,153,26,154,27,155,28,156,29,157',
                'recording-1..': '16,144,17,145,18,146,19,147,20,148,21,149,22,150,23,151',
                'tpproc-0-1.': '30,158,31,159',
                'cleanup-1.': '24,152,25,153,26,154,27,155,28,156,29,157',
                'consumer-1.': '24,152,25,153,26,154,27,155,28,156,29,157',
                'periodic-1.': '24,152,25,153,26,154,27,155,28,156,29,157'
            },
            'parent': '0,128,1,129,2,130,3,131,4,132,5,133,6,134,7,135,8,136,9,137,10,138,11,139,12,140,13,141,14,142,15,143,16,144,17,145,18,146,19,147,20,148,21,149,22,150,23,151,24,152,25,153,26,154,27,155,28,156,29,157,30,158,31,159'
        },
        'runp02srv004eth1': {
            'threads': {
                'rte-worker-34': '34',
                'rte-worker-35': '35',
                'rte-worker-36': '36',
                'rte-worker-37': '37',
                'rawproc-0-2..': '33,161,162,163,164,165,38,166,39,167,40,168,41,169,42,170,43,171,44,172,45,173,46,174,47,175',
                'cleanup-2..': '56,184,57,185,58,186,59,187,60,188,61,189',
                'consumer-2..': '56,184,57,185,58,186,59,187,60,188,61,189',
                'periodic-2..': '56,184,57,185,58,186,59,187,60,188,61,189',
                'recording-2..': '48,176,49,177,50,178,51,179,52,180,53,181,54,182,55,183',
                'tpproc-0-2.': '62,190,63,191',
                'cleanup-2.': '56,184,57,185,58,186,59,187,60,188,61,189',
                'consumer-2.': '56,184,57,185,58,186,59,187,60,188,61,189',
                'periodic-2.': '56,184,57,185,58,186,59,187,60,188,61,189'
            },
            'parent': '32,160,33,161,34,162,35,163,36,164,37,165,38,166,39,167,40,168,41,169,42,170,43,171,44,172,45,173,46,174,47,175,48,176,49,177,50,178,51,179,52,180,53,181,54,182,55,183,56,184,57,185,58,186,59,187,60,188,61,189,62,190,63,191'
        },
        'runp02srv004eth2': {
            'threads': {
                'rte-worker-66': '66',
                'rte-worker-67': '67',
                'rte-worker-68': '68',
                'rte-worker-69': '69',
                'rawproc-0-3..': '65,193,194,195,196,197,70,198,71,199,72,200,73,201,74,202,75,203,76,204,77,205,78,206,79,207',
                'cleanup-3..': '88,216,89,217,90,218,91,219,92,220,93,221',
                'consumer-3..': '88,216,89,217,90,218,91,219,92,220,93,221',
                'periodic-3..': '88,216,89,217,90,218,91,219,92,220,93,221',
                'recording-3..': '80,208,81,209,82,210,83,211,84,212,85,213,86,214,87,215',
                'tpproc-0-3.': '94,222,95,223',
                'cleanup-3.': '88,216,89,217,90,218,91,219,92,220,93,221',
                'consumer-3.': '88,216,89,217,90,218,91,219,92,220,93,221',
                'periodic-3.': '88,216,89,217,90,218,91,219,92,220,93,221'
            },
            'parent': '64,192,65,193,66,194,67,195,68,196,69,197,70,198,71,199,72,200,73,201,74,202,75,203,76,204,77,205,78,206,79,207,80,208,81,209,82,210,83,211,84,212,85,213,86,214,87,215,88,216,89,217,90,218,91,219,92,220,93,221,94,222,95,223'
        },
        'runp02srv004eth3': {
            'threads': {
                'rte-worker-98': '98',
                'rte-worker-99': '99',
                'rte-worker-100': '100',
                'rte-worker-101': '101',
                'rawproc-0-4..': '97,225,226,227,228,229,102,230,103,231,104,232,105,233,106,234,107,235,108,236,109,237,110,238,111,239',
                'cleanup-4..': '120,248,121,249,122,250,123,251,124,252,125,253',
                'consumer-4..': '120,248,121,249,122,250,123,251,124,252,125,253',
                'periodic-4..': '120,248,121,249,122,250,123,251,124,252,125,253',
                'recording-4..': '112,240,113,241,114,242,115,243,116,244,117,245,118,246,119,247',
                'tpproc-0-4.': '126,254,127,255',
                'cleanup-4.': '120,248,121,249,122,250,123,251,124,252,125,253',
                'consumer-4.': '120,248,121,249,122,250,123,251,124,252,125,253',
                'periodic-4.': '120,248,121,249,122,250,123,251,124,252,125,253'
            },
            'parent': '96,224,97,225,98,226,99,227,100,228,101,229,102,230,103,231,104,232,105,233,106,234,107,235,108,236,109,237,110,238,111,239,112,240,113,241,114,242,115,243,116,244,117,245,118,246,119,247,120,248,121,249,122,250,123,251,124,252,125,253,126,254,127,255'
        }
    }
}
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── remaining CPUs in CPU map ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
[]
pinning has been written to cpupin-all-running.json
pinning has been written to cpupin-all.json
```