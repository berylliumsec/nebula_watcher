# Nebula-Watcher

Welcome to the Nebula-Watcher 

![nebula](/images/nebula_watcher.png)


## Content
- [Acknowledgement](#Acknowledgement)
- [Why?](#why)
- [Features](#features)
- [Dependencies](#dependencies)
- [Installation](#installation)
- [Usage](#usage)
- [Options](#options)
- [How-it-works](#how-it-works)


## Acknowledgement

First i would like to thank the All-Mighty God who is the source of all knowledge, without Him, this would not be possible.


## Why?

Nebula-Watcher offers a method for ethical hackers to monitor the IP addresses and ports they've engaged with during a penetration test. It serves as a visual tool to ensure comprehensive coverage of all intended IP addresses and ports under examination.

## Features

- Parses NMAP scan results (in plain text format) from a specified directory and returns only IP addresses with open ports.
- Monitors network connections and matches them against the parsed NMAP scan results.
- Generates a visual diagram depicting the activity, with different colors indicating the type of connection.
- Periodically updates the diagram, maintaining a history of the ethical hacking activity.

**Example**

Before connecting to port 443:

![Before](/images/before_ethical_hacking_activity.png)

After connecting to port 443:

![After](/images/after_ethical_hacking_activity.png)

## Dependencies

- [graphviz](https://graphviz.org/)
- [Python3](https://www.python.org/downloads/)
- [diagrams](https://github.com/mingrammer/diagrams)
- [psutil](https://psutil.readthedocs.io/en/latest/)


## Installation

The easiest way to get started is to use the docker image.


**Docker**:

Pulling the image:

``` bash
docker pull berylliumsec/nebula_watcher:latest
```
Running the image docker image :

```bash
docker run --network host -v directory_that_contains_nmap_results/nmap_plain_text:/app/results -v where/you/want/the/diagram:/app/output  berylliumsec/nebula_watcher:latest
```

To change the diagram name from the default:

```bash
docker run --network host -v directory_that_contains_nmap_results/nmap_plain_text:/app/results -v where/you/want/the/diagram:/app/output  berylliumsec/nebula_watcher:latest python3 nebula_watcher.py --diagram_name /app/your_diagram_name
```


**PIP**:

```
pip install nebula-watcher
```

To run nebula-watcher simply enter:

```bash 
nebula-watcher
``` 

## Usage

Utilizing Nebula-Watcher is straightforward. Simply execute the tool, whether through the installed pip package or Docker. It will then autonomously monitor the IP addresses and ports you've engaged.

## Options:

- --results_dir : Specify the directory containing NMAP scan results. (Default: ./results)
- --diagram_name : Specify the name for the generated diagram. (Default: hacking_activity)
- --clear_state : Use this flag if you want to start the script without using the previous state. This can be helpful for debugging purposes.
- --help: display the above options.

**IMPORTANT**

- Ensure that your plain-text NMAP results are located within a directory titled results situated in the current working directory. If you intend to utilize a custom directory, please reference the aforementioned options for guidance.

- By default, the generated diagram will be saved in the current working directory with the name ethical_hacking_activity.png. However, you have the flexibility to specify an alternate filename, as detailed in the provided options.

- In cases where there is a significant number of IP addresses with open ports, it might be necessary to zoom into the diagram for clarity.

- The monitoring tool creates a state.json file in the current working directory. This ensures the preservation of states even post-closure of the monitoring tool.

- For accurate results, it is recommended to initiate Nebula-Watcher only after completing your general scans. Initiating beforehand may lead to the tool interpreting that all IPs and ports have been engaged during testing.

## How It Works

- The script first parses the NMAP scan results to identify open ports on different IP addresses.
- It then monitors live network connections on the machine it's running on.
- When a network connection matches an IP and port from the NMAP results, the color of the arrow goes from red to blue on the diagram.
- The diagram is periodically updated to reflect the current state of the network connections.
