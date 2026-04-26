import os

path = r"c:\Users\HomePC\Downloads\Documents\lan_office-1.py"

with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    # Replace any line that starts with # and contains multiple box-drawing characters
    if line.strip().startswith('#') and any(c in line for c in '─═'):
        # Replace the box-drawing characters with -
        new_line = line.replace('─', '-').replace('═', '=')
        new_lines.append(new_line)
    else:
        new_lines.append(line)

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("All fancy separators standardized.")
