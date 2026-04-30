cd c:\Users\HomePC\Downloads\Documents && python -c "
with open('meeting_assistant_ios26.py', 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.split('\n')
    for i in range(min(50, len(lines)):
        print(f'{i+1:4}: {lines[i]}')
"