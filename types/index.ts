export interface FileData {
  file: File;
  rawFile: File;  // Add raw File object for transcription
  detectedType?: string;
  detectedFormat?: string;
  metadata?: MediaMetadata;
  uploadUrl?: string;
}

export interface MediaMetadata {
  duration?: number;
  width?: number;
  height?: number;
  codec?: string;
  bitrate?: number;
  sampleRate?: number;
  channels?: number;
  format?: string;
}

export interface ConversionOptions {
  outputFormat: string;
  quality?: 'low' | 'medium' | 'high' | 'ultra';
  videoBitrate?: string;
  audioBitrate?: string;
  resolution?: string;
  fps?: number;
}

export interface ConversionStatus {
  status: 'idle' | 'uploading' | 'analyzing' | 'converting' | 'completed' | 'error';
  progress: number;
  message?: string;
  downloadUrl?: string;
  error?: string;
}

export interface DetectionResult {
  detected_type: string;
  detected_format: string;
  confidence: number;
  metadata: MediaMetadata;
  suggested_formats: string[];
}
