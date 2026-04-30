cd c:\Users\HomePC\Downloads\Documents && python -c "
with open('meeting_assistant_ios26.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines, 1):
    print(f'{i:4d}: {line}', end='')
"