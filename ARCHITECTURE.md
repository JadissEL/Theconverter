# System Architecture Document

## Overview

TheConverter is a full-stack web application designed for high-performance media file conversion with intelligent format detection. The system follows a client-server architecture with serverless deployment capabilities.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                             │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────┐             │
│  │  Browser   │  │   Mobile    │  │  Desktop     │             │
│  │  (Chrome)  │  │  (Safari)   │  │  (Edge)      │             │
│  └─────┬──────┘  └──────┬──────┘  └──────┬───────┘             │
│        └─────────────────┴────────────────┘                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTPS/REST
┌──────────────────────────▼──────────────────────────────────────┐
│                   Presentation Layer (Next.js)                   │
│  ┌──────────────────────────────────────────────────────┐       │
│  │  React Components                                     │       │
│  │  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  │       │
│  │  │FileUploader │  │ConversionPanel│  │ StatusBar  │  │       │
│  │  └─────────────┘  └──────────────┘  └────────────┘  │       │
│  └──────────────────────────────────────────────────────┘       │
│  ┌──────────────────────────────────────────────────────┐       │
│  │  State Management (React Hooks)                       │       │
│  └──────────────────────────────────────────────────────┘       │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP API Calls
┌──────────────────────────▼──────────────────────────────────────┐
│                   API Gateway Layer                              │
│  ┌──────────────────────────────────────────────────────┐       │
│  │  FastAPI Application                                  │       │
│  │  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  │       │
│  │  │   /detect   │  │  /convert    │  │  /cleanup  │  │       │
│  │  └─────────────┘  └──────────────┘  └────────────┘  │       │
│  └──────────────────────────────────────────────────────┘       │
│  ┌──────────────────────────────────────────────────────┐       │
│  │  Middleware (CORS, Validation, Error Handling)        │       │
│  └──────────────────────────────────────────────────────┘       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                   Business Logic Layer                           │
│  ┌─────────────────────┐      ┌─────────────────────┐           │
│  │  FileDetector       │      │  MediaConverter     │           │
│  │  ┌───────────────┐  │      │  ┌───────────────┐ │           │
│  │  │ Magic Bytes   │  │      │  │ Codec Select  │ │           │
│  │  │ MIME Analysis │  │      │  │ Quality Opt   │ │           │
│  │  │ FFprobe Meta  │  │      │  │ FFmpeg Exec   │ │           │
│  │  │ Extension     │  │      │  │ Validation    │ │           │
│  │  └───────────────┘  │      │  └───────────────┘ │           │
│  └─────────────────────┘      └─────────────────────┘           │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                   Processing Engine Layer                        │
│  ┌──────────────────────────────────────────────────────┐       │
│  │  FFmpeg                                               │       │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌────────┐ │       │
│  │  │ Decoder │→ │ Filter  │→ │ Encoder │→ │ Muxer  │ │       │
│  │  └─────────┘  └─────────┘  └─────────┘  └────────┘ │       │
│  └──────────────────────────────────────────────────────┘       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                   Storage Layer                                  │
│  ┌─────────────────┐  ┌──────────────┐  ┌─────────────┐        │
│  │ Temporary Files │  │ Cloud Storage│  │ Cache Layer │        │
│  │ (/tmp)          │  │ (Optional)   │  │ (Optional)  │        │
│  └─────────────────┘  └──────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Frontend Components

#### FileUploader Component
**Purpose**: Handle file upload and initial detection

**Responsibilities**:
- Drag-and-drop interface
- File validation (size, type)
- Upload to backend
- Display file metadata
- Error handling

**Data Flow**:
```
User Drop File → Validate → Upload to /detect → Display Metadata
```

#### ConversionPanel Component
**Purpose**: Manage conversion process and options

**Responsibilities**:
- Format selection UI
- Quality preset selection
- Conversion initiation
- Progress tracking
- Download management

**Data Flow**:
```
Select Format → Choose Quality → POST /convert → Track Progress → Download
```

### 2. Backend Components

#### FileDetector Class
**Purpose**: Intelligent file type detection

**Detection Methods** (Priority Order):
1. **Magic Bytes** (90% confidence)
   - Read first 32 bytes
   - Match against known signatures
   - Fast and reliable

2. **MIME Type** (80% confidence)
   - Use python-magic library
   - OS-level file type detection
   - Fallback if magic bytes fail

3. **FFprobe Metadata** (95% confidence)
   - Extract full metadata
   - Determine codec information
   - Most accurate but slower

4. **Extension Analysis** (50% confidence)
   - Last resort fallback
   - Use file extension
   - Least reliable

**Output**:
```python
{
    "detected_type": "video",
    "detected_format": "mp4",
    "confidence": 0.95,
    "metadata": {
        "duration": 120.5,
        "width": 1920,
        "height": 1080,
        "codec": "h264",
        "bitrate": 2500000
    },
    "suggested_formats": ["mp4", "webm", "avi", ...]
}
```

#### MediaConverter Class
**Purpose**: High-performance media conversion

**Conversion Pipeline**:

```
Input File
    ↓
[Validation]
    ↓
[Format Detection]
    ↓
[Codec Selection] ← Quality Preset
    ↓
[FFmpeg Command Building]
    ↓
[Async Execution]
    ↓
[Output Validation]
    ↓
Output File
```

**Quality Optimization**:

| Preset | Audio | Video | Use Case |
|--------|-------|-------|----------|
| Low    | 96k   | 500k  | Quick preview |
| Medium | 128k  | 1000k | Web streaming |
| High   | 192k  | 2500k | High quality |
| Ultra  | 320k  | 5000k | Archival |

**Codec Selection Logic**:
```python
def select_codec(output_format, input_metadata):
    if is_audio_format(output_format):
        return AUDIO_CODECS[output_format]
    else:
        # Intelligent selection based on:
        # - Output format requirements
        # - Input codec compatibility
        # - Quality preset
        # - Hardware acceleration availability
        return optimal_codec
```

### 3. API Endpoints

#### POST /detect
**Purpose**: Detect file type and extract metadata

**Request**:
```
multipart/form-data
- file: binary
```

**Response**:
```json
{
    "detected_type": "audio",
    "detected_format": "mp3",
    "confidence": 0.9,
    "metadata": {...},
    "suggested_formats": [...]
}
```

**Processing Time**: < 1 second

#### POST /convert
**Purpose**: Convert media file to target format

**Request**:
```
multipart/form-data
- file: binary
- output_format: string
- quality: string (low|medium|high|ultra)
```

**Response**:
```
binary file (streamed)
Content-Type: application/{format}
Content-Disposition: attachment; filename="output.{ext}"
```

**Processing Time**: Varies by file size and quality

#### DELETE /cleanup
**Purpose**: Clean old temporary files

**Response**:
```json
{
    "status": "success",
    "deleted_files": 5
}
```

## Data Flow Diagrams

### File Upload Flow

```
┌──────┐     ┌──────────┐     ┌─────────┐     ┌──────────┐
│Client│────▶│FileUpload│────▶│FastAPI  │────▶│Detector  │
└──────┘     │Component │     │/detect  │     └─────┬────┘
              └──────────┘     └─────────┘           │
                                    ▲                │
                                    │                ▼
                                    │         ┌──────────┐
                                    └─────────│FFprobe   │
                                              └──────────┘
```

### Conversion Flow

```
┌──────┐     ┌───────────┐     ┌─────────┐     ┌──────────┐
│Client│────▶│Conversion │────▶│FastAPI  │────▶│Converter │
└───┬──┘     │Panel      │     │/convert │     └────┬─────┘
    │        └───────────┘     └─────────┘          │
    │                                               ▼
    │                                        ┌──────────┐
    │                                        │FFmpeg    │
    │                                        └────┬─────┘
    │                                             │
    │        ┌──────────┐                        ▼
    └────────│Download  │◀───────────────┌──────────┐
             └──────────┘                 │Output    │
                                          └──────────┘
```

## Technology Stack Justification

### Frontend: Next.js + TypeScript

**Why Next.js?**
- Server-side rendering for better SEO
- API routes for backend integration
- Optimized bundling and code splitting
- Excellent developer experience
- Easy Vercel deployment

**Why TypeScript?**
- Type safety reduces bugs
- Better IDE support
- Self-documenting code
- Easier refactoring

### Backend: FastAPI + Python

**Why FastAPI?**
- High performance (comparable to Node.js)
- Automatic API documentation
- Async support for concurrent requests
- Pydantic validation
- Easy to test

**Why Python?**
- Excellent libraries for media processing
- FFmpeg Python bindings
- Easy subprocess management
- Rich ecosystem

### Processing: FFmpeg

**Why FFmpeg?**
- Industry standard
- Supports 100+ formats
- Highly optimized
- Extensive codec support
- Command-line flexibility

## Scalability Considerations

### Horizontal Scaling

**Frontend**:
- Stateless Next.js deployment
- CDN for static assets
- Edge functions for API routes

**Backend**:
- Serverless functions (auto-scale)
- Stateless API design
- Shared nothing architecture

### Vertical Scaling

**Resource Allocation**:
- Memory: 3008MB per function
- CPU: Proportional to memory
- Timeout: 300 seconds max

**Optimization**:
- Streaming for large files
- Progressive upload/download
- Chunked processing

### Caching Strategy

**Client-Side**:
- Service worker for offline support
- Local storage for preferences
- IndexedDB for large data

**Server-Side**:
- Redis for conversion cache
- CDN for static content
- Smart invalidation

## Security Architecture

### Input Validation

```python
# File size check
if file.size > MAX_FILE_SIZE:
    raise HTTPException(413, "File too large")

# MIME type validation
allowed_types = ['audio/*', 'video/*']
if not matches_allowed_type(file.content_type):
    raise HTTPException(415, "Unsupported media type")

# Content inspection
if contains_malicious_content(file):
    raise HTTPException(400, "Suspicious file content")
```

### Rate Limiting

```python
@app.post("/convert")
@limiter.limit("10/minute")
async def convert_file(...):
    ...
```

### CORS Configuration

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)
```

## Error Handling

### Client-Side

```typescript
try {
    const response = await axios.post('/api/python/convert', formData);
    // Success
} catch (error) {
    if (error.response?.status === 413) {
        // File too large
    } else if (error.response?.status === 415) {
        // Unsupported format
    } else {
        // Generic error
    }
}
```

### Server-Side

```python
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
```

## Monitoring & Logging

### Application Logs

```python
logger.info(f"Conversion started: {filename}")
logger.warning(f"Large file detected: {size}MB")
logger.error(f"Conversion failed: {error}")
```

### Metrics

- Request count
- Conversion success rate
- Average processing time
- Error rate
- File size distribution

### Alerting

- Error rate > 5%
- Average latency > 30s
- Disk usage > 80%
- Memory usage > 90%

## Deployment Architecture

### Vercel Deployment

```
GitHub Repository
       ↓
   [Trigger: git push]
       ↓
   Vercel Build
       ├─ Next.js Build
       └─ Python Function Package
       ↓
   [Deploy]
       ├─ Static Assets → CDN
       ├─ Next.js → Edge Network
       └─ Python API → Serverless Functions
       ↓
   Production
```

### Environment Configuration

```
Development:
- Next.js: localhost:3000
- FastAPI: localhost:8000
- FFmpeg: Local installation

Production:
- Next.js: Vercel Edge Network
- FastAPI: Vercel Serverless Functions
- FFmpeg: Bundled in deployment
```

## Performance Benchmarks

### Expected Performance

| File Size | Format       | Quality | Time    |
|-----------|--------------|---------|---------|
| 10MB      | MP3 → WAV    | High    | ~5s     |
| 50MB      | MP4 → WebM   | High    | ~30s    |
| 100MB     | AVI → MP4    | Ultra   | ~60s    |
| 500MB     | MKV → MP4    | High    | ~180s   |

### Optimization Techniques

1. **Parallel Processing**: Multiple CPU cores
2. **Hardware Acceleration**: GPU encoding (when available)
3. **Smart Caching**: Avoid re-conversion
4. **Streaming**: Progressive upload/download
5. **Compression**: Efficient codec selection

## Future Enhancements

### Phase 2
- Batch conversion
- User authentication
- Conversion history
- Cloud storage integration

### Phase 3
- Real-time streaming conversion
- WebRTC for browser-based processing
- Distributed processing cluster
- Machine learning for quality optimization

### Phase 4
- Mobile applications (iOS/Android)
- Desktop applications (Electron)
- API monetization
- Enterprise features
