'use client';

import { useState } from 'react';
import FileUploader from '@/components/FileUploader';
import ConversionPanel from '@/components/ConversionPanel';
import TranscriptionPanel from '@/components/TranscriptionPanel';
import { FileData } from '@/types';

export default function Home() {
  const [uploadedFile, setUploadedFile] = useState<FileData | null>(null);
  const [isConverting, setIsConverting] = useState(false);
  const [activeTab, setActiveTab] = useState<'convert' | 'transcribe'>('convert');

  return (
    <main className="min-h-screen gradient-bg flex items-center justify-center p-4">
      <div className="max-w-6xl w-full">
        <div className="text-center mb-12">
          <h1 className="text-6xl font-bold text-white mb-4 tracking-tight">
            TheConverter
          </h1>
          <p className="text-xl text-white/80 max-w-2xl mx-auto">
            Universal media converter with intelligent format detection and AI-powered transcription.
            Upload any audio or video file to convert or transcribe with speaker detection.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          <FileUploader 
            onFileUploaded={setUploadedFile}
            isConverting={isConverting}
          />
          
          <div className="glass-effect rounded-3xl p-8 shadow-2xl">
            {/* Tab Buttons */}
            <div className="flex gap-2 mb-6">
              <button
                onClick={() => setActiveTab('convert')}
                className={`flex-1 py-3 rounded-xl font-semibold transition-all ${
                  activeTab === 'convert'
                    ? 'bg-white/20 text-white'
                    : 'bg-white/5 text-white/60 hover:bg-white/10'
                }`}
              >
                Convert
              </button>
              <button
                onClick={() => setActiveTab('transcribe')}
                className={`flex-1 py-3 rounded-xl font-semibold transition-all ${
                  activeTab === 'transcribe'
                    ? 'bg-white/20 text-white'
                    : 'bg-white/5 text-white/60 hover:bg-white/10'
                }`}
              >
                Transcribe
              </button>
            </div>

            <h2 className="text-2xl font-bold text-white mb-6">
              {activeTab === 'convert' ? 'Convert File' : 'Transcribe Audio'}
            </h2>

            {activeTab === 'convert' ? (
              <ConversionPanel 
                file={uploadedFile}
                onConversionStart={() => setIsConverting(true)}
                onConversionEnd={() => setIsConverting(false)}
              />
            ) : (
              <TranscriptionPanel 
                file={uploadedFile?.rawFile || null}
              />
            )}
          </div>
        </div>

        <div className="mt-12 text-center text-white/60 text-sm">
          <p>Powered by FFmpeg & Whisper AI • Speaker Diarization • High-Speed Processing</p>
        </div>
      </div>
    </main>
  );
}
