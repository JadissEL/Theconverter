#!/bin/bash

# TheConverter Startup Script
# This script starts both frontend and backend servers

echo "🚀 Starting TheConverter..."

# Kill existing processes
pkill -f "next dev" 2>/dev/null
pkill -f "uvicorn main:app" 2>/dev/null
sleep 2

# Start Backend (FastAPI)
echo "📡 Starting Backend API on port 8000..."
cd /workspaces/Theconverter/api
python -m uvicorn main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --timeout-keep-alive 600 \
  --limit-max-requests 0 \
  > /tmp/backend.log 2>&1 &

BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

# Wait for backend to start
sleep 3

# Start Frontend (Next.js)
echo "🌐 Starting Frontend on port 3000..."
cd /workspaces/Theconverter
npm run dev > /tmp/nextjs.log 2>&1 &

FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"

# Wait for frontend to compile
sleep 5

# Check if services are running
echo ""
echo "✅ Services Status:"
curl -s http://localhost:8000/health > /dev/null && echo "   Backend: ✅ Running" || echo "   Backend: ❌ Failed"
curl -s http://localhost:3000 > /dev/null && echo "   Frontend: ✅ Running" || echo "   Frontend: ❌ Failed"

echo ""
echo "📝 Access Points:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📊 Logs:"
echo "   Backend: tail -f /tmp/backend.log"
echo "   Frontend: tail -f /tmp/nextjs.log"
echo ""
echo "🛑 To stop: pkill -f 'next dev' && pkill -f 'uvicorn main:app'"
