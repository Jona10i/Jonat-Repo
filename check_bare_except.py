#!/usr/bin/env python3
"""Check for bare except clauses in meeting_assistant_ios26.py"""

with open('meeting_assistant_ios26.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("Lines with bare except:")
for i, line in enumerate(lines, 1):
    stripped = line.strip()
    if stripped == 'except:' or (stripped.startswith('except') and ':' in stripped and 'Exception' not in stripped):
        print(f"  Line {i}: {repr(line)}")
