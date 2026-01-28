#!/usr/bin/env python3
"""
Voice Transcriber - A sleek voice recording app with automatic Whisper transcription
"""

import customtkinter as ctk
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import threading
import time
import os
from datetime import datetime
from pathlib import Path
import json

# Try to import OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# App directories
APP_DIR = Path(__file__).parent
RECORDINGS_DIR = APP_DIR / "recordings"
TRANSCRIPTS_DIR = APP_DIR / "transcripts"
CONFIG_FILE = APP_DIR / "config.json"

# Ensure directories exist
RECORDINGS_DIR.mkdir(exist_ok=True)
TRANSCRIPTS_DIR.mkdir(exist_ok=True)

# Audio settings
SAMPLE_RATE = 44100
CHANNELS = 1

class VoiceTranscriber(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title("Voice Transcriber")
        self.geometry("400x500")
        self.resizable(False, False)
        
        # Set dark theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        
        # State
        self.is_recording = False
        self.audio_data = []
        self.start_time = None
        self.timer_thread = None
        self.current_filename = None
        
        # Load config
        self.api_key = self.load_api_key()
        
        # Build UI
        self.create_widgets()
        
    def load_api_key(self):
        """Load API key from config or environment"""
        # Try environment variable first
        key = os.environ.get("OPENAI_API_KEY")
        if key:
            return key
        
        # Try config file
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE) as f:
                    config = json.load(f)
                    return config.get("openai_api_key")
            except:
                pass
        return None
    
    def save_api_key(self, key):
        """Save API key to config"""
        config = {}
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE) as f:
                    config = json.load(f)
            except:
                pass
        config["openai_api_key"] = key
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)
        self.api_key = key
        
    def create_widgets(self):
        # Main container
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self.main_frame, 
            text="🎙️ Voice Transcriber",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack(pady=(10, 20))
        
        # Status indicator frame
        self.status_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.status_frame.pack(pady=10)
        
        # Status light (canvas for the circle)
        self.status_canvas = ctk.CTkCanvas(
            self.status_frame, 
            width=30, 
            height=30, 
            bg="#2b2b2b", 
            highlightthickness=0
        )
        self.status_canvas.pack(side="left", padx=(0, 10))
        self.status_light = self.status_canvas.create_oval(5, 5, 25, 25, fill="#555555", outline="#333333")
        
        # Status text
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Ready",
            font=ctk.CTkFont(size=16)
        )
        self.status_label.pack(side="left")
        
        # Timer display
        self.timer_label = ctk.CTkLabel(
            self.main_frame,
            text="00:00:00",
            font=ctk.CTkFont(size=48, weight="bold")
        )
        self.timer_label.pack(pady=30)
        
        # Record button
        self.record_button = ctk.CTkButton(
            self.main_frame,
            text="⏺ START RECORDING",
            font=ctk.CTkFont(size=18, weight="bold"),
            width=250,
            height=60,
            corner_radius=30,
            fg_color="#dc3545",
            hover_color="#c82333",
            command=self.toggle_recording
        )
        self.record_button.pack(pady=20)
        
        # Progress bar (hidden by default)
        self.progress_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.progress_frame.pack(pady=10, fill="x", padx=20)
        
        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="",
            font=ctk.CTkFont(size=12)
        )
        self.progress_label.pack()
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, width=300)
        self.progress_bar.pack(pady=5)
        self.progress_bar.set(0)
        self.progress_frame.pack_forget()  # Hide initially
        
        # Last recording info
        self.info_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.info_frame.pack(pady=10, fill="x", padx=20)
        
        self.info_label = ctk.CTkLabel(
            self.info_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#888888"
        )
        self.info_label.pack()
        
        # Settings button (for API key)
        self.settings_button = ctk.CTkButton(
            self.main_frame,
            text="⚙️ Settings",
            font=ctk.CTkFont(size=12),
            width=100,
            height=30,
            fg_color="transparent",
            hover_color="#333333",
            command=self.open_settings
        )
        self.settings_button.pack(pady=(20, 0))
        
    def toggle_recording(self):
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()
            
    def start_recording(self):
        self.is_recording = True
        self.audio_data = []
        self.start_time = time.time()
        
        # Update UI
        self.status_canvas.itemconfig(self.status_light, fill="#ff0000")  # Red light
        self.status_label.configure(text="Recording...")
        self.record_button.configure(
            text="⏹ STOP RECORDING",
            fg_color="#28a745",
            hover_color="#218838"
        )
        
        # Start recording thread
        self.recording_thread = threading.Thread(target=self.record_audio, daemon=True)
        self.recording_thread.start()
        
        # Start timer thread
        self.timer_thread = threading.Thread(target=self.update_timer, daemon=True)
        self.timer_thread.start()
        
    def stop_recording(self):
        self.is_recording = False
        
        # Update UI
        self.status_canvas.itemconfig(self.status_light, fill="#555555")  # Gray light
        self.status_label.configure(text="Processing...")
        self.record_button.configure(
            text="⏺ START RECORDING",
            fg_color="#dc3545",
            hover_color="#c82333",
            state="disabled"
        )
        
        # Save and transcribe in background
        threading.Thread(target=self.save_and_transcribe, daemon=True).start()
        
    def record_audio(self):
        """Record audio in a separate thread"""
        def callback(indata, frames, time_info, status):
            if self.is_recording:
                self.audio_data.append(indata.copy())
        
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, callback=callback):
            while self.is_recording:
                time.sleep(0.1)
                
    def update_timer(self):
        """Update the timer display"""
        while self.is_recording:
            elapsed = time.time() - self.start_time
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            self.timer_label.configure(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            time.sleep(0.1)
            
    def save_and_transcribe(self):
        """Save the recording and transcribe it"""
        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.current_filename = f"recording_{timestamp}"
            audio_path = RECORDINGS_DIR / f"{self.current_filename}.wav"
            transcript_path = TRANSCRIPTS_DIR / f"{self.current_filename}.txt"
            
            # Concatenate audio data
            if not self.audio_data:
                self.after(0, lambda: self.status_label.configure(text="No audio recorded"))
                self.after(0, lambda: self.record_button.configure(state="normal"))
                return
                
            audio_array = np.concatenate(self.audio_data, axis=0)
            
            # Save WAV file
            self.after(0, lambda: self.status_label.configure(text="Saving audio..."))
            wav.write(str(audio_path), SAMPLE_RATE, audio_array)
            
            # Show progress
            self.after(0, lambda: self.progress_frame.pack(pady=10, fill="x", padx=20))
            self.after(0, lambda: self.progress_label.configure(text="Transcribing..."))
            self.after(0, lambda: self.progress_bar.set(0.1))
            
            # Transcribe
            transcript = self.transcribe_audio(audio_path)
            
            if transcript:
                # Save transcript
                with open(transcript_path, "w") as f:
                    f.write(f"Recording: {self.current_filename}\n")
                    f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Duration: {self.timer_label.cget('text')}\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(transcript)
                
                self.after(0, lambda: self.progress_bar.set(1.0))
                self.after(0, lambda: self.status_label.configure(text="✓ Done!"))
                self.after(0, lambda: self.info_label.configure(
                    text=f"Saved: {self.current_filename}\n{len(transcript)} characters transcribed"
                ))
            else:
                self.after(0, lambda: self.status_label.configure(text="Audio saved (no transcription)"))
                self.after(0, lambda: self.info_label.configure(text=f"Saved: {audio_path.name}"))
                
        except Exception as e:
            self.after(0, lambda: self.status_label.configure(text=f"Error: {str(e)[:30]}"))
            print(f"Error: {e}")
            
        finally:
            # Reset UI
            self.after(0, lambda: self.record_button.configure(state="normal"))
            self.after(2000, lambda: self.progress_frame.pack_forget())
            self.after(2000, lambda: self.status_label.configure(text="Ready"))
            
    def transcribe_audio(self, audio_path):
        """Transcribe audio using OpenAI Whisper API with chunking"""
        if not self.api_key:
            print("No API key configured")
            return None
            
        if not OPENAI_AVAILABLE:
            print("OpenAI package not installed")
            return None
            
        try:
            client = OpenAI(api_key=self.api_key)
            
            # Check file size - Whisper has a 25MB limit
            file_size = os.path.getsize(audio_path)
            max_size = 24 * 1024 * 1024  # 24MB to be safe
            
            if file_size <= max_size:
                # Single file transcription
                self.after(0, lambda: self.progress_bar.set(0.3))
                with open(audio_path, "rb") as f:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=f,
                        response_format="text"
                    )
                self.after(0, lambda: self.progress_bar.set(0.9))
                return transcript
            else:
                # Need to chunk the audio
                return self.transcribe_chunked(client, audio_path)
                
        except Exception as e:
            print(f"Transcription error: {e}")
            return None
            
    def transcribe_chunked(self, client, audio_path):
        """Transcribe long audio by chunking"""
        from pydub import AudioSegment
        
        self.after(0, lambda: self.progress_label.configure(text="Splitting audio..."))
        
        # Load audio
        audio = AudioSegment.from_wav(str(audio_path))
        
        # Chunk into 10-minute segments (Whisper handles this well)
        chunk_length_ms = 10 * 60 * 1000  # 10 minutes
        chunks = []
        
        for i in range(0, len(audio), chunk_length_ms):
            chunks.append(audio[i:i + chunk_length_ms])
            
        transcripts = []
        total_chunks = len(chunks)
        
        for i, chunk in enumerate(chunks):
            self.after(0, lambda i=i: self.progress_label.configure(
                text=f"Transcribing chunk {i+1}/{total_chunks}..."
            ))
            self.after(0, lambda i=i: self.progress_bar.set((i + 0.5) / total_chunks))
            
            # Export chunk to temp file
            chunk_path = RECORDINGS_DIR / f"temp_chunk_{i}.wav"
            chunk.export(str(chunk_path), format="wav")
            
            try:
                with open(chunk_path, "rb") as f:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=f,
                        response_format="text"
                    )
                transcripts.append(transcript)
            finally:
                # Clean up temp file
                chunk_path.unlink(missing_ok=True)
                
            self.after(0, lambda i=i: self.progress_bar.set((i + 1) / total_chunks))
            
        return "\n\n".join(transcripts)
        
    def open_settings(self):
        """Open settings dialog for API key"""
        dialog = ctk.CTkInputDialog(
            text="Enter your OpenAI API key:",
            title="Settings"
        )
        key = dialog.get_input()
        if key:
            self.save_api_key(key)
            self.status_label.configure(text="API key saved!")
            self.after(2000, lambda: self.status_label.configure(text="Ready"))


def main():
    app = VoiceTranscriber()
    app.mainloop()


if __name__ == "__main__":
    main()
