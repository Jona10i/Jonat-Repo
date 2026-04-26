import os

path = r"c:\Users\HomePC\Downloads\Documents\lan_office-1.py"

with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip_until = -1

for i, line in enumerate(lines):
    if i < skip_until:
        continue
    
    # 1. Define Font Constant
    if "BROADCAST_PORT  = 55000" in line and "DEFAULT_FONT_FAMILY" not in "".join(lines[i-5:i+5]):
        new_lines.append('DEFAULT_FONT_FAMILY = "Segoe UI"\n')
        new_lines.append(line)
        continue

    # 2. Use Font Constant
    if '"Segoe UI"' in line:
        line = line.replace('"Segoe UI"', 'DEFAULT_FONT_FAMILY')

    # 3. Remove old_name
    if "old_name = self.username" in line:
        continue

    # 4. Remove unnecessary list() in _prune_peers
    if "for ip, info in list(self.peers.items()):" in line:
        line = line.replace("list(self.peers.items())", "self.peers.copy().items()")

    new_lines.append(line)

# Complexity fixes (Refactor _listen_presence)
# This is more complex, but I'll skip it for now and just do the simple ones first
# to see if it fixes the linting.

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Simple fixes applied.")
