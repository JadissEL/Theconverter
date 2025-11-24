#!/bin/bash

# Installation script for transcription dependencies
# This installs heavy ML libraries - may take several minutes

echo "🚀 Installing transcription dependencies..."
echo "⚠️  This may take 5-10 minutes due to large ML libraries"
echo ""

cd /workspaces/Theconverter/api

# Install PyTorch (latest CPU version)
echo "📦 Installing PyTorch (CPU)..."
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install Whisper and dependencies
echo "📦 Installing OpenAI Whisper..."
pip install -U openai-whisper

# Install audio processing
echo "📦 Installing audio processing libraries..."
pip install soundfile scipy scikit-learn

# Install PDF generation
echo "📦 Installing PDF libraries..."
pip install reportlab PyPDF2

echo ""
echo "✅ Installation complete!"
echo ""
echo "The system will use Whisper + clustering for speaker detection"
