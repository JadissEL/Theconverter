# Transcription Feature - Documentation

## Overview

TheConverter now includes advanced AI-powered transcription with speaker diarization (speaker detection and separation).

## Features

✅ **Automatic Speech Recognition (ASR)** using OpenAI Whisper
✅ **Speaker Diarization** - Automatically detect and label different speakers
✅ **Multi-language Support** - Auto-detect or specify language
✅ **PDF Export** - Download transcriptions as professional PDFs
✅ **Speaker Filtering** - Export transcripts for specific speakers only
✅ **Timestamps** - Precise time markers for each segment
✅ **Multiple Quality Levels** - Choose from tiny to large models

## Installation

### Quick Install

```bash
cd /workspaces/Theconverter
./scripts/install_transcription.sh
```

### Manual Install

```bash
cd api
pip install torch==2.1.2 torchaudio==2.1.2 --index-url https://download.pytorch.org/whl/cpu
pip install openai-whisper==20231117
pip install soundfile==0.12.1 scipy==1.11.4 scikit-learn==1.3.2
pip install reportlab==4.0.7 PyPDF2==3.0.1
```

## API Endpoints

### 1. Transcribe Audio

**POST** `/transcribe`

Transcribe audio/video with speaker detection.

**Form Data:**
- `file`: Audio or video file
- `num_speakers` (optional): Expected number of speakers (auto-detect if not provided)
- `language` (optional): Language code (e.g., 'en', 'fr', 'es') - auto-detect if not provided
- `model_size` (optional): Whisper model ('tiny', 'base', 'small', 'medium', 'large') - default: 'base'

**Response:**
```json
{
  "segments": [
    {
      "start_time": 0.0,
      "end_time": 3.5,
      "speaker": "Speaker 1",
      "text": "Hello, how are you today?",
      "confidence": 0.95
    },
    {
      "start_time": 3.7,
      "end_time": 6.2,
      "speaker": "Speaker 2",
      "text": "I'm doing great, thanks for asking!",
      "confidence": 0.92
    }
  ],
  "duration": 180.5,
  "speakers": ["Speaker 1", "Speaker 2"],
  "language": "en",
  "model_used": "whisper-base"
}
```

### 2. Generate PDF

**POST** `/transcribe/pdf`

Transcribe audio and generate a downloadable PDF.

**Form Data:**
- `file`: Audio or video file
- `num_speakers` (optional): Expected number of speakers
- `language` (optional): Language code
- `model_size` (optional): Whisper model size
- `speaker_filter` (optional): Filter to specific speaker (e.g., "Speaker 1")
- `title` (optional): PDF title - default: "Interview Transcription"
- `include_timestamps` (optional): Include timestamps - default: true

**Response:** PDF file download

## Usage Examples

### Frontend (React)

```typescript
// Transcribe audio
const formData = new FormData();
formData.append('file', audioFile);
formData.append('num_speakers', '2');
formData.append('language', 'en');
formData.append('model_size', 'base');

const response = await axios.post('/api/python/transcribe', formData);
console.log(response.data.segments);

// Download PDF for Speaker 1 only
formData.append('speaker_filter', 'Speaker 1');
const pdf = await axios.post('/api/python/transcribe/pdf', formData, {
  responseType: 'blob'
});
```

### cURL Examples

```bash
# Basic transcription
curl -X POST "http://localhost:8000/transcribe" \
  -F "file=@interview.mp3" \
  -F "model_size=base"

# Transcription with options
curl -X POST "http://localhost:8000/transcribe" \
  -F "file=@interview.mp3" \
  -F "num_speakers=2" \
  -F "language=en" \
  -F "model_size=small"

# Generate PDF for all speakers
curl -X POST "http://localhost:8000/transcribe/pdf" \
  -F "file=@interview.mp3" \
  -F "num_speakers=2" \
  --output transcript.pdf

# Generate PDF for Speaker 1 only
curl -X POST "http://localhost:8000/transcribe/pdf" \
  -F "file=@interview.mp3" \
  -F "speaker_filter=Speaker 1" \
  --output speaker1.pdf
```

## Model Sizes

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| tiny | 39M | Very Fast | Basic | Quick tests |
| base | 74M | Fast | Good | **Recommended** |
| small | 244M | Medium | Better | High accuracy |
| medium | 769M | Slow | Great | Professional |
| large | 1550M | Very Slow | Best | Critical work |

## Speaker Diarization

The system uses a hybrid approach:

1. **Whisper** provides accurate transcription with word-level timestamps
2. **Audio Clustering** groups segments by speaker using:
   - Energy levels
   - Zero-crossing rate
   - Spectral centroid
   - K-means clustering

### Accuracy Tips

- Specify `num_speakers` if known (improves accuracy)
- Use higher quality models for better results
- Ensure good audio quality (low background noise)
- Works best with 2-4 speakers

## Supported Languages

Auto-detect or specify:
- English (en)
- Spanish (es)
- French (fr)
- German (de)
- Italian (it)
- Portuguese (pt)
- Arabic (ar)
- Chinese (zh)
- Japanese (ja)
- Korean (ko)
- And 90+ more languages!

## PDF Export Features

- Professional formatting with color-coded speakers
- Timestamps for each segment
- Metadata (duration, speakers, language, model)
- Filter by speaker
- Page numbers and watermarks
- A4/Letter page sizes

## Performance

### Typical Processing Times

- **Tiny model**: ~0.5x real-time (1 min audio = 30s processing)
- **Base model**: ~1x real-time (1 min audio = 1 min processing)
- **Small model**: ~2x real-time (1 min audio = 2 min processing)
- **Medium model**: ~4x real-time (1 min audio = 4 min processing)
- **Large model**: ~8x real-time (1 min audio = 8 min processing)

*Times vary based on CPU/GPU and audio complexity*

## Limitations

- First transcription loads the model (10-30 seconds delay)
- Models are loaded into memory (base model: ~140MB RAM)
- CPU-only installation is slower than GPU
- Very long files (>1 hour) may take significant time
- Speaker diarization accuracy depends on audio quality

## Troubleshooting

### "Model not found" error
```bash
# Models download automatically on first use
# Ensure internet connection and wait for download
```

### Slow performance
```bash
# Use smaller model or GPU acceleration
# For GPU: pip install torch torchaudio (without --index-url)
```

### Speaker detection inaccurate
```bash
# Specify num_speakers explicitly
# Use higher quality model
# Ensure speakers have distinct voices
```

## Advanced Configuration

### Environment Variables

```bash
# Whisper cache directory
WHISPER_CACHE_DIR=/tmp/whisper_models

# Default model size
DEFAULT_WHISPER_MODEL=base

# Enable GPU (if available)
TORCH_DEVICE=cuda  # or 'cpu'
```

## Integration with Conversion

The transcription feature works seamlessly with the existing conversion system:

1. Upload file → Auto-detect format
2. **Convert** tab → Convert to any format
3. **Transcribe** tab → Generate transcript with speakers
4. Download → Get both converted media AND transcript PDF

## Credits

- **OpenAI Whisper** - Speech recognition
- **scikit-learn** - Speaker clustering
- **ReportLab** - PDF generation
- **FFmpeg** - Audio preprocessing

## License

Same as main project (see LICENSE file)
