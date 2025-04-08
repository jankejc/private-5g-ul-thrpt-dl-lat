import os

# Customize your suffix here
SUFFIX = ".log"

def rename_dirs_deep_first(root_path):
    for dirpath, dirnames, _ in os.walk(root_path, topdown=False):  # ⬅️ bottom-up walk
        for dirname in dirnames:
            old_path = os.path.join(dirpath, dirname)
            new_name = dirname + SUFFIX
            new_path = os.path.join(dirpath, new_name)

            # Avoid double-renaming
            if not dirname.endswith(SUFFIX):
                print(f"Renaming: {old_path} → {new_path}")
                os.rename(old_path, new_path)

if __name__ == "__main__":
    base_path = os.getcwd()  # or specify a custom path
    rename_dirs_deep_first(base_path)
