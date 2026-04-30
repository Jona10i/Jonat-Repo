cd c:\Users\HomePC\Downloads\Documents && python -c "
import re
with open('meeting_assistant.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the duplicate header pattern
lines = content.split('\n')
unique_lines = []
seen = set()
for line in lines:
    if line not in seen or not line.strip().startswith('import ') and line not in seen:
        unique_lines.append(line)
        seen.add(line)

print(f'Original lines: {len(lines)}')
print(f'Unique lines: {len(unique_lines)}')
"