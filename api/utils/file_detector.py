"""
Intelligent File Type Detector
Uses multiple detection methods:
1. Magic bytes (file signature)
2. File extension analysis
3. Metadata extraction
4. Content inspection
"""

import magic
import mimetypes
from pathlib import Path
from typing import Dict, Optional
import logging
import subprocess
import json

logger = logging.getLogger(__name__)


class FileDetector:
    """Intelligent file type detection with multiple fallback methods"""
    
    # Common magic bytes for media files
    MAGIC_BYTES = {
        b'ID3': 'mp3',
        b'\xff\xfb': 'mp3',
        b'\xff\xf3': 'mp3',
        b'\xff\xf2': 'mp3',
        b'RIFF': 'wav',
        b'fLaC': 'flac',
        b'OggS': 'ogg',
        b'\x00\x00\x00\x18ftypmp42': 'mp4',
        b'\x00\x00\x00\x20ftypisom': 'mp4',
        b'\x00\x00\x00\x1cftyp': 'mp4',
        b'\x1aE\xdf\xa3': 'webm',
        b'RIFF....WEBP': 'webp',
        b'GIF87a': 'gif',
        b'GIF89a': 'gif',
    }
    
    def __init__(self):
        """Initialize the file detector"""
        # Try to initialize python-magic
        try:
            self.magic = magic.Magic(mime=True)
            self.magic_available = True
        except:
            self.magic = None
            self.magic_available = False
            logger.warning("python-magic not available, using fallback detection")
    
    async def detect(self, file_path: Path) -> Dict:
        """
        Detect file type using multiple methods
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            Dictionary with detection results and metadata
        """
        detected_format = None
        detected_type = None
        confidence = 0.0
        
        # Method 1: Magic bytes
        magic_format = self._detect_by_magic_bytes(file_path)
        if magic_format:
            detected_format = magic_format
            confidence = 0.9
            logger.info(f"Detected by magic bytes: {magic_format}")
        
        # Method 2: MIME type detection
        if not detected_format and self.magic_available:
            mime_format = self._detect_by_mime(file_path)
            if mime_format:
                detected_format = mime_format
                confidence = 0.8
                logger.info(f"Detected by MIME: {mime_format}")
        
        # Method 3: FFprobe metadata
        ffprobe_result = self._detect_by_ffprobe(file_path)
        if ffprobe_result:
            if not detected_format:
                detected_format = ffprobe_result.get('format', 'unknown')
                confidence = 0.95
            detected_type = ffprobe_result.get('type', 'unknown')
            metadata = ffprobe_result.get('metadata', {})
        else:
            metadata = {}
        
        # Method 4: Extension fallback
        if not detected_format:
            ext = file_path.suffix.lstrip('.').lower()
            if ext:
                detected_format = ext
                confidence = 0.5
                logger.info(f"Detected by extension: {ext}")
        
        # Determine media type
        if not detected_type:
            detected_type = self._determine_media_type(detected_format)
        
        # Generate suggested formats
        suggested_formats = self._suggest_formats(detected_type)
        
        return {
            'detected_type': detected_type,
            'detected_format': detected_format or 'unknown',
            'confidence': confidence,
            'metadata': metadata,
            'suggested_formats': suggested_formats
        }
    
    def _detect_by_magic_bytes(self, file_path: Path) -> Optional[str]:
        """Detect format by reading magic bytes"""
        try:
            with open(file_path, 'rb') as f:
                header = f.read(32)
                
                for magic_bytes, format_name in self.MAGIC_BYTES.items():
                    if header.startswith(magic_bytes):
                        return format_name
                
                # Special case for MP4 variants
                if b'ftyp' in header[:32]:
                    return 'mp4'
                    
        except Exception as e:
            logger.error(f"Magic bytes detection error: {e}")
        
        return None
    
    def _detect_by_mime(self, file_path: Path) -> Optional[str]:
        """Detect format using MIME type"""
        try:
            if self.magic_available:
                mime_type = self.magic.from_file(str(file_path))
                
                # Convert MIME to format
                mime_to_format = {
                    'audio/mpeg': 'mp3',
                    'audio/wav': 'wav',
                    'audio/x-wav': 'wav',
                    'audio/flac': 'flac',
                    'audio/ogg': 'ogg',
                    'audio/aac': 'aac',
                    'audio/mp4': 'm4a',
                    'video/mp4': 'mp4',
                    'video/x-msvideo': 'avi',
                    'video/quicktime': 'mov',
                    'video/x-matroska': 'mkv',
                    'video/webm': 'webm',
                    'image/gif': 'gif',
                }
                
                return mime_to_format.get(mime_type)
                
        except Exception as e:
            logger.error(f"MIME detection error: {e}")
        
        return None
    
    def _detect_by_ffprobe(self, file_path: Path) -> Optional[Dict]:
        """Use FFprobe to extract detailed metadata"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                str(file_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                
                format_info = data.get('format', {})
                streams = data.get('streams', [])
                
                # Extract metadata
                metadata = {
                    'duration': float(format_info.get('duration', 0)),
                    'bitrate': int(format_info.get('bit_rate', 0)),
                    'format': format_info.get('format_name', '').split(',')[0],
                }
                
                # Determine if audio or video
                has_video = any(s.get('codec_type') == 'video' for s in streams)
                has_audio = any(s.get('codec_type') == 'audio' for s in streams)
                
                media_type = 'video' if has_video else 'audio' if has_audio else 'unknown'
                
                # Extract stream-specific metadata
                for stream in streams:
                    codec_type = stream.get('codec_type')
                    
                    if codec_type == 'video':
                        metadata['width'] = stream.get('width')
                        metadata['height'] = stream.get('height')
                        metadata['codec'] = stream.get('codec_name')
                    
                    elif codec_type == 'audio':
                        metadata['sample_rate'] = stream.get('sample_rate')
                        metadata['channels'] = stream.get('channels')
                        if not metadata.get('codec'):
                            metadata['codec'] = stream.get('codec_name')
                
                return {
                    'type': media_type,
                    'format': metadata.get('format'),
                    'metadata': metadata
                }
                
        except subprocess.TimeoutExpired:
            logger.warning("FFprobe timeout - file may be very large or corrupted")
            # Return basic info even on timeout
            return {
                'type': 'unknown',
                'format': 'unknown',
                'metadata': {'error': 'timeout', 'note': 'File too large for quick analysis'}
            }
        except Exception as e:
            logger.warning(f"FFprobe detection error: {e}")
            # Still try to provide basic detection
            return {
                'type': 'unknown',
                'format': 'unknown',
                'metadata': {'error': str(e)}
            }
        
        return None
    
    def _determine_media_type(self, format_name: str) -> str:
        """Determine if format is audio or video"""
        audio_formats = {'mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a', 'wma', 'opus'}
        video_formats = {'mp4', 'avi', 'mov', 'mkv', 'webm', 'flv', 'wmv', 'gif'}
        
        if format_name in audio_formats:
            return 'audio'
        elif format_name in video_formats:
            return 'video'
        else:
            return 'unknown'
    
    def _suggest_formats(self, media_type: str) -> list:
        """Suggest appropriate output formats based on media type"""
        if media_type == 'audio':
            return ['mp3', 'wav', 'aac', 'flac', 'ogg', 'm4a']
        elif media_type == 'video':
            return ['mp4', 'webm', 'avi', 'mov', 'mkv', 'gif']
        else:
            # For unknown files, suggest both audio and video formats
            return ['mp3', 'wav', 'mp4', 'webm', 'aac', 'flac']
