#!/usr/bin/env python3
"""Final SonarLint fixes for meeting_assistant_ios26.py"""

import re

def main():
    filepath = r'c:\Users\HomePC\Downloads\Documents\meeting_assistant_ios26.py'
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix 1: Add FONT_DISPLAY and FONT_TEXT constants after DEFAULT_FONT_FAMILY
    content = content.replace(
        'DEFAULT_FONT_FAMILY = "Segoe UI"  # Fallback font',
        'DEFAULT_FONT_FAMILY = "Segoe UI"  # Fallback font\nFONT_DISPLAY = ("SF Pro Display", 12)\nFONT_TEXT = ("SF Pro Text", 12)'
    )
    
    # Fix 2: Replace font literals with constants
    # Looking for patterns like ("SF Pro Display", 12) and ("SF Pro Text", 12)
    content = content.replace('("SF Pro Display", 12)', 'FONT_DISPLAY')
    content = content.replace('("SF Pro Text", 12)', 'FONT_TEXT')
    
    # Fix 3: Fix bare except clauses at lines 339, 395, 432
    lines = content.split('\n')
    new_lines = []
    for i, line in enumerate(lines, 1):
        if i in [339, 395, 432] and line.strip() == 'except:':
            new_lines.append(line.replace('except:', 'except Exception:'))
        else:
            new_lines.append(line)
    content = '\n'.join(new_lines)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("All SonarLint fixes applied!")

if __name__ == "__main__":
    main()
