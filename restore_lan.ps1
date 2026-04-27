$path = "c:\Users\HomePC\Downloads\Documents\lan_office-1.py"
$lines = Get-Content $path

$newLines = @()
foreach ($line in $lines) {
    # Fix the 5-space indentation and 1-space indentation errors
    # specifically for the methods that were broken
    if ($line.StartsWith("      @staticmethod")) {
        $newLines += "    @staticmethod"
    } elseif ($line.StartsWith("      def _compute_checksum")) {
        $newLines += "    def _compute_checksum(self, filepath):"
    } elseif ($line.StartsWith("      def _show_progress")) {
        $newLines += "    def _show_progress(self, show=True):"
    } elseif ($line.StartsWith("          ")) {
        # Fix 10-space to 8-space
        $newLines += "        " + $line.TrimStart()
    } else {
        $newLines += $line
    }
}

# If the methods were deleted, I'll re-add them at the correct location
$content = $newLines -join "`r`n"
if ($content -notmatch "_compute_checksum") {
    # Re-insert the missing methods before _start_networking
    $insertionPoint = "    def _start_networking(self):"
    $methods = @"
    @staticmethod
    def _compute_checksum(filepath):
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            while True:
                chunk = f.read(4096)
                if not chunk: break
                sha256.update(chunk)
        return sha256.hexdigest()

    def _show_progress(self, show=True):
        if show:
            self.progress_frame.pack(fill='x', side='bottom')
            self.progress_val.set(0)
            self.cancel_btn.pack(side='right', padx=8)
            self.progress_bar.pack(fill='x', side='left', expand=True)
        else:
            self.cancel_btn.pack_forget()
            self.progress_frame.pack_forget()

"@
    $content = $content.Replace($insertionPoint, $methods + "`r`n" + $insertionPoint)
}

Set-Content $path $content -Encoding UTF8
Write-Output "File restored and indentation fixed."
