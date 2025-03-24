import os
from colorama import Fore, Style

def parse_folder_structure(directory):
    """
    Recursively parses the folder structure under the given directory
    and returns a tree structure of folder names, ensuring no duplicates.
    This version organizes the structure in a format similar to LOG_FILE_STRUCTURE_INITIAL_CUT_TEST_RX_GAIN_50.

    Args:
        directory (str): The starting directory to parse (e.g., "results").

    Returns:
        list: A nested list representing the folder structure as a tree, without duplicates.
    """

    def traverse(path, seen_folders):
        structure = []

        # Loop through the items in the current directory
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):  # If the item is a directory
                # Check if the folder name has already been added
                if item not in seen_folders:
                    # Mark this folder as seen
                    seen_folders.add(item)

                    # Recursively traverse subdirectories
                    substructure = traverse(item_path, seen_folders)
                    if substructure:
                        structure.append([item, substructure])
                    else:
                        structure.append([item])

        return structure

    # Start parsing from the given directory
    seen_folders = set()  # To track the folders that have been processed
    return traverse(directory, seen_folders)


def organize_file_structure(results, base_station, test_name, logs, side, ping_packet_sizes, types_of_logs):
    """
    Organizes the parsed folder structure into a more organized format as required.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(current_dir, '..', '..', results, base_station, test_name)  # Go two levels up and then to "results"

    # Get the folder structure
    folder_structure = parse_folder_structure(results_dir)

    # Initialize the structure to match the desired format
    log_file_structure = [
        [results],
        [base_station],
        [test_name],
        [logs],
        [],  # Configs will be populated below
        [],  # Attenuations will be populated below
        [],  # Bandwidths will be populated below
        [*side],
        [*ping_packet_sizes],
        [*types_of_logs]
    ]

    # Initialize categories to collect folder names
    configs = []
    attenuations = []
    bandwidths = []

    # Loop through the folder structure to populate the categories
    def find_category_folders(structure):
        for item in structure:
            if isinstance(item, list):  # This is a subdirectory, we need to recurse
                find_category_folders(item)  # Recurse through nested directories
            else:  # This is a folder name
                print(f"Found folder: {item}")  # Debug print to see all folder names
                if "config" in item:
                    configs.append(item)
                if "attenuation" in item:  # Look for folders containing "attenuation"
                    attenuations.append(item)
                if "M" in item:  # Assuming bandwidth names contain 'M'
                    bandwidths.append(item)

    # Start finding the categories
    find_category_folders(folder_structure)

    # Ensure categories are populated even if no folder was found
    log_file_structure[4] = configs if configs else []
    log_file_structure[5] = attenuations if attenuations else []
    if bandwidths:
        log_file_structure[6] = bandwidths

    return log_file_structure



def print_success(message: str) -> None:
    print(f"{Fore.GREEN}{message}{Style.RESET_ALL}")


def print_error(message: str) -> None:
    print(f"{Fore.RED}{message}{Style.RESET_ALL}")
