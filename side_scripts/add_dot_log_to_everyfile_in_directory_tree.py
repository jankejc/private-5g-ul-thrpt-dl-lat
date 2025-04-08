import os

def add_log_suffix_recursively(root_directory):
    for dirpath, dirnames, filenames in os.walk(root_directory):
        for filename in filenames:
            if filename.endswith('.log'):
                continue  # skip if it already ends with .log

            old_path = os.path.join(dirpath, filename)
            new_filename = filename + '.log'
            new_path = os.path.join(dirpath, new_filename)

            os.rename(old_path, new_path)
            print(f"Renamed: {old_path} -> {new_path}")

# Example usage:
# Replace with the path to your root directory
root_dir = "/path/to/dir"
add_log_suffix_recursively(root_dir)
