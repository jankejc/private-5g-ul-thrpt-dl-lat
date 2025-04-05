import os

# 👇 Change this to whatever prefix you want
PREFIX = "rep_"

# Get current working directory
current_dir = os.getcwd()

# Iterate over items in the directory
for item in os.listdir(current_dir):
    full_path = os.path.join(current_dir, item)

    if os.path.isdir(full_path) and not item.startswith(PREFIX):
        new_name = PREFIX + item
        new_path = os.path.join(current_dir, new_name)

        print(f"Renaming: {item} → {new_name}")
        os.rename(full_path, new_path)
