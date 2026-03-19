'use client';

import { useState } from 'react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { PlatformPicker } from '@/components/features/PlatformPicker';
import { FileUploader } from '@/components/features/FileUploader';
import { ActionStatus } from '@/components/features/ActionStatus';

const PLATFORMS = [
  { id: 'ANCP', name: 'ANCP', description: 'Assoc. Nac. de Criadores e Pesquisadores', icon: '🧬' },
  { id: 'PMGZ', name: 'PMGZ', description: 'Prog. de Melhoramento Genético Zebuíno', icon: '🐂' },
  { id: 'Geneplus', name: 'Geneplus', description: 'Programa Embrapa Geneplus', icon: '📊' },
];

export default function Home() {
  const [platform, setPlatform] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<'idle' | 'uploading' | 'processing' | 'success' | 'error'>('idle');
  const [progress, setProgress] = useState(0);

  const handleUpload = async () => {
    if (!file || !platform) return;
    setStatus('processing');
    setProgress(30);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('source_system', platform);

    try {
      const response = await fetch('http://localhost:8000/process-genetic-data', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Falha no processamento');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `melhora_plus_tratado_${platform}.xlsx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      
      setStatus('success');
      setProgress(100);
    } catch (err) {
      console.error(err);
      setStatus('error');
    }
  };

  const handleReset = () => {
    setStatus('idle');
    setFile(null);
    setProgress(0);
  };

  return (
    <DashboardLayout>
      <div className="space-y-8 max-w-7xl mx-auto w-full animate-in fade-in duration-700">
        <section className="space-y-2">
          <h1 className="text-4xl font-bold text-white tracking-tight">Tratamento de Dados</h1>
          <p className="text-slate-400 text-lg">Unifique e padronize seus relatórios genéticos em segundos.</p>
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Step 1: Platform Selection */}
          <section className="lg:col-span-12 bento-card space-y-8">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-2xl bg-blue-600/10 flex items-center justify-center border border-blue-500/20">
                  <span className="text-blue-400 font-bold">01</span>
                </div>
                <h2 className="text-2xl font-bold text-white">Selecione a Plataforma</h2>
              </div>
              {platform && (
                <span className="text-xs font-bold text-blue-400 bg-blue-400/10 px-3 py-1 rounded-full uppercase tracking-wider border border-blue-400/20 animate-in zoom-in-95 duration-300">
                  Selecionado
                </span>
              )}
            </div>
            
            <PlatformPicker 
              platforms={PLATFORMS} 
              selectedId={platform} 
              onSelect={(id) => setPlatform(id)} 
            />
          </section>

          {/* Step 2: File Upload */}
          <section className={`lg:col-span-7 bento-card space-y-8 transition-all duration-700 ${!platform ? 'opacity-30 blur-[2px] pointer-events-none' : 'opacity-100 uppercase tracking-widest'}`}>
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-2xl bg-emerald-600/10 flex items-center justify-center border border-emerald-500/20">
                <span className="text-emerald-400 font-bold">02</span>
              </div>
              <h2 className="text-2xl font-bold text-white">Upload do Relatório</h2>
            </div>
            
            <FileUploader 
              file={file} 
              onFileChange={(f) => setFile(f)} 
              status={status === 'success' ? 'success' : 'idle'} 
            />
          </section>

          {/* Step 3: Action Area / Status */}
          <section className={`lg:col-span-5 bento-card space-y-8 transition-all duration-700 ${!file ? 'opacity-30 blur-[2px] pointer-events-none' : 'opacity-100'}`}>
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-2xl bg-blue-600/10 flex items-center justify-center border border-blue-500/20">
                <span className="text-blue-400 font-bold">03</span>
              </div>
              <h2 className="text-2xl font-bold text-white">Execução</h2>
            </div>

            <ActionStatus 
              status={status === 'uploading' ? 'processing' : status} 
              progress={progress} 
              fileName={file?.name} 
              platform={platform} 
              onAction={handleUpload} 
              onReset={handleReset} 
            />
          </section>
        </div>
      </div>
    </DashboardLayout>
  );
}
