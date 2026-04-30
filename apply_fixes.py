#!/usr/bin/env python3
"""Apply SonarLint fixes to meeting_assistant_ios26.py"""

import re

def main():
    filepath = r'c:\Users\HomePC\Downloads\Documents\meeting_assistant_ios26.py'
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix 1: Add FONT_DISPLAY, FONT_TEXT constants after DEFAULT_FONT_FAMILY
    content = content.replace(
        'DEFAULT_FONT_FAMILY = "Segoe UI"  # Fallback font',
        'DEFAULT_FONT_FAMILY = "Segoe UI"  # Fallback font\nFONT_DISPLAY = ("SF Pro Display", 12)\nFONT_TEXT = ("SF Pro Text", 12)'
    )
    
    # Fix 2: Rename class iOS26Styles to IOS26Styles
    content = content.replace('class iOS26Styles', 'class IOS26Styles')
    
    # Fix 3: Replace bare except: with except Exception: at lines 337, 393, 430
    lines = content.split('\n')
    new_lines = []
    for i, line in enumerate(lines, 1):
        if i in [337, 393, 430] and line.strip() == 'except:':
            new_lines.append(line.replace('except:', 'except Exception:'))
        else:
            new_lines.append(line)
    content = '\n'.join(new_lines)
    
    # Fix 4: Prefix unused parameters zc and type with underscores in remove_service
    content = content.replace(
        'def remove_service(self, zc, type, name):',
        'def remove_service(self, _zc, _type, name):'
    )
    
    # Fix 5: Replace tempfile.mktemp with NamedTemporaryFile (properly indented)
    content = content.replace(
        '        temp_path = tempfile.mktemp(suffix=".wav")',
        '        temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)\n        temp_path = temp_file.name\n        temp_file.close()'
    )
    
    # Fix 6: Remove unused app variable in main()
    content = content.replace(
        '    app = MeetingAssistantApp(root)',
        '    MeetingAssistantApp(root)'
    )
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Fixes applied successfully!")

if __name__ == "__main__":
    main()
