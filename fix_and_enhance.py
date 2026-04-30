#!/usr/bin/env python3
"""Script to fix meeting_assistant.py and add enhancements"""

import re

# Read the file
with open('meeting_assistant.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove duplicate imports (keep first occurrence)
lines = content.split('\n')
clean_lines = []
seen_imports = set()
seen_docstring = False

for line in lines:
    stripped = line.strip()
    
    # Skip duplicate shebang/comments at start
    if stripped == '#!/usr/bin/env python3' and seen_docstring:
        continue
    if stripped.startswith('"""') and seen_docstring:
        # Look for end of docstring
        if stripped.endswith('"""') and len(stripped) > 3:
            continue
    if 'Meeting Assistant - iOS 26 Edition' in stripped and seen_docstring:
        continue
    if stripped == '"""' and seen_docstring:
        continue
    
    # Track imports to avoid duplicates
    if stripped.startswith('import ') or stripped.startswith('from '):
        if stripped in seen_imports:
            continue
        seen_imports.add(stripped)
    
    # Mark when we've seen the docstring
    if 'Meeting Assistant - iOS 26 Edition' in stripped:
        seen_docstring = True
    
    clean_lines.append(line)

# Join cleaned content
cleaned_content = '\n'.join(clean_lines)

# Now add the enhancements

# 1. Add Windows DWM API imports after zeroconf import
dwm_imports = '''from zeroconf import ServiceInfo, Zeroconf, ServiceBrowser

# Windows DWM API for rounded corners (Windows 11 style)
import ctypes
from ctypes import wintypes

# DWM API Constants for rounded window corners
DWMWA_WINDOW_CORNER_PREFERENCE = 33
DWMWCP_DEFAULT = 0
DWMWCP_DONOTROUND = 1
DWMWCP_ROUND = 2
DWMWCP_ROUNDSMALL = 3

def apply_dwm_rounded_corners(hwnd, corner_type=DWMWCP_ROUND):
    """Apply Windows DWM rounded corners to a window"""
    try:
        # Load dwmapi.dll
        dwmapi = ctypes.windll.dwmapi
        
        # Set window corner preference
        corner_preference = ctypes.c_int(corner_type)
        dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_WINDOW_CORNER_PREFERENCE,
            ctypes.byref(corner_preference),
            ctypes.sizeof(corner_preference)
        )
        return True
    except Exception as e:
        print(f"DWM rounded corners not applied: {e}")
        return False
'''

cleaned_content = cleaned_content.replace(
    'from zeroconf import ServiceInfo, Zeroconf, ServiceBrowser\n\n# Audio processing',
    dwm_imports + '\n# Audio processing'
)

# 2. Add MediaStorageManager class after the iOS26Styles class
media_storage_class = '''

class MediaStorageManager:
    """Manages media storage directories for audio files and meeting recordings"""
    
    def __init__(self, base_dir=None):
        """Initialize media storage manager"""
        if base_dir is None:
            base_dir = os.path.join(os.path.expanduser("~"), "Documents", "MeetingAssistant")
        self.base_dir = base_dir
        self.media_dir = os.path.join(base_dir, "media")
        self.audio_dir = os.path.join(self.media_dir, "audio")
        self.recordings_dir = os.path.join(self.media_dir, "recordings")
        self.exports_dir = os.path.join(self.media_dir, "exports")
        self.temp_dir = os.path.join(self.media_dir, "temp")
        
        # Create directories
        self._create_directories()
    
    def _create_directories(self):
        """Create all media directories if they don't exist"""
        dirs = [self.base_dir, self.media_dir, self.audio_dir, 
                self.recordings_dir, self.exports_dir, self.temp_dir]
        for d in dirs:
            os.makedirs(d, exist_ok=True)
    
    def get_audio_path(self, filename):
        """Get path for audio file"""
        return os.path.join(self.audio_dir, filename)
    
    def get_recording_path(self, filename):
        """Get path for recording file"""
        return os.path.join(self.recordings_dir, filename)
    
    def get_export_path(self, filename):
        """Get path for export file"""
        return os.path.join(self.exports_dir, filename)
    
    def get_temp_path(self, filename=None):
        """Get path for temp file"""
        if filename:
            return os.path.join(self.temp_dir, filename)
        return tempfile.mktemp(dir=self.temp_dir)
    
    def save_audio(self, source_path, filename=None):
        """Save audio file to media storage"""
        if filename is None:
            filename = os.path.basename(source_path)
        dest_path = self.get_audio_path(filename)
        shutil.copy2(source_path, dest_path)
        return dest_path
    
    def save_recording(self, source_path, meeting_name=None):
        """Save recording with timestamp"""
        if meeting_name is None:
            meeting_name = f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        filename = f"{meeting_name}.wav"
        dest_path = self.get_recording_path(filename)
        shutil.copy2(source_path, dest_path)
        return dest_path
    
    def list_recordings(self):
        """List all recordings"""
        if os.path.exists(self.recordings_dir):
            return [f for f in os.listdir(self.recordings_dir) if f.endswith('.wav')]
        return []
    
    def list_audio(self):
        """List all audio files"""
        if os.path.exists(self.audio_dir):
            return [f for f in os.listdir(self.audio_dir) 
                   if f.endswith(('.wav', '.mp3', '.m4a', '.flac'))]
        return []
    
    def cleanup_temp(self, max_age_hours=24):
        """Clean up temp files older than specified hours"""
        if not os.path.exists(self.temp_dir):
            return
        now = time.time()
        for f in os.listdir(self.temp_dir):
            path = os.path.join(self.temp_dir, f)
            if os.path.isfile(path):
                age_hours = (now - os.path.getmtime(path)) / 3600
                if age_hours > max_age_hours:
                    try:
                        os.remove(path)
                    except:
                        pass

'''

# Find where to insert MediaStorageManager (after iOS26Styles class)
ios26styles_pattern = r'(class iOS26Styles:.*?)(?=\nclass |\n# |\ndef |\nDEFAULT_FONT_FAMILY)'
match = re.search(ios26styles_pattern, cleaned_content, re.DOTALL)
if match:
    end_pos = match.end()
    cleaned_content = cleaned_content[:end_pos] + media_storage_class + cleaned_content[end_pos:]

# 3. Modify MeetingAssistantApp.__init__ to add DWM rounded corners and media manager
# Find the __init__ method and add our enhancements
init_pattern = r'(def __init__\(self, root\):.*?)(self\._load_config\(\))'

def replace_init(match):
    original = match.group(1)
    # Add media manager initialization
    original = original.replace(
        'self.floating_bubble = None',
        '''self.floating_bubble = None
        
        # Media storage manager
        self.media_manager = MediaStorageManager()'''
    )
    
    # Add DWM rounded corners after window setup
    original = original.replace(
        'self._position_window_right()',
        '''self._position_window_right()
        
        # Apply Windows DWM rounded corners (Windows 11 style)
        self.root.update()
        try:
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            if hwnd:
                apply_dwm_rounded_corners(hwnd, DWMWCP_ROUND)
        except Exception as e:
            print(f"Could not apply rounded corners: {e}")'''
    )
    
    return original + match.group(2)

cleaned_content = re.sub(init_pattern, replace_init, cleaned_content, flags=re.DOTALL)

# 4. Enhance the _build_ios26_peers_section method
old_peers_section = '''    def _build_ios26_peers_section(self):
        """Build iOS 26 style peers section"""
        peers_frame = tk.Frame(self.content_frame, bg=IOS26_COLORS["bg_primary"])
        peers_frame.pack(fill="x", pady=(16, 0))
        
        # Section title
        peers_title = tk.Label(peers_frame, text="Online Users",
                              font=(DEFAULT_FONT_FAMILY, 13, "bold"),
                              bg=IOS26_COLORS["bg_primary"], fg=IOS26_COLORS["text_secondary"])
        peers_title.pack(anchor="w", pady=(0, 8))
        
        # Peers list
        self.peers_listbox = tk.Listbox(peers_frame,
                                       bg=IOS26_COLORS["bg_secondary"],
                                       fg=IOS26_COLORS["text_primary"],
                                       selectbackground=IOS26_COLORS["system_blue"],
                                       selectforeground=IOS26_COLORS["text_primary"],
                                       relief="flat", borderwidth=0,
                                       font=(DEFAULT_FONT_FAMILY, 12),
                                       activestyle="none", highlightthickness=0,
                                       height=4)
        self.peers_listbox.pack(fill="x")
        self.peers_listbox.bind("<<ListboxSelect>>", self._on_peer_select)'''

new_peers_section = '''    def _build_ios26_peers_section(self):
        """Build iOS 26 style peers section with enhanced visual presentation"""
        # Main container with glass effect
        peers_container = tk.Frame(self.content_frame, bg=IOS26_COLORS["bg_primary"])
        peers_container.pack(fill="x", pady=(16, 0))
        
        # Section header with icon
        header_frame = tk.Frame(peers_container, bg=IOS26_COLORS["bg_primary"])
        header_frame.pack(fill="x", pady=(0, 12))
        
        # Online indicator dot
        online_dot = tk.Canvas(header_frame, width=10, height=10, 
                              bg=IOS26_COLORS["bg_primary"], highlightthickness=0)
        online_dot.pack(side="left", padx=(0, 8))
        online_dot.create_oval(2, 2, 8, 8, fill=IOS26_COLORS["system_green"], outline="")
        
        peers_title = tk.Label(header_frame, text="Online Users",
                              font=(DEFAULT_FONT_FAMILY, 14, "bold"),
                              bg=IOS26_COLORS["bg_primary"], fg=IOS26_COLORS["text_primary"])
        peers_title.pack(side="left")
        
        # User count badge
        self.peers_count_label = tk.Label(header_frame, text="0",
                                         font=(DEFAULT_FONT_FAMILY, 11, "bold"),
                                         bg=IOS26_COLORS["bg_tertiary"],
                                         fg=IOS26_COLORS["text_secondary"],
                                         padx=8, pady=2)
        self.peers_count_label.pack(side="right")
        
        # Scrollable frame for peers
        canvas = tk.Canvas(peers_container, bg=IOS26_COLORS["bg_primary"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(peers_container, orient="vertical", command=canvas.yview)
        self.peers_frame = tk.Frame(canvas, bg=IOS26_COLORS["bg_primary"])
        
        self.peers_frame.bind("<Configure>", 
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.peers_frame, anchor="nw", width=360)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Store peer widgets for updates
        self.peer_widgets = {}
        
        # Initial empty state
        self._show_empty_peers_state()
    
    def _show_empty_peers_state(self):
        """Show empty state when no peers online"""
        for widget in self.peers_frame.winfo_children():
            widget.destroy()
        
        empty_label = tk.Label(self.peers_frame, 
                              text="No users online\\nJoin the network to see others",
                              font=(DEFAULT_FONT_FAMILY, 12),
                              bg=IOS26_COLORS["bg_primary"], 
                              fg=IOS26_COLORS["text_tertiary"],
                              justify="center")
        empty_label.pack(pady=20)
    
    def _get_avatar_color(self, name):
        """Generate consistent avatar color from name"""
        colors = [
            IOS26_COLORS["system_blue"],
            IOS26_COLORS["system_green"],
            IOS26_COLORS["system_purple"],
            IOS26_COLORS["system_pink"],
            IOS26_COLORS["system_orange"],
            IOS26_COLORS["system_teal"],
            IOS26_COLORS["system_indigo"],
            IOS26_COLORS["system_red"],
        ]
        hash_val = sum(ord(c) for c in name) if name else 0
        return colors[hash_val % len(colors)]
    
    def _get_initials(self, name):
        """Get initials from name"""
        if not name:
            return "?"
        parts = name.split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[-1][0]).upper()
        return name[:2].upper() if len(name) >= 2 else name.upper()
    
    def _create_peer_widget(self, ip, name):
        """Create a visual peer widget with avatar and status"""
        # Container frame
        peer_frame = tk.Frame(self.peers_frame, bg=IOS26_COLORS["bg_secondary"],
                             padx=12, pady=8)
        peer_frame.pack(fill="x", pady=(0, 4))
        peer_frame.bind("<Button-1>", lambda e, ip=ip: self._select_peer(ip))
        
        # Avatar circle with initials
        avatar_size = 40
        avatar_canvas = tk.Canvas(peer_frame, width=avatar_size, height=avatar_size,
                                 bg=IOS26_COLORS["bg_secondary"], highlightthickness=0,
                                 cursor="hand2")
        avatar_canvas.pack(side="left", padx=(0, 12))
        
        # Draw avatar circle
        avatar_color = self._get_avatar_color(name)
        avatar_canvas.create_oval(2, 2, avatar_size-2, avatar_size-2, 
                                  fill=avatar_color, outline="")
        
        # Add initials
        initials = self._get_initials(name)
        avatar_canvas.create_text(avatar_size//2, avatar_size//2, text=initials,
                                  font=(DEFAULT_FONT_FAMILY, 14, "bold"),
                                  fill=IOS26_COLORS["text_primary"])
        
        # Click handler for avatar
        avatar_canvas.bind("<Button-1>", lambda e, ip=ip: self._select_peer(ip))
        
        # Info container
        info_frame = tk.Frame(peer_frame, bg=IOS26_COLORS["bg_secondary"])
        info_frame.pack(side="left", fill="both", expand=True)
        info_frame.bind("<Button-1>", lambda e, ip=ip: self._select_peer(ip))
        
        # Name label
        name_label = tk.Label(info_frame, text=name,
                             font=(DEFAULT_FONT_FAMILY, 14, "bold"),
                             bg=IOS26_COLORS["bg_secondary"], 
                             fg=IOS26_COLORS["text_primary"],
                             anchor="w", cursor="hand2")
        name_label.pack(fill="x")
        name_label.bind("<Button-1>", lambda e, ip=ip: self._select_peer(ip))
        
        # IP label with online indicator
        ip_frame = tk.Frame(info_frame, bg=IOS26_COLORS["bg_secondary"])
        ip_frame.pack(fill="x")
        
        # Small online dot
        online_canvas = tk.Canvas(ip_frame, width=8, height=8,
                                 bg=IOS26_COLORS["bg_secondary"], highlightthickness=0)
        online_canvas.pack(side="left", padx=(0, 6))
        online_canvas.create_oval(1, 1, 7, 7, fill=IOS26_COLORS["system_green"], outline="")
        
        ip_label = tk.Label(ip_frame, text=ip,
                           font=(DEFAULT_FONT_FAMILY, 11),
                           bg=IOS26_COLORS["bg_secondary"], 
                           fg=IOS26_COLORS["text_secondary"])
        ip_label.pack(side="left")
        
        # Hover effects
        def on_enter(e, f=peer_frame, n=name_label, a=avatar_canvas, i=ip_frame):
            f.configure(bg=IOS26_COLORS["bg_tertiary"])
            n.configure(bg=IOS26_COLORS["bg_tertiary"])
            a.configure(bg=IOS26_COLORS["bg_tertiary"])
            i.configure(bg=IOS26_COLORS["bg_tertiary"])
            for child in i.winfo_children():
                child.configure(bg=IOS26_COLORS["bg_tertiary"])
        
        def on_leave(e, f=peer_frame, n=name_label, a=avatar_canvas, i=ip_frame):
            f.configure(bg=IOS26_COLORS["bg_secondary"])
            n.configure(bg=IOS26_COLORS["bg_secondary"])
            a.configure(bg=IOS26_COLORS["bg_secondary"])
            i.configure(bg=IOS26_COLORS["bg_secondary"])
            for child in i.winfo_children():
                child.configure(bg=IOS26_COLORS["bg_secondary"])
        
        for widget in [peer_frame, name_label, avatar_canvas, info_frame, ip_frame]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
        
        return peer_frame
    
    def _select_peer(self, ip):
        """Select a peer by IP"""
        self.selected_peer_ip = ip
        # Visual feedback
        for widget in self.peers_frame.winfo_children():
            if isinstance(widget, tk.Frame):
                widget.configure(bg=IOS26_COLORS["bg_secondary"])
        # Highlight selected (would need to track widget mapping)
        self.status_label.config(text=f"Selected: {self.peers.get(ip, {}).get('name', ip)}",
                                fg=IOS26_COLORS["system_blue"])
    
    def _on_peer_select(self, event):
        """Handle peer selection from old listbox (kept for compatibility)"""
        pass  # Deprecated, use _select_peer instead'''

cleaned_content = cleaned_content.replace(old_peers_section, new_peers_section)

# 5. Update _update_peers_list to use the new visual widgets
old_update_peers = '''    def _update_peers_list(self):
        """Update peers list periodically"""
        while self.running:
            try:
                with self.peers_lock:
                    peer_list = list(self.peers.items())
                
                # Update UI
                self.root.after(0, self._refresh_peers_display, peer_list)
                
                time.sleep(5)
            except Exception as e:
                self.logger.debug(f"Peers update error: {e}")
    
    def _refresh_peers_display(self, peer_list):
        """Refresh peers display"""
        try:
            if hasattr(self, 'peers_listbox'):
                self.peers_listbox.delete(0, "end")
                for ip, info in peer_list:
                    display = f"{info.get('name', 'Unknown')} ({ip})"
                    self.peers_listbox.insert("end", display)
        except Exception as e:
            self.logger.debug(f"Refresh peers error: {e}")'''

new_update_peers = '''    def _update_peers_list(self):
        """Update peers list periodically"""
        while self.running:
            try:
                with self.peers_lock:
                    peer_list = list(self.peers.items())
                
                # Update UI
                self.root.after(0, self._refresh_peers_display, peer_list)
                
                time.sleep(5)
            except Exception as e:
                self.logger.debug(f"Peers update error: {e}")
    
    def _refresh_peers_display(self, peer_list):
        """Refresh peers display with visual widgets"""
        try:
            if hasattr(self, 'peers_frame'):
                # Clear existing widgets
                for widget in self.peers_frame.winfo_children():
                    widget.destroy()
                
                # Update count
                if hasattr(self, 'peers_count_label'):
                    self.peers_count_label.config(text=str(len(peer_list)))
                
                # Show empty state or peer widgets
                if not peer_list:
                    self._show_empty_peers_state()
                else:
                    for ip, info in peer_list:
                        name = info.get('name', 'Unknown')
                        self._create_peer_widget(ip, name)
                        
        except Exception as e:
            self.logger.debug(f"Refresh peers error: {e}")'''

cleaned_content = cleaned_content.replace(old_update_peers, new_update_peers)

# Write the enhanced file
with open('meeting_assistant.py', 'w', encoding='utf-8') as f:
    f.write(cleaned_content)

print("✅ File enhanced successfully!")
print("\nEnhancements added:")
print("1. Windows DWM API for rounded corners (Windows 11 style)")
print("2. MediaStorageManager class for dedicated media directories")
print("3. Enhanced username listing with avatars and visual presentation")
