import os

path = r"c:\Users\HomePC\Downloads\Documents\lan_office-1.py"

with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "_update_file_button_state" in line:
        print(f"Line {i+1}: {line.strip()}")
