'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Download, Loader2, Sparkles, CheckCircle, XCircle } from 'lucide-react';
import { FileData, ConversionOptions, ConversionStatus } from '@/types';
import axios from 'axios';

interface ConversionPanelProps {
  file: FileData | null;
  onConversionStart: () => void;
  onConversionEnd: () => void;
}

const AUDIO_FORMATS = [
  { value: 'mp3', label: 'MP3', description: 'Universal audio format' },
  { value: 'wav', label: 'WAV', description: 'Lossless audio' },
  { value: 'aac', label: 'AAC', description: 'High-quality compressed' },
  { value: 'flac', label: 'FLAC', description: 'Lossless compression' },
  { value: 'ogg', label: 'OGG', description: 'Open-source format' },
  { value: 'm4a', label: 'M4A', description: 'Apple audio format' },
];

const VIDEO_FORMATS = [
  { value: 'mp4', label: 'MP4', description: 'Universal video format' },
  { value: 'webm', label: 'WebM', description: 'Web-optimized' },
  { value: 'avi', label: 'AVI', description: 'Classic format' },
  { value: 'mov', label: 'MOV', description: 'Apple video format' },
  { value: 'mkv', label: 'MKV', description: 'High-quality container' },
  { value: 'gif', label: 'GIF', description: 'Animated image' },
];

const QUALITY_PRESETS = [
  { value: 'low', label: 'Low', description: 'Fastest, smaller file' },
  { value: 'medium', label: 'Medium', description: 'Balanced' },
  { value: 'high', label: 'High', description: 'Better quality' },
  { value: 'ultra', label: 'Ultra', description: 'Best quality' },
];

export default function ConversionPanel({ file, onConversionStart, onConversionEnd }: ConversionPanelProps) {
  const [selectedFormat, setSelectedFormat] = useState('');
  const [quality, setQuality] = useState<'low' | 'medium' | 'high' | 'ultra'>('high');
  const [status, setStatus] = useState<ConversionStatus>({
    status: 'idle',
    progress: 0,
  });

  const isVideo = file?.detectedType?.toLowerCase().includes('video');
  const availableFormats = isVideo ? VIDEO_FORMATS : AUDIO_FORMATS;

  const handleConvert = async () => {
    if (!file || !selectedFormat) return;

    onConversionStart();
    setStatus({ status: 'uploading', progress: 10 });

    try {
      const formData = new FormData();
      formData.append('file', file.file);
      formData.append('output_format', selectedFormat);
      formData.append('quality', quality);

      setStatus({ status: 'uploading', progress: 5 });

      const response = await axios.post('/api/python/convert', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        responseType: 'blob',
        timeout: 600000, // 10 minutes timeout
        maxContentLength: 500 * 1024 * 1024, // 500MB
        maxBodyLength: 500 * 1024 * 1024, // 500MB
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / (progressEvent.total || 1));
          setStatus({ status: 'uploading', progress: Math.min(percentCompleted, 50) });
        },
        onDownloadProgress: (progressEvent) => {
          // Conversion is happening
          if (progressEvent.loaded > 0) {
            setStatus({ status: 'converting', progress: 50 + Math.round((progressEvent.loaded * 40) / (progressEvent.total || 1)) });
          }
        },
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const filename = `${file.file.name.split('.')[0]}_converted.${selectedFormat}`;

      setStatus({ 
        status: 'completed', 
        progress: 100, 
        downloadUrl: url,
        message: filename
      });

      // Auto-download
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();

    } catch (err: any) {
      setStatus({
        status: 'error',
        progress: 0,
        error: err.response?.data?.detail || 'Conversion failed',
      });
      console.error('Conversion error:', err);
    } finally {
      onConversionEnd();
    }
  };

  const resetConversion = () => {
    setStatus({ status: 'idle', progress: 0 });
    setSelectedFormat('');
  };

  return (
    <div className="glass-effect rounded-3xl p-8 shadow-2xl">
      <h2 className="text-2xl font-bold text-white mb-6">Convert File</h2>

      {!file ? (
        <div className="flex flex-col items-center justify-center py-16 text-white/60">
          <Sparkles className="w-16 h-16 mb-4" />
          <p className="text-lg">Upload a file to get started</p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Format Selection */}
          <div>
            <label className="block text-white font-semibold mb-3">
              Output Format
            </label>
            <div className="grid grid-cols-2 gap-3">
              {availableFormats.map((format) => (
                <motion.button
                  key={format.value}
                  onClick={() => setSelectedFormat(format.value)}
                  className={`
                    p-4 rounded-xl text-left transition-all
                    ${selectedFormat === format.value
                      ? 'bg-white text-purple-600 shadow-lg'
                      : 'bg-white/10 text-white hover:bg-white/20'
                    }
                  `}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  disabled={status.status === 'converting'}
                >
                  <div className="font-bold text-lg">{format.label}</div>
                  <div className="text-xs opacity-70">{format.description}</div>
                </motion.button>
              ))}
            </div>
          </div>

          {/* Quality Selection */}
          <div>
            <label className="block text-white font-semibold mb-3">
              Quality
            </label>
            <div className="grid grid-cols-4 gap-2">
              {QUALITY_PRESETS.map((preset) => (
                <motion.button
                  key={preset.value}
                  onClick={() => setQuality(preset.value as any)}
                  className={`
                    p-3 rounded-lg text-center transition-all text-sm
                    ${quality === preset.value
                      ? 'bg-white text-purple-600 shadow-lg'
                      : 'bg-white/10 text-white hover:bg-white/20'
                    }
                  `}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  disabled={status.status === 'converting'}
                >
                  <div className="font-bold">{preset.label}</div>
                </motion.button>
              ))}
            </div>
          </div>

          {/* Progress Bar */}
          <AnimatePresence>
            {(status.status === 'converting' || status.status === 'uploading') && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 20 }}
                className="space-y-2"
              >
                <div className="flex justify-between text-white text-sm">
                  <span>{status.status === 'uploading' ? 'Uploading...' : 'Converting...'}</span>
                  <span>{status.progress}%</span>
                </div>
                <div className="h-2 bg-white/20 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-gradient-to-r from-blue-400 to-purple-500"
                    initial={{ width: 0 }}
                    animate={{ width: `${status.progress}%` }}
                    transition={{ duration: 0.5 }}
                  />
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Status Messages */}
          <AnimatePresence>
            {status.status === 'completed' && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className="p-4 bg-green-500/20 border border-green-500/50 rounded-xl flex items-start space-x-3"
              >
                <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-green-200 font-semibold">Conversion completed!</p>
                  <p className="text-green-200/70 text-sm mt-1">{status.message}</p>
                </div>
              </motion.div>
            )}

            {status.status === 'error' && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className="p-4 bg-red-500/20 border border-red-500/50 rounded-xl flex items-start space-x-3"
              >
                <XCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-red-200 font-semibold">Conversion failed</p>
                  <p className="text-red-200/70 text-sm mt-1">{status.error}</p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Action Buttons */}
          <div className="flex gap-3">
            <motion.button
              onClick={handleConvert}
              disabled={!selectedFormat || status.status === 'converting'}
              className={`
                flex-1 py-4 rounded-xl font-bold text-lg
                transition-all flex items-center justify-center space-x-2
                ${!selectedFormat || status.status === 'converting'
                  ? 'bg-white/20 text-white/40 cursor-not-allowed'
                  : 'bg-white text-purple-600 hover:bg-white/90 shadow-lg'
                }
              `}
              whileHover={selectedFormat && status.status !== 'converting' ? { scale: 1.02 } : {}}
              whileTap={selectedFormat && status.status !== 'converting' ? { scale: 0.98 } : {}}
            >
              {status.status === 'converting' ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Converting...</span>
                </>
              ) : (
                <>
                  <Download className="w-5 h-5" />
                  <span>Convert</span>
                </>
              )}
            </motion.button>

            {status.status === 'completed' && (
              <motion.button
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                onClick={resetConversion}
                className="px-6 py-4 rounded-xl font-bold bg-white/10 text-white hover:bg-white/20"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                New Conversion
              </motion.button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
