# Meeting Assistant - Fireflies.ai Alternative

A comprehensive AI-powered meeting assistant with transcription, analysis, and file sharing capabilities.

## Features

### Core Features
- **Audio Recording**: Record meetings directly from microphone
- **Audio Upload**: Transcribe pre-recorded audio files (WAV, MP3, M4A, FLAC)
- **AI Transcription**: Uses OpenAI Whisper for accurate speech-to-text
- **Meeting Analysis**:
  - Action item extraction
  - Key decision identification
  - Topic analysis
  - Sentiment analysis
  - Executive summary generation
  - Participant identification

### Collaboration Features
- **Peer Discovery**: Automatic discovery of other Meeting Assistant users on LAN
- **File Sharing**: Send/receive files between users
- **Meeting Sharing**: Share complete meeting transcripts and analyses with peers
- **Direct Messaging**: Chat with discovered users

### Search & History
- **Searchable Meeting History**: All meetings saved locally
- **Export Options**: Export meetings as JSON
- **Persistent Storage**: Meeting history survives app restarts

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

1. **Join Network**: Enter your display name and click "Join Network"
2. **Record Meeting**: Click "● Start Recording" to capture audio
3. **Upload Audio**: Click "Upload Audio" to transcribe existing files
4. **View Analysis**: Switch to "Analysis" tab to see AI-generated insights
5. **Share**: Select a user and click "Share Meeting" to collaborate

### Recording Meetings
- Click "● Start Recording" to begin capturing audio
- Click "■ Stop Recording" when done
- The AI automatically transcribes and analyzes the meeting

### Sharing Meetings
1. Select a user from the "ONLINE USERS" list
2. Process or upload a meeting
3. Click "Share Meeting" to send to the selected user

### Viewing History
- Switch to "Meeting History" tab to see all past meetings
- Click on any meeting to view its transcript and analysis
- Use "Export All" to backup meetings as JSON

## Architecture

### Components
- **MeetingAnalyzer**: Handles Whisper transcription and NLP analysis
- **AudioRecorder**: Captures microphone input using sounddevice
- **DiscoveryWorker**: ZeroConf-based peer discovery
- **LANOfficeApp**: Main GUI application with tkinter

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

## File Structure
```
meeting_assistant.py     # Main application
requirements.txt        # Python dependencies
meeting_config.json     # User configuration
meeting_history.jsonl   # Meeting history
meeting_assistant.log   # Application logs
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

## Notes
- First run may download AI models (Whisper, BART, etc.)
- Models are cached locally after first download
- All processing happens locally - no cloud required
- Peer discovery requires users to be on the same network
