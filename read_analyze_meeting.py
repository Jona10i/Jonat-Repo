#!/usr/bin/env python3
"""Read and display the analyze_meeting method"""

with open('meeting_assistant_ios26.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find analyze_meeting method
in_method = False
method_lines = []
start_line = None

for i, line in enumerate(lines, 1):
    if 'def analyze_meeting(self, transcript):' in line:
        in_method = True
        start_line = i
        method_lines.append((i, line))
    elif in_method:
        # Check if we've reached the end of the method (next method or class)
        if line.strip() and not line.startswith(' ') and not line.startswith('\t') and not line.startswith('#'):
            if 'def ' in line or 'class ' in line:
                break
        method_lines.append((i, line))

print(f"analyze_meeting method found at line {start_line}")
print(f"Total lines in method: {len(method_lines)}")
print("\n--- Method content ---")
for line_num, line in method_lines[:60]:  # Print first 60 lines
    print(f"{line_num}: {line}", end='')
