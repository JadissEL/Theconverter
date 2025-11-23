from pydantic import BaseModel
from typing import Optional, Dict, List

class MediaMetadata(BaseModel):
    duration: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    codec: Optional[str] = None
    bitrate: Optional[int] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    format: Optional[str] = None

class DetectionResponse(BaseModel):
    detected_type: str
    detected_format: str
    confidence: float
    metadata: MediaMetadata
    suggested_formats: List[str]

class ConversionRequest(BaseModel):
    output_format: str
    quality: str = "high"
