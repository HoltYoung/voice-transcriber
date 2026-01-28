# 🎙️ Voice Transcriber

A sleek, dark-themed voice recording app with automatic transcription using OpenAI's Whisper API.

## Features

- **One-click recording** - Press to start, press again to stop
- **Visual indicators** - Red light when recording, gray when idle
- **Live timer** - Shows recording duration in real-time
- **Automatic transcription** - Uses OpenAI Whisper API after recording stops
- **Smart chunking** - Handles long recordings by splitting into manageable pieces
- **Auto-save** - Recordings saved to `recordings/`, transcripts to `transcripts/`

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
python recorder.py
```

## First Time Setup

1. Launch the app
2. Click **⚙️ Settings**
3. Enter your OpenAI API key (get one at https://platform.openai.com/api-keys)
4. Start recording!

## Usage

1. **Click the red button** to start recording
2. **Click the green button** to stop
3. Wait for transcription to complete
4. Find your files in `recordings/` and `transcripts/`

## File Locations

- **Audio files**: `recordings/recording_YYYYMMDD_HHMMSS.wav`
- **Transcripts**: `transcripts/recording_YYYYMMDD_HHMMSS.txt`
- **Config**: `config.json` (stores your API key)

## Requirements

- Python 3.9+
- macOS, Windows, or Linux
- OpenAI API key (for transcription)
- Microphone access

## Cost

Whisper API costs ~$0.006 per minute of audio. A 1-hour lecture costs about $0.36.

## Troubleshooting

**No audio recorded**: Check your microphone permissions in System Preferences > Security & Privacy > Privacy > Microphone

**Transcription fails**: Verify your API key in Settings. Check your OpenAI account has credits.

---

Built with ❤️ for quick lecture transcription
