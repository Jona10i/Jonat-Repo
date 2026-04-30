cd c:\Users\HomePC\Downloads\Documents && python -c "
import re

# Read the file
with open('meeting_assistant_ios26.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find all FONT_DISPLAY, FONT_TEXT, APP_NAME literals
font_display_matches = re.findall(r'FONT_DISPLAY\s*=\s*[^\n]+', content)
font_text_matches = re.findall(r'FONT_TEXT\s*=\s*[^\n]+', content)
app_name_matches = re.findall(r'APP_NAME\s*=\s*[^\n]+', content)

print('FONT_DISPLAY matches:', len(font_display_matches))
print('FONT_TEXT matches:', len(font_text_matches))
print('APP_NAME matches:', len(app_name_matches))

# Find class iOS26Styles
ios_class = re.findall(r'class iOS26Styles', content)
print('iOS26Styles class found:', len(ios_class))

# Find bare except clauses
bare_except = re.findall(r'except:\s*$', content, re.MULTILINE)
print('Bare except clauses:', len(bare_except))

# Find lines with bare except
lines = content.split('\n')
for i, line in enumerate(lines, 1):
    if 'except:' in line and 'Exception' not in line:
        print(f'Line {i}: {line.strip()}')
"