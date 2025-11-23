# Development Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
# Frontend
npm install

# Backend
cd api
pip install -r requirements.txt
cd ..
```

### 2. Install FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install ffmpeg libmagic1
```

**Windows:**
- Download from [ffmpeg.org](https://ffmpeg.org/download.html)
- Add to PATH

### 3. Environment Setup

```bash
cp .env.example .env.local
```

### 4. Run Development Servers

**Terminal 1 - Frontend:**
```bash
npm run dev
```

**Terminal 2 - Backend:**
```bash
cd api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Access Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Testing the API

### Test File Detection

```bash
curl -X POST "http://localhost:8000/detect" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test.mp3"
```

### Test File Conversion

```bash
curl -X POST "http://localhost:8000/convert" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test.mp3" \
  -F "output_format=wav" \
  -F "quality=high" \
  --output converted.wav
```

## Development Tips

### Hot Reload

Both servers support hot reload:
- Frontend: Auto-reloads on file changes
- Backend: Use `--reload` flag with uvicorn

### Debugging

**Frontend:**
- Open Chrome DevTools
- Check Console for errors
- Use React Developer Tools

**Backend:**
- Check terminal output
- Visit `/docs` for interactive API testing
- Add logging: `logger.info("Debug message")`

### Code Quality

```bash
# Lint frontend
npm run lint

# Format Python code
cd api
black .
isort .
```

## Common Issues

### Port Already in Use

```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

### Module Not Found

```bash
# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Python
pip install -r api/requirements.txt --force-reinstall
```
