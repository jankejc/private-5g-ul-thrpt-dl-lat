import os

# Suffix to add before file extension
SUFFIX = ".log"

def add_suffix_to_files(root_path):
    for dirpath, _, filenames in os.walk(root_path):
        for filename in filenames:
            name, ext = os.path.splitext(filename)

            # Skip already renamed
            if name.endswith(SUFFIX):
                continue

            old_path = os.path.join(dirpath, filename)
            new_filename = name + SUFFIX + ext
            new_path = os.path.join(dirpath, new_filename)

            print(f"Renaming file: {filename} → {new_filename}")
            os.rename(old_path, new_path)

if __name__ == "__main__":
    base_path = os.getcwd()  # Or specify a different root
    add_suffix_to_files(base_path)
