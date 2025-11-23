# 🎬 TheConverter - Universal Media Converter

A high-performance, intelligent web application for converting any audio or video file to any format. Built with Next.js, FastAPI, and FFmpeg, optimized for deployment on Vercel.

![TheConverter](https://img.shields.io/badge/Next.js-14-black) ![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green) ![FFmpeg](https://img.shields.io/badge/FFmpeg-Powered-blue)

---

## ✨ Features

### 🎯 Core Capabilities
- **Universal File Upload**: Accept any audio/video file, even with unknown or missing extensions
- **Intelligent Detection**: Multi-method file type detection using:
  - Magic byte inspection
  - MIME type analysis
  - FFprobe metadata extraction
  - Extension fallback
- **Smart Conversion**: High-speed transcoding with:
  - Automatic codec selection
  - Quality optimization (Low, Medium, High, Ultra)
  - Parallel processing support
  - Intelligent bitrate management
- **Real-time Progress**: Live conversion status with progress indicators
- **Premium UI**: Modern, Apple-inspired interface with smooth animations

### 🎨 Supported Formats

**Audio Formats:**
- MP3 (MPEG Audio Layer III)
- WAV (Waveform Audio)
- AAC (Advanced Audio Coding)
- FLAC (Lossless Audio)
- OGG (Ogg Vorbis)
- M4A (Apple Audio)

**Video Formats:**
- MP4 (MPEG-4)
- WebM (Web-optimized)
- AVI (Audio Video Interleave)
- MOV (Apple QuickTime)
- MKV (Matroska)
- GIF (Animated)

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ FileUploader │  │ Conversion   │  │  UI          │      │
│  │  Component   │  │  Panel       │  │  Components  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTP/REST API
┌────────────────────────────▼────────────────────────────────┐
│                    Backend (FastAPI)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ File         │  │ Media        │  │  API         │      │
│  │ Detector     │  │ Converter    │  │  Endpoints   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────────┬────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │     FFmpeg      │
                    │  Processing     │
                    └─────────────────┘
```

### Component Breakdown

1. **Frontend (Next.js + TypeScript)**
   - `FileUploader`: Drag-and-drop interface with file analysis
   - `ConversionPanel`: Format selection and conversion controls
   - Real-time status updates and progress tracking

2. **Backend (FastAPI + Python)**
   - `/detect`: Intelligent file type detection endpoint
   - `/convert`: High-performance conversion endpoint
   - `FileDetector`: Multi-method detection system
   - `MediaConverter`: Optimized FFmpeg pipeline

3. **Processing Engine (FFmpeg)**
   - Codec selection and optimization
   - Quality presets
   - Parallel processing
   - Stream manipulation

---

## 🚀 Tech Stack

### Frontend
- **Next.js 14** - React framework with server-side rendering
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **Framer Motion** - Smooth animations
- **React Dropzone** - File upload handling
- **Axios** - HTTP client
- **Lucide React** - Modern icons

### Backend
- **FastAPI** - High-performance Python API framework
- **FFmpeg** - Media processing engine
- **python-magic** - File type detection
- **Pydantic** - Data validation
- **Asyncio** - Asynchronous processing

### Deployment
- **Vercel** - Serverless deployment platform
- **Vercel Serverless Functions** - Python API hosting
- **Edge Network** - Global CDN

---

## 📦 Installation

### Prerequisites
- Node.js 18+ and npm
- Python 3.9+
- FFmpeg installed on your system

### Local Development Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/theconverter.git
cd theconverter
```

2. **Install frontend dependencies**
```bash
npm install
```

3. **Install backend dependencies**
```bash
cd api
pip install -r requirements.txt
cd ..
```

4. **Install FFmpeg** (if not already installed)

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
Download from [ffmpeg.org](https://ffmpeg.org/download.html)

5. **Set up environment variables**
```bash
cp .env.example .env.local
```

Edit `.env.local` with your configuration.

6. **Run the development servers**

Terminal 1 - Frontend:
```bash
npm run dev
```

Terminal 2 - Backend:
```bash
cd api
uvicorn main:app --reload
```

7. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 🌐 Deployment to Vercel

### Step 1: Prepare Your Project

1. **Install Vercel CLI**
```bash
npm i -g vercel
```

2. **Login to Vercel**
```bash
vercel login
```

### Step 2: Configure Environment Variables

In your Vercel project dashboard, add:
- `BLOB_READ_WRITE_TOKEN` (if using Vercel Blob storage)
- `MAX_FILE_SIZE` (optional, default: 524288000)

### Step 3: Deploy

```bash
vercel --prod
```

### Step 4: Custom Domain (Optional)

1. Go to your Vercel project settings
2. Navigate to "Domains"
3. Add your custom domain
4. Update DNS records as instructed

### Important Notes for Vercel Deployment

⚠️ **FFmpeg Limitations**: Vercel serverless functions have a 250MB deployment size limit. For production use, consider:
- Using a Docker-based deployment with FFmpeg pre-installed
- Implementing a separate worker service for heavy conversions
- Using cloud storage for temporary file handling

**Alternative Deployment Options:**
- **Railway**: Better for Python + FFmpeg workloads
- **Render**: Supports Docker containers
- **AWS Lambda**: With custom layers for FFmpeg
- **Google Cloud Run**: Docker-based deployment

---

## 🔧 Configuration

### Quality Presets

The converter supports 4 quality levels:

| Quality | Audio Bitrate | Video Bitrate | Use Case |
|---------|---------------|---------------|----------|
| Low     | 96k           | 500k          | Fast conversion, smaller files |
| Medium  | 128k          | 1000k         | Balanced quality/size |
| High    | 192k          | 2500k         | Good quality (default) |
| Ultra   | 320k          | 5000k         | Maximum quality |

### Codec Selection

The system automatically selects optimal codecs:

**Audio:**
- MP3: libmp3lame
- AAC: aac
- WAV: pcm_s16le
- FLAC: flac
- OGG: libvorbis

**Video:**
- MP4: libx264 + aac
- WebM: libvpx-vp9 + libopus
- AVI: mpeg4 + mp3
- MOV: libx264 + aac
- MKV: libx264 + aac

---

## 🎯 Intelligent Conversion Pipeline

### Detection Algorithm

```python
1. Magic Bytes Detection (90% confidence)
   ↓ (if fails)
2. MIME Type Analysis (80% confidence)
   ↓ (if fails)
3. FFprobe Metadata (95% confidence)
   ↓ (if fails)
4. Extension Fallback (50% confidence)
```

### Conversion Optimization

1. **Pre-processing**: File validation and stream analysis
2. **Codec Selection**: Based on input/output formats
3. **Quality Optimization**: Bitrate and resolution calculation
4. **Parallel Processing**: Multi-threaded encoding when possible
5. **Post-processing**: Validation and cleanup

---

## 📁 Project Structure

```
theconverter/
├── app/                      # Next.js app directory
│   ├── globals.css          # Global styles
│   ├── layout.tsx           # Root layout
│   └── page.tsx             # Home page
├── components/              # React components
│   ├── FileUploader.tsx     # File upload component
│   └── ConversionPanel.tsx  # Conversion UI
├── types/                   # TypeScript definitions
│   └── index.ts
├── api/                     # Python backend
│   ├── main.py             # FastAPI application
│   ├── index.py            # Vercel entry point
│   ├── requirements.txt    # Python dependencies
│   ├── models/             # Pydantic models
│   │   └── schemas.py
│   └── utils/              # Utility modules
│       ├── file_detector.py
│       └── media_converter.py
├── public/                 # Static assets
├── vercel.json            # Vercel configuration
├── next.config.js         # Next.js configuration
├── tailwind.config.ts     # Tailwind configuration
├── tsconfig.json          # TypeScript configuration
└── package.json           # Node dependencies
```

---

## 🎨 UI/UX Design

### Design Principles

- **Apple-inspired aesthetic**: Clean, minimal, premium
- **Smooth animations**: Framer Motion for fluid interactions
- **Glass morphism**: Semi-transparent panels with backdrop blur
- **Responsive design**: Mobile-first approach
- **Accessibility**: WCAG 2.1 AA compliant

### Color Palette

- Primary gradient: Purple (#667eea) to Violet (#764ba2)
- Background: Dynamic (light/dark mode)
- Accent: White with transparency
- Success: Green (#10b981)
- Error: Red (#ef4444)

---

## 🔥 Optional Enhancements

### 1. Authentication & User Accounts
```bash
npm install next-auth
```
- User registration and login
- Conversion history tracking
- Saved presets

### 2. Cloud Storage Integration
```bash
npm install @vercel/blob
```
- Persistent file storage
- Download history
- Share converted files

### 3. Batch Conversion
- Upload multiple files
- Queue management
- Parallel processing

### 4. Advanced Options
- Custom codec parameters
- Filters and effects
- Subtitle support
- Metadata editing

### 5. API Monetization
- Usage limits and quotas
- Premium tier with higher limits
- API key management
- Payment integration (Stripe)

### 6. Performance Optimizations
- Redis caching for duplicate conversions
- WebSocket for real-time progress
- CDN for converted file delivery
- Database for analytics

---

## 🐛 Troubleshooting

### Common Issues

**1. FFmpeg not found**
```bash
# Verify FFmpeg installation
ffmpeg -version

# Install if missing (macOS)
brew install ffmpeg
```

**2. Python module errors**
```bash
# Reinstall dependencies
cd api
pip install -r requirements.txt --upgrade
```

**3. CORS errors in development**
- Ensure backend is running on port 8000
- Check `next.config.js` rewrites configuration

**4. File upload fails**
- Check file size limits
- Verify MIME types are allowed
- Check server logs for details

---

## 📊 Performance Metrics

- **Detection Speed**: < 1 second for most files
- **Conversion Speed**: Varies by file size and quality
  - Audio: ~1-2x real-time
  - Video: ~0.5-1x real-time
- **Supported File Size**: Up to 500MB (configurable)
- **Concurrent Conversions**: Limited by serverless function memory

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- FFmpeg team for the powerful media processing engine
- Vercel for the deployment platform
- Next.js team for the amazing framework
- FastAPI for the high-performance Python API framework

---

## 📞 Support

For issues, questions, or contributions:
- 🐛 [Report a bug](https://github.com/yourusername/theconverter/issues)
- 💡 [Request a feature](https://github.com/yourusername/theconverter/issues)
- 📧 Email: support@theconverter.com

---

**Built with ❤️ by Your Team**

*Converting media files shouldn't be complicated. That's why we built TheConverter.*
