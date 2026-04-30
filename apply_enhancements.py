#!/usr/bin/env python3
"""Apply enhancements to meeting_assistant.py"""

import os

# Read the file
with open('meeting_assistant.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add DWM API imports after zeroconf import
old_zeroconf = "from zeroconf import ServiceInfo, Zeroconf, ServiceBrowser\n\n# Audio processing"
new_zeroconf = """from zeroconf import ServiceInfo, Zeroconf, ServiceBrowser

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
    \"\"\"Apply Windows DWM rounded corners to a window\"\"\"
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

# Audio processing"""

if old_zeroconf in content:
    content = content.replace(old_zeroconf, new_zeroconf)
    print("Added DWM API imports")
else:
    print("WARNING: Could not find zeroconf import location")

# 2. Add MediaStorageManager class after iOS26Styles class
media_class = '''

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
            meeting_name = f"recording_{datetime.now().strftime(\'%Y%m%d_%H%M%S\')}".replace("\'", "'")
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

# Find the end of iOS26Styles class
ios26_end = '        label.configure(\n            bg=IOS26_COLORS["bg_primary"],\n            fg=color,\n            font=(DEFAULT_FONT_FAMILY, size, weight)\n        )'

if ios26_end in content:
    content = content.replace(ios26_end, ios26_end + '\n' + media_class)
    print("Added MediaStorageManager class")
else:
    print("WARNING: Could not find iOS26Styles class end")

# 3. Add DWM rounded corners call in __init__
old_position = "        self._position_window_right()"
new_position = """        self._position_window_right()
        
        # Apply Windows DWM rounded corners (Windows 11 style)
        self.root.update()
        try:
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            if hwnd:
                apply_dwm_rounded_corners(hwnd, DWMWCP_ROUND)
        except Exception as e:
            print(f"Could not apply rounded corners: {e}")"""

if old_position in content:
    content = content.replace(old_position, new_position)
    print("Added DWM rounded corners call")
else:
    print("WARNING: Could not find _position_window_right")

# 4. Add media_manager initialization
old_floating = "        # Floating bubble\n        self.floating_bubble = None"
new_floating = """        # Floating bubble
        self.floating_bubble = None
        
        # Media storage manager
        self.media_manager = MediaStorageManager()"""

if old_floating in content:
    content = content.replace(old_floating, new_floating)
    print("Added media_manager initialization")
else:
    print("WARNING: Could not find floating_bubble initialization")

# Write the enhanced file
with open('meeting_assistant.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\nEnhancements applied!")
