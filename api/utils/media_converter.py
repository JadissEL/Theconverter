"""
Intelligent Media Converter
High-performance conversion pipeline with:
- Smart codec selection
- Quality optimization
- Parallel processing support
- Fast transcoding techniques
"""

import subprocess
import logging
from pathlib import Path
from typing import Dict, Optional
import asyncio

logger = logging.getLogger(__name__)


class MediaConverter:
    """High-performance media conversion with intelligent optimization"""
    
    # Quality presets for different output levels
    QUALITY_PRESETS = {
        'audio': {
            'low': {'bitrate': '96k', 'sample_rate': 22050},
            'medium': {'bitrate': '128k', 'sample_rate': 44100},
            'high': {'bitrate': '192k', 'sample_rate': 44100},
            'ultra': {'bitrate': '320k', 'sample_rate': 48000},
        },
        'video': {
            'low': {'video_bitrate': '500k', 'audio_bitrate': '96k', 'crf': 28},
            'medium': {'video_bitrate': '1000k', 'audio_bitrate': '128k', 'crf': 23},
            'high': {'video_bitrate': '2500k', 'audio_bitrate': '192k', 'crf': 20},
            'ultra': {'video_bitrate': '5000k', 'audio_bitrate': '320k', 'crf': 18},
        }
    }
    
    # Optimal codec selection
    CODEC_MAP = {
        'mp3': {'audio_codec': 'libmp3lame'},
        'aac': {'audio_codec': 'aac'},
        'm4a': {'audio_codec': 'aac'},
        'wav': {'audio_codec': 'pcm_s16le'},
        'flac': {'audio_codec': 'flac'},
        'ogg': {'audio_codec': 'libvorbis'},
        'mp4': {'video_codec': 'libx264', 'audio_codec': 'aac'},
        'webm': {'video_codec': 'libvpx-vp9', 'audio_codec': 'libopus'},
        'avi': {'video_codec': 'mpeg4', 'audio_codec': 'mp3'},
        'mov': {'video_codec': 'libx264', 'audio_codec': 'aac'},
        'mkv': {'video_codec': 'libx264', 'audio_codec': 'aac'},
        'gif': {'video_codec': 'gif'},
    }
    
    def __init__(self):
        """Initialize the media converter"""
        self._verify_ffmpeg()
    
    def _verify_ffmpeg(self):
        """Verify FFmpeg is available"""
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            logger.info("FFmpeg is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("FFmpeg is not installed or not in PATH")
            raise RuntimeError("FFmpeg is required but not found")
    
    def verify_ffmpeg_available(self) -> bool:
        """Check if FFmpeg is available (for health checks)"""
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, timeout=5)
            return True
        except:
            return False
    
    async def convert(
        self,
        input_path: Path,
        output_path: Path,
        output_format: str,
        quality: str = 'high',
        input_metadata: Optional[Dict] = None
    ) -> bool:
        """
        Convert media file with intelligent optimization
        
        Args:
            input_path: Path to input file
            output_path: Path to output file
            output_format: Desired output format
            quality: Quality preset (low, medium, high, ultra)
            input_metadata: Optional metadata from detection phase
            
        Returns:
            True if conversion successful, False otherwise
        """
        try:
            # Determine if audio or video conversion
            is_audio = self._is_audio_format(output_format)
            media_type = 'audio' if is_audio else 'video'
            
            # Get quality preset
            preset = self.QUALITY_PRESETS[media_type].get(quality, self.QUALITY_PRESETS[media_type]['high'])
            
            # Build FFmpeg command
            cmd = self._build_ffmpeg_command(
                input_path=input_path,
                output_path=output_path,
                output_format=output_format,
                preset=preset,
                input_metadata=input_metadata
            )
            
            logger.info(f"Executing conversion: {' '.join(cmd)}")
            
            # Execute conversion asynchronously
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"Conversion successful: {output_path.name}")
                return True
            else:
                logger.error(f"Conversion failed: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Conversion error: {str(e)}")
            return False
    
    def _build_ffmpeg_command(
        self,
        input_path: Path,
        output_path: Path,
        output_format: str,
        preset: Dict,
        input_metadata: Optional[Dict]
    ) -> list:
        """Build optimized FFmpeg command"""
        
        cmd = [
            'ffmpeg',
            '-i', str(input_path),
            '-y',  # Overwrite output file
        ]
        
        # Get codec configuration
        codec_config = self.CODEC_MAP.get(output_format, {})
        
        # Audio-only conversion
        if self._is_audio_format(output_format):
            # Audio codec
            if 'audio_codec' in codec_config:
                cmd.extend(['-codec:a', codec_config['audio_codec']])
            
            # Bitrate
            if 'bitrate' in preset:
                cmd.extend(['-b:a', preset['bitrate']])
            
            # Sample rate
            if 'sample_rate' in preset:
                cmd.extend(['-ar', str(preset['sample_rate'])])
            
            # Remove video stream if present
            cmd.extend(['-vn'])
            
            # Quality settings for specific formats
            if output_format == 'mp3':
                cmd.extend(['-q:a', '2'])  # VBR quality
            elif output_format == 'flac':
                cmd.extend(['-compression_level', '8'])
        
        # Video conversion
        else:
            # Video codec
            if 'video_codec' in codec_config:
                cmd.extend(['-codec:v', codec_config['video_codec']])
            
            # Audio codec
            if 'audio_codec' in codec_config:
                cmd.extend(['-codec:a', codec_config['audio_codec']])
            
            # Video bitrate
            if 'video_bitrate' in preset:
                cmd.extend(['-b:v', preset['video_bitrate']])
            
            # Audio bitrate
            if 'audio_bitrate' in preset:
                cmd.extend(['-b:a', preset['audio_bitrate']])
            
            # CRF (Constant Rate Factor) for quality
            if 'crf' in preset and codec_config.get('video_codec') in ['libx264', 'libx265']:
                cmd.extend(['-crf', str(preset['crf'])])
            
            # Preset for encoding speed/compression
            if codec_config.get('video_codec') == 'libx264':
                cmd.extend(['-preset', 'medium'])  # Balance speed and quality
            
            # Pixel format for compatibility
            if codec_config.get('video_codec') in ['libx264', 'libx265']:
                cmd.extend(['-pix_fmt', 'yuv420p'])
            
            # Special handling for GIF
            if output_format == 'gif':
                # Generate palette for better quality
                cmd.extend([
                    '-vf', 'fps=10,scale=480:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse',
                    '-loop', '0'
                ])
        
        # Add output path
        cmd.append(str(output_path))
        
        return cmd
    
    def _is_audio_format(self, format_name: str) -> bool:
        """Check if format is audio-only"""
        audio_formats = {'mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a', 'wma', 'opus'}
        return format_name.lower() in audio_formats
    
    def get_supported_formats(self) -> Dict[str, list]:
        """Get list of supported input and output formats"""
        return {
            'audio': ['mp3', 'wav', 'aac', 'flac', 'ogg', 'm4a'],
            'video': ['mp4', 'webm', 'avi', 'mov', 'mkv', 'gif']
        }
