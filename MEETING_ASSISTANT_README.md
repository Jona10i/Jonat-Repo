# Meeting Assistant - iOS 26 Edition

A beautifully redesigned AI-powered meeting assistant with iOS 26 design aesthetics, featuring glassmorphism effects, rounded corners, vibrant colors, and modern animations.

## ✨ iOS 26 Design Features

### Visual Design
- **Glassmorphism Effects** - Translucent backgrounds with subtle blur
- **Rounded Corners** - iOS-style 24px corner radius throughout
- **Vibrant Color Palette** - iOS system colors (blue, purple, pink, green, orange)
- **Compact Window** - Right-side positioned, 420x720px format
- **Floating Bubble** - Minimize to a draggable bubble at bottom-right

### Animations & Interactions
- **Smooth Tab Transitions** - Fade and slide animations between views
- **Button Feedback** - Scale and color transitions on hover/click
- **Bubble Animations** - Spring physics on the floating minimize bubble
- **Status Updates** - Color-coded status indicators

## Features

### Core Capabilities
- **Audio Recording** - Record meetings directly from microphone
- **Audio Upload** - Transcribe existing audio files (WAV, MP3, M4A, FLAC)
- **AI Transcription** - Uses OpenAI Whisper (local, no API key needed)
- **Action Item Extraction** - Identifies tasks and follow-ups
- **Key Decision Detection** - Finds important decisions made
- **Topic Analysis** - Extracts discussed topics using NLP
- **Sentiment Analysis** - Determines meeting tone
- **Executive Summary** - Generates concise meeting overview
- **Participant Identification** - Recognizes speakers

### Collaboration Features
- **Peer Discovery** - Auto-discovers other users on LAN (ZeroConf)
- **File Transfer** - Send/receive files between users
- **Meeting Sharing** - Share complete transcripts & analyses with peers
- **Direct Messaging** - Chat with discovered users

### Search & History
- **Searchable Meeting History** - All meetings saved locally
- **Export Options** - Export meetings as JSON
- **Persistent Storage** - Meeting history survives app restarts

## Installation

### Prerequisites
- Python 3.8+
- Windows/Linux/macOS

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Additional Setup (for NLP features)
```bash
python -m spacy download en_core_web_sm
```

## Usage

### Starting the Application
```bash
python meeting_assistant.py
```

### How to Use

1. **Enter Your Name** - Type your display name and click "Get Started"
2. **Record Meeting** - Click "● Start Recording" to capture audio
3. **Upload Audio** - Click "Upload Audio" to transcribe existing files
4. **View Analysis** - Switch between Transcript, Analysis, and History tabs
5. **Share** - Select a user and click "Share Meeting" to collaborate

### iOS 26 UI Features

#### Minimize to Bubble
- Click the **−** button in the top-right to minimize to a floating bubble
- The bubble appears at the bottom-right of your screen
- Click the bubble to restore the window
- Drag the bubble to reposition it

#### Tab Navigation
- **Transcript** - View full meeting transcription
- **Analysis** - See AI-generated insights (summary, action items, decisions, topics, participants, sentiment)
- **History** - Access all past meetings

#### Color Coding
- 🔵 **Blue** - Primary actions, active states
- 🟢 **Green** - Success, recording stopped
- 🔴 **Red** - Recording in progress
- 🟣 **Purple** - Accent highlights

## Architecture

### Components
- **MeetingAnalyzer** - Handles Whisper transcription and NLP analysis
- **AudioRecorder** - Captures microphone input using sounddevice
- **DiscoveryWorker** - ZeroConf-based peer discovery
- **FloatingBubble** - iOS 26 style minimize widget
- **MeetingAssistantApp** - Main GUI application with iOS 26 styling

### Network Protocols
- `_meeting._tcp.local`: Service discovery
- Port 55001: Chat messages
- Port 55002: File transfers
- Port 55003: Meeting sharing

## AI Models Used

### Transcription
- OpenAI Whisper (base model)
- Local execution - no API key needed

### NLP Analysis
- Facebook BART-Large-CNN for summarization
- DistilBERT for sentiment analysis
- spaCy for entity recognition and linguistic analysis

## iOS 26 Design System

### Colors
```python
IOS26_COLORS = {
    "system_blue": "#0A84FF",
    "system_green": "#30D158",
    "system_indigo": "#5E5CE6",
    "system_orange": "#FF9F0A",
    "system_pink": "#FF375F",
    "system_purple": "#BF5AF2",
    "system_red": "#FF453A",
    "system_teal": "#64D2FF",
    "system_yellow": "#FFD60A",
}
```

### Dimensions
- Window: 420x720px (compact mode)
- Corner Radius: 24px (large), 16px (medium), 12px (small)
- Floating Bubble: 64px diameter
- Button Height: 48px
- Spacing: 4px, 8px, 16px, 24px, 32px scale

### Typography
- Font: SF Pro Display/Text (fallback: Segoe UI)
- Large Title: 32px bold
- Title: 22px bold
- Body: 15px regular
- Caption: 12px regular

## File Structure
```
meeting_assistant.py         # Main iOS 26 styled application
meeting_assistant_ios26.py   # Backup of iOS 26 version
requirements.txt             # Python dependencies
meeting_config.json          # User configuration
meeting_history.jsonl        # Meeting history
meeting_assistant.log        # Application logs
MEETING_ASSISTANT_README.md  # This documentation
```

## Dependencies

### Required
- openai-whisper: Speech recognition
- sounddevice: Audio recording
- numpy: Audio processing
- zeroconf: Peer discovery

### Optional (for full AI features)
- transformers: Hugging Face models
- torch: PyTorch backend
- spacy: NLP processing

## Troubleshooting

### Audio Recording Not Available
Install sounddevice: `pip install sounddevice`

### Whisper Not Available
Install Whisper: `pip install -U openai-whisper`

### NLP Models Not Available
Install dependencies: `pip install transformers torch spacy`
Download model: `python -m spacy download en_core_web_sm`

### Window Position
The app automatically positions itself on the right side of the screen. If it appears off-screen, move it manually or adjust your display settings.

## Notes
- First run may download AI models (Whisper, BART, etc.)
- Models are cached locally after first download
- All processing happens locally - no cloud required
- Peer discovery requires users to be on the same network
- The floating bubble stays on top of other windows for easy access

## Keyboard Shortcuts
- `Enter` in name field - Start app
- Click `−` - Minimize to bubble
- Click bubble - Restore window
- Drag bubble - Reposition
