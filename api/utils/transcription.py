"""
Advanced Transcription System with Speaker Diarization
Supports multi-speaker detection and transcription
"""

import asyncio
import logging
import tempfile
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import json
from dataclasses import dataclass, asdict
from datetime import timedelta

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionSegment:
    """Single transcription segment with speaker info"""
    start_time: float
    end_time: float
    speaker: str
    text: str
    confidence: float = 0.0
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def format_timestamp(self, seconds: float) -> str:
        """Format seconds to HH:MM:SS.mmm"""
        td = timedelta(seconds=seconds)
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        milliseconds = int(td.microseconds / 1000)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
    
    @property
    def start_formatted(self) -> str:
        return self.format_timestamp(self.start_time)
    
    @property
    def end_formatted(self) -> str:
        return self.format_timestamp(self.end_time)
    
    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


@dataclass
class TranscriptionResult:
    """Complete transcription result"""
    segments: List[TranscriptionSegment]
    duration: float
    speakers: List[str]
    language: str = "en"
    model_used: str = "whisper-base"
    
    def get_speaker_segments(self, speaker: str) -> List[TranscriptionSegment]:
        """Get all segments for a specific speaker"""
        return [seg for seg in self.segments if seg.speaker == speaker]
    
    def get_full_text(self, speaker: Optional[str] = None) -> str:
        """Get full transcription text, optionally filtered by speaker"""
        if speaker:
            segments = self.get_speaker_segments(speaker)
        else:
            segments = self.segments
        return "\n".join([seg.text for seg in segments])
    
    def to_dict(self) -> dict:
        return {
            "segments": [seg.to_dict() for seg in self.segments],
            "duration": self.duration,
            "speakers": self.speakers,
            "language": self.language,
            "model_used": self.model_used
        }


class TranscriptionEngine:
    """Advanced transcription engine with speaker diarization"""
    
    def __init__(self, model_size: str = "base"):
        """
        Initialize transcription engine
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
        """
        self.model_size = model_size
        self.whisper_model = None
        self.diarization_pipeline = None
        self._initialized = False
        
        logger.info(f"TranscriptionEngine initialized with model: {model_size}")
    
    async def _lazy_init(self):
        """Lazy initialization of heavy models"""
        if self._initialized:
            return
        
        try:
            # Import heavy libraries only when needed
            import whisper
            import torch
            
            logger.info("Loading Whisper model...")
            self.whisper_model = await asyncio.to_thread(
                whisper.load_model, 
                self.model_size
            )
            
            # Note: pyannote.audio requires authentication token for pretrained models
            # For production, use: HuggingFace token via environment variable
            # For now, we'll use a simpler approach with Whisper's timestamps
            
            self._initialized = True
            logger.info("Transcription models loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize transcription models: {e}")
            raise
    
    async def transcribe_with_speakers(
        self,
        audio_path: Path,
        num_speakers: Optional[int] = None,
        language: Optional[str] = None
    ) -> TranscriptionResult:
        """
        Transcribe audio with speaker diarization
        
        Args:
            audio_path: Path to audio file
            num_speakers: Expected number of speakers (None for auto-detect)
            language: Language code (None for auto-detect)
            
        Returns:
            TranscriptionResult with speaker-labeled segments
        """
        await self._lazy_init()
        
        try:
            # Convert to WAV if needed for better compatibility
            wav_path = await self._convert_to_wav(audio_path)
            
            # Step 1: Transcribe with Whisper (gets timestamps)
            logger.info("Starting transcription with Whisper...")
            transcription = await self._transcribe_whisper(wav_path, language)
            
            # Step 2: Perform speaker diarization
            logger.info("Performing speaker diarization...")
            speaker_segments = await self._diarize_speakers(wav_path, num_speakers)
            
            # Step 3: Merge transcription with speaker info
            logger.info("Merging transcription with speaker labels...")
            result = self._merge_transcription_speakers(
                transcription, 
                speaker_segments,
                wav_path
            )
            
            # Cleanup temp file if created
            if wav_path != audio_path:
                wav_path.unlink()
            
            logger.info(f"Transcription complete: {len(result.segments)} segments, {len(result.speakers)} speakers")
            return result
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}", exc_info=True)
            raise
    
    async def _convert_to_wav(self, audio_path: Path) -> Path:
        """Convert audio to WAV format if needed"""
        if audio_path.suffix.lower() == '.wav':
            return audio_path
        
        wav_path = audio_path.parent / f"{audio_path.stem}_temp.wav"
        
        cmd = [
            'ffmpeg',
            '-i', str(audio_path),
            '-ar', '16000',  # 16kHz for Whisper
            '-ac', '1',      # Mono
            '-y',
            str(wav_path)
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        await process.communicate()
        
        if process.returncode != 0:
            raise RuntimeError("Audio conversion failed")
        
        return wav_path
    
    async def _transcribe_whisper(
        self, 
        audio_path: Path,
        language: Optional[str] = None
    ) -> dict:
        """Transcribe using Whisper"""
        
        def transcribe():
            options = {
                "task": "transcribe",
                "verbose": False,
                "word_timestamps": True  # Critical for speaker alignment
            }
            
            if language:
                options["language"] = language
            
            result = self.whisper_model.transcribe(
                str(audio_path),
                **options
            )
            return result
        
        # Run in thread to avoid blocking
        result = await asyncio.to_thread(transcribe)
        return result
    
    async def _diarize_speakers(
        self,
        audio_path: Path,
        num_speakers: Optional[int] = None
    ) -> List[Tuple[float, float, str]]:
        """
        Perform speaker diarization
        
        Returns:
            List of (start_time, end_time, speaker_id) tuples
        """
        
        # Advanced implementation would use pyannote.audio
        # For this version, we'll use a simplified approach based on
        # audio features and clustering
        
        try:
            return await self._simple_speaker_detection(audio_path, num_speakers)
        except Exception as e:
            logger.warning(f"Speaker diarization failed, using fallback: {e}")
            # Fallback: assign all to Speaker 1
            duration = await self._get_audio_duration(audio_path)
            return [(0.0, duration, "Speaker 1")]
    
    async def _simple_speaker_detection(
        self,
        audio_path: Path,
        num_speakers: Optional[int] = None
    ) -> List[Tuple[float, float, str]]:
        """
        Simplified speaker detection using energy-based segmentation
        and spectral clustering
        """
        import numpy as np
        import soundfile as sf
        from scipy.signal import find_peaks
        from sklearn.cluster import KMeans
        
        def detect_speakers():
            # Read audio
            audio, sr = sf.read(str(audio_path))
            
            # Parameters
            window_size = int(sr * 2)  # 2-second windows
            hop_size = int(sr * 0.5)   # 0.5-second hop
            
            # Extract features for each window
            features = []
            timestamps = []
            
            for i in range(0, len(audio) - window_size, hop_size):
                window = audio[i:i + window_size]
                
                # Extract simple features
                energy = np.sum(window ** 2)
                zero_crossing_rate = np.sum(np.abs(np.diff(np.sign(window)))) / len(window)
                spectral_centroid = self._compute_spectral_centroid(window, sr)
                
                features.append([energy, zero_crossing_rate, spectral_centroid])
                timestamps.append(i / sr)
            
            features = np.array(features)
            
            # Normalize features
            features = (features - features.mean(axis=0)) / (features.std(axis=0) + 1e-8)
            
            # Cluster into speakers
            n_speakers = num_speakers or 2  # Default to 2 speakers
            kmeans = KMeans(n_clusters=n_speakers, random_state=42, n_init=10)
            labels = kmeans.fit_predict(features)
            
            # Convert to segments
            segments = []
            current_speaker = labels[0]
            start_time = 0.0
            
            for i, label in enumerate(labels):
                if label != current_speaker or i == len(labels) - 1:
                    end_time = timestamps[i] if i < len(timestamps) else timestamps[-1] + 2
                    speaker_id = f"Speaker {current_speaker + 1}"
                    segments.append((start_time, end_time, speaker_id))
                    
                    start_time = end_time
                    current_speaker = label
            
            return segments
        
        segments = await asyncio.to_thread(detect_speakers)
        return segments
    
    def _compute_spectral_centroid(self, audio, sr):
        """Compute spectral centroid of audio segment"""
        import numpy as np
        from scipy.fft import fft
        
        spectrum = np.abs(fft(audio))
        freqs = np.fft.fftfreq(len(audio), 1/sr)
        
        # Use only positive frequencies
        positive_freqs = freqs[:len(freqs)//2]
        positive_spectrum = spectrum[:len(spectrum)//2]
        
        if np.sum(positive_spectrum) == 0:
            return 0
        
        centroid = np.sum(positive_freqs * positive_spectrum) / np.sum(positive_spectrum)
        return centroid
    
    async def _get_audio_duration(self, audio_path: Path) -> float:
        """Get audio duration in seconds"""
        import soundfile as sf
        info = sf.info(str(audio_path))
        return info.duration
    
    def _merge_transcription_speakers(
        self,
        transcription: dict,
        speaker_segments: List[Tuple[float, float, str]],
        audio_path: Path
    ) -> TranscriptionResult:
        """Merge Whisper transcription with speaker labels"""
        
        segments = []
        
        for segment in transcription.get('segments', []):
            start_time = segment['start']
            end_time = segment['end']
            text = segment['text'].strip()
            
            # Find which speaker is active at this time
            speaker = self._find_speaker_at_time(
                (start_time + end_time) / 2,  # Use midpoint
                speaker_segments
            )
            
            segments.append(TranscriptionSegment(
                start_time=start_time,
                end_time=end_time,
                speaker=speaker,
                text=text,
                confidence=segment.get('avg_logprob', 0.0)
            ))
        
        # Get unique speakers
        speakers = sorted(set(seg.speaker for seg in segments))
        
        # Get duration
        duration = transcription.get('duration', 0)
        if not duration and segments:
            duration = segments[-1].end_time
        
        return TranscriptionResult(
            segments=segments,
            duration=duration,
            speakers=speakers,
            language=transcription.get('language', 'en'),
            model_used=f"whisper-{self.model_size}"
        )
    
    def _find_speaker_at_time(
        self,
        time: float,
        speaker_segments: List[Tuple[float, float, str]]
    ) -> str:
        """Find which speaker is active at given time"""
        for start, end, speaker in speaker_segments:
            if start <= time <= end:
                return speaker
        
        # Default to first speaker if not found
        return speaker_segments[0][2] if speaker_segments else "Speaker 1"


# Global instance (lazy loaded)
_transcription_engine: Optional[TranscriptionEngine] = None


def get_transcription_engine(model_size: str = "base") -> TranscriptionEngine:
    """Get or create transcription engine instance"""
    global _transcription_engine
    
    if _transcription_engine is None:
        _transcription_engine = TranscriptionEngine(model_size)
    
    return _transcription_engine
