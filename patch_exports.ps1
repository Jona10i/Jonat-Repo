$path = "c:\Users\HomePC\Downloads\Documents\lan_office-1.py"
$content = Get-Content $path -Raw

# Identify the start of _export_as_text and the end of _export_as_csv
$startIdx = $content.IndexOf("    def _export_as_text(self):")
$endMarker = "    # -----------------------------------------"
$endIdx = $content.IndexOf($endMarker, $startIdx)

if ($startIdx -gt 0 -and $endIdx -gt $startIdx) {
    $before = $content.Substring(0, $startIdx)
    $after = $content.Substring($endIdx)
    
    $newExports = Get-Content "c:\Users\HomePC\Downloads\Documents\restore_exports.py" -Raw
    
    $newContent = $before + $newExports + "`r`n" + $after
    Set-Content $path $newContent -Encoding UTF8
    Write-Output "Exports restored."
} else {
    Write-Output "Markers not found."
}
