import os
import re
import csv

from matplotlib import pyplot as plt


from pathlib import Path

from log_analyzer.consts import BOXPLOT_FOLDER_NAME
from log_analyzer.utils import print_error, print_success


class LogAnalyzer:
    def __init__(self, log_file_structure: dict):
        self.file_structure = log_file_structure
        self.ping_means = []
        self.ping_sizes = []
        self.full_data_dict = []
        self.partial_means = []
        self.rtt_for_file = []
        self.all_config_rtt_values = []
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

    def extract_avg_rtt(self, ping_log: str):
        avg_rtt = None
        try:
            with open(ping_log, 'r') as f:
                lines = f.readlines()
                rtt_line = ''
                for line in lines:
                    if 'rtt min/avg/max/mdev' in line or 'round-trip min/avg/max/stddev' in line:
                        rtt_line = line
                if rtt_line:
                    avg_rtt = rtt_line.split('=')[1].split('/')[1].strip()
                    print_success(f"Test {ping_log}: Avg RTT = {avg_rtt} ms")
                else:
                    print_error(f"Test {ping_log}: No RTT data found in ping log.")
            return avg_rtt
        except FileNotFoundError:
            print_error(f"Test {ping_log}: Ping log file not found: {ping_log}")
        except Exception as e:
            print_error(f"Test {ping_log}: Error analyzing ping log: {e}")


    def prepare_dict_for_test_data(self, file, mean):
        parametrizable_test_metrics = {}

        for folders in self.file_structure:
            # if len(folders) > 1:
                for folder_name in folders:
                    if folder_name in list(file.parts):
                        if "B" in folder_name:
                            parametrizable_test_metrics.update({"size": folder_name})
                            parametrizable_test_metrics.update({"mean_rtt_value": mean})
                        elif ".cfg" in folder_name:
                            parametrizable_test_metrics.update({"config": folder_name})
                        else:
                            parametrizable_test_metrics.update({folder_name: folder_name})

        self.full_data_dict.append(parametrizable_test_metrics)

    def update_rtt_vaules_for_config_dict(self,file, rtt_vaules):
        rtt_vaules_for_config_dict = {}
        current_config = None
        for folders in self.file_structure:
            for folder_name in folders:
                if folder_name in list(file.parts):
                    if ".cfg" in folder_name:
                        current_config = folder_name
                    elif "B" in folder_name:
                        rtt_vaules_for_config_dict.update({"size": folder_name})
                        rtt_vaules_for_config_dict.update({"rtt_values": rtt_vaules})
                    elif "attn" in folder_name:
                        rtt_vaules_for_config_dict.update({"attn": folder_name})

        for config_dict in self.all_config_rtt_values:
            if current_config in config_dict:
                config_dict[current_config].append(rtt_vaules_for_config_dict)
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

            for config in self.all_config_rtt_values:
                for config_name, measurements in config.items():
                    attenuation_groups = {}
                    for measurement in measurements:
                        attenuation = measurement['attn']
                        if attenuation not in attenuation_groups:
                            attenuation_groups[attenuation] = []
                        attenuation_groups[attenuation].append(measurement)

                    for attenuation, group_measurements in attenuation_groups.items():
                        plt.figure(figsize=(6, 7))
                        rtt_data = []
                        labels = []

                        for measurement in group_measurements:
                            size = measurement['size']
                            rtt_values = measurement['rtt_values']

                            rtt_data.append(rtt_values)
                            labels.append(int(re.sub(r'[a-zA-Z]', '', size)))

                        labels.sort()
                        for i in range(len(labels)):
                            labels[i] = f"{labels[i]}"
                        boxplot = plt.boxplot(rtt_data, labels=labels, patch_artist=False, showmeans=True)
                        plt.title(
                            f"RTT Distributions for \n {self.format_config_name_for_boxplot_title(config_name)}\n(Attenuation: {self.extract_digits(attenuation)}dB)", fontsize=24)
                        plt.xlabel("Packet Size [bytes]", fontsize=20)
                        plt.ylabel("RTT [ms]", fontsize=20)
                        plt.xticks(rotation=45, ha='right', fontsize=20)
                        plt.yticks(fontsize=20)
                        plt.xlim(0.85, 1.15)  # zoom into the only boxplot
                        for i, rtt_values in enumerate(rtt_data):
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
        def traverse(path, structure, level=0):
            # print("level: " + str(level))
            # print("len(struct): " + str(len(structure)))
            if level == len(structure):
                rtt_values_from_single_file = []
                for file in path.iterdir():
                    if file.is_file() and file.suffix == ".log" and "ping" in file.name:
                        print(f"Processing ping log file: {file}")
                        avg_rtt = self.extract_avg_rtt(file)
                        relative_file_path = self.extract_relative_path(file)
                        if avg_rtt is not None:
                            self.rtt_for_file.append((relative_file_path, avg_rtt))
                            rtt_values_from_single_file.append(float(avg_rtt))

                if len(rtt_values_from_single_file) > 0:
                    self.update_rtt_vaules_for_config_dict(file, rtt_values_from_single_file)
                    mean_rtt_value = self.calculate_mean_value(rtt_values_from_single_file)
                    self.prepare_dict_for_test_data(file, mean_rtt_value)
                return

            for folder_name in structure[level]:
                next_path = path / folder_name
                if next_path.exists():
                    print(f"Traversing into: {next_path}")
                    traverse(next_path, structure, level + 1)

        current_dir = Path(__file__).resolve().parent.parent
        traverse(current_dir, self.file_structure)

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
                    self.all_config_rtt_values.append({folder_name: []})


    def run(self):
        self.setup()
        self.parse_folder_structure()
        print(f"{self.full_data_dict=}")
        self.plot_boxplots_for_tests()
