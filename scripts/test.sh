#!/bin/bash

# Quick test script for TheConverter

echo "🧪 TheConverter Test Suite"
echo "=========================="

# Check if servers are running
check_server() {
    local url=$1
    local name=$2
    
    if curl -s "$url" > /dev/null; then
        echo "✅ $name is running"
        return 0
    else
        echo "❌ $name is not running"
        return 1
    fi
}

echo ""
echo "1. Checking servers..."
check_server "http://localhost:3000" "Frontend"
check_server "http://localhost:8000" "Backend API"

echo ""
echo "2. Testing API endpoints..."

# Test health check
echo "   Testing health check..."
curl -s http://localhost:8000/ | jq '.' || echo "❌ Health check failed"

# Create a test audio file (1 second of silence)
echo ""
echo "3. Creating test file..."
ffmpeg -f lavfi -i anullsrc=r=44100:cl=mono -t 1 -q:a 9 -acodec libmp3lame test_audio.mp3 -y 2>/dev/null
echo "✅ Test file created: test_audio.mp3"

# Test detection
echo ""
echo "4. Testing file detection..."
curl -X POST -F "file=@test_audio.mp3" http://localhost:8000/detect 2>/dev/null | jq '.'

# Test conversion
echo ""
echo "5. Testing file conversion..."
curl -X POST \
    -F "file=@test_audio.mp3" \
    -F "output_format=wav" \
    -F "quality=high" \
    http://localhost:8000/convert \
    --output test_output.wav 2>/dev/null

if [ -f test_output.wav ]; then
    echo "✅ Conversion successful: test_output.wav"
    ls -lh test_output.wav
else
    echo "❌ Conversion failed"
fi

# Cleanup
echo ""
echo "6. Cleanup..."
rm -f test_audio.mp3 test_output.wav
echo "✅ Test files removed"

echo ""
echo "✨ Test suite completed!"
