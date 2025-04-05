import os
import re

folder_path = '.'  # ← podaj ścieżkę do folderu z logami jeśli nie w tym samym

for filename in os.listdir(folder_path):
    if not filename.endswith('.log'):
        continue

    if filename.startswith('ping_'):
        continue  # już zmieniony

    # dopasuj np. 20250404-001811_7.log
    match = re.match(r'^(\d{8}-\d+)_([0-9]+)\.log$', filename)
    if match:
        timestamp = match.group(1)
        rep = match.group(2)

        new_filename = f'ping_{timestamp}_rep_{rep}.log'

        old_path = os.path.join(folder_path, filename)
        new_path = os.path.join(folder_path, new_filename)

        print(f'Renaming: {filename} → {new_filename}')
        os.rename(old_path, new_path)
