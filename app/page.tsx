'use client';

import { useState } from 'react';
import FileUploader from '@/components/FileUploader';
import ConversionPanel from '@/components/ConversionPanel';
import { FileData } from '@/types';

export default function Home() {
  const [uploadedFile, setUploadedFile] = useState<FileData | null>(null);
  const [isConverting, setIsConverting] = useState(false);

  return (
    <main className="min-h-screen gradient-bg flex items-center justify-center p-4">
      <div className="max-w-6xl w-full">
        <div className="text-center mb-12">
          <h1 className="text-6xl font-bold text-white mb-4 tracking-tight">
            TheConverter
          </h1>
          <p className="text-xl text-white/80 max-w-2xl mx-auto">
            Universal media converter with intelligent format detection.
            Upload any audio or video file and convert it to any format.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          <FileUploader 
            onFileUploaded={setUploadedFile}
            isConverting={isConverting}
          />
          
          <ConversionPanel 
            file={uploadedFile}
            onConversionStart={() => setIsConverting(true)}
            onConversionEnd={() => setIsConverting(false)}
          />
        </div>

        <div className="mt-12 text-center text-white/60 text-sm">
          <p>Powered by FFmpeg • Intelligent Detection • High-Speed Processing</p>
        </div>
      </div>
    </main>
  );
}
