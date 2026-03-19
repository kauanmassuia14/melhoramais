'use client';

import { ChartBarIcon } from '@heroicons/react/24/outline';
import { Button } from '@/components/ui/Button';

interface ActionStatusProps {
  status: 'idle' | 'processing' | 'success' | 'error';
  progress: number;
  fileName: string | undefined;
  platform: string;
  onAction: () => void;
  onReset: () => void;
}

export const ActionStatus = ({ status, progress, fileName, platform, onAction, onReset }: ActionStatusProps) => {
  return (
    <div className="h-full flex flex-col justify-between space-y-8">
      <div className="flex-1 flex flex-col items-center justify-center space-y-8">
        {(status === 'idle') && (
          <div className="w-full text-center space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <div className="p-6 bg-slate-900/50 rounded-2xl border border-slate-800 text-left">
              <div className="text-xs text-slate-500 uppercase tracking-widest mb-4 font-bold">Arquivo Preparado</div>
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-blue-500/10 rounded-xl flex items-center justify-center border border-blue-500/20">
                  <ChartBarIcon className="w-6 h-6 text-blue-400" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="text-white font-mono text-sm truncate">{fileName || 'Nenhum arquivo'}</div>
                  <div className="text-xs text-slate-500 uppercase">{platform} Engine v2.4</div>
                </div>
              </div>
            </div>
            <Button onClick={onAction} className="w-full py-5 text-lg" variant="primary">
              Tratar Dados Genéticos
            </Button>
          </div>
        )}

        {status === 'processing' && (
          <div className="w-full space-y-8 text-center animate-in fade-in duration-500">
            <div className="relative h-4 w-full bg-slate-900 rounded-full overflow-hidden border border-slate-800">
              <div 
                className="absolute h-full bg-gradient-to-r from-blue-600 to-blue-400 transition-all duration-1000 ease-out shadow-[0_0_20px_rgba(37,99,235,0.5)]" 
                style={{ width: `${progress}%` }}
              >
                 <div className="absolute inset-0 bg-[linear-gradient(45deg,rgba(255,255,255,0.2)25%,transparent 25%,transparent 50%,rgba(255,255,255,0.2)50%,rgba(255,255,255,0.2)75%,transparent 75%,transparent)] bg-[length:20px_20px] animate-[shimmer_1s_infinite_linear]"></div>
              </div>
            </div>
            <div className="space-y-3">
               <p className="text-2xl font-bold text-white animate-pulse tracking-tight">Limpando e Padronizando...</p>
               <p className="text-slate-500 text-sm">Validando mapeamentos e aplicando regras de tratamento.</p>
            </div>
          </div>
        )}

        {status === 'success' && (
          <div className="w-full space-y-4 animate-in fade-in zoom-in-95 duration-500">
              <Button onClick={onReset} variant="secondary" className="w-full py-4 font-bold">
                Novo Processamento
              </Button>
              <div className="text-xs text-slate-500 text-center font-medium opacity-80 uppercase tracking-widest">
                Log registrado com sucesso
              </div>
          </div>
        )}

        {status === 'error' && (
          <div className="w-full text-center space-y-6 animate-in shake duration-500">
            <div className="p-6 bg-red-500/10 border border-red-500/20 rounded-[2rem]">
              <p className="text-red-400 font-bold text-lg mb-1">Falha Crítica</p>
              <p className="text-sm text-red-400/70">O arquivo não possui o formato esperado pela plataforma selecionada.</p>
            </div>
            <button onClick={onReset} className="text-sm text-slate-400 hover:text-white underline font-semibold transition-colors">
              Tentar novamente
            </button>
          </div>
        )}
      </div>

      <style jsx>{`
        @keyframes shimmer {
          0% { background-position: 0 0; }
          100% { background-position: 20px 0; }
        }
        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          25% { transform: translateX(-4px); }
          75% { transform: translateX(4px); }
        }
        .animate-in {
          animation-fill-mode: forwards;
        }
      `}</style>
    </div>
  );
};
