cd c:\Users\HomePC\Downloads\Documents && powershell -Command "
$content = Get-Content meeting_assistant_ios26.py -Raw

# Fix 1: Add FONT_DISPLAY, FONT_TEXT constants after DEFAULT_FONT_FAMILY
$content = $content -replace '(DEFAULT_FONT_FAMILY = \"Segoe UI\"  # Fallback font)', '$1\nFONT_DISPLAY = (\"SF Pro Display\", 12)\nFONT_TEXT = (\"SF Pro Text\", 12)'

# Fix 2: Rename class iOS26Styles to IOS26Styles  
$content = $content -replace 'class iOS26Styles', 'class IOS26Styles'
$content = $content -replace 'iOS26Styles', 'IOS26Styles'

# Fix 3: Replace bare except clauses at lines 337, 393, 430
$lines = $content -split '\n'
for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match '^\s*except:\s*$') {
        # Check if it's one of the target lines
        if (($i+1) -in @(337, 393, 430)) {
            $lines[$i] = $lines[$i] -replace 'except:', 'except Exception:'
        }
    }
}
$content = $lines -join '\n'

# Fix 4: Prefix unused parameters in remove_service
$content = $content -replace 'def remove_service\(self, zc, type, name\):', 'def remove_service(self, _zc, _type, name):'

# Fix 5: Replace tempfile.mktemp with NamedTemporaryFile
$content = $content -replace 'temp_path = tempfile.mktemp\(suffix=\".wav\"\)', "`t`$temp_file = tempfile.NamedTemporaryFile(suffix=`\".wav\"`, delete=False)`n`t`$temp_path = `$temp_file.name`n`t`$temp_file.close()"

# Fix 6: Remove unused app variable in main
$content = $content -replace '^(\s+)app = MeetingAssistantApp\(root\)', '$1MeetingAssistantApp(root)'

Set-Content meeting_assistant_ios26.py $content -Encoding UTF8
Write-Host 'Fixes applied!'"