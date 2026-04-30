#!/usr/bin/env python3
"""
Meeting Assistant - iOS 26 Edition
A beautifully redesigned meeting transcription and analysis tool with:
- iOS 26 design aesthetics (glassmorphism, rounded corners, vibrant colors)
- Compact window mode with right-side positioning
- Floating bubble minimize widget
- Smooth iOS-style animations
- Audio recording and transcription
- Action item extraction
- Key decision identification
- Topic analysis
- Sentiment analysis
- Executive summary generation
- Searchable meeting notes
- File sharing between users
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import socket
import threading
import json
import os
import time
import struct
import hashlib
import logging
import traceback
import queue
import wave
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from zeroconf import ServiceInfo, Zeroconf, ServiceBrowser

# Audio processing
try:
    import sounddevice as sd
    import numpy as np
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    print("Warning: sounddevice not available. Audio recording disabled.")

# Whisper for transcription
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("Warning: whisper not available. Install with: pip install -U openai-whisper")

# NLP libraries
try:
    from transformers import pipeline
    import spacy
    NLP_AVAILABLE = True
except ImportError:
    NLP_AVAILABLE = False
    print("Warning: transformers/spacy not available. NLP features disabled.")

# ---------------------------------------------
#  iOS 26 DESIGN SYSTEM
# ---------------------------------------------

# iOS 26 Color Palette - Vibrant System Colors
IOS26_COLORS = {
    # Backgrounds
    "bg_primary": "#000000",           # Pure black for OLED
    "bg_secondary": "#1C1C1E",         # Dark gray
    "bg_tertiary": "#2C2C2E",          # Lighter gray
    "bg_elevated": "#1C1C1E",          # Elevated surfaces
    
    # Glassmorphism - Translucent layers
    "glass_light": "#FFFFFF",          # White for glass effect
    "glass_dark": "#000000",           # Black for glass effect
    "glass_tint": "#3A3A3C",           # Tint color
    
    # iOS System Colors - Vibrant
    "system_blue": "#0A84FF",          # iOS Blue
    "system_green": "#30D158",         # iOS Green
    "system_indigo": "#5E5CE6",        # iOS Indigo
    "system_orange": "#FF9F0A",        # iOS Orange
    "system_pink": "#FF375F",          # iOS Pink
    "system_purple": "#BF5AF2",        # iOS Purple
    "system_red": "#FF453A",           # iOS Red
    "system_teal": "#64D2FF",          # iOS Teal
    "system_yellow": "#FFD60A",        # iOS Yellow
    "system_mint": "#66D4CF",          # iOS Mint
    "system_cyan": "#5AC8FA",          # iOS Cyan
    
    # Gradients
    "gradient_start": "#5E5CE6",       # Indigo
    "gradient_end": "#BF5AF2",         # Purple
    "accent_gradient": ["#0A84FF", "#5E5CE6", "#BF5AF2"],
    
    # Text
    "text_primary": "#FFFFFF",         # Primary text
    "text_secondary": "#8E8E93",       # Secondary text
    "text_tertiary": "#48484A",        # Tertiary text
    "text_accent": "#0A84FF",          # Accent text
    
    # Surfaces
    "surface": "#1C1C1E",
    "surface_highlight": "#2C2C2E",
    "separator": "#38383A",
    
    # Status
    "success": "#30D158",
    "warning": "#FF9F0A",
    "error": "#FF453A",
    "recording": "#FF375F",
}

# iOS 26 Typography
IOS26_FONTS = {
    "large_title": ("SF Pro Display", 32, "bold"),
    "title1": ("SF Pro Display", 28, "bold"),
    "title2": ("SF Pro Display", 22, "bold"),
    "title3": ("SF Pro Display", 20, "semibold"),
    "headline": ("SF Pro Text", 17, "semibold"),
    "body": ("SF Pro Text", 17, "normal"),
    "callout": ("SF Pro Text", 16, "normal"),
    "subhead": ("SF Pro Text", 15, "normal"),
    "footnote": ("SF Pro Text", 13, "normal"),
    "caption1": ("SF Pro Text", 12, "normal"),
    "caption2": ("SF Pro Text", 11, "normal"),
}

# iOS 26 Dimensions
IOS26_DIMS = {
    "window_width": 420,           # Compact width
    "window_height": 720,          # Compact height
    "corner_radius": 24,           # Large rounded corners
    "corner_radius_sm": 16,        # Small rounded corners
    "corner_radius_xs": 12,        # Extra small rounded corners
    "button_height": 48,           # Standard button height
    "input_height": 44,            # Input field height
    "spacing_xs": 4,
    "spacing_sm": 8,
    "spacing_md": 16,
    "spacing_lg": 24,
    "spacing_xl": 32,
    "bubble_size": 64,             # Floating bubble size
}

# Animation timings (ms)
IOS26_ANIMATION = {
    "fast": 150,
    "normal": 250,
    "slow": 400,
    "spring": 500,
}

DEFAULT_FONT_FAMILY = "Segoe UI"  # Fallback font
BROADCAST_PORT = 55000
CHAT_PORT = 55001
FILE_PORT = 55002
MEETING_PORT = 55003
BROADCAST_INTERVAL = 5
CHAT_HISTORY_FILE = "chat_history.jsonl"
MEETING_HISTORY_FILE = "meeting_history.jsonl"
MAX_HISTORY_LOAD = 100
BUFFER_SIZE = 4096
CONFIG_FILE = "meeting_config.json"
APP_NAME = "Meeting Assistant"
ALL_FILES = "All files"

# Audio config
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_DURATION = 30


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(2)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


class iOS26Styles:
    """iOS 26 Design System Styles"""
    
    @staticmethod
    def apply_rounded_corners(widget, radius=None, bg_color=None):
        """Apply iOS-style rounded corners to a widget"""
        if radius is None:
            radius = IOS26_DIMS["corner_radius"]
        if bg_color is None:
            bg_color = IOS26_COLORS["bg_secondary"]
        
        # Create a canvas with rounded rectangle
