#!/bin/bash

# Build script for Vercel Python API
# This installs FFmpeg and system dependencies

echo "Installing system dependencies..."

# Install FFmpeg
apt-get update
apt-get install -y ffmpeg libmagic1

# Install Python dependencies
pip install -r requirements.txt

echo "Build complete!"
