"""
Segment Processor for handling large media files
Divides files into smaller segments for faster processing
"""

import subprocess
import logging
import asyncio
from pathlib import Path
from typing import List, Dict, Optional, Callable
import json
import math

logger = logging.getLogger(__name__)


class SegmentProcessor:
    """Process large media files by dividing them into segments"""
    
    def __init__(self, segment_duration_minutes: int = 1):
        """
        Initialize segment processor
        
        Args:
            segment_duration_minutes: Duration of each segment in minutes (default: 1)
        """
        self.segment_duration = segment_duration_minutes * 60  # Convert to seconds
        self._verify_ffmpeg()
    
    def _verify_ffmpeg(self):
        """Verify FFmpeg is available"""
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, timeout=5)
            logger.info("FFmpeg verified for segment processing")
        except:
            raise RuntimeError("FFmpeg is required for segment processing")
    
    async def get_duration(self, file_path: Path) -> float:
        """Get media file duration in seconds"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                str(file_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                duration = float(data.get('format', {}).get('duration', 0))
                return duration
            
        except Exception as e:
            logger.error(f"Failed to get duration: {e}")
        
        return 0
    
    async def split_into_segments(
        self,
        input_path: Path,
        output_dir: Path,
        progress_callback: Optional[Callable] = None
    ) -> List[Path]:
        """
        Split media file into segments
        
        Args:
            input_path: Path to input file
            output_dir: Directory to save segments
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of segment file paths
        """
        try:
            # Get total duration
            total_duration = await self.get_duration(input_path)
            
            if total_duration == 0:
                logger.error("Could not determine file duration")
                return []
            
            # Calculate number of segments
            num_segments = math.ceil(total_duration / self.segment_duration)
            
            logger.info(f"Splitting {total_duration:.1f}s file into {num_segments} segments of {self.segment_duration}s each")
            
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Detect input format
            input_ext = input_path.suffix.lstrip('.') or 'mp3'
            
            # Split using FFmpeg - use same format as input for copy codec
            segment_pattern = str(output_dir / f"segment_%03d.{input_ext}")
            
            cmd = [
                'ffmpeg',
                '-i', str(input_path),
                '-f', 'segment',
                '-segment_time', str(self.segment_duration),
                '-c', 'copy',  # Copy codec for speed
                '-reset_timestamps', '1',
                '-y',
                segment_pattern
            ]
            
            logger.info(f"Executing split: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Split failed: {stderr.decode()}")
                return []
            
            # Find all created segments (any extension)
            segments = sorted(output_dir.glob("segment_*.*"))
            
            logger.info(f"Created {len(segments)} segments")
            
            if progress_callback:
                await progress_callback(100)
            
            return segments
            
        except Exception as e:
            logger.error(f"Segment splitting error: {e}", exc_info=True)
            return []
    
    async def convert_segments(
        self,
        segments: List[Path],
        output_format: str,
        quality: str = 'high',
        progress_callback: Optional[Callable] = None
    ) -> List[Path]:
        """
        Convert all segments to target format
        
        Args:
            segments: List of segment paths
            output_format: Target format
            quality: Quality preset
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of converted segment paths
        """
        converted_segments = []
        total_segments = len(segments)
        
        for idx, segment in enumerate(segments):
            try:
                output_path = segment.with_suffix(f'.{output_format}')
                
                # Convert segment
                success = await self._convert_segment(
                    segment,
                    output_path,
                    output_format,
                    quality
                )
                
                if success:
                    converted_segments.append(output_path)
                    logger.info(f"Converted segment {idx + 1}/{total_segments}")
                else:
                    logger.error(f"Failed to convert segment {idx + 1}/{total_segments}")
                
                # Report progress
                if progress_callback:
                    progress = ((idx + 1) / total_segments) * 100
                    await progress_callback(progress)
                    
            except Exception as e:
                logger.error(f"Error converting segment {idx + 1}: {e}")
        
        return converted_segments
    
    async def _convert_segment(
        self,
        input_path: Path,
        output_path: Path,
        output_format: str,
        quality: str
    ) -> bool:
        """Convert a single segment"""
        try:
            # Quality presets
            quality_settings = {
                'low': {'bitrate': '96k'},
                'medium': {'bitrate': '128k'},
                'high': {'bitrate': '192k'},
                'ultra': {'bitrate': '320k'},
            }
            
            preset = quality_settings.get(quality, quality_settings['high'])
            
            cmd = [
                'ffmpeg',
                '-i', str(input_path),
                '-b:a', preset['bitrate'],
                '-y',
                str(output_path)
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.wait()
            
            return process.returncode == 0 and output_path.exists()
            
        except Exception as e:
            logger.error(f"Segment conversion error: {e}")
            return False
    
    async def merge_segments(
        self,
        segments: List[Path],
        output_path: Path,
        progress_callback: Optional[Callable] = None
    ) -> bool:
        """
        Merge converted segments into final file
        
        Args:
            segments: List of segment paths to merge
            output_path: Path for final merged file
            progress_callback: Optional callback for progress updates
            
        Returns:
            True if merge successful
        """
        try:
            # Create concat file list
            concat_file = output_path.parent / "concat_list.txt"
            
            with open(concat_file, 'w') as f:
                for segment in segments:
                    f.write(f"file '{segment.absolute()}'\n")
            
            # Merge using FFmpeg concat
            cmd = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', str(concat_file),
                '-c', 'copy',
                '-y',
                str(output_path)
            ]
            
            logger.info(f"Merging {len(segments)} segments")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.wait()
            
            # Cleanup concat file
            concat_file.unlink(missing_ok=True)
            
            if process.returncode == 0 and output_path.exists():
                logger.info(f"Successfully merged into {output_path.name}")
                
                if progress_callback:
                    await progress_callback(100)
                
                return True
            else:
                logger.error("Merge failed")
                return False
                
        except Exception as e:
            logger.error(f"Merge error: {e}", exc_info=True)
            return False
    
    async def process_large_file(
        self,
        input_path: Path,
        output_path: Path,
        output_format: str,
        quality: str = 'high',
        progress_callback: Optional[Callable] = None
    ) -> bool:
        """
        Complete workflow for processing large files
        
        Args:
            input_path: Path to input file
            output_path: Path for final output
            output_format: Target format
            quality: Quality preset
            progress_callback: Optional callback for progress updates
            
        Returns:
            True if processing successful
        """
        temp_dir = None
        
        try:
            # Create temporary directory for segments
            temp_dir = output_path.parent / f"segments_{output_path.stem}"
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Step 1: Split into segments (0-20%)
            async def split_progress(p):
                if progress_callback:
                    await progress_callback(p * 0.2)
            
            segments = await self.split_into_segments(input_path, temp_dir, split_progress)
            
            if not segments:
                logger.error("Failed to split file into segments")
                return False
            
            # Step 2: Convert segments (20-90%)
            async def convert_progress(p):
                if progress_callback:
                    await progress_callback(20 + (p * 0.7))
            
            converted_segments = await self.convert_segments(
                segments,
                output_format,
                quality,
                convert_progress
            )
            
            if not converted_segments:
                logger.error("Failed to convert segments")
                return False
            
            # Step 3: Merge segments (90-100%)
            async def merge_progress(p):
                if progress_callback:
                    await progress_callback(90 + (p * 0.1))
            
            success = await self.merge_segments(
                converted_segments,
                output_path,
                merge_progress
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Large file processing error: {e}", exc_info=True)
            return False
            
        finally:
            # Cleanup temporary directory
            if temp_dir and temp_dir.exists():
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                    logger.info(f"Cleaned up temporary directory: {temp_dir}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp directory: {e}")
