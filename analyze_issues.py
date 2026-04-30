#!/usr/bin/env python3
"""Analyze SonarLint issues in meeting_assistant_ios26.py"""

import re

with open('meeting_assistant_ios26.py', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')

print("=== ANALYSIS RESULTS ===")
print(f"Total lines: {len(lines)}")
print()

# 1. Check for FONT_DISPLAY, FONT_TEXT, APP_NAME literals
font_display_count = content.count('FONT_DISPLAY')
font_text_count = content.count('FONT_TEXT')
app_name_count = content.count('APP_NAME')
print(f"FONT_DISPLAY occurrences: {font_display_count}")
print(f"FONT_TEXT occurrences: {font_text_count}")
print(f"APP_NAME occurrences: {app_name_count}")

# 2. Check for class iOS26Styles
ios_class_count = content.count('class iOS26Styles')
ios_style_count = content.count('iOS26Styles')
print(f"'class iOS26Styles' found: {ios_class_count}")
print(f"'iOS26Styles' total occurrences: {ios_style_count}")

# 3. Find bare except clauses
bare_except_lines = []
for i, line in enumerate(lines, 1):
    if re.match(r'^\s*except:\s*$', line):
        bare_except_lines.append(i)
print(f"Bare except clauses at lines: {bare_except_lines}")

# 4. Check for tempfile.mktemp
tempfile_count = content.count('tempfile.mktemp')
print(f"tempfile.mktemp occurrences: {tempfile_count}")

# 5. Check for unused parameters in remove_service
remove_service_match = re.search(r'def remove_service\(self,\s*(\w+),\s*(\w+),\s*(\w+)\)', content)
if remove_service_match:
    print(f"remove_service params: {remove_service_match.groups()}")

# 6. Check for 'app' variable in main
app_match = re.search(r'app\s*=\s*MeetingAssistantApp\(root\)', content)
print(f"'app' variable assignment found: {app_match is not None}")

print("\n=== END ANALYSIS ===")
