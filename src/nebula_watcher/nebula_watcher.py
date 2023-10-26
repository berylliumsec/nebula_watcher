import argparse
import importlib.resources as resources
import json
import logging
import os
import re
import time
import xml.etree.ElementTree as ET

import psutil
from diagrams import Cluster, Diagram, Edge
from diagrams.custom import Custom

# Setting up logging
logging.basicConfig(level=logging.INFO)


class Watcher:
    CVE_PATTERN = re.compile(r"CVE-\d{4}-\d{4,7}", re.IGNORECASE)

    def __init__(self):
        self.args = self._parse_arguments()
        self.ip_port_color = self._load_previous_state() or {}
        resources_path = "diagram_resources"
        self.ethical_hacker_png_path = self.return_path(
            f"{resources_path}/ethical_hacker.png"
        )
        self.ip_png_path = self.return_path(f"{resources_path}/ip.png")
        self.port_png_path = self.return_path(f"{resources_path}/port.png")
        self.cve_icon_path = self.return_path(f"{resources_path}/cve.png")
        self.service_icon_path = self.return_path(f"{resources_path}/service.png")
        self.device_icon_path = self.return_path(f"{resources_path}/device.png")
        if self.args.clear_state and os.path.exists("state.json"):
            os.remove("state.json")
        self._load_state()

    def _load_state(self):
        state_file = "state.json"
        if os.path.exists(state_file):
            with open(state_file, "r") as file:
                self.ip_port_color = json.load(file)

    def _parse_arguments(self):
        parser = argparse.ArgumentParser(description="Hacking Coverage tool")
        parser.add_argument(
            "--results_dir",
            type=str,
            default="./results",
            help="Directory to retrieve command results.",
        )
        parser.add_argument(
            "--diagram_name",
            type=str,
            default="ethical_hacking_activity",
            help="Name of the generated diagram.",
        )
        parser.add_argument(
            "--clear_state",
            action="store_true",
            help="Clear the previous state and start fresh.",
        )

        return parser.parse_args()

    def _load_previous_state(self):
        """Load the previous state from a file if it exists."""
        state_file = "state.json"
        if os.path.exists(state_file):
            with open(state_file, "r") as file:
                return json.load(file)
        return None

    def is_run_as_package(self):
        return "site-packages" in os.path.abspath(__file__)

    def return_path(self, path):
        if self.is_run_as_package():
            directory, filename = os.path.split(path)
            with resources.path(
                f"nebula_watcher.{directory}", filename
            ) as correct_path:
                return str(correct_path)
        elif os.environ.get("IN_DOCKER"):
            return f"/app/{path}"
        return path

    def _save_current_state(self):
        state_file = "state.json"
        with open(state_file, "w") as file:
            json.dump(self.ip_port_color, file)

    def generate_diagram(self, hosts):

        # Aggregate the data by IP address
        unique_hosts = {}
        for host in hosts:
            ip = host["ip"]
            if ip not in unique_hosts:
                unique_hosts[ip] = {"ports": set(), "services": set(), "cves": set()}
            unique_hosts[ip]["ports"].update(host["ports"])
            unique_hosts[ip]["services"].update(host["services"])
            unique_hosts[ip]["cves"].update(host["cves"])

        # Define custom graph attributes for width and ratio
        graph_attributes = {"ratio": "1.5", "rankdir": "LR", "ranksep": "2"}

        # Define attributes for bolder nodes and edges
        node_attributes = {"fontsize": "20", "width": "1", "height": "1"}

        edge_attributes = {
            "penwidth": "3",
        }
        default_edge_color = "red"  # Default to red

        with Diagram(
            self.args.diagram_name,
            show=False,
            direction="LR",
            graph_attr=graph_attributes,
            node_attr=node_attributes,
        ):

            # Create user icon/node
            user_node = Custom("User", self.ethical_hacker_png_path)

            # Outer cluster for devices
            with Cluster("Devices", direction="LR"):

                for ip_address, data in unique_hosts.items():
                    if ip_address not in self.ip_port_color:
                        self.ip_port_color[ip_address] = {
                            "connection": "red",  # default color
                            "ports": {},  # for individual port colors if needed later
                        }
                    ports = list(data["ports"])
                    services = list(data["services"])
                    cves = list(data["cves"])

                    # Initialize colors for ports if not already present
                    for port in ports:
                        if str(port) not in self.ip_port_color[ip_address]["ports"]:
                            self.ip_port_color[ip_address]["ports"][str(port)] = "red"

                    # Inner cluster for each IP to group it with its ports vertically
                    with Cluster(ip_address, direction="TB"):
                        ip_node = Custom(ip_address, self.ip_png_path)
                        connection_color = self.ip_port_color[ip_address].get(
                            "connection", default_edge_color
                        )
                        (
                            user_node
                            >> Edge(
                                color=connection_color,
                                style="dashed",
                                **edge_attributes,
                            )
                            >> ip_node
                        )

                        # Ports and services
                        for port, service in zip(ports, services):
                            port_color = self.ip_port_color[ip_address]["ports"].get(
                                str(port), default_edge_color
                            )

                            # If there's any associated CVE, adjust the border
                            if cves:
                                port_node = Custom(
                                    f"{service} ({port})",
                                    self.service_icon_path,
                                    border_color="red",
                                )
                                (
                                    ip_node
                                    >> Edge(color=port_color, **edge_attributes)
                                    >> port_node
                                )

                                # Point to a single CVE icon
                                cve_node = Custom("CVE(s) Present", self.cve_icon_path)
                                (
                                    port_node
                                    << Edge(color=default_edge_color, **edge_attributes)
                                    << cve_node
                                )
                            else:
                                port_node = Custom(
                                    f"{service} ({port})", self.service_icon_path
                                )
                                (
                                    ip_node
                                    >> Edge(color=port_color, **edge_attributes)
                                    >> port_node
                                )

        self._save_current_state()

    def parse_nmap(self):
        if not os.path.exists(self.args.results_dir):
            logging.warning(f"The directory: {self.args.results_dir} does not exist.")
            return []

        files_to_process = [
            f
            for root, dirs, files in os.walk(self.args.results_dir)
            for f in files
            if f.lower().endswith(".xml")
        ]
        if not files_to_process:
            logging.info(f"No results found in the directory: {self.args.results_dir}")
            return []

        associated_cve_results = []

        for filename in files_to_process:
            filepath = os.path.join(self.args.results_dir, filename)

            if os.path.isfile(filepath):
                tree = ET.parse(filepath)
                xml_root = tree.getroot()
            else:
                xml_root = ET.ElementTree(ET.fromstring(filepath))

            parsed_results = []
            global_cve_matches = set()  # Global CVEs

            # Extract CVEs from the entire XML once
            for elem in xml_root.iter():
                # Check element tag for CVE
                tag_cves = self.CVE_PATTERN.findall(elem.tag)
                global_cve_matches.update(tag_cves)

                # Check element text for CVE
                if elem.text:
                    text_cves = self.CVE_PATTERN.findall(elem.text)
                    global_cve_matches.update(text_cves)

                # Check all attributes for CVEs
                for attrib_name, attrib_value in elem.attrib.items():
                    attrib_name_cves = self.CVE_PATTERN.findall(attrib_name)
                    global_cve_matches.update(attrib_name_cves)

                    attrib_value_cves = self.CVE_PATTERN.findall(attrib_value)
                    global_cve_matches.update(attrib_value_cves)

            for host in xml_root.findall("host"):
                host_cve_matches = set()  # Local set for the host's CVEs

                device_name = host.find("hostnames/hostname").attrib.get(
                    "name", "Unknown"
                )
                ip_address = host.find("address").attrib.get("addr", "Unknown")

                ports = []
                services = []

                for port in host.findall("ports/port"):
                    port_id = port.attrib.get("portid")
                    port_state = port.find("state").attrib.get("state")
                    service_name = port.find("service").attrib.get("name")

                    if port_state == "open" and port_id not in ports:
                        ports.append(port_id)
                        if service_name == "domain":
                            services.append("dns")
                        else:
                            services.append(service_name)

                    # Extract CVEs related to this specific port and update host_cve_matches
                    for elem in port.iter():
                        # Check element tag for CVE
                        tag_cves = self.CVE_PATTERN.findall(elem.tag)
                        host_cve_matches.update(tag_cves)

                        # Check element text for CVE
                        if elem.text:
                            text_cves = self.CVE_PATTERN.findall(elem.text)
                            host_cve_matches.update(text_cves)

                        # Check all attributes for CVEs
                        for attrib_name, attrib_value in elem.attrib.items():
                            attrib_name_cves = self.CVE_PATTERN.findall(attrib_name)
                            host_cve_matches.update(attrib_name_cves)

                            attrib_value_cves = self.CVE_PATTERN.findall(attrib_value)
                            host_cve_matches.update(attrib_value_cves)

                # Appending to parsed_results with global CVEs for each host
                parsed_results.append(
                    {
                        "hostname": device_name,
                        "ip": ip_address,
                        "ports": ports,
                        "services": services,
                        "cves": list(global_cve_matches),  # Using the global CVEs
                    }
                )

                # Appending to associated_cve_results with associated CVEs for each host and port
                associated_cve_results.append(
                    {
                        "hostname": device_name,
                        "ip": ip_address,
                        "ports": ports,
                        "services": services,
                        "cves": list(
                            host_cve_matches
                        ),  # Using the local/associated CVEs
                    }
                )

        return associated_cve_results

    def monitor_network_connections(self):
        unique_matches = set()
        refresh_interval = 60  # Run parse_nmap every 60 seconds

        last_parsed_time = 0
        targets = self.parse_nmap()  # Initial parse

        try:
            while True:
                current_time = time.time()

                # Check if the refresh interval has passed for Nmap parsing
                if current_time - last_parsed_time > refresh_interval:
                    logging.info("Refreshing nmap.")
                    targets = self.parse_nmap()
                    last_parsed_time = current_time

                # Continuously check for connections
                connections = psutil.net_connections(kind="inet")
                for conn in connections:
                    if conn.laddr and len(conn.raddr) == 2:
                        remote_ip, remote_port = conn.raddr
                        for target in targets:
                            if (
                                remote_ip == target["ip"]
                                and str(remote_port) in target["ports"]
                            ):
                                match_str = f"{remote_ip}:{remote_port}"
                                if match_str not in unique_matches:
                                    logging.info(f"Activity detected: {match_str}")
                                    unique_matches.add(match_str)

                                    # Update the color in the mapping for both IP and specific port
                                    self.ip_port_color[remote_ip][
                                        "connection"
                                    ] = "green"
                                    self.ip_port_color[remote_ip]["ports"][
                                        str(remote_port)
                                    ] = "green"
                                    self.generate_diagram(targets)

                # Sleep for a short interval to prevent maxing out CPU
                time.sleep(0.5)

        except KeyboardInterrupt:
            logging.info("Monitoring stopped due to keyboard interruption.")

    def _extract_cves(self, root_elem):
        """Extract CVEs from the provided XML element."""
        cve_matches = set()
        for elem in root_elem.iter():
            tag_cves = self.CVE_PATTERN.findall(elem.tag)
            cve_matches.update(tag_cves)

            if elem.text:
                text_cves = self.CVE_PATTERN.findall(elem.text)
                cve_matches.update(text_cves)

            for _, attrib_value in elem.attrib.items():
                attrib_value_cves = self.CVE_PATTERN.findall(attrib_value)
                cve_matches.update(attrib_value_cves)

        return cve_matches


def main_func():
    monitor = Watcher()
    targets = monitor.parse_nmap()
    monitor.generate_diagram(targets)
    monitor.monitor_network_connections()


if __name__ == "__main__":
    main_func()
