'use client';

import { useState, useEffect } from 'react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Card } from '@/components/ui/Card';
import { api, type ProcessingLog } from '@/lib/api';
import {
  CheckCircleIcon,
  ExclamationCircleIcon,
  TagIcon,
} from '@heroicons/react/24/outline';

export default function HistoryPage() {
  const [logs, setLogs] = useState<ProcessingLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getLogs()
      .then(setLogs)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('pt-BR');
  };

  return (
    <DashboardLayout>
      <div className="space-y-8 animate-in fade-in duration-700">
        <section className="space-y-2">
          <h1 className="text-4xl font-bold text-white tracking-tight">Histórico de Tratamentos</h1>
          <p className="text-slate-400 text-lg">Gerencie e faça download de todos os seus processamentos anteriores.</p>
        </section>

        {loading && <p className="text-slate-400">Carregando histórico...</p>}
        {error && <p className="text-red-400">Erro: {error}</p>}

        {!loading && logs.length === 0 && (
          <Card variant="bento" className="p-12 text-center">
            <p className="text-slate-500 text-lg">Nenhum processamento encontrado.</p>
            <p className="text-slate-600 text-sm mt-2">Faça upload de um arquivo para começar.</p>
          </Card>
        )}

        {logs.length > 0 && (
          <Card variant="bento" className="overflow-hidden p-0">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-900/50">
                  <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-widest">Data</th>
                  <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-widest">Plataforma</th>
                  <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-widest">Arquivo</th>
                  <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-widest text-center">Total</th>
                  <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-widest text-center">Inseridos</th>
                  <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-widest text-center">Atualizados</th>
                  <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-widest">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-blue-500/5 transition-colors group">
                    <td className="px-6 py-5 text-sm text-slate-300 font-medium">{formatDate(log.started_at)}</td>
                    <td className="px-6 py-5">
                      <span className="flex items-center gap-2 text-sm text-white font-bold">
                        <TagIcon className="w-4 h-4 text-blue-400" />
                        {log.source_system}
                      </span>
                    </td>
                    <td className="px-6 py-5 text-sm text-slate-400 font-mono italic">{log.filename || '-'}</td>
                    <td className="px-6 py-5 text-sm text-slate-300 text-center font-bold">{log.total_rows}</td>
                    <td className="px-6 py-5 text-sm text-emerald-400 text-center font-bold">{log.rows_inserted}</td>
                    <td className="px-6 py-5 text-sm text-amber-400 text-center font-bold">{log.rows_updated}</td>
                    <td className="px-6 py-5">
                      {log.status === 'completed' ? (
                        <span className="inline-flex items-center gap-1.5 py-1 px-3 rounded-full bg-emerald-500/10 text-emerald-400 text-xs font-bold border border-emerald-500/20">
                          <CheckCircleIcon className="w-4 h-4" />
                          Sucesso
                        </span>
                      ) : log.status === 'failed' ? (
                        <span className="inline-flex items-center gap-1.5 py-1 px-3 rounded-full bg-red-500/10 text-red-500 text-xs font-bold border border-red-500/20">
                          <ExclamationCircleIcon className="w-4 h-4" />
                          Erro
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 py-1 px-3 rounded-full bg-amber-500/10 text-amber-400 text-xs font-bold border border-amber-500/20">
                          Processando
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
}
