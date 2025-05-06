import os
import re
import csv
import numpy as np

from matplotlib import pyplot as plt


from pathlib import Path

from trace_mcs_log_analyzer.consts import BOXPLOT_FOLDER_NAME
from trace_mcs_log_analyzer.utils import print_error, print_success


class LogAnalyzer:
    def __init__(self, log_file_structure: dict):
        self.file_structure = log_file_structure
        self.mcs_means = []
        self.ping_sizes = []
        self.full_data_dict = []
        self.partial_means = []
        self.mcs_for_file = []
        self.all_config_mcs_values = []
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

    def extract_avg_mcs(self, mcs_log: str):
        mcs_values = []
        inside_cell = False

        try:
            with open(mcs_log, 'r') as f:
                for line in f:
                    line = line.strip()

                    if '"ul_mcs"' in line or 'ul_mcs' in line:
                        try:
                            # This will match: ul_mcs: 30.1 or "ul_mcs": 30.1
                            mcs_str = line.split(":")[1].strip().rstrip(',')
                            mcs_val = float(mcs_str)
                            mcs_values.append(mcs_val)

                        except Exception as e:
                            print(f"Skipping malformed mcs line: {line}, error: {e}")
                            continue

            if mcs_values:
                avg_mcs = sum(mcs_values) / len(mcs_values)
                print_success(f"Test {mcs_log}: Avg mcs = {avg_mcs:.3f} dB")
                return avg_mcs
            else:
                print_error(f"Test {mcs_log}: No valid mcs values found.")
                return None

        except FileNotFoundError:
            print_error(f"Test {mcs_log}: File not found.")
        except Exception as e:
            print_error(f"Test {mcs_log}: Unexpected error: {e}")

    def prepare_dict_for_test_data(self, file, mean):
        parametrizable_test_metrics = {}

        for folders in self.file_structure:
            # if len(folders) > 1:
                for folder_name in folders:
                    if folder_name in list(file.parts):
                        if "B" in folder_name:
                            parametrizable_test_metrics.update({"size": folder_name})
                            parametrizable_test_metrics.update({"mean_mcs_value": mean})
                        elif ".cfg" in folder_name:
                            parametrizable_test_metrics.update({"config": folder_name})
                        else:
                            parametrizable_test_metrics.update({folder_name: folder_name})

        self.full_data_dict.append(parametrizable_test_metrics)

    def update_mcs_vaules_for_config_dict(self,file, mcs_vaules):
        mcs_vaules_for_config_dict = {}
        current_config = None
        for folders in self.file_structure:
            for folder_name in folders:
                if folder_name in list(file.parts):
                    if ".cfg" in folder_name:
                        current_config = folder_name
                    elif "B" in folder_name:
                        mcs_vaules_for_config_dict.update({"size": folder_name})
                        mcs_vaules_for_config_dict.update({"mcs_values": mcs_vaules})
                    elif "attn" in folder_name:
                        mcs_vaules_for_config_dict.update({"attn": folder_name})

        for config_dict in self.all_config_mcs_values:
            if current_config in config_dict:
                config_dict[current_config].append(mcs_vaules_for_config_dict)
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
            writer.writerow([
                "configuration", "attenuation (dB)", "packet size (B)",
                "mean", "median", "std", "min", "max",
                "q1", "q3"
            ])

            for config in self.all_config_mcs_values:
                for config_name, measurements in config.items():
                    attenuation_groups = {}
                    for measurement in measurements:
                        attenuation = measurement['attn']
                        if attenuation not in attenuation_groups:
                            attenuation_groups[attenuation] = []
                        attenuation_groups[attenuation].append(measurement)

                    for attenuation, group_measurements in attenuation_groups.items():
                        plt.figure(figsize=(6, 7))

                        size_to_mcs_values = {}

                        for measurement in group_measurements:
                            size = measurement['size']
                            size_clean = int(re.sub(r'[a-zA-Z]', '', size))

                            if size_clean not in size_to_mcs_values:
                                size_to_mcs_values[size_clean] = []

                            size_to_mcs_values[size_clean].extend(measurement['mcs_values'])

                        # Then sort and prepare for plotting
                        labels, mcs_data = zip(*sorted(size_to_mcs_values.items()))
                        labels = [str(label) for label in labels]

                        boxplot = plt.boxplot(mcs_data, labels=labels, patch_artist=False, showmeans=True)
                        plt.title(
                            f"UL MCS Distributions for \n {self.format_config_name_for_boxplot_title(config_name)}\n(Attenuation: {self.extract_digits(attenuation)}dB)",
                            fontsize=24)
                        plt.xlabel("Packet Size [bytes]", fontsize=20)
                        plt.ylabel("UL MCS", fontsize=20)
                        plt.xticks(rotation=45, ha='right', fontsize=20)
                        plt.yticks(fontsize=20)
                        # plt.xlim(0.65, 1.35) # packet sizes don't fit

                        for i, mcs_values in enumerate(mcs_data):
                            mcs_array = np.array(mcs_values)
                            mean = np.mean(mcs_array)
                            median = np.median(mcs_array)
                            std = np.std(mcs_array)
                            min_val = np.min(mcs_array)
                            max_val = np.max(mcs_array)
                            q1 = np.percentile(mcs_array, 25)
                            q3 = np.percentile(mcs_array, 75)

                            writer.writerow([
                                config_name,
                                self.extract_digits(attenuation),
                                labels[i],
                                round(mean, 3),
                                round(median, 3),
                                round(std, 3),
                                round(min_val, 3),
                                round(max_val, 3),
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
                mcs_values_from_single_file = []
                for file in path.iterdir():
                    if file.is_file() and file.suffix == ".log" in file.name:
                        print(f"Processing TRACE log file: {file}")
                        avg_mcs = self.extract_avg_mcs(file)
                        relative_file_path = self.extract_relative_path(file)
                        if avg_mcs is not None:
                            self.mcs_for_file.append((relative_file_path, avg_mcs))
                            mcs_values_from_single_file.append(float(avg_mcs))

                if len(mcs_values_from_single_file) > 0:
                    self.update_mcs_vaules_for_config_dict(file, mcs_values_from_single_file)
                    mean_mcs_value = self.calculate_mean_value(mcs_values_from_single_file)
                    self.prepare_dict_for_test_data(file, mean_mcs_value)
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
                    self.all_config_mcs_values.append({folder_name: []})


    def run(self):
        self.setup()
        self.parse_folder_structure()
        print(f"{self.full_data_dict=}")
        self.plot_boxplots_for_tests()
