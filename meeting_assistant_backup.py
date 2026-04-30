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
        canvas = tk.Canvas(widget, bg=widget.cget("bg"), highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        
        # Draw rounded rectangle
        width = widget.winfo_width()
        height = widget.winfo_height()
        
        canvas.create_oval(0, 0, radius*2, radius*2, fill=bg_color, outline="")
        canvas.create_oval(width-radius*2, 0, width, radius*2, fill=bg_color, outline="")
        canvas.create_oval(0, height-radius*2, radius*2, height, fill=bg_color, outline="")
        canvas.create_oval(width-radius*2, height-radius*2, width, height, fill=bg_color, outline="")
        canvas.create_rectangle(radius, 0, width-radius, height, fill=bg_color, outline="")
        canvas.create_rectangle(0, radius, width, height-radius, fill=bg_color, outline="")
        
        return canvas
    
    @staticmethod
    def create_glass_frame(parent, bg_alpha=0.8, blur_radius=20):
        """Create a glassmorphism frame"""
        frame = tk.Frame(parent, bg=IOS26_COLORS["bg_secondary"])
        frame.configure(highlightbackground=IOS26_COLORS["separator"], 
                     highlightthickness=1)
        return frame
    
    @staticmethod
    def style_button(button, style="primary", size="regular"):
        """Apply iOS button styles"""
        styles = {
            "primary": {
                "bg": IOS26_COLORS["system_blue"],
                "fg": IOS26_COLORS["text_primary"],
                "activebg": "#0066CC",
            },
            "secondary": {
                "bg": IOS26_COLORS["bg_tertiary"],
                "fg": IOS26_COLORS["text_primary"],
                "activebg": IOS26_COLORS["surface_highlight"],
            },
            "success": {
                "bg": IOS26_COLORS["system_green"],
                "fg": IOS26_COLORS["text_primary"],
                "activebg": "#28B350",
            },
            "danger": {
                "bg": IOS26_COLORS["system_red"],
                "fg": IOS26_COLORS["text_primary"],
                "activebg": "#CC372E",
            },
            "glass": {
                "bg": IOS26_COLORS["bg_tertiary"],
                "fg": IOS26_COLORS["text_primary"],
                "activebg": IOS26_COLORS["surface_highlight"],
            }
        }
        
        s = styles.get(style, styles["primary"])
        
        button.configure(
            bg=s["bg"],
            fg=s["fg"],
            activebackground=s["activebg"],
            activeforeground=s["fg"],
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            cursor="hand2",
            font=(DEFAULT_FONT_FAMILY, 15, "bold" if style == "primary" else "normal")
        )
        
        # Add rounded corners effect
        button.configure(highlightbackground=s["bg"], highlightthickness=0)
    
    @staticmethod
    def style_entry(entry):
        """Apply iOS text input style"""
        entry.configure(
            bg=IOS26_COLORS["bg_tertiary"],
            fg=IOS26_COLORS["text_primary"],
            insertbackground=IOS26_COLORS["system_blue"],
            relief="flat",
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=IOS26_COLORS["separator"],
            highlightcolor=IOS26_COLORS["system_blue"],
            font=(DEFAULT_FONT_FAMILY, 16)
        )
    
    @staticmethod
    def style_label(label, style="body"):
        """Apply iOS label styles"""
        label_styles = {
            "large_title": (IOS26_COLORS["text_primary"], 32, "bold"),
            "title": (IOS26_COLORS["text_primary"], 22, "bold"),
            "headline": (IOS26_COLORS["text_primary"], 17, "semibold"),
            "body": (IOS26_COLORS["text_primary"], 15, "normal"),
            "callout": (IOS26_COLORS["text_secondary"], 14, "normal"),
            "caption": (IOS26_COLORS["text_secondary"], 12, "normal"),
            "accent": (IOS26_COLORS["system_blue"], 15, "semibold"),
        }
        
        color, size, weight = label_styles.get(style, label_styles["body"])
        label.configure(
            bg=IOS26_COLORS["bg_primary"],
            fg=color,
            font=(DEFAULT_FONT_FAMILY, size, weight)
        )


class DiscoveryWorker(threading.Thread):
    """ZeroConf-based service discovery worker"""

    def __init__(self, port, username, peers_lock, peers, logger):
        super().__init__(daemon=True)
        self.port = port
        self.username = username
        self.peers_lock = peers_lock
        self.peers = peers
        self.logger = logger
        self.zc = None
        self.info = None
        self.running = True

    def run(self):
        try:
            self.zc = Zeroconf()
            self.register_me()
            self.browser = ServiceBrowser(self.zc, "_meeting._tcp.local.", self)
            self.logger.info("ZeroConf discovery started")
            while self.running:
                time.sleep(1)
        except Exception as e:
            self.logger.error(f"ZeroConf discovery error: {e}")
        finally:
            if self.zc:
                try:
                    self.zc.close()
                except:
                    pass

    def register_me(self):
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
            self.info = ServiceInfo(
                "_meeting._tcp.local.",
                f"{self.username}._meeting._tcp.local.",
                addresses=[socket.inet_aton(local_ip)],
                port=self.port,
                properties={'version': '1.0', 'ip': local_ip}
            )
            self.zc.register_service(self.info)
            self.logger.info(f"Registered service: {self.username} at {local_ip}:{self.port}")
        except Exception as e:
            self.logger.error(f"Failed to register service: {e}")

    def add_service(self, zc, type, name):
        try:
            info = zc.get_service_info(type, name)
            if info and info.addresses:
                ip = socket.inet_ntoa(info.addresses[0])
                service_name = name.split('.')[0]
                if ip == socket.gethostbyname(socket.gethostname()):
                    return
                with self.peers_lock:
                    if ip not in self.peers:
                        self.peers[ip] = {"name": service_name, "last_seen": time.time()}
                        self.logger.info(f"Discovered peer: {service_name} at {ip}:{info.port}")
        except Exception as e:
            self.logger.debug(f"Error adding service {name}: {e}")

    def update_service(self, zc, type, name):
        self.add_service(zc, type, name)

    def remove_service(self, zc, type, name):
        try:
            service_name = name.split('.')[0]
            with self.peers_lock:
                to_remove = None
                for ip, info in self.peers.items():
                    if info['name'] == service_name:
                        to_remove = ip
                        break
                if to_remove:
                    del self.peers[to_remove]
                    self.logger.info(f"Peer left: {service_name}")
        except Exception as e:
            self.logger.debug(f"Error removing service {name}: {e}")

    def stop(self):
        self.running = False
        if self.zc and self.info:
            try:
                self.zc.unregister_service(self.info)
            except:
                pass


class MeetingAnalyzer:
    """Handles transcription and NLP analysis of meetings"""

    def __init__(self, logger):
        self.logger = logger
        self.whisper_model = None
        self.summarizer = None
        self.sentiment_analyzer = None
        self.nlp = None
        self._load_models()

    def _load_models(self):
        """Load AI models for transcription and analysis"""
        if WHISPER_AVAILABLE:
            try:
                self.logger.info("Loading Whisper model...")
                self.whisper_model = whisper.load_model("base")
                self.logger.info("Whisper model loaded")
            except Exception as e:
                self.logger.error(f"Failed to load Whisper: {e}")

        if NLP_AVAILABLE:
            try:
                self.logger.info("Loading NLP models...")
                self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
                self.sentiment_analyzer = pipeline("sentiment-analysis")
                self.nlp = spacy.load("en_core_web_sm")
                self.logger.info("NLP models loaded")
            except Exception as e:
                self.logger.error(f"Failed to load NLP models: {e}")
                try:
                    os.system("python -m spacy download en_core_web_sm")
                    self.nlp = spacy.load("en_core_web_sm")
                except:
                    pass

    def transcribe_audio(self, audio_path):
        """Transcribe audio file using Whisper"""
        if not self.whisper_model:
            return None, "Whisper not available"
        try:
            result = self.whisper_model.transcribe(audio_path)
            return result["text"], None
        except Exception as e:
            return None, str(e)

    def analyze_meeting(self, transcript):
        """Analyze meeting transcript for insights"""
        analysis = {
            "action_items": [],
            "decisions": [],
            "topics": [],
            "sentiment": None,
            "summary": None,
            "participants": []
        }

        if not transcript or not NLP_AVAILABLE:
            return analysis

        try:
            doc = self.nlp(transcript)
            action_keywords = ["need to", "should", "will", "must", "going to", "plan to", "follow up"]
            for sent in doc.sents:
                sent_text = sent.text.lower()
                if any(keyword in sent_text for keyword in action_keywords):
                    if "?" not in sent.text:
                        analysis["action_items"].append(sent.text.strip())

            decision_keywords = ["decided", "agreed", "conclusion", "resolved", "approved"]
            for sent in doc.sents:
                sent_text = sent.text.lower()
                if any(keyword in sent_text for keyword in decision_keywords):
                    analysis["decisions"].append(sent.text.strip())

            topics = set()
            for ent in doc.ents:
                if ent.label_ in ["ORG", "PRODUCT", "EVENT", "GPE", "WORK_OF_ART"]:
                    topics.add(ent.text)
            for chunk in doc.noun_chunks:
                if len(chunk.text) > 3:
                    topics.add(chunk.text)
            analysis["topics"] = list(topics)[:10]

            chunks = [transcript[i:i+512] for i in range(0, len(transcript), 512)]
            sentiments = []
            for chunk in chunks[:5]:
                result = self.sentiment_analyzer(chunk[:512])[0]
                sentiments.append(result['label'])
            analysis["sentiment"] = max(set(sentiments), key=sentiments.count) if sentiments else "NEUTRAL"

            if len(transcript) > 100:
                summary_input = transcript[:1024]
                summary = self.summarizer(summary_input, max_length=150, min_length=30, do_sample=False)
                analysis["summary"] = summary[0]['summary_text']

            names = set()
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    names.add(ent.text)
            analysis["participants"] = list(names)[:10]

        except Exception as e:
            self.logger.error(f"Analysis error: {e}")

        return analysis


class AudioRecorder:
    """Handles audio recording from microphone"""

    def __init__(self, sample_rate=SAMPLE_RATE, channels=CHANNELS):
        self.sample_rate = sample_rate
        self.channels = channels
        self.recording = False
        self.audio_queue = queue.Queue()
        self.frames = []

    def start_recording(self):
        """Start recording audio"""
        if not AUDIO_AVAILABLE:
            return False
        self.recording = True
        self.frames = []
        self.record_thread = threading.Thread(target=self._record, daemon=True)
        self.record_thread.start()
        return True

    def _record(self):
        """Recording loop"""
        def callback(indata, frames, time_info, status):
            if self.recording:
                self.frames.append(indata.copy())

        with sd.InputStream(samplerate=self.sample_rate, channels=self.channels, callback=callback):
            while self.recording:
                sd.sleep(100)

    def stop_recording(self):
        """Stop recording and return audio data"""
        self.recording = False
        if self.frames:
            return np.concatenate(self.frames, axis=0)
        return None

    def save_to_file(self, audio_data, filepath):
        """Save audio data to WAV file"""
        if audio_data is None:
            return False
        try:
            with wave.open(filepath, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes((audio_data * 32767).astype(np.int16).tobytes())
            return True
        except Exception as e:
            print(f"Error saving audio: {e}")
            return False


class FloatingBubble:
    """iOS 26 Style Floating Bubble for minimized window"""
    
    def __init__(self, app):
        self.app = app
        self.root = tk.Toplevel(app.root)
        self.root.title("")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.95)
        
        # Position at bottom right
        self._position_bubble()
        
        # Create circular bubble
        self._create_bubble_ui()
        
        # Animation state
        self.visible = False
        self.root.withdraw()
        
        # Drag functionality
        self.drag_data = {"x": 0, "y": 0, "dragging": False}
        self._setup_drag()
    
    def _position_bubble(self):
        """Position bubble at bottom right of screen"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        bubble_size = IOS26_DIMS["bubble_size"]
        padding = 20
        
        x = screen_width - bubble_size - padding
        y = screen_height - bubble_size - padding - 40  # Account for taskbar
        
        self.root.geometry(f"{bubble_size}x{bubble_size}+{x}+{y}")
    
    def _create_bubble_ui(self):
        """Create the bubble UI with iOS 26 styling"""
        size = IOS26_DIMS["bubble_size"]
        
        # Main canvas for circular shape
        self.canvas = tk.Canvas(self.root, width=size, height=size, 
                               bg=IOS26_COLORS["bg_primary"], highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        # Create gradient effect (simulated with overlapping circles)
        center = size // 2
        radius = size // 2 - 4
        
        # Outer glow
        self.canvas.create_oval(
            center - radius - 2, center - radius - 2,
            center + radius + 2, center + radius + 2,
            fill=IOS26_COLORS["system_blue"], outline="", tags="glow"
        )
        
        # Main circle with gradient colors
        self.circle = self.canvas.create_oval(
            center - radius, center - radius,
            center + radius, center + radius,
            fill=IOS26_COLORS["system_blue"], outline="",
            tags="bubble"
        )
        
        # Icon (microphone symbol)
        icon_y_offset = -2
        # Mic body
        self.canvas.create_rectangle(
            center - 6, center - 8 + icon_y_offset,
            center + 6, center + 2 + icon_y_offset,
            fill=IOS26_COLORS["text_primary"], outline="", width=0
        )
        # Mic stand
        self.canvas.create_line(
            center, center + 2 + icon_y_offset,
            center, center + 10 + icon_y_offset,
            fill=IOS26_COLORS["text_primary"], width=2
        )
        # Mic base
        self.canvas.create_arc(
            center - 8, center + 6 + icon_y_offset,
            center + 8, center + 16 + icon_y_offset,
            start=0, extent=180, fill="", outline=IOS26_COLORS["text_primary"], width=2
        )
        
        # Bind click to restore
        self.canvas.bind("<Button-1>", self._on_bubble_click)
        self.canvas.bind("<Enter>", self._on_hover_enter)
        self.canvas.bind("<Leave>", self._on_hover_leave)
    
    def _setup_drag(self):
        """Setup drag functionality for the bubble"""
        self.canvas.bind("<ButtonPress-1>", self._start_drag)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._end_drag)
    
    def _start_drag(self, event):
        self.drag_data["x"] = event.x_root - self.root.winfo_x()
        self.drag_data["y"] = event.y_root - self.root.winfo_y()
        self.drag_data["dragging"] = True
    
    def _on_drag(self, event):
        if self.drag_data["dragging"]:
            x = event.x_root - self.drag_data["x"]
            y = event.y_root - self.drag_data["y"]
            self.root.geometry(f"+{x}+{y}")
    
    def _end_drag(self, event):
        self.drag_data["dragging"] = False
        # Check if it was a click (minimal movement)
        if abs(event.x - self.drag_data.get("start_x", event.x)) < 5:
            self._on_bubble_click(event)
    
    def _on_bubble_click(self, event):
        """Handle bubble click - restore main window"""
        self.hide()
        self.app.restore_from_bubble()
    
    def _on_hover_enter(self, event):
        """Hover enter animation"""
        self.canvas.itemconfig("bubble", fill="#0066CC")
        self._animate_scale(1.1)
    
    def _on_hover_leave(self, event):
        """Hover leave animation"""
        self.canvas.itemconfig("bubble", fill=IOS26_COLORS["system_blue"])
        self._animate_scale(1.0)
    
    def _animate_scale(self, target_scale):
        """Simple scale animation"""
        size = IOS26_DIMS["bubble_size"]
        center = size // 2
        base_radius = size // 2 - 4
        new_radius = int(base_radius * target_scale)
        
        self.canvas.coords("bubble",
            center - new_radius, center - new_radius,
            center + new_radius, center + new_radius)
    
    def show(self):
        """Show the bubble with animation"""
        self.visible = True
        self.root.deiconify()
        self._position_bubble()
        self._fade_in()
    
    def hide(self):
        """Hide the bubble"""
        self.visible = False
        self.root.withdraw()
    
    def _fade_in(self):
        """Fade in animation"""
        alpha = 0.0
        def fade():
            nonlocal alpha
            alpha += 0.1
            if alpha <= 0.95:
                self.root.attributes("-alpha", alpha)
                self.root.after(20, fade)
        fade()
    
    def destroy(self):
        """Destroy the bubble window"""
        self.root.destroy()


class MeetingAssistantApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        
        # iOS 26 Compact Window Setup
        self.window_width = IOS26_DIMS["window_width"]
        self.window_height = IOS26_DIMS["window_height"]
        self.is_compact = True
        self.is_minimized = False
        
        # Position on right side of screen
        self._position_window_right()
        
        # iOS 26 Styling
        self.root.configure(bg=IOS26_COLORS["bg_primary"])
        self.root.attributes("-alpha", 0.98)
        
        # Remove default window decorations for custom styling
        self.root.overrideredirect(False)
        
        self.local_ip = get_local_ip()
        self.logger = self._setup_logging()

        # Networking
        self.peers = {}
        self.peers_lock = threading.Lock()
        self.discovery_worker = None
        self.running = False
        self.selected_peer_ip = None

        # Meeting components
        self.analyzer = MeetingAnalyzer(self.logger)
        self.recorder = AudioRecorder()
        self.is_recording = False
        self.current_meeting = None
        self.meetings = []

        # Floating bubble
        self.floating_bubble = None

        # Load config and build UI
        self._load_config()
        self._build_ios26_ui()

    def _position_window_right(self):
        """Position window on right side of screen"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate position (right side with padding)
        x = screen_width - self.window_width - 20
        y = (screen_height - self.window_height) // 2
        
        self.root.geometry(f"{self.window_width}x{self.window_height}+{x}+{y}")

    def _setup_logging(self):
        logger = logging.getLogger(f"MeetingAssistant-{self.local_ip}")
        logger.setLevel(logging.DEBUG)

        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(ch_formatter)

        fh = logging.FileHandler('meeting_assistant.log', encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        fh_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(fh_formatter)

        logger.addHandler(ch)
        logger.addHandler(fh)
        return logger

    def _load_config(self):
        self.config = {
            "username": "",
            "download_dir": os.path.expanduser("~/Downloads"),
            "broadcast_port": BROADCAST_PORT,
            "chat_port": CHAT_PORT,
            "file_port": FILE_PORT,
            "meeting_port": MEETING_PORT
        }
        self.username = ""
        self.download_dir = self.config["download_dir"]

        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    loaded = json.load(f)
                    self.config.update(loaded)
                    self.username = self.config.get("username", "")
                    self.download_dir = self.config.get("download_dir", self.download_dir)
            except Exception:
                pass

    def _save_config(self):
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config, f)
        except Exception:
            pass

    def _build_ios26_ui(self):
        """Build iOS 26 styled UI"""
        # Main container with rounded corners feel
        self.main_container = tk.Frame(self.root, bg=IOS26_COLORS["bg_primary"])
        self.main_container.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Custom title bar
        self._build_title_bar()
        
        # Content area
        self.content_frame = tk.Frame(self.main_container, bg=IOS26_COLORS["bg_primary"])
        self.content_frame.pack(fill="both", expand=True, padx=16, pady=8)
        
        if not self.username:
            self._build_ios26_login()
        else:
            self._build_ios26_main_content()
            self._start_networking()

    def _build_title_bar(self):
        """Build iOS 26 style title bar with minimize button"""
        title_bar = tk.Frame(self.main_container, bg=IOS26_COLORS["bg_primary"], height=44)
        title_bar.pack(fill="x", padx=0, pady=0)
        title_bar.pack_propagate(False)
        
        # Title
        title_label = tk.Label(title_bar, text="Meeting Assistant", 
                              font=(DEFAULT_FONT_FAMILY, 16, "bold"),
                              bg=IOS26_COLORS["bg_primary"], 
                              fg=IOS26_COLORS["text_primary"])
        title_label.pack(side="left", padx=16, pady=8)
        
        # Control buttons frame
        controls = tk.Frame(title_bar, bg=IOS26_COLORS["bg_primary"])
        controls.pack(side="right", padx=8)
        
        # Minimize to bubble button
        self.minimize_btn = tk.Button(controls, text="−", 
                                     font=(DEFAULT_FONT_FAMILY, 18, "bold"),
                                     bg=IOS26_COLORS["bg_primary"],
                                     fg=IOS26_COLORS["text_secondary"],
                                     relief="flat", borderwidth=0,
                                     cursor="hand2", command=self._minimize_to_bubble)
        self.minimize_btn.pack(side="left", padx=4)
        
        # Close button
        close_btn = tk.Button(controls, text="×", 
                             font=(DEFAULT_FONT_FAMILY, 20, "bold"),
                             bg=IOS26_COLORS["bg_primary"],
                             fg=IOS26_COLORS["system_red"],
                             relief="flat", borderwidth=0,
                             cursor="hand2", command=self.root.quit)
        close_btn.pack(side="left", padx=4)

    def _build_ios26_login(self):
        """Build iOS 26 style login screen"""
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Center container
        login_container = tk.Frame(self.content_frame, bg=IOS26_COLORS["bg_primary"])
        login_container.place(relx=0.5, rely=0.4, anchor="center")
        
        # App icon (gradient circle)
        icon_canvas = tk.Canvas(login_container, width=80, height=80,
                               bg=IOS26_COLORS["bg_primary"], highlightthickness=0)
        icon_canvas.pack(pady=(0, 24))
        
        # Gradient circle
        icon_canvas.create_oval(4, 4, 76, 76, fill=IOS26_COLORS["system_blue"], outline="")
        icon_canvas.create_text(40, 40, text="◉", font=(DEFAULT_FONT_FAMILY, 32),
                               fill=IOS26_COLORS["text_primary"])
        
        # Title
        title = tk.Label(login_container, text="Meeting Assistant",
                        font=(DEFAULT_FONT_FAMILY, 24, "bold"),
                        bg=IOS26_COLORS["bg_primary"], fg=IOS26_COLORS["text_primary"])
        title.pack(pady=(0, 8))
        
        # Subtitle
        subtitle = tk.Label(login_container, text="AI-Powered Transcription",
                           font=(DEFAULT_FONT_FAMILY, 14),
                           bg=IOS26_COLORS["bg_primary"], fg=IOS26_COLORS["text_secondary"])
        subtitle.pack(pady=(0, 32))
        
        # Input container with glass effect
        input_frame = tk.Frame(login_container, bg=IOS26_COLORS["bg_secondary"],
                            highlightbackground=IOS26_COLORS["separator"],
                            highlightthickness=1)
        input_frame.pack(fill="x", pady=(0, 16))
        
        # Name label
        name_label = tk.Label(input_frame, text="Your Name",
                             font=(DEFAULT_FONT_FAMILY, 12),
                             bg=IOS26_COLORS["bg_secondary"], fg=IOS26_COLORS["text_secondary"])
        name_label.pack(anchor="w", padx=12, pady=(12, 4))
        
        # Name entry
        self.name_entry = tk.Entry(input_frame, font=(DEFAULT_FONT_FAMILY, 16),
                                  bg=IOS26_COLORS["bg_tertiary"],
                                  fg=IOS26_COLORS["text_primary"],
                                  insertbackground=IOS26_COLORS["system_blue"],
                                  relief="flat", borderwidth=0)
        self.name_entry.pack(fill="x", padx=12, pady=(4, 12), ipady=8)
        if self.username:
            self.name_entry.insert(0, self.username)
        
        # Join button with iOS style
        join_btn = tk.Button(login_container, text="Get Started",
                            font=(DEFAULT_FONT_FAMILY, 17, "bold"),
                            bg=IOS26_COLORS["system_blue"],
                            fg=IOS26_COLORS["text_primary"],
                            relief="flat", borderwidth=0,
                            cursor="hand2", command=self._start_app)
        join_btn.pack(fill="x", pady=(8, 0), ipady=12)
        
        # IP address display
        ip_label = tk.Label(login_container, text=f"Your IP: {self.local_ip}",
                           font=(DEFAULT_FONT_FAMILY, 11),
                           bg=IOS26_COLORS["bg_primary"], fg=IOS26_COLORS["text_tertiary"])
        ip_label.pack(pady=(16, 0))

    def _build_ios26_main_content(self):
        """Build iOS 26 style main content"""
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Header with user info
        header = tk.Frame(self.content_frame, bg=IOS26_COLORS["bg_primary"])
        header.pack(fill="x", pady=(0, 16))
        
        # Welcome text
        welcome = tk.Label(header, text=f"Welcome, {self.username}",
                          font=(DEFAULT_FONT_FAMILY, 20, "bold"),
                          bg=IOS26_COLORS["bg_primary"], fg=IOS26_COLORS["text_primary"])
        welcome.pack(anchor="w")
        
        # Status
        self.status_label = tk.Label(header, text="Ready to record",
                                      font=(DEFAULT_FONT_FAMILY, 13),
                                      bg=IOS26_COLORS["bg_primary"], fg=IOS26_COLORS["text_secondary"])
        self.status_label.pack(anchor="w", pady=(4, 0))
        
        # Main action button (Record)
        self.record_btn = tk.Button(self.content_frame, text="● Start Recording",
                                   font=(DEFAULT_FONT_FAMILY, 17, "bold"),
                                   bg=IOS26_COLORS["system_red"],
                                   fg=IOS26_COLORS["text_primary"],
                                   relief="flat", borderwidth=0,
                                   cursor="hand2", command=self._toggle_recording)
        self.record_btn.pack(fill="x", pady=(16, 8), ipady=16)
        
        # Secondary actions
        actions_frame = tk.Frame(self.content_frame, bg=IOS26_COLORS["bg_primary"])
        actions_frame.pack(fill="x", pady=(0, 16))
        
        # Upload button
        upload_btn = tk.Button(actions_frame, text="Upload Audio",
                              font=(DEFAULT_FONT_FAMILY, 15),
                              bg=IOS26_COLORS["bg_secondary"],
                              fg=IOS26_COLORS["text_primary"],
                              relief="flat", borderwidth=0,
                              cursor="hand2", command=self._upload_audio)
        upload_btn.pack(fill="x", pady=(0, 8), ipady=12)
        
        # Share button
        share_btn = tk.Button(actions_frame, text="Share Meeting",
                             font=(DEFAULT_FONT_FAMILY, 15),
                             bg=IOS26_COLORS["bg_secondary"],
                             fg=IOS26_COLORS["text_primary"],
                             relief="flat", borderwidth=0,
                             cursor="hand2", command=self._share_meeting)
        share_btn.pack(fill="x", ipady=12)
        
        # Content tabs
        self._build_ios26_tabs()
        
        # Peers section
        self._build_ios26_peers_section()

    def _build_ios26_tabs(self):
        """Build iOS 26 style tabs"""
        # Tab container
        tabs_frame = tk.Frame(self.content_frame, bg=IOS26_COLORS["bg_primary"])
        tabs_frame.pack(fill="both", expand=True, pady=(16, 0))
        
        # Tab buttons
        tab_buttons = tk.Frame(tabs_frame, bg=IOS26_COLORS["bg_primary"])
        tab_buttons.pack(fill="x", pady=(0, 8))
        
        self.current_tab = "transcription"
        
        self.transcription_tab_btn = tk.Button(tab_buttons, text="Transcript",
                                              font=(DEFAULT_FONT_FAMILY, 13, "bold"),
                                              bg=IOS26_COLORS["system_blue"],
                                              fg=IOS26_COLORS["text_primary"],
                                              relief="flat", borderwidth=0,
                                              cursor="hand2",
                                              command=lambda: self._switch_tab("transcription"))
        self.transcription_tab_btn.pack(side="left", expand=True, fill="x", ipady=8)
        
        self.analysis_tab_btn = tk.Button(tab_buttons, text="Analysis",
                                         font=(DEFAULT_FONT_FAMILY, 13),
                                         bg=IOS26_COLORS["bg_secondary"],
                                         fg=IOS26_COLORS["text_secondary"],
                                         relief="flat", borderwidth=0,
                                         cursor="hand2",
                                         command=lambda: self._switch_tab("analysis"))
        self.analysis_tab_btn.pack(side="left", expand=True, fill="x", ipady=8)
        
        self.history_tab_btn = tk.Button(tab_buttons, text="History",
                                        font=(DEFAULT_FONT_FAMILY, 13),
                                        bg=IOS26_COLORS["bg_secondary"],
                                        fg=IOS26_COLORS["text_secondary"],
                                        relief="flat", borderwidth=0,
                                        cursor="hand2",
                                        command=lambda: self._switch_tab("history"))
        self.history_tab_btn.pack(side="left", expand=True, fill="x", ipady=8)
        
        # Tab content
        self.tab_content = tk.Frame(tabs_frame, bg=IOS26_COLORS["bg_secondary"])
        self.tab_content.pack(fill="both", expand=True)
        
        # Build initial tab content
        self._build_transcription_tab()

    def _build_transcription_tab(self):
        """Build transcription tab content"""
        for widget in self.tab_content.winfo_children():
            widget.destroy()
        
        self.transcription_text = scrolledtext.ScrolledText(
            self.tab_content, state="disabled",
            bg=IOS26_COLORS["bg_secondary"],
            fg=IOS26_COLORS["text_primary"],
            font=(DEFAULT_FONT_FAMILY, 12),
            relief="flat", padx=12, pady=8, wrap="word",
            highlightthickness=0
        )
        self.transcription_text.pack(fill="both", expand=True)

    def _build_analysis_tab(self):
        """Build analysis tab content"""
        for widget in self.tab_content.winfo_children():
            widget.destroy()
        
        # Scrollable frame for analysis
        canvas = tk.Canvas(self.tab_content, bg=IOS26_COLORS["bg_secondary"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.tab_content, orient="vertical", command=canvas.yview)
        self.analysis_content = tk.Frame(canvas, bg=IOS26_COLORS["bg_secondary"])
        
        self.analysis_content.bind("<Configure>", 
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.analysis_content, anchor="nw", width=360)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Analysis sections
        sections = [
            ("Summary", "summary_text"),
            ("Action Items", "action_items"),
            ("Decisions", "decisions"),
            ("Topics", "topics"),
            ("Participants", "participants"),
            ("Sentiment", "sentiment")
        ]
        
        for title, attr_name in sections:
            section_frame = tk.Frame(self.analysis_content, bg=IOS26_COLORS["bg_tertiary"],
                                    padx=12, pady=12)
            section_frame.pack(fill="x", padx=8, pady=4)
            
            title_label = tk.Label(section_frame, text=title,
                                  font=(DEFAULT_FONT_FAMILY, 13, "bold"),
                                  bg=IOS26_COLORS["bg_tertiary"],
                                  fg=IOS26_COLORS["system_blue"])
            title_label.pack(anchor="w")
            
            text_widget = tk.Text(section_frame, height=3,
                                 bg=IOS26_COLORS["bg_tertiary"],
                                 fg=IOS26_COLORS["text_primary"],
                                 font=(DEFAULT_FONT_FAMILY, 11),
                                 relief="flat", state="disabled",
                                 wrap="word")
            text_widget.pack(fill="x", pady=(8, 0))
            setattr(self, f"{attr_name}_widget", text_widget)

    def _build_history_tab(self):
        """Build history tab content"""
        for widget in self.tab_content.winfo_children():
            widget.destroy()
        
        # Toolbar
        toolbar = tk.Frame(self.tab_content, bg=IOS26_COLORS["bg_secondary"])
        toolbar.pack(fill="x", pady=(0, 8))
        
        refresh_btn = tk.Button(toolbar, text="Refresh",
                               font=(DEFAULT_FONT_FAMILY, 11),
                               bg=IOS26_COLORS["bg_tertiary"],
                               fg=IOS26_COLORS["text_primary"],
                               relief="flat", borderwidth=0,
                               cursor="hand2", command=self._load_meeting_history)
        refresh_btn.pack(side="left", padx=4, pady=4)
        
        export_btn = tk.Button(toolbar, text="Export",
                              font=(DEFAULT_FONT_FAMILY, 11),
                              bg=IOS26_COLORS["bg_tertiary"],
                              fg=IOS26_COLORS["text_primary"],
                              relief="flat", borderwidth=0,
                              cursor="hand2", command=self._export_all_meetings)
        export_btn.pack(side="left", padx=4, pady=4)
        
        # History list
        self.history_list = tk.Listbox(self.tab_content,
                                      bg=IOS26_COLORS["bg_secondary"],
                                      fg=IOS26_COLORS["text_primary"],
                                      selectbackground=IOS26_COLORS["system_blue"],
                                      selectforeground=IOS26_COLORS["text_primary"],
                                      relief="flat", borderwidth=0,
                                      font=(DEFAULT_FONT_FAMILY, 12),
                                      activestyle="none", highlightthickness=0)
        self.history_list.pack(fill="both", expand=True)
        self.history_list.bind("<<ListboxSelect>>", self._on_history_select)
        
        self._load_meeting_history()

    def _build_ios26_peers_section(self):
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
        self.peers_listbox.bind("<<ListboxSelect>>", self._on_peer_select)

    def _switch_tab(self, tab_name):
        """Switch between tabs with animation"""
        # Update button styles
        buttons = {
            "transcription": self.transcription_tab_btn,
            "analysis": self.analysis_tab_btn,
            "history": self.history_tab_btn
        }
        
        for name, btn in buttons.items():
            if name == tab_name:
                btn.configure(bg=IOS26_COLORS["system_blue"],
                            fg=IOS26_COLORS["text_primary"],
                            font=(DEFAULT_FONT_FAMILY, 13, "bold"))
            else:
                btn.configure(bg=IOS26_COLORS["bg_secondary"],
                            fg=IOS26_COLORS["text_secondary"],
                            font=(DEFAULT_FONT_FAMILY, 13))
        
        # Build tab content
        if tab_name == "transcription":
            self._build_transcription_tab()
        elif tab_name == "analysis":
            self._build_analysis_tab()
        elif tab_name == "history":
            self._build_history_tab()
        
        self.current_tab = tab_name

    def _minimize_to_bubble(self):
        """Minimize window to floating bubble"""
        self.is_minimized = True
        self.root.withdraw()
        
        if not self.floating_bubble:
            self.floating_bubble = FloatingBubble(self)
        
        self.floating_bubble.show()

    def restore_from_bubble(self):
        """Restore window from floating bubble"""
        self.is_minimized = False
        self.root.deiconify()
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.after(100, lambda: self.root.attributes("-topmost", False))

    def _start_app(self):
        """Start the app after login"""
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Name required", "Please enter a display name.")
            return
        self.username = name
        self.config["username"] = name
        self._save_config()
        self._build_ios26_main_content()
        self._start_networking()

    def _toggle_recording(self):
        """Toggle audio recording"""
        if not AUDIO_AVAILABLE:
            messagebox.showerror("Audio Error", "Audio recording not available. Install sounddevice.")
            return

        if not self.is_recording:
            if self.recorder.start_recording():
                self.is_recording = True
                self.record_btn.config(text="■ Stop Recording", bg=IOS26_COLORS["system_green"])
                self.status_label.config(text="Recording...", fg=IOS26_COLORS["system_red"])
        else:
            audio_data = self.recorder.stop_recording()
            self.is_recording = False
            self.record_btn.config(text="● Start Recording", bg=IOS26_COLORS["system_red"])
            self.status_label.config(text="Processing...", fg=IOS26_COLORS["system_blue"])
            self._process_recorded_audio(audio_data)

    def _process_recorded_audio(self, audio_data):
        """Process recorded audio"""
        if audio_data is None:
            return
        temp_path = tempfile.mktemp(suffix=".wav")
        if self.recorder.save_to_file(audio_data, temp_path):
            self._transcribe_and_analyze(temp_path)
            os.remove(temp_path)

    def _upload_audio(self):
        """Upload audio file"""
        path = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[("Audio files", "*.wav *.mp3 *.m4a *.flac"), (ALL_FILES, "*.*")]
        )
        if path:
            self._transcribe_and_analyze(path)

    def _transcribe_and_analyze(self, audio_path):
        """Transcribe and analyze audio"""
        self.status_label.config(text="Transcribing...")
        self.root.update()

        transcript, error = self.analyzer.transcribe_audio(audio_path)
        if error:
            messagebox.showerror("Transcription Error", f"Failed to transcribe: {error}")
            self.status_label.config(text="Ready", fg=IOS26_COLORS["text_secondary"])
            return

        self._update_transcription(transcript)

        self.status_label.config(text="Analyzing...")
        self.root.update()

        analysis = self.analyzer.analyze_meeting(transcript)
        self._update_analysis(analysis)

        meeting_data = {
            "timestamp": time.time(),
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "transcript": transcript,
            "analysis": analysis
        }
        self.current_meeting = meeting_data
        self.meetings.append(meeting_data)
        self._save_meeting(meeting_data)
        self._load_meeting_history()

        self.status_label.config(text="Analysis complete", fg=IOS26_COLORS["system_green"])

    def _update_transcription(self, text):
        """Update transcription display"""
        self.transcription_text.config(state="normal")
        self.transcription_text.delete(1.0, "end")
        self.transcription_text.insert("end", text)
        self.transcription_text.config(state="disabled")

    def _update_analysis(self, analysis):
        """Update analysis display"""
        widgets = [
            ("summary_text", analysis.get("summary", "No summary available.")),
            ("action_items", "\n".join(f"• {item}" for item in analysis.get("action_items", [])) or "No action items."),
            ("decisions", "\n".join(f"• {dec}" for dec in analysis.get("decisions", [])) or "No decisions."),
            ("topics", ", ".join(analysis.get("topics", [])) or "No topics."),
            ("participants", ", ".join(analysis.get("participants", [])) or "No participants."),
            ("sentiment", analysis.get("sentiment", "Unknown"))
        ]

        for attr_name, content in widgets:
            widget = getattr(self, f"{attr_name}_widget", None)
            if widget:
                widget.config(state="normal")
                widget.delete(1.0, "end")
                widget.insert("end", content)
                widget.config(state="disabled")

    def _save_meeting(self, meeting_data):
        """Save meeting to history"""
        try:
            with open(MEETING_HISTORY_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(meeting_data) + "\n")
        except Exception as e:
            self.logger.error(f"Failed to save meeting: {e}")

    def _load_meeting_history(self):
        """Load meeting history"""
        self.meetings = []
        if hasattr(self, 'history_list'):
            self.history_list.delete(0, "end")

        if os.path.exists(MEETING_HISTORY_FILE):
            try:
                with open(MEETING_HISTORY_FILE, "r", encoding="utf-8") as f:
                    for line in f:
                        meeting = json.loads(line.strip())
                        self.meetings.append(meeting)
                        if hasattr(self, 'history_list'):
                            display = f"{meeting['datetime']}"
                            self.history_list.insert("end", display)
            except Exception as e:
                self.logger.error(f"Failed to load history: {e}")

    def _on_history_select(self, event):
        """Handle history selection"""
        sel = self.history_list.curselection()
        if sel:
            meeting = self.meetings[sel[0]]
            self._update_transcription(meeting.get("transcript", ""))
            self._update_analysis(meeting.get("analysis", {}))
            self._switch_tab("transcription")

    def _export_all_meetings(self):
        """Export all meetings"""
        if not self.meetings:
            messagebox.showinfo("No Meetings", "No meetings to export.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump({"meetings": self.meetings}, f, indent=2)
                messagebox.showinfo("Export Successful", f"Exported {len(self.meetings)} meetings.")
            except Exception as e:
                messagebox.showerror("Export Error", str(e))

    def _share_meeting(self):
        """Share current meeting"""
        if not self.current_meeting and not self.meetings:
            messagebox.showinfo("No Meeting", "No meeting to share.")
            return

        if not self.selected_peer_ip:
            messagebox.showinfo("Select User", "Please select a user from the list.")
            return

        meeting = self.current_meeting or self.meetings[-1]
        self._send_meeting_to_peer(self.selected_peer_ip, meeting)

    def _send_meeting_to_peer(self, ip, meeting_data):
        """Send meeting to peer"""
        try:
            payload = json.dumps({
                "type": "meeting",
                "data": meeting_data,
                "sender": self.username
            }).encode()

            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10)
            s.connect((ip, MEETING_PORT))
            s.sendall(struct.pack("!I", len(payload)) + payload)
            s.close()

            self.status_label.config(text=f"Shared with {self.peers.get(ip, {}).get('name', ip)}",
                                    fg=IOS26_COLORS["system_green"])
        except Exception as e:
            self.status_label.config(text=f"Share failed: {e}", fg=IOS26_COLORS["system_red"])

    def _start_networking(self):
        """Start networking"""
        if self.running:
            return

        self.running = True
        self.discovery_worker = DiscoveryWorker(
            self.config["meeting_port"], self.username, self.peers_lock, self.peers, self.logger
        )
        self.discovery_worker.start()

        threading.Thread(target=self._chat_listener, daemon=True).start()
        threading.Thread(target=self._file_listener, daemon=True).start()
        threading.Thread(target=self._meeting_listener, daemon=True).start()
        threading.Thread(target=self._update_peers_list, daemon=True).start()

        self.logger.info("Networking started")

    def _chat_listener(self):
        """Listen for chat"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("0.0.0.0", self.config["chat_port"]))
            sock.listen(5)

            while self.running:
                conn, addr = sock.accept()
                threading.Thread(target=self._handle_chat, args=(conn, addr), daemon=True).start()
        except Exception as e:
            self.logger.error(f"Chat listener error: {e}")

    def _handle_chat(self, conn, addr):
        """Handle chat message"""
        try:
            conn.settimeout(10)
            size_data = conn.recv(4)
            if not size_data:
                return
            size = struct.unpack("!I", size_data)[0]
            data = conn.recv(size)
            msg = json.loads(data.decode())

            if msg.get("type") == "chat":
                self.root.after(0, self._show_chat_notification, 
                               msg.get("name", "Unknown"), msg.get("text", ""))
        except Exception as e:
            self.logger.debug(f"Chat handler error: {e}")
        finally:
            conn.close()

    def _show_chat_notification(self, name, text):
        """Show chat notification"""
        self.status_label.config(text=f"Message from {name}: {text[:30]}...",
                                fg=IOS26_COLORS["system_blue"])

    def _file_listener(self):
        """Listen for files"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("0.0.0.0", self.config["file_port"]))
            sock.listen(5)

            while self.running:
                conn, addr = sock.accept()
                threading.Thread(target=self._handle_file, args=(conn, addr), daemon=True).start()
        except Exception as e:
            self.logger.error(f"File listener error: {e}")

    def _handle_file(self, conn, addr):
        """Handle incoming file"""
        try:
            conn.settimeout(30)
            size_data = conn.recv(4)
            if not size_data:
                return
            size = struct.unpack("!I", size_data)[0]
            meta_data = conn.recv(size)
            meta = json.loads(meta_data.decode())

            filename = meta.get("filename", "unknown")
            filesize = meta.get("filesize", 0)
            sender = meta.get("sender", "Unknown")

            filepath = os.path.join(self.download_dir, filename)
            received = 0
            with open(filepath, "wb") as f:
                while received < filesize:
                    chunk = conn.recv(min(BUFFER_SIZE, filesize - received))
                    if not chunk:
                        break
                    f.write(chunk)
                    received += len(chunk)

            self.root.after(0, self._show_file_notification, filename, sender)
        except Exception as e:
            self.logger.error(f"File receive error: {e}")
        finally:
            conn.close()

    def _show_file_notification(self, filename, sender):
        """Show file received notification"""
        self.status_label.config(text=f"Received '{filename}' from {sender}",
                                fg=IOS26_COLORS["system_green"])

    def _meeting_listener(self):
        """Listen for shared meetings"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("0.0.0.0", MEETING_PORT))
            sock.listen(5)

            while self.running:
                conn, addr = sock.accept()
                threading.Thread(target=self._handle_meeting_share, args=(conn, addr), daemon=True).start()
        except Exception as e:
            self.logger.error(f"Meeting listener error: {e}")

    def _handle_meeting_share(self, conn, addr):
        """Handle shared meeting"""
        try:
            conn.settimeout(10)
            size_data = conn.recv(4)
            if not size_data:
                return
            size = struct.unpack("!I", size_data)[0]
            data = conn.recv(size)
            msg = json.loads(data.decode())

            if msg.get("type") == "meeting":
                meeting_data = msg.get("data")
                sender = msg.get("sender", "Unknown")

                self.meetings.append(meeting_data)
                self._save_meeting(meeting_data)

                self.root.after(0, self._load_meeting_history)
                self.root.after(0, self._show_meeting_notification, sender)
        except Exception as e:
            self.logger.error(f"Meeting share error: {e}")
        finally:
            conn.close()

    def _show_meeting_notification(self, sender):
        """Show meeting received notification"""
        self.status_label.config(text=f"Meeting received from {sender}",
                                fg=IOS26_COLORS["system_green"])
        messagebox.showinfo("Meeting Shared", f"Received meeting from {sender}")

    def _update_peers_list(self):
        """Update peers list"""
        while self.running:
            try:
                with self.peers_lock:
                    peer_list = list(self.peers.items())

                if hasattr(self, 'peers_listbox'):
                    self.peers_listbox.delete(0, "end")
                    for ip, info in peer_list:
                        display = f"● {info['name']}"
                        self.peers_listbox.insert("end", display)

                time.sleep(5)
            except Exception as e:
                self.logger.debug(f"Peers update error: {e}")

    def _on_peer_select(self, event):
        """Handle peer selection"""
        sel = self.peers_listbox.curselection()
        if sel:
            with self.peers_lock:
                peers_list = list(self.peers.keys())
                if sel[0] < len(peers_list):
                    self.selected_peer_ip = peers_list[sel[0]]
                    peer_name = self.peers[self.selected_peer_ip]['name']
                    self.status_label.config(text=f"Selected: {peer_name}",
                                            fg=IOS26_COLORS["system_blue"])


def main():
    root = tk.Tk()
    app = MeetingAssistantApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
