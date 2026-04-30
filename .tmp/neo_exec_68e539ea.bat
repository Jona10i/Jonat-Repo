cd c:\Users\HomePC\Downloads\Documents && python -c "
with open('meeting_assistant_ios26.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    if 'except:' in line and 'Exception' not in line:
        print(f'Line {i}: {line.rstrip()}')
"