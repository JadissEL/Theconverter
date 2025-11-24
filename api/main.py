from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import tempfile
import shutil
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from utils.file_detector import FileDetector
from utils.media_converter import MediaConverter
from utils.segment_processor import SegmentProcessor
from utils.logger import setup_logger, log_with_context
from utils.cache import ConversionCache
from utils.validator import FileValidator
from utils.rate_limiter import RateLimiter, RateLimitConfig
from utils.transcription import get_transcription_engine, TranscriptionResult
from utils.pdf_generator import generate_transcription_pdf
from models.schemas import DetectionResponse, ConversionRequest

# Configure logging
logger = setup_logger('theconverter.api', level=os.getenv('LOG_LEVEL', 'INFO'))

# Initialize utilities
file_detector = FileDetector()
media_converter = MediaConverter()
segment_processor = SegmentProcessor(segment_duration_minutes=1)  # 1 minute segments
file_validator = FileValidator()
conversion_cache = ConversionCache(
    max_cache_size_mb=int(os.getenv('CACHE_SIZE_MB', '1000')),
    max_age_hours=int(os.getenv('CACHE_AGE_HOURS', '24'))
)

# Rate limiter configuration
rate_limiter = RateLimiter(
    RateLimitConfig(
        requests_per_minute=int(os.getenv('RATE_LIMIT_PER_MINUTE', '10')),
        requests_per_hour=int(os.getenv('RATE_LIMIT_PER_HOUR', '100')),
        requests_per_day=int(os.getenv('RATE_LIMIT_PER_DAY', '1000'))
    )
)

# Temporary directory for processing
TEMP_DIR = Path(tempfile.gettempdir()) / "theconverter"
TEMP_DIR.mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting TheConverter API")
    logger.info(f"Temporary directory: {TEMP_DIR}")
    logger.info(f"Cache directory: {conversion_cache.cache_dir}")
    
    # Log cache stats
    cache_stats = conversion_cache.get_stats()
    logger.info(f"Cache: {cache_stats['total_entries']} entries, {cache_stats['total_size_mb']}MB")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down TheConverter API")
    logger.info("Cleaning up temporary files...")


app = FastAPI(
    title="TheConverter API",
    description="Intelligent media conversion API with automatic format detection",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv('ALLOWED_ORIGINS', '*').split(','),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware for rate limiting
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply rate limiting to all requests"""
    # Skip rate limiting for health checks
    if request.url.path in ["/", "/health", "/metrics"]:
        return await call_next(request)
    
    # Get client identifier (IP address)
    client_ip = request.client.host if request.client else "unknown"
    
    # Check rate limit
    allowed, error_msg = await rate_limiter.check_rate_limit(client_ip)
    
    if not allowed:
        logger.warning(f"Rate limit exceeded for {client_ip}: {error_msg}")
        return JSONResponse(
            status_code=429,
            content={"detail": error_msg},
            headers={"Retry-After": "60"}
        )
    
    # Add rate limit headers
    response = await call_next(request)
    remaining = rate_limiter.get_remaining(client_ip)
    response.headers["X-RateLimit-Remaining-Minute"] = str(remaining['minute'])
    response.headers["X-RateLimit-Remaining-Hour"] = str(remaining['hour'])
    response.headers["X-RateLimit-Remaining-Day"] = str(remaining['day'])
    
    return response


# Request logging middleware
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log all requests with timing information"""
    import time
    
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    
    log_with_context(
        logger,
        20,  # INFO level
        f"{request.method} {request.url.path}",
        status_code=response.status_code,
        duration_ms=round(duration * 1000, 2),
        client_ip=request.client.host if request.client else "unknown"
    )
    
    return response

# Temporary directory for processing
TEMP_DIR = Path(tempfile.gettempdir()) / "theconverter"
TEMP_DIR.mkdir(exist_ok=True)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "TheConverter API",
        "version": "2.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check with system information"""
    import psutil
    
    return {
        "status": "healthy",
        "version": "2.0.0",
        "system": {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage(str(TEMP_DIR)).percent
        },
        "cache": conversion_cache.get_stats(),
        "temp_dir": str(TEMP_DIR),
        "ffmpeg_available": media_converter.verify_ffmpeg_available()
    }


@app.get("/metrics")
async def metrics():
    """Prometheus-compatible metrics endpoint"""
    import psutil
    
    cache_stats = conversion_cache.get_stats()
    
    metrics_text = f"""
# HELP theconverter_cache_entries Total number of cache entries
# TYPE theconverter_cache_entries gauge
theconverter_cache_entries {cache_stats['total_entries']}

# HELP theconverter_cache_size_bytes Cache size in bytes
# TYPE theconverter_cache_size_bytes gauge
theconverter_cache_size_bytes {cache_stats['total_size_mb'] * 1024 * 1024}

# HELP theconverter_cpu_percent CPU usage percentage
# TYPE theconverter_cpu_percent gauge
theconverter_cpu_percent {psutil.cpu_percent(interval=0.1)}

# HELP theconverter_memory_percent Memory usage percentage
# TYPE theconverter_memory_percent gauge
theconverter_memory_percent {psutil.virtual_memory().percent}
    """
    
    return JSONResponse(content=metrics_text, media_type="text/plain")


@app.post("/detect", response_model=DetectionResponse)
async def detect_file(file: UploadFile = File(...)):
    """
    Detect file type and extract metadata using intelligent detection.
    Supports files with missing or incorrect extensions.
    """
    temp_path = None
    try:
        # Save uploaded file temporarily
        temp_path = TEMP_DIR / f"detect_{file.filename}"
        
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        log_with_context(
            logger, 20, "File detection started",
            filename=file.filename,
            size_bytes=temp_path.stat().st_size
        )
        
        # Validate file
        is_valid, errors = file_validator.full_validation(temp_path)
        if not is_valid:
            logger.warning(f"File validation failed: {errors}")
            raise HTTPException(status_code=400, detail=f"File validation failed: {'; '.join(errors)}")
        
        # Detect file type and extract metadata
        detection_result = await file_detector.detect(temp_path)
        
        log_with_context(
            logger, 20, "Detection complete",
            format=detection_result['detected_format'],
            confidence=detection_result['confidence']
        )
        
        return JSONResponse(content=detection_result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Detection error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")
        
    finally:
        # Cleanup
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file: {e}")


@app.post("/convert")
async def convert_file(
    file: UploadFile = File(...),
    output_format: str = Form(...),
    quality: str = Form(default="high")
):
    """
    Convert media file to specified format with intelligent optimization.
    
    Args:
        file: Input media file
        output_format: Desired output format (mp3, mp4, wav, etc.)
        quality: Quality preset (low, medium, high, ultra)
    """
    input_path = None
    output_path = None
    cached_file = None
    
    try:
        # Validate output format
        if not output_format or len(output_format) > 10:
            raise HTTPException(status_code=400, detail="Invalid output format")
        
        # Save uploaded file
        input_filename = f"input_{file.filename}"
        input_path = TEMP_DIR / input_filename
        
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        log_with_context(
            logger, 20, "Conversion started",
            filename=file.filename,
            output_format=output_format,
            quality=quality,
            size_bytes=input_path.stat().st_size
        )
        
        # Validate file
        is_valid, errors = file_validator.full_validation(input_path)
        if not is_valid:
            logger.warning(f"File validation failed: {errors}")
            raise HTTPException(status_code=400, detail=f"File validation failed: {'; '.join(errors)}")
        
        # Check cache first
        cached_file = await conversion_cache.get(input_path, output_format, quality)
        if cached_file:
            logger.info(f"Cache hit for {file.filename}")
            return FileResponse(
                path=str(cached_file),
                filename=f"{Path(file.filename).stem}_converted.{output_format}",
                media_type=f"application/{output_format}"
            )
        
        logger.info("Cache miss - performing conversion")
        
        # Detect input file type
        detection = await file_detector.detect(input_path)
        
        # Get file duration to decide on processing method
        file_duration = detection.get('metadata', {}).get('duration', 0)
        file_size_mb = input_path.stat().st_size / (1024 * 1024)
        
        # Use segment processing for large files (>5 minutes or >50MB)
        use_segmentation = file_duration > 300 or file_size_mb > 50
        
        # Generate output filename
        base_name = Path(file.filename).stem
        output_filename = f"{base_name}_converted.{output_format}"
        output_path = TEMP_DIR / output_filename
        
        if use_segmentation:
            logger.info(f"Using segment processing for large file (duration: {file_duration}s, size: {file_size_mb:.1f}MB)")
            
            # Process using segments - pass detected format for splitting
            detected_format = detection.get('format', 'mp4')
            success = await segment_processor.process_large_file(
                input_path=input_path,
                output_path=output_path,
                output_format=output_format,
                quality=quality,
                input_format=detected_format
            )
        else:
            logger.info("Using standard conversion")
            
            # Perform standard conversion
            success = await media_converter.convert(
                input_path=input_path,
                output_path=output_path,
                output_format=output_format,
                quality=quality,
                input_metadata=detection.get('metadata', {})
            )
        
        if not success or not output_path.exists():
            raise HTTPException(status_code=500, detail="Conversion failed")
        
        log_with_context(
            logger, 20, "Conversion successful",
            filename=output_filename,
            output_size_bytes=output_path.stat().st_size
        )
        
        # Store in cache
        await conversion_cache.set(
            input_path,
            output_path,
            output_format,
            quality,
            detection.get('metadata', {})
        )
        
        # Stream the converted file in chunks to avoid memory issues
        def iterfile():
            with open(output_path, mode="rb") as file_like:
                yield from file_like
        
        # Return streaming response for large files
        return StreamingResponse(
            iterfile(),
            media_type=f"audio/{output_format}" if output_format in ['mp3', 'wav', 'aac', 'flac', 'ogg', 'm4a'] else f"video/{output_format}",
            headers={
                "Content-Disposition": f'attachment; filename="{output_filename}"',
                "Content-Length": str(output_path.stat().st_size),
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Conversion error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")
    
    finally:
        # Cleanup input file immediately
        if input_path and input_path.exists():
            try:
                input_path.unlink()
            except:
                pass


@app.delete("/cleanup")
async def cleanup_temp_files():
    """Clean up temporary files older than 1 hour"""
    try:
        import time
        current_time = time.time()
        deleted_count = 0
        freed_bytes = 0
        
        for file_path in TEMP_DIR.iterdir():
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > 3600:  # 1 hour
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    deleted_count += 1
                    freed_bytes += file_size
        
        logger.info(f"Cleanup: deleted {deleted_count} files, freed {freed_bytes / 1024 / 1024:.2f}MB")
        
        return {
            "status": "success",
            "deleted_files": deleted_count,
            "freed_mb": round(freed_bytes / 1024 / 1024, 2)
        }
        
    except Exception as e:
        logger.error(f"Cleanup error: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}


@app.post("/cache/clear")
async def clear_cache():
    """Clear conversion cache"""
    try:
        stats_before = conversion_cache.get_stats()
        conversion_cache.clear()
        
        logger.info(f"Cache cleared: {stats_before['total_entries']} entries, {stats_before['total_size_mb']}MB")
        
        return {
            "status": "success",
            "cleared_entries": stats_before['total_entries'],
            "freed_mb": stats_before['total_size_mb']
        }
    except Exception as e:
        logger.error(f"Cache clear error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cache/stats")
async def cache_stats():
    """Get cache statistics"""
    return conversion_cache.get_stats()


@app.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    num_speakers: Optional[int] = Form(None),
    language: Optional[str] = Form(None),
    model_size: str = Form("base"),
    request: Request = None
):
    """
    Transcribe audio/video file with speaker diarization
    
    Args:
        file: Audio or video file
        num_speakers: Expected number of speakers (None for auto-detect)
        language: Language code (None for auto-detect)
        model_size: Whisper model size (tiny, base, small, medium, large)
    
    Returns:
        JSON with transcription segments and speaker labels
    """
    input_path = None
    
    try:
        # Rate limiting
        client_ip = request.client.host if request else "unknown"
        if not rate_limiter.check_rate_limit(client_ip):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Validate file
        validation = await file_validator.validate_file(file)
        if not validation.is_valid:
            raise HTTPException(status_code=400, detail=validation.error_message)
        
        log_with_context(
            logger, 20, "Transcription started",
            filename=file.filename,
            size_bytes=file.size,
            num_speakers=num_speakers,
            language=language,
            model=model_size
        )
        
        # Save uploaded file
        input_path = TEMP_DIR / f"transcribe_{file.filename}"
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get transcription engine
        engine = get_transcription_engine(model_size=model_size)
        
        # Perform transcription
        result = await engine.transcribe_with_speakers(
            audio_path=input_path,
            num_speakers=num_speakers,
            language=language
        )
        
        log_with_context(
            logger, 20, "Transcription complete",
            segments=len(result.segments),
            speakers=len(result.speakers),
            duration=result.duration
        )
        
        # Return result as JSON
        return JSONResponse(content=result.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcription error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    
    finally:
        # Cleanup input file
        if input_path and input_path.exists():
            try:
                input_path.unlink()
            except:
                pass


@app.post("/transcribe/pdf")
async def generate_transcription_pdf_endpoint(
    file: UploadFile = File(...),
    num_speakers: Optional[int] = Form(None),
    language: Optional[str] = Form(None),
    model_size: str = Form("base"),
    speaker_filter: Optional[str] = Form(None),
    title: str = Form("Interview Transcription"),
    include_timestamps: bool = Form(True),
    request: Request = None
):
    """
    Transcribe audio and generate PDF
    
    Args:
        file: Audio or video file
        num_speakers: Expected number of speakers
        language: Language code
        model_size: Whisper model size
        speaker_filter: Optional speaker to filter (e.g., "Speaker 1")
        title: PDF title
        include_timestamps: Include timestamps in PDF
    
    Returns:
        PDF file
    """
    input_path = None
    
    try:
        # Rate limiting
        client_ip = request.client.host if request else "unknown"
        if not rate_limiter.check_rate_limit(client_ip):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Validate file
        validation = await file_validator.validate_file(file)
        if not validation.is_valid:
            raise HTTPException(status_code=400, detail=validation.error_message)
        
        log_with_context(
            logger, 20, "PDF transcription started",
            filename=file.filename,
            speaker_filter=speaker_filter
        )
        
        # Save uploaded file
        input_path = TEMP_DIR / f"transcribe_pdf_{file.filename}"
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get transcription engine
        engine = get_transcription_engine(model_size=model_size)
        
        # Perform transcription
        result = await engine.transcribe_with_speakers(
            audio_path=input_path,
            num_speakers=num_speakers,
            language=language
        )
        
        # Generate PDF
        pdf_bytes = generate_transcription_pdf(
            transcription=result,
            speaker_filter=speaker_filter,
            title=title,
            include_timestamps=include_timestamps
        )
        
        # Determine filename
        base_name = Path(file.filename).stem
        if speaker_filter:
            pdf_filename = f"{base_name}_{speaker_filter.replace(' ', '_')}.pdf"
        else:
            pdf_filename = f"{base_name}_transcription.pdf"
        
        log_with_context(
            logger, 20, "PDF generated",
            filename=pdf_filename,
            size_bytes=len(pdf_bytes)
        )
        
        # Return PDF
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{pdf_filename}"',
                "Content-Length": str(len(pdf_bytes))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF generation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
    
    finally:
        # Cleanup input file
        if input_path and input_path.exists():
            try:
                input_path.unlink()
            except:
                pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv('PORT', '8000')),
        log_level="info",
        access_log=True
    )
