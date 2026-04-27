$path = "c:\Users\HomePC\Downloads\Documents\lan_office-1.py"
$content = Get-Content $path -Raw

# This regex finds the duplicated block that was accidentally inserted
# It starts from the first occurrence of self.dm_clear_btn = tk.Button inside _on_peer_select
# and ends at the next occurrence of def _on_peer_select

# Actually, I'll just restore the known good sections.
# I will use a simpler approach: finding the start and end of the mess.

$cleanStart = $content.IndexOf("    def _on_peer_select(self, event):")
$cleanEnd = $content.LastIndexOf("    def _clear_dm_selection(self):")

if ($cleanStart -gt 0 -and $cleanEnd -gt $cleanStart) {
    $before = $content.Substring(0, $cleanStart)
    $after = $content.Substring($cleanEnd)
    
    # Reconstruct the middle part correctly
    $middle = @"
    def _on_peer_select(self, event):
        sel = self.peers_listbox.curselection()
        if not sel:
            return
        label = self.peers_listbox.get(sel[0])
        # find IP for this label
        with self.peers_lock:
            for ip, info in self.peers.items():
                 display = f"🟢 {info['name']}"
                 if display == label:
                     self.selected_peer_ip = ip
                     self._update_file_button_state()
                     self.chat_title.config(text=f"💬  DM → {info['name']}")
                     self.dm_clear_btn.pack(side="right", pady=6, padx=10)
                     return

"@
    $newContent = $before + $middle + $after
    Set-Content $path $newContent -Encoding UTF8
    Write-Output "File cleaned successfully."
} else {
    Write-Output "Could not find markers for cleaning."
}
