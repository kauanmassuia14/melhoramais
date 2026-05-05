'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Card } from '@/components/ui/Card';
import { api, type ProcessingLog, type ApiError } from '@/lib/api';
import {
  CheckCircleIcon,
  ExclamationCircleIcon,
  TagIcon,
  ArrowRightIcon,
  ArrowPathIcon,
  TrashIcon,
} from '@heroicons/react/24/outline';

export default function HistoryPage() {
  const [logs, setLogs] = useState<ProcessingLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedLogs, setSelectedLogs] = useState<Set<number>>(new Set());
  const [deleting, setDeleting] = useState(false);

  const loadLogs = () => {
    setLoading(true);
    setError(null);
    api.getLogs()
      .then(setLogs)
      .catch((err: ApiError) => setError(err.message || 'Erro ao carregar histórico'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadLogs();
  }, []);

  const allSelected = logs.length > 0 && selectedLogs.size === logs.length;

  const toggleSelectAll = () => {
    if (allSelected) {
      setSelectedLogs(new Set());
    } else {
      setSelectedLogs(new Set(logs.map((l) => l.id)));
    }
  };

  const toggleSelectLog = (logId: number) => {
    const newSelected = new Set(selectedLogs);
    if (newSelected.has(logId)) {
      newSelected.delete(logId);
    } else {
      newSelected.add(logId);
    }
    setSelectedLogs(newSelected);
  };

  const handleDeleteSelected = async () => {
    if (selectedLogs.size === 0) return;
    if (!confirm(`Tem certeza que deseja excluir ${selectedLogs.size} processo(s) e todos os seus dados?`)) return;
    
    setDeleting(true);
    try {
      const idsToDelete = Array.from(selectedLogs);
      await api.deleteLogs(idsToDelete);
      setLogs((prev) => prev.filter((l) => !selectedLogs.has(l.id)));
      setSelectedLogs(new Set());
    } catch (err: any) {
      alert(err.message || 'Erro ao excluir logs');
    } finally {
      setDeleting(false);
    }
  };

  const handleDeleteLog = async (logId: number) => {
    if (!confirm('Tem certeza que deseja excluir esse processo e todos os seus dados?')) return;
    try {
      await api.deleteLog(logId);
      setLogs((prev) => prev.filter((l) => l.id !== logId));
    } catch (err: any) {
      alert(err.message || 'Erro ao excluir log');
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('pt-BR');
  };

  return (
    <DashboardLayout>
      <div className="space-y-8 animate-in fade-in duration-700">
        <section className="flex items-center justify-between">
          <div className="space-y-2">
            <h1 className="text-4xl font-bold text-white tracking-tight">Histórico de Tratamentos</h1>
            <p className="text-slate-400 text-lg">Gerencie e faça download de todos os seus processamentos anteriores.</p>
          </div>
          <div className="flex items-center gap-3">
            {selectedLogs.size > 0 && (
              <button
                onClick={handleDeleteSelected}
                disabled={deleting}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm font-medium hover:bg-red-500/20 transition-all disabled:opacity-50"
              >
                <TrashIcon className="w-4 h-4" />
                Excluir ({selectedLogs.size})
              </button>
            )}
            <button
              onClick={loadLogs}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 rounded-xl border border-white/[0.06] bg-white/[0.02] text-sm text-text-secondary hover:bg-white/[0.04] transition-all disabled:opacity-50"
            >
              <ArrowPathIcon className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Atualizar
            </button>
          </div>
        </section>

        {error && (
          <div className="flex items-center justify-between p-4 rounded-xl bg-rose-neon/[0.08] border border-rose-neon/20">
            <div className="flex items-center gap-3">
              <ExclamationCircleIcon className="w-5 h-5 text-rose-neon-400" />
              <span className="text-sm text-rose-neon-400">{error}</span>
            </div>
            <button
              onClick={loadLogs}
              className="px-4 py-2 rounded-lg bg-rose-neon/10 border border-rose-neon/20 text-rose-neon-400 text-sm hover:bg-rose-neon/20 transition-all"
            >
              Tentar novamente
            </button>
          </div>
        )}

        {loading && <p className="text-slate-400">Carregando histórico...</p>}

        {!loading && logs.length === 0 && !error && (
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
                  <th className="px-4 py-4 text-xs font-bold text-slate-500 uppercase tracking-widest w-10">
                    <input
                      type="checkbox"
                      checked={allSelected}
                      onChange={toggleSelectAll}
                      className="w-4 h-4 rounded border-slate-600 bg-slate-800 text-blue-500 focus:ring-blue-500 focus:ring-offset-0"
                    />
                  </th>
                  <th className="px-4 py-4 text-xs font-bold text-slate-500 uppercase tracking-widest">Data</th>
                  <th className="px-4 py-4 text-xs font-bold text-slate-500 uppercase tracking-widest">Plataforma</th>
                  <th className="px-4 py-4 text-xs font-bold text-slate-500 uppercase tracking-widest">Arquivo</th>
                  <th className="px-4 py-4 text-xs font-bold text-slate-500 uppercase tracking-widest text-center">Total</th>
                  <th className="px-4 py-4 text-xs font-bold text-slate-500 uppercase tracking-widest text-center">Inseridos</th>
                  <th className="px-4 py-4 text-xs font-bold text-slate-500 uppercase tracking-widest text-center">Atualizados</th>
                  <th className="px-4 py-4 text-xs font-bold text-slate-500 uppercase tracking-widest">Status</th>
                  <th className="px-4 py-4 text-xs font-bold text-slate-500 uppercase tracking-widest">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {logs.map((log) => (
                  <tr key={log.id} className={`hover:bg-blue-500/5 transition-colors group ${selectedLogs.has(log.id) ? 'bg-blue-500/10' : ''}`}>
                    <td className="px-4 py-5">
                      <input
                        type="checkbox"
                        checked={selectedLogs.has(log.id)}
                        onChange={() => toggleSelectLog(log.id)}
                        className="w-4 h-4 rounded border-slate-600 bg-slate-800 text-blue-500 focus:ring-blue-500 focus:ring-offset-0"
                      />
                    </td>
                    <td className="px-4 py-5 text-sm text-slate-300 font-medium">{formatDate(log.started_at)}</td>
                    <td className="px-4 py-5">
                      <span className="flex items-center gap-2 text-sm text-white font-bold">
                        <TagIcon className="w-4 h-4 text-blue-400" />
                        {log.source_system}
                      </span>
                    </td>
                    <td className="px-4 py-5 text-sm text-slate-400 font-mono italic">{log.filename || '-'}</td>
                    <td className="px-4 py-5 text-sm text-slate-300 text-center font-bold">{log.total_rows}</td>
                    <td className="px-4 py-5 text-sm text-emerald-400 text-center font-bold">{log.rows_inserted}</td>
                    <td className="px-4 py-5 text-sm text-amber-400 text-center font-bold">{log.rows_updated}</td>
                    <td className="px-4 py-5">
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
                    <td className="px-4 py-5 flex items-center gap-2">
                      <Link
                        href={`/history/${log.id}`}
                        className="inline-flex items-center gap-1.5 py-1 px-3 rounded-full bg-cyan-500/10 text-cyan-400 text-xs font-medium border border-cyan-500/20 hover:bg-cyan-500/20 transition-all"
                      >
                        Ver detalhes
                        <ArrowRightIcon className="w-3 h-3" />
                      </Link>
                      <button
                        onClick={() => handleDeleteLog(log.id)}
                        className="p-1 rounded-full text-red-400 hover:text-red-300 hover:bg-red-500/10 transition-colors"
                        title="Excluir"
                      >
                        <TrashIcon className="w-4 h-4" />
                      </button>
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