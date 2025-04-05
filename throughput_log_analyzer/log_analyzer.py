import os
import re
import csv
import pandas as pd

from scapy.all import PcapReader
from matplotlib import pyplot as plt
from tqdm import tqdm

from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from throughput_log_analyzer.consts import BOXPLOT_FOLDER_NAME
from throughput_log_analyzer.utils import print_error, print_success


class LogAnalyzer:
    def __init__(self, log_file_structure: dict):
        self.file_structure = log_file_structure
        self.throughput_means = []
        self.ping_sizes = []
        self.full_data_dict = []
        self.partial_means = []
        self.throughput_for_file = []
        self.all_config_throughput_values = []
        self.attenuations = []

    def setup(self):
        self.put_config_names_into_dict()
        self.prepare_folder_for_graphs(BOXPLOT_FOLDER_NAME)
        self.get_ping_sizes()
        self.get_attenuations()


    def extract_relative_path(self, full_path):
        path_str = str(full_path)
        start_index = path_str.find('.cfg')
        if start_index == -1:
            raise ValueError("'.cfg' not found in the given path.")
        return path_str[start_index:]


    def compute_avg_throughput(self, pcap_file, src_ip="10.15.20.10", dst_ip="10.15.20.239", start_sec=5, end_sec=25) -> float:
        timestamps = []
        sizes = []

        with PcapReader(str(pcap_file)) as pcap:
            for pkt in pcap:
                if pkt.haslayer("IP"):
                    ip_layer = pkt["IP"]
                    if ip_layer.src == src_ip and ip_layer.dst == dst_ip:
                        timestamps.append(pkt.time)
                        sizes.append(len(pkt))

        if not timestamps:
            print(f"No matching packets found in {pcap_file}.")
            return 0.0

        # Normalize timestamps
        df = pd.DataFrame({"time": timestamps, "size": sizes})
        df["time"] = df["time"] - df["time"].min()

        # Select interval
        mask = (df["time"] >= start_sec) & (df["time"] < end_sec)
        interval_df = df.loc[mask]

        if interval_df.empty:
            print(f"No packets found in interval {start_sec}–{end_sec}s for {pcap_file}.")
            return 0.0

        total_bits = interval_df["size"].sum() * 8
        duration = end_sec - start_sec  # seconds

        throughput_mibps = total_bits / duration / (1024 * 1024)  # Convert to Mibps
        return throughput_mibps


    def prepare_dict_for_test_data(self, file, mean):
        parametrizable_test_metrics = {}

        for folders in self.file_structure:
            # if len(folders) > 1:
                for folder_name in folders:
                    if folder_name in list(file.parts):
                        if "B" in folder_name:
                            parametrizable_test_metrics.update({"size": folder_name})
                            parametrizable_test_metrics.update({"mean_throughput_value": mean})
                        elif ".cfg" in folder_name:
                            parametrizable_test_metrics.update({"config": folder_name})
                        else:
                            parametrizable_test_metrics.update({folder_name: folder_name})

        self.full_data_dict.append(parametrizable_test_metrics)

    def update_throughput_values_for_config_dict(self, file, throughput_values):
        throughput_values_for_config_dict = {}
        current_config = None
        for folders in self.file_structure:
            for folder_name in folders:
                if folder_name in list(file.parts):
                    if ".cfg" in folder_name:
                        current_config = folder_name
                    elif "B" in folder_name:
                        throughput_values_for_config_dict.update({"size": folder_name})
                        throughput_values_for_config_dict.update({"throughput_values": throughput_values})
                    elif "attn" in folder_name:
                        throughput_values_for_config_dict.update({"attn": folder_name})

        for config_dict in self.all_config_throughput_values:
            if current_config in config_dict:
                config_dict[current_config].append(throughput_values_for_config_dict)
                break


    def calculate_mean_value(self, partial_means):
        sum = 0
        for value in partial_means:
            sum+=value
        return sum/len(partial_means)


    def format_config_name_for_boxplot_title(self, config_name):
        # Remove `.cfg` if present
        config_name = config_name.replace('.cfg', '')

        # Split by '-'
        parts = config_name.split('-')

        # Remove first two parts (e.g. "pb", "178")
        parts = parts[2:]

        # If odd number of words, place more on second line
        half = len(parts) // 2
        first_line = '-'.join(parts[:half])
        second_line = '-'.join(parts[half:])

        return f"{first_line}\n{second_line}"

    def plot_boxplots_for_tests(self):
        csv_table_path = os.path.join(self.boxplot_path, "boxplot_stats.csv")
        with open(csv_table_path, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["configuration", "attenuation (dB)", "packet size (B)", "mean (ms)", "median (ms)", "q1 (ms)", "q3 (ms)"])

            for config in self.all_config_throughput_values:
                for config_name, measurements in config.items():
                    attenuation_groups = {}
                    for measurement in measurements:
                        attenuation = measurement['attn']
                        if attenuation not in attenuation_groups:
                            attenuation_groups[attenuation] = []
                        attenuation_groups[attenuation].append(measurement)

                    for attenuation, group_measurements in attenuation_groups.items():
                        plt.figure(figsize=(6, 7))
                        throughput_data = []
                        labels = []

                        for measurement in group_measurements:
                            size = measurement['size']
                            throughput_values = measurement['throughput_values']

                            throughput_data.append(throughput_values)
                            labels.append(int(re.sub(r'[a-zA-Z]', '', size)))

                        labels.sort()
                        for i in range(len(labels)):
                            labels[i] = f"{labels[i]}"
                        boxplot = plt.boxplot(throughput_data, labels=labels, patch_artist=False, showmeans=True)
                        plt.title(
                            f"Throughput Distributions for \n {self.format_config_name_for_boxplot_title(config_name)}\n(Attenuation: {self.extract_digits(attenuation)}dB)", fontsize=24)
                        plt.xlabel("Packet Size [bytes]", fontsize=20)
                        plt.ylabel("Throughput [Mibps]", fontsize=20)
                        plt.xticks(rotation=45, ha='right', fontsize=20)
                        plt.yticks(fontsize=20)
                        plt.xlim(0.85, 1.15)  # zoom into the only boxplot
                        for i, throughput_values in enumerate(throughput_data):
                            median = boxplot['medians'][i].get_ydata()[0]
                            path = boxplot['boxes'][i].get_path()
                            vertices = path.vertices
                            q1 = vertices[0][1]  # Bottom of the box
                            q3 = vertices[2][1]  # Top of the box
                            mean = boxplot['means'][i].get_ydata()[0] if 'means' in boxplot else None

                            x = i + 1

                            writer.writerow([
                                config_name,
                                self.extract_digits(attenuation),
                                self.extract_digits(size),
                                round(mean, 3),
                                round(median, 3),
                                round(q1, 3),
                                round(q3, 3)
                            ])

                        plt.tight_layout()
                        filename = f"{config_name}_{attenuation}dB_boxplots.png"
                        plt.savefig(os.path.join(self.boxplot_path, filename))
                        plt.close()


    def extract_digits(self, text) -> str:
        return ''.join(char for char in text if char.isdigit())

    def parse_folder_structure(self):
        files_to_process = []

        def traverse(path, structure, level=0):
            if level == len(structure):
                for file in path.iterdir():
                    if file.is_file() and file.suffix == ".pcap" and "pcap" in file.name:
                        files_to_process.append(file)
                return

            for folder_name in structure[level]:
                next_path = path / folder_name
                if next_path.exists():
                    print(f"Traversing into: {next_path}")
                    traverse(next_path, structure, level + 1)

        current_dir = Path(__file__).resolve().parent.parent
        traverse(current_dir, self.file_structure)

        # Process all pcap files in parallel
        print(f"Processing {len(files_to_process)} pcap files using multiprocessing...")
        with ProcessPoolExecutor(max_workers=16) as executor:
            future_to_file = {
                executor.submit(self.compute_avg_throughput, str(pcap_file)): pcap_file
                for pcap_file in files_to_process
            }

            progress_bar = tqdm(total=len(future_to_file), desc="Processing .pcap files", ncols=100)

            for future in as_completed(future_to_file):
                file = future_to_file[future]
                try:
                    avg_throughput = future.result()
                    relative_file_path = self.extract_relative_path(file)
                    if avg_throughput is not None:
                        self.throughput_for_file.append((relative_file_path, avg_throughput))
                        self.update_throughput_values_for_config_dict(file, [float(avg_throughput)])
                        self.prepare_dict_for_test_data(file, avg_throughput)
                except Exception as e:
                    print(f"\n Error processing {file}: {e}")
                finally:
                    progress_bar.update(1)

            progress_bar.close()


    def prepare_folder_for_graphs(self, folder_name):
        self.boxplot_path = os.path.join('results', folder_name)
        os.makedirs(self.boxplot_path, exist_ok=True)


    def get_ping_sizes(self):
        for folders in self.file_structure:
            if all(item.isdigit() for item in folders):
                self.ping_sizes = folders.copy()
        self.ping_sizes.append(self.ping_sizes)


    def get_attenuations(self):
        for folders in self.file_structure:
            if any("attn" in item for item in folders):
                self.attenuations = folders.copy()
        self.attenuations.append(self.attenuations)


    def put_config_names_into_dict(self):
        for folder_level in self.file_structure:
            for folder_name in folder_level:
                if ".cfg" in folder_name:
                    self.all_config_throughput_values.append({folder_name: []})


    def run(self):
        self.setup()
        self.parse_folder_structure()
        print(f"{self.full_data_dict=}")
        self.plot_boxplots_for_tests()
