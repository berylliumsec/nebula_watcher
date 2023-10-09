import re
import os
import argparse
import psutil
from diagrams import Diagram, Edge, Cluster
from diagrams.custom import Custom
import time
import logging
import json
import importlib.resources as resources
logging.basicConfig(level=logging.INFO)
class Watcher:

    def __init__(self):
        self.args = self._parse_arguments()
        self.ip_port_color = self._load_previous_state() or {}
        self.ethical_hacker_png_path= self.return_path("diagram_resources/ethical_hacker.png")
        self.ip_png_path= self.return_path("diagram_resources/ip.png")
        self.port_png_path= self.return_path("diagram_resources/port.png")
        if self.args.clear_state and os.path.exists('state.json'):
            os.remove('state.json')
    def _load_previous_state(self):
        """Load the previous state from a file if it exists."""
        state_file = 'state.json'
        if os.path.exists(state_file):
            with open(state_file, 'r') as file:
                return json.load(file)
        return None

    def is_run_as_package(self):
    # Check if the script is within a 'site-packages' directory
        return 'site-packages' in os.path.abspath(__file__)
    
    def return_path(self, path):
        if self.is_run_as_package():
            # Split the input path to get the directory and filename
            directory, filename = os.path.split(path)
            with resources.path(f'nebula_watcher.{directory}', filename) as correct_path:
                return str(correct_path)
        elif os.environ.get('IN_DOCKER'):
            correct_path =  "/app/"+path
            return correct_path

        return path
    def _save_current_state(self):
        """Save the current state to a file."""
        state_file = 'state.json'
        with open(state_file, 'w') as file:
            json.dump(self.ip_port_color, file)

    def generate_diagram(self):
                    
        # Define custom graph attributes for width and ratio
        graph_attributes = {
            "ratio": "1.5",  # Makes the diagram 1.5 times wider than its height
            "rankdir": "LR",  # Left to Right
            "ranksep": "2"  # Increase separation between ranks (layers) of the graph
        }

        # Define attributes for bolder nodes and edges
        node_attributes = {
            "fontsize": "20",  # Increase font size for bolder text
            "width": "1",  # Adjust node width
            "height": "1"   # Adjust node height
        }

        edge_attributes = {
            "penwidth": "3"  # Increase line width for bolder arrows
        }

        with Diagram(self.args.diagram_name, show=False, direction="LR", graph_attr=graph_attributes, node_attr=node_attributes):  # Top-level direction Left to Right
                
            # Create user icon/node
            user_node = Custom("User", self.ethical_hacker_png_path)

            # Outer cluster for IPs
            with Cluster("IP Addresses", direction="LR"):  # This cluster also expands Left to Right
                    
                for ip_address, ports in self.ip_port_color.items():
                        
                    # If there are no ports for an IP, continue to the next iteration
                    if not ports:
                        continue

                    # Inner cluster for each IP to group it with its ports vertically
                    with Cluster(ip_address, direction="TB"):  # Expanding Top to Bottom for each IP
                        ip_node = Custom(ip_address, self.ip_png_path)
                            
                        # Determine the color for the connection to the user
                        user_to_ip_color = "firebrick"
                        for _, color in ports.items():
                            if color == "green":
                                user_to_ip_color = "green"
                                break

                        # Create an edge from user to the IP with the determined color, dashed style, and increased penwidth
                        user_node >> Edge(color=user_to_ip_color, style="dashed", **edge_attributes) >> ip_node
                            
                        for port, color in ports.items():
                            port_node = Custom(port, self.port_png_path)
                                
                            # Create an edge from IP to the port with increased penwidth
                            ip_node >> Edge(color=color, style="dashed", **edge_attributes) >> port_node
                        
        self._save_current_state()





    def _parse_arguments(self):
        parser = argparse.ArgumentParser(description='Hacking Coverage tool')
        parser.add_argument('--results_dir', type=str, default='./results',
                            help='Directory to retrieve command results.')
        parser.add_argument('--diagram_name', type=str, default='ethical_hacking_activity',
                            help='Name of the generated diagram.')
        parser.add_argument('--clear_state', action='store_true',
                            help='Clear the previous state and start fresh.')

        return parser.parse_args()



    def parse_nmap(self):
        ip_port_map = {}

        # Check if the folder exists
        if not os.path.exists(self.args.results_dir):
            logging.warning(f"The directory: {self.args.results_dir} does not exist.")
            return []

        for root, dirs, files in os.walk(self.args.results_dir):
            if not files:
                logging.info(f"No results found in the directory: {self.args.results_dir}")
                return []

            for filename in files:
                filepath = os.path.join(root, filename)
                with open(filepath, 'r') as f:
                    data = f.read()

                if not data or not isinstance(data, str):
                    logging.warning(f"Data in {filename} is empty or not of type string.")
                    continue

                hosts = re.split(r'Nmap scan report for ', data)
                if len(hosts) <= 1:
                    logging.warning(f"No valid Nmap reports found in {filename}.")
                    continue

                for host in hosts[1:]:
                    match = re.search(r'(?:[a-zA-Z0-9.-]+\s)?\(([\d\.]+)\)', host)
                    if not match:
                        continue

                    ip_address = match.group(1) or "Unknown"
                    ports = set()

                    service_matches = re.findall(r'(\d+)/(tcp|udp)\s+(\w+)\s+([\w-]+)', host)
                    for match in service_matches:
                        port, _, state, _ = match
                        if state == "open":
                            ports.add(port)

                    # Only proceed if there are open ports
                    if not ports:
                        continue

                    if ip_address in ip_port_map:
                        ip_port_map[ip_address].update(ports)
                    else:
                        ip_port_map[ip_address] = ports

        for ip, ports in ip_port_map.items():
            if ip not in self.ip_port_color:
                self.ip_port_color[ip] = {port: "firebrick" for port in ports}
            else:
                for port in ports:
                    if port not in self.ip_port_color[ip]:
                        self.ip_port_color[ip][port] = "firebrick"

        self.generate_diagram()

        # Filter out IPs without open ports in the return statement
        return [{"ip": ip, "ports": list(ports)} for ip, ports in ip_port_map.items() if ports]






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
                connections = psutil.net_connections(kind='inet')
                for conn in connections:
                    if conn.laddr and len(conn.raddr) == 2:
                        remote_ip, remote_port = conn.raddr
                        for target in targets:
                            if remote_ip == target['ip'] and str(remote_port) in target['ports']:
                                match_str = f"{remote_ip}:{remote_port}"
                                if match_str not in unique_matches:
                                    logging.info(f"Activity detected: {match_str}")
                                    unique_matches.add(match_str)

                                    # Update the color in the mapping and regenerate the diagram
                                    self.ip_port_color[remote_ip][str(remote_port)] = "green"
                                    self.generate_diagram()

                # Sleep for a short interval to prevent maxing out CPU
                time.sleep(0.5)

        except KeyboardInterrupt:
            logging.info("Monitoring stopped due to keyboard interruption.")



def main_func():
    monitor = Watcher()
    monitor.monitor_network_connections()

if __name__ == "__main__":
    main_func()
