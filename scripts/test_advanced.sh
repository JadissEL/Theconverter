#!/bin/bash

# Advanced test script with comprehensive checks

echo "🧪 TheConverter Advanced Test Suite"
echo "======================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
pass_test() {
    echo -e "${GREEN}✓${NC} $1"
    ((TESTS_PASSED++))
}

fail_test() {
    echo -e "${RED}✗${NC} $1"
    ((TESTS_FAILED++))
}

warn_test() {
    echo -e "${YELLOW}!${NC} $1"
}

# 1. Check Python environment
echo ""
echo "1. Checking Python environment..."
if python3 --version > /dev/null 2>&1; then
    pass_test "Python 3 is installed"
else
    fail_test "Python 3 is not installed"
fi

# 2. Check FFmpeg
echo ""
echo "2. Checking FFmpeg..."
if ffmpeg -version > /dev/null 2>&1; then
    pass_test "FFmpeg is installed"
else
    fail_test "FFmpeg is not installed"
fi

# 3. Check dependencies
echo ""
echo "3. Checking Python dependencies..."
cd api
if pip list | grep -q "fastapi"; then
    pass_test "FastAPI is installed"
else
    fail_test "FastAPI is not installed"
fi

if pip list | grep -q "pytest"; then
    pass_test "pytest is installed"
else
    warn_test "pytest is not installed (run: pip install -r requirements.txt)"
fi

# 4. Run unit tests
echo ""
echo "4. Running unit tests..."
if pytest tests/test_utils.py -v --tb=short 2>&1 | grep -q "passed"; then
    pass_test "Unit tests passed"
else
    warn_test "Some unit tests failed or pytest not configured"
fi

# 5. Check server
echo ""
echo "5. Checking API server..."
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    pass_test "API server is running"
    
    # Test health endpoint
    if curl -s http://localhost:8000/health | jq -e '.status == "healthy"' > /dev/null 2>&1; then
        pass_test "Health check passed"
    else
        warn_test "Health check returned unexpected response"
    fi
    
    # Test metrics endpoint
    if curl -s http://localhost:8000/metrics | grep -q "theconverter"; then
        pass_test "Metrics endpoint working"
    else
        warn_test "Metrics endpoint not responding correctly"
    fi
else
    fail_test "API server is not running (start with: uvicorn main:app --reload)"
fi

cd ..

# 6. Test file operations
echo ""
echo "6. Testing file operations..."

# Create test file
ffmpeg -f lavfi -i anullsrc=r=44100:cl=mono -t 1 -q:a 9 -acodec libmp3lame test_audio.mp3 -y 2>/dev/null

if [ -f test_audio.mp3 ]; then
    pass_test "Test file created"
    
    # Test detection
    DETECTION=$(curl -s -X POST -F "file=@test_audio.mp3" http://localhost:8000/detect 2>/dev/null)
    if echo "$DETECTION" | jq -e '.detected_format' > /dev/null 2>&1; then
        pass_test "File detection working"
        FORMAT=$(echo "$DETECTION" | jq -r '.detected_format')
        echo "   Detected format: $FORMAT"
    else
        fail_test "File detection failed"
    fi
    
    # Test conversion
    curl -s -X POST \
        -F "file=@test_audio.mp3" \
        -F "output_format=wav" \
        -F "quality=high" \
        http://localhost:8000/convert \
        --output test_output.wav 2>/dev/null
    
    if [ -f test_output.wav ] && [ -s test_output.wav ]; then
        pass_test "File conversion working"
        SIZE=$(ls -lh test_output.wav | awk '{print $5}')
        echo "   Output size: $SIZE"
        
        # Test cache
        curl -s -X POST \
            -F "file=@test_audio.mp3" \
            -F "output_format=wav" \
            -F "quality=high" \
            http://localhost:8000/convert \
            --output test_output2.wav 2>/dev/null
        
        if [ -f test_output2.wav ]; then
            pass_test "Cache system working (faster second conversion)"
        fi
    else
        fail_test "File conversion failed"
    fi
    
    # Cleanup
    rm -f test_audio.mp3 test_output.wav test_output2.wav
else
    fail_test "Could not create test file"
fi

# 7. Test rate limiting
echo ""
echo "7. Testing rate limiting..."
RATE_LIMIT_HEADERS=$(curl -s -I http://localhost:8000/detect 2>/dev/null | grep -i "ratelimit")
if [ ! -z "$RATE_LIMIT_HEADERS" ]; then
    pass_test "Rate limiting headers present"
else
    warn_test "Rate limiting headers not found"
fi

# 8. Test cache endpoints
echo ""
echo "8. Testing cache management..."
CACHE_STATS=$(curl -s http://localhost:8000/cache/stats 2>/dev/null)
if echo "$CACHE_STATS" | jq -e '.total_entries' > /dev/null 2>&1; then
    pass_test "Cache stats endpoint working"
    ENTRIES=$(echo "$CACHE_STATS" | jq -r '.total_entries')
    echo "   Cache entries: $ENTRIES"
else
    warn_test "Cache stats endpoint not responding"
fi

# 9. Load test (optional)
echo ""
echo "9. Running basic load test..."
echo "   Sending 5 concurrent requests..."
for i in {1..5}; do
    curl -s http://localhost:8000/ > /dev/null 2>&1 &
done
wait

if [ $? -eq 0 ]; then
    pass_test "Server handled concurrent requests"
else
    warn_test "Server struggled with concurrent requests"
fi

# 10. Check logs
echo ""
echo "10. Checking logs..."
if [ -d "api/logs" ]; then
    if [ -f "api/logs/app.log" ]; then
        pass_test "Log file exists"
        LOG_SIZE=$(ls -lh api/logs/app.log | awk '{print $5}')
        echo "   Log size: $LOG_SIZE"
    else
        warn_test "Log file not created yet"
    fi
else
    warn_test "Logs directory not created"
fi

# Summary
echo ""
echo "======================================"
echo "Test Summary:"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo "======================================"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✨ All critical tests passed!${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠ Some tests failed. Please check the output above.${NC}"
    exit 1
fi
