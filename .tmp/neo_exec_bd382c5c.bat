cd c:\Users\HomePC\Downloads\Documents && python -c "
with open('meeting_assistant_ios26.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Print lines 443-500 (analyze_meeting method)
for i in range(442, min(500, len(lines))):
    print(f'{i+1}: {lines[i]}', end='')
"