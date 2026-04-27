import os

path = r"c:\Users\HomePC\Downloads\Documents\lan_office-1.py"

with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
method_added = False

for line in lines:
    new_lines.append(line)
    if "def _clear_dm_selection(self):" in line:
        # Find the end of this method
        pass
    
    if "self.dm_clear_btn.pack_forget()" in line and not method_added:
        new_lines.append("\n")
        new_lines.append("    def _update_file_button_state(self):\n")
        new_lines.append("        \"\"\"Enable the file button only when a recipient is selected.\"\"\"\n")
        new_lines.append("        if hasattr(self, 'file_btn'):\n")
        new_lines.append("            if self.selected_peer_ip:\n")
        new_lines.append("                self.file_btn.config(state=\"normal\", cursor=\"hand2\")\n")
        new_lines.append("            else:\n")
        new_lines.append("                self.file_btn.config(state=\"disabled\", cursor=\"\")\n")
        method_added = True

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Method _update_file_button_state added successfully.")
