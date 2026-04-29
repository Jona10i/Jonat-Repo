#!/usr/bin/env python3
"""
Meeting Assistant - Fireflies.ai Alternative
A comprehensive meeting transcription and analysis tool with:
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
#  CONFIGURATION
# ---------------------------------------------
DEFAULT_FONT_FAMILY = "Segoe UI"
BROADCAST_PORT = 55000
CHAT_PORT = 55001
FILE_PORT = 55002
MEETING_PORT = 55003  # New port for meeting sharing
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
CHUNK_DURATION = 30  # seconds per chunk


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
                # Try to download spacy model if not available
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
            # Extract action items (sentences with action verbs)
            doc = self.nlp(transcript)
            action_keywords = ["need to", "should", "will", "must", "going to", "plan to", "follow up"]
            for sent in doc.sents:
                sent_text = sent.text.lower()
                if any(keyword in sent_text for keyword in action_keywords):
                    if "?" not in sent.text:  # Skip questions
                        analysis["action_items"].append(sent.text.strip())

            # Extract decisions (sentences with decision indicators)
            decision_keywords = ["decided", "agreed", "conclusion", "resolved", "approved"]
            for sent in doc.sents:
                sent_text = sent.text.lower()
                if any(keyword in sent_text for keyword in decision_keywords):
                    analysis["decisions"].append(sent.text.strip())

            # Extract topics (named entities and noun chunks)
            topics = set()
            for ent in doc.ents:
                if ent.label_ in ["ORG", "PRODUCT", "EVENT", "GPE", "WORK_OF_ART"]:
                    topics.add(ent.text)
            for chunk in doc.noun_chunks:
                if len(chunk.text) > 3:
                    topics.add(chunk.text)
            analysis["topics"] = list(topics)[:10]

            # Sentiment analysis
            chunks = [transcript[i:i+512] for i in range(0, len(transcript), 512)]
            sentiments = []
            for chunk in chunks[:5]:  # Limit to first 5 chunks for performance
                result = self.sentiment_analyzer(chunk[:512])[0]
                sentiments.append(result['label'])
            analysis["sentiment"] = max(set(sentiments), key=sentiments.count) if sentiments else "NEUTRAL"

            # Generate summary
            if len(transcript) > 100:
                summary_input = transcript[:1024]  # Limit input size
                summary = self.summarizer(summary_input, max_length=150, min_length=30, do_sample=False)
                analysis["summary"] = summary[0]['summary_text']

            # Extract participants (unique names)
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
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(self.sample_rate)
                wf.writeframes((audio_data * 32767).astype(np.int16).tobytes())
            return True
        except Exception as e:
            print(f"Error saving audio: {e}")
            return False


class MeetingAssistantApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("1200x800")
        self.root.configure(bg="#1e1e2e")

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

        # Load config and build UI
        self._load_config()
        self._build_login_screen()

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

    def _build_login_screen(self):
        self.login_frame = tk.Frame(self.root, bg="#1e1e2e")
        self.login_frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(self.login_frame, text=APP_NAME, font=(DEFAULT_FONT_FAMILY, 28, "bold"),
                 bg="#1e1e2e", fg="#cdd6f4").pack(pady=(0, 6))
        tk.Label(self.login_frame, text="AI-Powered Meeting Assistant", font=(DEFAULT_FONT_FAMILY, 11),
                 bg="#1e1e2e", fg="#6c7086").pack(pady=(0, 30))

        tk.Label(self.login_frame, text="Your display name:", font=(DEFAULT_FONT_FAMILY, 11),
                 bg="#1e1e2e", fg="#cdd6f4").pack(anchor="w")

        self.name_entry = tk.Entry(self.login_frame, font=(DEFAULT_FONT_FAMILY, 13),
                                   bg="#313244", fg="#cdd6f4", insertbackground="#cdd6f4",
                                   relief="flat", width=26, bd=8)
        self.name_entry.pack(pady=(4, 14))
        if self.username:
            self.name_entry.insert(0, self.username)
            self.name_entry.selection_range(0, "end")

        self.name_entry.bind("<Return>", lambda e: self._start_app())

        join_btn = tk.Button(self.login_frame, text="Join Network →",
                             font=(DEFAULT_FONT_FAMILY, 12, "bold"),
                             bg="#89b4fa", fg="#1e1e2e", relief="flat",
                             activebackground="#74c7ec", activeforeground="#1e1e2e",
                             padx=20, pady=8, cursor="hand2",
                             command=self._start_app)
        join_btn.pack()

        tk.Label(self.login_frame, text=f"Your IP: {self.local_ip}",
                font=(DEFAULT_FONT_FAMILY, 9), bg="#1e1e2e", fg="#45475a").pack(pady=(16, 0))

    def _start_app(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Name required", "Please enter a display name.")
            return
        self.username = name
        self.config["username"] = name
        self._save_config()
        self.login_frame.destroy()
        self._build_main_ui()
        self._start_networking()

    def _build_main_ui(self):
        # Main container
        main_container = tk.Frame(self.root, bg="#1e1e2e")
        main_container.pack(fill="both", expand=True)

        # Sidebar
        sidebar = tk.Frame(main_container, bg="#181825", width=200)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="ONLINE USERS", font=(DEFAULT_FONT_FAMILY, 8, "bold"),
                 bg="#181825", fg="#6c7086", padx=12, pady=10).pack(anchor="w")

        self.peers_listbox = tk.Listbox(sidebar, bg="#181825", fg="#cdd6f4",
                                        selectbackground="#313244", selectforeground="#89b4fa",
                                        relief="flat", bd=0, font=(DEFAULT_FONT_FAMILY, 11),
                                        activestyle="none", highlightthickness=0)
        self.peers_listbox.pack(fill="both", expand=True, padx=4)
        self.peers_listbox.bind("<<ListboxSelect>>", self._on_peer_select)

        # Meeting controls
        tk.Label(sidebar, text="MEETING CONTROLS", font=(DEFAULT_FONT_FAMILY, 8, "bold"),
                 bg="#181825", fg="#6c7086", padx=12, pady=10).pack(anchor="w")

        self.record_btn = tk.Button(sidebar, text="● Start Recording",
                                   font=(DEFAULT_FONT_FAMILY, 10, "bold"),
                                   bg="#f38ba8", fg="#1e1e2e", relief="flat",
                                   activebackground="#eba0ac", padx=10, pady=5,
                                   cursor="hand2", command=self._toggle_recording)
        self.record_btn.pack(fill="x", padx=8, pady=4)

        tk.Button(sidebar, text="Upload Audio",
                  font=(DEFAULT_FONT_FAMILY, 10),
                  bg="#313244", fg="#cdd6f4", relief="flat",
                  activebackground="#45475a", padx=10, pady=5,
                  cursor="hand2", command=self._upload_audio).pack(fill="x", padx=8, pady=4)

        tk.Button(sidebar, text="Share Meeting",
                  font=(DEFAULT_FONT_FAMILY, 10),
                  bg="#313244", fg="#cdd6f4", relief="flat",
                  activebackground="#45475a", padx=10, pady=5,
                  cursor="hand2", command=self._share_meeting).pack(fill="x", padx=8, pady=4)

        # Main content area
        content = tk.Frame(main_container, bg="#1e1e2e")
        content.pack(side="right", fill="both", expand=True)

        # Header
        header = tk.Frame(content, bg="#181825", height=48)
        header.pack(fill="x")
        header.pack_propagate(False)

        self.title_label = tk.Label(header, text="Meeting Assistant",
                                   font=(DEFAULT_FONT_FAMILY, 12, "bold"),
                                   bg="#181825", fg="#cdd6f4", padx=16)
        self.title_label.pack(side="left", pady=10)

        tk.Button(header, text="Profile", font=(DEFAULT_FONT_FAMILY, 9),
                  bg="#313244", fg="#cdd6f4", relief="flat",
                  activebackground="#45475a", padx=10, cursor="hand2",
                  command=self._open_settings).pack(side="right", pady=10, padx=10)

        # Notebook for tabs
        self.notebook = ttk.Notebook(content)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Transcription tab
        self.transcription_frame = tk.Frame(self.notebook, bg="#1e1e2e")
        self.notebook.add(self.transcription_frame, text="Transcription")

        self.transcription_text = scrolledtext.ScrolledText(
            self.transcription_frame, state="disabled", bg="#1e1e2e", fg="#cdd6f4",
            font=(DEFAULT_FONT_FAMILY, 11), relief="flat", padx=12, pady=8, wrap="word"
        )
        self.transcription_text.pack(fill="both", expand=True)

        # Analysis tab
        self.analysis_frame = tk.Frame(self.notebook, bg="#1e1e2e")
        self.notebook.add(self.analysis_frame, text="Analysis")

        self._build_analysis_panel()

        # History tab
        self.history_frame = tk.Frame(self.notebook, bg="#1e1e2e")
        self.notebook.add(self.history_frame, text="Meeting History")

        self._build_history_panel()

        # Status bar
        self.status_label = tk.Label(content, text="Ready", font=(DEFAULT_FONT_FAMILY, 9),
                                     bg="#181825", fg="#6c7086", anchor="w", padx=10, pady=4)
        self.status_label.pack(fill="x", side="bottom")

        self._log_system("Welcome to Meeting Assistant! Start recording or upload audio.")

    def _build_analysis_panel(self):
        """Build the analysis panel with sections for different insights"""
        canvas = tk.Canvas(self.analysis_frame, bg="#1e1e2e", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.analysis_frame, orient="vertical", command=canvas.yview)
        self.analysis_content = tk.Frame(canvas, bg="#1e1e2e")

        self.analysis_content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.analysis_content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Sections
        sections = [
            ("Executive Summary", "summary_text"),
            ("Action Items", "action_items"),
            ("Key Decisions", "decisions"),
            ("Topics Discussed", "topics"),
            ("Participants", "participants"),
            ("Overall Sentiment", "sentiment")
        ]

        for title, attr_name in sections:
            frame = tk.LabelFrame(self.analysis_content, text=title,
                                  font=(DEFAULT_FONT_FAMILY, 11, "bold"),
                                  bg="#1e1e2e", fg="#89b4fa", padx=10, pady=5)
            frame.pack(fill="x", padx=10, pady=5)

            text = scrolledtext.ScrolledText(frame, height=4 if attr_name != "summary_text" else 6,
                                               bg="#313244", fg="#cdd6f4",
                                               font=(DEFAULT_FONT_FAMILY, 10),
                                               relief="flat", state="disabled")
            text.pack(fill="both", expand=True)
            setattr(self, f"{attr_name}_widget", text)

    def _build_history_panel(self):
        """Build meeting history panel"""
        toolbar = tk.Frame(self.history_frame, bg="#181825", height=40)
        toolbar.pack(fill="x", pady=(0, 5))
        toolbar.pack_propagate(False)

        tk.Button(toolbar, text="Refresh", font=(DEFAULT_FONT_FAMILY, 9),
                  bg="#313244", fg="#cdd6f4", relief="flat",
                  activebackground="#45475a", padx=10, cursor="hand2",
                  command=self._load_meeting_history).pack(side="left", padx=5, pady=5)

        tk.Button(toolbar, text="Export All", font=(DEFAULT_FONT_FAMILY, 9),
                  bg="#313244", fg="#cdd6f4", relief="flat",
                  activebackground="#45475a", padx=10, cursor="hand2",
                  command=self._export_all_meetings).pack(side="left", padx=5, pady=5)

        self.history_list = tk.Listbox(self.history_frame, bg="#181825", fg="#cdd6f4",
                                       selectbackground="#313244", selectforeground="#89b4fa",
                                       relief="flat", bd=0, font=(DEFAULT_FONT_FAMILY, 11),
                                       activestyle="none", highlightthickness=0)
        self.history_list.pack(fill="both", expand=True, padx=10, pady=5)
        self.history_list.bind("<<ListboxSelect>>", self._on_history_select)

        self._load_meeting_history()

    def _toggle_recording(self):
        """Toggle audio recording"""
        if not AUDIO_AVAILABLE:
            messagebox.showerror("Audio Error", "Audio recording not available. Install sounddevice.")
            return

        if not self.is_recording:
            if self.recorder.start_recording():
                self.is_recording = True
                self.record_btn.config(text="■ Stop Recording", bg="#a6e3a1")
                self._log_system("Recording started...")
                self.status_label.config(text="Recording...")
        else:
            audio_data = self.recorder.stop_recording()
            self.is_recording = False
            self.record_btn.config(text="● Start Recording", bg="#f38ba8")
            self._log_system("Recording stopped. Processing...")
            self.status_label.config(text="Processing transcription...")
            self._process_recorded_audio(audio_data)

    def _process_recorded_audio(self, audio_data):
        """Process recorded audio through transcription and analysis"""
        if audio_data is None:
            return

        # Save to temp file
        temp_path = tempfile.mktemp(suffix=".wav")
        if self.recorder.save_to_file(audio_data, temp_path):
            self._transcribe_and_analyze(temp_path)
            os.remove(temp_path)

    def _upload_audio(self):
        """Upload audio file for transcription"""
        path = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[("Audio files", "*.wav *.mp3 *.m4a *.flac"), (ALL_FILES, "*.*")]
        )
        if path:
            self._transcribe_and_analyze(path)

    def _transcribe_and_analyze(self, audio_path):
        """Transcribe audio and analyze meeting"""
        self.status_label.config(text="Transcribing...")
        self.root.update()

        transcript, error = self.analyzer.transcribe_audio(audio_path)
        if error:
            messagebox.showerror("Transcription Error", f"Failed to transcribe: {error}")
            self.status_label.config(text="Ready")
            return

        self._update_transcription(transcript)

        self.status_label.config(text="Analyzing meeting...")
        self.root.update()

        analysis = self.analyzer.analyze_meeting(transcript)
        self._update_analysis(analysis)

        # Save meeting
        meeting_data = {
            "timestamp": time.time(),
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "transcript": transcript,
            "analysis": analysis
        }
        self.meetings.append(meeting_data)
        self._save_meeting(meeting_data)
        self._load_meeting_history()

        self.status_label.config(text="Analysis complete")
        self._log_system("Meeting processed and analyzed successfully")

    def _update_transcription(self, text):
        """Update transcription display"""
        self.transcription_text.config(state="normal")
        self.transcription_text.delete(1.0, "end")
        self.transcription_text.insert("end", text)
        self.transcription_text.config(state="disabled")

    def _update_analysis(self, analysis):
        """Update analysis panel with results"""
        widgets = [
            ("summary_text", analysis.get("summary", "No summary available.")),
            ("action_items", "\n".join(f"• {item}" for item in analysis.get("action_items", [])) or "No action items found."),
            ("decisions", "\n".join(f"• {dec}" for dec in analysis.get("decisions", [])) or "No decisions found."),
            ("topics", ", ".join(analysis.get("topics", [])) or "No topics identified."),
            ("participants", ", ".join(analysis.get("participants", [])) or "No participants identified."),
            ("sentiment", analysis.get("sentiment", "Unknown"))
        ]

        for attr_name, content in widgets:
            widget = getattr(self, f"{attr_name}_widget")
            widget.config(state="normal")
            widget.delete(1.0, "end")
            widget.insert("end", content)
            widget.config(state="disabled")

    def _save_meeting(self, meeting_data):
        """Save meeting to history file"""
        try:
            with open(MEETING_HISTORY_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(meeting_data) + "\n")
        except Exception as e:
            self.logger.error(f"Failed to save meeting: {e}")

    def _load_meeting_history(self):
        """Load meeting history"""
        self.meetings = []
        self.history_list.delete(0, "end")

        if os.path.exists(MEETING_HISTORY_FILE):
            try:
                with open(MEETING_HISTORY_FILE, "r", encoding="utf-8") as f:
                    for line in f:
                        meeting = json.loads(line.strip())
                        self.meetings.append(meeting)
                        display = f"{meeting['datetime']} - {meeting['analysis'].get('topics', ['General'])[0] if meeting['analysis'].get('topics') else 'General'}"
                        self.history_list.insert("end", display)
            except Exception as e:
                self.logger.error(f"Failed to load history: {e}")

    def _on_history_select(self, event):
        """Load selected meeting from history"""
        sel = self.history_list.curselection()
        if sel:
            meeting = self.meetings[sel[0]]
            self._update_transcription(meeting.get("transcript", ""))
            self._update_analysis(meeting.get("analysis", {}))

    def _export_all_meetings(self):
        """Export all meetings to file"""
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
        """Share current meeting with selected peer"""
        if not self.current_meeting and not self.meetings:
            messagebox.showinfo("No Meeting", "No meeting to share.")
            return

        if not self.selected_peer_ip:
            messagebox.showinfo("Select User", "Please select a user from the sidebar.")
            return

        meeting = self.current_meeting or self.meetings[-1]
        self._send_meeting_to_peer(self.selected_peer_ip, meeting)

    def _send_meeting_to_peer(self, ip, meeting_data):
        """Send meeting data to peer"""
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

            self._log_system(f"Meeting shared with {self.peers.get(ip, {}).get('name', ip)}")
        except Exception as e:
            self._log_system(f"Failed to share meeting: {e}")

    def _start_networking(self):
        """Start network discovery and listeners"""
        if self.running:
            return

        self.running = True

        # Start discovery
        self.discovery_worker = DiscoveryWorker(
            self.config["meeting_port"], self.username, self.peers_lock, self.peers, self.logger
        )
        self.discovery_worker.start()

        # Start listeners
        threading.Thread(target=self._chat_listener, daemon=True).start()
        threading.Thread(target=self._file_listener, daemon=True).start()
        threading.Thread(target=self._meeting_listener, daemon=True).start()
        threading.Thread(target=self._update_peers_list, daemon=True).start()

        self.logger.info("Networking started")

    def _chat_listener(self):
        """Listen for chat messages"""
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
        """Handle incoming chat message"""
        try:
            conn.settimeout(10)
            size_data = conn.recv(4)
            if not size_data:
                return
            size = struct.unpack("!I", size_data)[0]
            data = conn.recv(size)
            msg = json.loads(data.decode())

            if msg.get("type") == "chat":
                self.root.after(0, self._log_message, msg.get("name", "Unknown"),
                                msg.get("text", ""), msg.get("dm", False))
        except Exception as e:
            self.logger.debug(f"Chat handler error: {e}")
        finally:
            conn.close()

    def _file_listener(self):
        """Listen for file transfers"""
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

            # Receive file
            filepath = os.path.join(self.download_dir, filename)
            received = 0
            with open(filepath, "wb") as f:
                while received < filesize:
                    chunk = conn.recv(min(BUFFER_SIZE, filesize - received))
                    if not chunk:
                        break
                    f.write(chunk)
                    received += len(chunk)

            self.root.after(0, self._log_system, f"Received '{filename}' from {sender}")
        except Exception as e:
            self.logger.error(f"File receive error: {e}")
        finally:
            conn.close()

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
        """Handle incoming shared meeting"""
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

                # Add to history
                self.meetings.append(meeting_data)
                self._save_meeting(meeting_data)

                self.root.after(0, self._load_meeting_history)
                self.root.after(0, self._log_system, f"Meeting received from {sender}")
                self.root.after(0, messagebox.showinfo, "Meeting Shared",
                                f"Received meeting from {sender}")
        except Exception as e:
            self.logger.error(f"Meeting share error: {e}")
        finally:
            conn.close()

    def _update_peers_list(self):
        """Update peers list periodically"""
        while self.running:
            try:
                with self.peers_lock:
                    peer_list = list(self.peers.items())

                self.peers_listbox.delete(0, "end")
                for ip, info in peer_list:
                    display = f"👤 {info['name']}"
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
                    self.title_label.config(text=f"DM with {peer_name}")

    def _open_settings(self):
        """Open settings dialog"""
        settings_win = tk.Toplevel(self.root)
        settings_win.title("Settings")
        settings_win.geometry("400x300")
        settings_win.configure(bg="#1e1e2e")
        settings_win.resizable(False, False)

        tk.Label(settings_win, text="Display name:", bg="#1e1e2e", fg="white",
                font=(DEFAULT_FONT_FAMILY, 10)).place(x=20, y=20)
        name_entry = tk.Entry(settings_win, font=(DEFAULT_FONT_FAMILY, 10))
        name_entry.insert(0, self.username)
        name_entry.place(x=150, y=20, width=200)

        tk.Label(settings_win, text="Download folder:", bg="#1e1e2e", fg="white",
                font=(DEFAULT_FONT_FAMILY, 10)).place(x=20, y=60)
        dl_entry = tk.Entry(settings_win, font=(DEFAULT_FONT_FAMILY, 10))
        dl_entry.insert(0, self.download_dir)
        dl_entry.place(x=150, y=60, width=200)

        def save():
            new_name = name_entry.get().strip()
            if new_name:
                self.username = new_name
                self.config["username"] = new_name
            self.download_dir = dl_entry.get()
            self.config["download_dir"] = self.download_dir
            self._save_config()
            settings_win.destroy()

        tk.Button(settings_win, text="Save", command=save,
                  bg="#4CAF50", fg="white", font=(DEFAULT_FONT_FAMILY, 10)).place(x=120, y=200, width=80)
        tk.Button(settings_win, text="Cancel", command=settings_win.destroy,
                  bg="#f44336", fg="white", font=(DEFAULT_FONT_FAMILY, 10)).place(x=220, y=200, width=80)

    def _log_system(self, text):
        """Log system message"""
        timestamp = time.strftime("%H:%M")
        self.transcription_text.config(state="normal")
        self.transcription_text.insert("end", f"[{timestamp}] 🔧 {text}\n", "system")
        self.transcription_text.config(state="disabled")
        self.transcription_text.see("end")

    def _log_message(self, sender, text, is_dm=False):
        """Log chat message"""
        timestamp = time.strftime("%H:%M")
        self.transcription_text.config(state="normal")
        tag = "name_other" if not is_dm else "name_self"
        self.transcription_text.insert("end", f"[{timestamp}] ", "timestamp")
        self.transcription_text.insert("end", f"{sender}: ", tag)
        self.transcription_text.insert("end", f"{text}\n", "msg_other")
        self.transcription_text.config(state="disabled")
        self.transcription_text.see("end")

    def on_closing(self):
        """Clean up on exit"""
        self.running = False
        if self.discovery_worker:
            self.discovery_worker.stop()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = MeetingAssistantApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
