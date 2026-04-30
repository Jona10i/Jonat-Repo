#!/usr/bin/env python3
"""Update the _update_peers_list method"""

with open('meeting_assistant.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the peers list update logic
old_code = '''                if hasattr(self, 'peers_listbox'):
                    self.peers_listbox.delete(0, "end")
                    for ip, info in peer_list:
                        display = f"�-? {info['name']}"
                        self.peers_listbox.insert("end", display)'''

new_code = '''                # Update UI on main thread with visual widgets
                self.root.after(0, self._refresh_peers_display, peer_list)'''

if old_code in content:
    content = content.replace(old_code, new_code)
    print("Updated _update_peers_list method")
else:
    print("WARNING: Could not find old code pattern")
    # Try with raw bytes
    import re
    pattern = r"if hasattr\(self, 'peers_listbox'\):.*?self\.peers_listbox\.insert\(\"end\", display\)"
    if re.search(pattern, content, re.DOTALL):
        print("Found pattern with regex")

with open('meeting_assistant.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done!")
