'use client';

import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileAudio, FileVideo, File, Check, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { FileData } from '@/types';
import axios from 'axios';

interface FileUploaderProps {
  onFileUploaded: (file: FileData) => void;
  isConverting: boolean;
}

export default function FileUploader({ onFileUploaded, isConverting }: FileUploaderProps) {
  const [uploading, setUploading] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<FileData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;
    
    const file = acceptedFiles[0];
    setError(null);
    setUploading(true);

    try {
      // Create form data
      const formData = new FormData();
      formData.append('file', file);

      // Detect file type and metadata
      const response = await axios.post('/api/python/detect', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const fileData: FileData = {
        file,
        detectedType: response.data.detected_type,
        detectedFormat: response.data.detected_format,
        metadata: response.data.metadata,
      };

      setUploadedFile(fileData);
      onFileUploaded(fileData);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to analyze file');
      console.error('Upload error:', err);
    } finally {
      setUploading(false);
    }
  }, [onFileUploaded]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    maxFiles: 1,
    disabled: uploading || isConverting,
  });

  const getFileIcon = () => {
    if (!uploadedFile) return <Upload className="w-12 h-12" />;
    
    const type = uploadedFile.detectedType?.toLowerCase() || '';
    if (type.includes('audio')) return <FileAudio className="w-12 h-12" />;
    if (type.includes('video')) return <FileVideo className="w-12 h-12" />;
    return <File className="w-12 h-12" />;
  };

  return (
    <div className="glass-effect rounded-3xl p-8 shadow-2xl">
      <h2 className="text-2xl font-bold text-white mb-6">Upload File</h2>
      
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer
          transition-all duration-300
          ${isDragActive ? 'border-white bg-white/10' : 'border-white/30 hover:border-white/50'}
          ${(uploading || isConverting) ? 'opacity-50 cursor-not-allowed' : ''}
          ${!(uploading || isConverting) ? 'hover:scale-[1.02] active:scale-[0.98]' : ''}
        `}
      >
        <input {...getInputProps()} />
        
        <div className="flex flex-col items-center space-y-4">
          <div className="text-white/80">
            {uploading ? (
              <Loader2 className="w-12 h-12 animate-spin" />
            ) : uploadedFile ? (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="relative"
              >
                {getFileIcon()}
                <div className="absolute -top-1 -right-1 bg-green-500 rounded-full p-1">
                  <Check className="w-4 h-4 text-white" />
                </div>
              </motion.div>
            ) : (
              getFileIcon()
            )}
          </div>

          <div className="text-white">
            {uploading ? (
              <p className="text-lg">Analyzing file...</p>
            ) : uploadedFile ? (
              <div className="space-y-2">
                <p className="text-lg font-semibold">{uploadedFile.file.name}</p>
                <p className="text-sm text-white/60">
                  {(uploadedFile.file.size / 1024 / 1024).toFixed(2)} MB
                </p>
                {uploadedFile.detectedFormat && (
                  <p className="text-sm text-green-400">
                    Detected: {uploadedFile.detectedFormat.toUpperCase()}
                  </p>
                )}
              </div>
            ) : (
              <div>
                <p className="text-lg font-semibold mb-2">
                  {isDragActive ? 'Drop your file here' : 'Drag & drop your file here'}
                </p>
                <p className="text-sm text-white/60">
                  or click to browse • Any audio/video format
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mt-4 p-4 bg-red-500/20 border border-red-500/50 rounded-xl text-red-200 text-sm"
          >
            {error}
          </motion.div>
        )}
      </AnimatePresence>

      {uploadedFile?.metadata && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-6 p-4 bg-white/5 rounded-xl space-y-2"
        >
          <h3 className="text-white font-semibold mb-3">File Information</h3>
          <div className="grid grid-cols-2 gap-3 text-sm">
            {uploadedFile.metadata.duration && (
              <div className="text-white/80">
                <span className="text-white/60">Duration:</span> {Math.round(uploadedFile.metadata.duration)}s
              </div>
            )}
            {uploadedFile.metadata.codec && (
              <div className="text-white/80">
                <span className="text-white/60">Codec:</span> {uploadedFile.metadata.codec}
              </div>
            )}
            {uploadedFile.metadata.width && uploadedFile.metadata.height && (
              <div className="text-white/80">
                <span className="text-white/60">Resolution:</span> {uploadedFile.metadata.width}x{uploadedFile.metadata.height}
              </div>
            )}
            {uploadedFile.metadata.bitrate && (
              <div className="text-white/80">
                <span className="text-white/60">Bitrate:</span> {Math.round(uploadedFile.metadata.bitrate / 1000)} kbps
              </div>
            )}
          </div>
        </motion.div>
      )}
    </div>
  );
}
