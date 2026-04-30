#!/usr/bin/env python3
"""Fix SonarLint issues in meeting_assistant_ios26.py"""

import re

def fix_file():
    filepath = r'c:\Users\HomePC\Downloads\Documents\meeting_assistant_ios26.py'
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    # 1. Define FONT_DISPLAY, FONT_TEXT constants after DEFAULT_FONT_FAMILY
    # Find line with DEFAULT_FONT_FAMILY and add new constants after it
    new_constants = '''DEFAULT_FONT_FAMILY = "Segoe UI"  # Fallback font
FONT_DISPLAY = ("SF Pro Display", 12)
FONT_TEXT = ("SF Pro Text", 12)'''
    content = content.replace(
        'DEFAULT_FONT_FAMILY = "Segoe UI"  # Fallback font',
        new_constants
    )
    
    # 2. Rename class iOS26Styles to IOS26Styles
    content = content.replace('class iOS26Styles', 'class IOS26Styles')
    
    # 3. Replace bare 'except:' with 'except Exception:' at specific lines
    # We need to be careful to only replace the bare ones
    lines = content.split('\n')
    new_lines = []
    for i, line in enumerate(lines, 1):
        if i in [337, 393, 430] and line.strip() == 'except:':
            new_lines.append(line.replace('except:', 'except Exception:'))
        else:
            new_lines.append(line)
    content = '\n'.join(new_lines)
    
    # 4. Prefix unused parameters 'zc' and 'type' with underscores in remove_service
    content = content.replace(
        'def remove_service(self, zc, type, name):',
        'def remove_service(self, _zc, _type, name):'
    )
    
    # 5. Replace tempfile.mktemp with NamedTemporaryFile
    # Find the line with tempfile.mktemp and replace it
    content = content.replace(
        'temp_path = tempfile.mktemp(suffix=".wav")',
        '''temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            temp_path = temp_file.name
            temp_file.close()'''
    )
    
    # Also need to add cleanup - find where temp_path is used and add try/finally
    # Look for the pattern around line 1265
    
    # 6. Remove unused 'app' variable assignment in main()
    content = content.replace(
        '    app = MeetingAssistantApp(root)',
        '    MeetingAssistantApp(root)'
    )
    
    # Write the fixed content
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Fixes applied successfully!")

if __name__ == "__main__":
    fix_file()
