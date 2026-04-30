cd c:\Users\HomePC\Downloads\Documents && python -c "
import re

# Read file
with open('meeting_assistant_ios26.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Process each line
new_lines = []
for i, line in enumerate(lines, 1):
    new_line = line
    
    # Fix 1: Add FONT_DISPLAY, FONT_TEXT after DEFAULT_FONT_FAMILY (line 157)
    if i == 157 and 'DEFAULT_FONT_FAMILY = \"Segoe UI\"  # Fallback font' in line:
        new_line = line.rstrip() + '\nFONT_DISPLAY = (\"SF Pro Display\", 12)\nFONT_TEXT = (\"SF Pro Text\", 12)\n'
    
    # Fix 2: Rename class iOS26Styles to IOS26Styles (line 189)
    if i == 189 and 'class iOS26Styles' in line:
        new_line = line.replace('class iOS26Styles', 'class IOS26Styles')
    
    # Fix 3: Replace bare except: with except Exception: at lines 337, 393, 430
    if i in [337, 393, 430] and line.strip() == 'except:':
        new_line = line.replace('except:', 'except Exception:')
    
    # Fix 4: Prefix unused parameters zc and type with underscores in remove_service
    if 'def remove_service(self, zc, type, name):' in line:
        new_line = line.replace('def remove_service(self, zc, type, name):', 'def remove_service(self, _zc, _type, name):')
    
    # Fix 5: Replace tempfile.mktemp with NamedTemporaryFile (around line 1265)
    if 'temp_path = tempfile.mktemp(suffix=\".wav\")' in line:
        new_line = '        temp_file = tempfile.NamedTemporaryFile(suffix=\".wav\", delete=False)\n        temp_path = temp_file.name\n        temp_file.close()\n'
    
    # Fix 6: Remove unused app variable in main (around line 1606)
    if i == 1606 and 'app = MeetingAssistantApp(root)' in line:
        new_line = line.replace('app = MeetingAssistantApp(root)', 'MeetingAssistantApp(root)')
    
    new_lines.append(new_line)

# Write back
with open('meeting_assistant_ios26.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('All SonarLint fixes applied!')
"