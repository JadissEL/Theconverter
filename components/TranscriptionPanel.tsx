'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FileText, Download, Loader2, Users, Volume2 } from 'lucide-react';
import axios from 'axios';

interface TranscriptionSegment {
  start_time: number;
  end_time: number;
  speaker: string;
  text: string;
  confidence: number;
}

interface TranscriptionResult {
  segments: TranscriptionSegment[];
  duration: number;
  speakers: string[];
  language: string;
  model_used: string;
}

interface TranscriptionPanelProps {
  file: File | null;
}

export default function TranscriptionPanel({ file }: TranscriptionPanelProps) {
  const [transcribing, setTranscribing] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState<TranscriptionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  
  // Options
  const [numSpeakers, setNumSpeakers] = useState<number | null>(null);
  const [language, setLanguage] = useState<string>('');
  const [modelSize, setModelSize] = useState<string>('base');

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleTranscribe = async () => {
    if (!file) return;

    setTranscribing(true);
    setError(null);
    setProgress(0);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('model_size', modelSize);
    
    if (numSpeakers) {
      formData.append('num_speakers', numSpeakers.toString());
    }
    if (language) {
      formData.append('language', language);
    }

    try {
      const response = await axios.post('/api/python/transcribe', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 600000, // 10 minutes
        onUploadProgress: (progressEvent) => {
          const percentCompleted = progressEvent.total 
            ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
            : 0;
          setProgress(percentCompleted);
        },
      });

      setResult(response.data);
      setProgress(100);
    } catch (err: any) {
      console.error('Transcription error:', err);
      setError(err.response?.data?.detail || 'Transcription failed');
    } finally {
      setTranscribing(false);
    }
  };

  const handleDownloadPDF = async (speakerFilter: string | null = null) => {
    if (!file) return;

    setGenerating(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('model_size', modelSize);
    formData.append('include_timestamps', 'true');
    
    if (numSpeakers) {
      formData.append('num_speakers', numSpeakers.toString());
    }
    if (language) {
      formData.append('language', language);
    }
    if (speakerFilter) {
      formData.append('speaker_filter', speakerFilter);
    }

    try {
      const response = await axios.post('/api/python/transcribe/pdf', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        responseType: 'blob',
        timeout: 600000,
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      const fileName = speakerFilter 
        ? `${file.name}_${speakerFilter.replace(' ', '_')}.pdf`
        : `${file.name}_transcription.pdf`;
      
      link.setAttribute('download', fileName);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      console.error('PDF generation error:', err);
      setError(err.response?.data?.detail || 'PDF generation failed');
    } finally {
      setGenerating(false);
    }
  };

  if (!file) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-white/60">
        <FileText className="w-16 h-16 mb-4" />
        <p className="text-lg">Upload a file to transcribe</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Options */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-white flex items-center gap-2">
          <Volume2 className="w-5 h-5" />
          Transcription Options
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm text-white/80 mb-2">
              Number of Speakers
            </label>
            <input
              type="number"
              min="1"
              max="10"
              placeholder="Auto-detect"
              value={numSpeakers || ''}
              onChange={(e) => setNumSpeakers(e.target.value ? parseInt(e.target.value) : null)}
              className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/40 focus:outline-none focus:border-white/40"
            />
          </div>

          <div>
            <label className="block text-sm text-white/80 mb-2">
              Language
            </label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-white/40"
            >
              <option value="">Auto-detect</option>
              <option value="en">English</option>
              <option value="es">Spanish</option>
              <option value="fr">French</option>
              <option value="de">German</option>
              <option value="it">Italian</option>
              <option value="pt">Portuguese</option>
              <option value="ar">Arabic</option>
              <option value="zh">Chinese</option>
              <option value="ja">Japanese</option>
              <option value="ko">Korean</option>
            </select>
          </div>

          <div>
            <label className="block text-sm text-white/80 mb-2">
              Model Quality
            </label>
            <select
              value={modelSize}
              onChange={(e) => setModelSize(e.target.value)}
              className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-white/40"
            >
              <option value="tiny">Tiny (Fast)</option>
              <option value="base">Base (Recommended)</option>
              <option value="small">Small (Better)</option>
              <option value="medium">Medium (Slow)</option>
              <option value="large">Large (Best)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Transcribe Button */}
      {!result && (
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleTranscribe}
          disabled={transcribing}
          className="w-full py-4 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl font-semibold hover:from-blue-600 hover:to-purple-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {transcribing ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Transcribing... {progress}%
            </>
          ) : (
            <>
              <FileText className="w-5 h-5" />
              Start Transcription
            </>
          )}
        </motion.button>
      )}

      {/* Error Display */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 bg-red-500/20 border border-red-500/50 rounded-lg text-red-200"
        >
          {error}
        </motion.div>
      )}

      {/* Results */}
      {result && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          {/* Stats */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-white/5 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-white">
                {result.segments.length}
              </div>
              <div className="text-sm text-white/60">Segments</div>
            </div>
            <div className="bg-white/5 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-white">
                {result.speakers.length}
              </div>
              <div className="text-sm text-white/60">Speakers</div>
            </div>
            <div className="bg-white/5 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-white">
                {formatTime(result.duration)}
              </div>
              <div className="text-sm text-white/60">Duration</div>
            </div>
          </div>

          {/* Download Buttons */}
          <div className="space-y-3">
            <h4 className="text-sm font-semibold text-white/80 flex items-center gap-2">
              <Download className="w-4 h-4" />
              Download PDF
            </h4>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <button
                onClick={() => handleDownloadPDF(null)}
                disabled={generating}
                className="px-4 py-3 bg-white/10 hover:bg-white/20 border border-white/20 rounded-lg text-white transition-all disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                Full Transcript
              </button>
              
              {result.speakers.map((speaker) => (
                <button
                  key={speaker}
                  onClick={() => handleDownloadPDF(speaker)}
                  disabled={generating}
                  className="px-4 py-3 bg-white/10 hover:bg-white/20 border border-white/20 rounded-lg text-white transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Users className="w-4 h-4" />}
                  {speaker} Only
                </button>
              ))}
            </div>
          </div>

          {/* Transcription Preview */}
          <div className="space-y-3">
            <h4 className="text-sm font-semibold text-white/80">Preview</h4>
            <div className="max-h-96 overflow-y-auto bg-white/5 rounded-lg p-4 space-y-4">
              {result.segments.map((segment, index) => (
                <div key={index} className="space-y-1">
                  <div className="flex items-center gap-3">
                    <span className={`text-sm font-semibold ${
                      segment.speaker === 'Speaker 1' ? 'text-blue-400' :
                      segment.speaker === 'Speaker 2' ? 'text-pink-400' :
                      segment.speaker === 'Speaker 3' ? 'text-green-400' :
                      'text-yellow-400'
                    }`}>
                      {segment.speaker}
                    </span>
                    <span className="text-xs text-white/40">
                      [{formatTime(segment.start_time)} - {formatTime(segment.end_time)}]
                    </span>
                  </div>
                  <p className="text-white/90 text-sm leading-relaxed">
                    {segment.text}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* New Transcription Button */}
          <button
            onClick={() => setResult(null)}
            className="w-full py-3 bg-white/10 hover:bg-white/20 border border-white/20 rounded-lg text-white transition-all"
          >
            Start New Transcription
          </button>
        </motion.div>
      )}
    </div>
  );
}
