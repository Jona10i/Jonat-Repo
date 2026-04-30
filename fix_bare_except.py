#!/usr/bin/env python3
"""Fix bare except clauses in meeting_assistant_ios26.py"""

with open('meeting_assistant_ios26.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace bare except: with except Exception:
# Need to be careful to only replace lines that have just "except:"
lines = content.split('\n')
new_lines = []
for line in lines:
    stripped = line.strip()
    if stripped == 'except:':
        new_lines.append(line.replace('except:', 'except Exception:'))
    else:
        new_lines.append(line)

content = '\n'.join(new_lines)

with open('meeting_assistant_ios26.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed bare except clauses!")
