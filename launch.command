#!/bin/bash
cd "$(dirname "$0")"

echo "========================================"
echo "   Voice Transcriber - Starting..."
echo "========================================"
echo

# Check if packages need installing
if ! pip3 show customtkinter >/dev/null 2>&1; then
    echo "First run detected - installing packages..."
    echo "This may take a few minutes..."
    echo
    pip3 install -r requirements.txt
    echo
    echo "Packages installed!"
    echo
fi

echo "Launching Voice Transcriber..."
echo "(First transcription downloads the AI model - be patient!)"
echo
python3 recorder.py
