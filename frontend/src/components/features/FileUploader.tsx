'use client';

import { CloudArrowUpIcon, CheckCircleIcon } from '@heroicons/react/24/outline';

interface FileUploaderProps {
  file: File | null;
  onFileChange: (file: File | null) => void;
  status: 'idle' | 'success';
}

export const FileUploader = ({ file, onFileChange, status }: FileUploaderProps) => {
  if (status === 'success') {
    return (
      <div className="flex flex-col items-center justify-center h-80 bg-emerald-500/5 border-2 border-emerald-500/20 rounded-[2.5rem] space-y-6 relative overflow-hidden group">
        <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/10 to-transparent"></div>
        <div className="w-24 h-24 rounded-full bg-emerald-500/20 flex items-center justify-center animate-pulse">
          <CheckCircleIcon className="w-12 h-12 text-emerald-400" />
        </div>
        <div className="text-center relative z-10">
          <p className="text-emerald-400 font-bold text-2xl mb-1">Processamento Concluído</p>
          <p className="text-slate-400">O arquivo foi tratado e baixado com sucesso.</p>
        </div>
      </div>
    );
  }

  return (
    <label className="group block relative cursor-pointer outline-none">
      <div className="flex flex-col items-center justify-center w-full h-80 border-2 border-dashed border-slate-800 rounded-[2.5rem] bg-slate-950/30 hover:bg-blue-500/5 hover:border-blue-500/40 transition-all duration-500">
        <div className="flex flex-col items-center justify-center p-8 text-center">
          <div className="w-20 h-20 mb-6 rounded-3xl bg-blue-600/10 flex items-center justify-center border border-blue-500/20 group-hover:scale-110 group-hover:bg-blue-600/20 transition-all duration-500 shadow-2xl">
            <CloudArrowUpIcon className="w-10 h-10 text-blue-400 animate-float" />
          </div>
          <p className="mb-2 text-lg text-white font-semibold group-hover:text-blue-400 transition-colors">
            {file ? file.name : 'Vincular novo arquivo'}
          </p>
          <p className="text-sm text-slate-500 max-w-[240px]">
            Arraste e solte o relatório bruto (.xlsx, .xls ou .pag) ou clique para navegar.
          </p>
        </div>
      </div>
      <input 
        type="file" 
        className="hidden" 
        onChange={(e) => onFileChange(e.target.files?.[0] || null)} 
        accept=".xlsx,.xls,.pag"
      />
    </label>
  );
};
