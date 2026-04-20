'use client';

import { useState, useEffect, use } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { GlassCard } from '@/components/ui/glass-card';
import { GlowButton } from '@/components/ui/glow-button';
import { api, type UploadDetail, type Animal, type ApiError } from '@/lib/api';
import {
  ArrowLeftIcon,
  DocumentArrowDownIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ClockIcon,
  CubeIcon,
  ArrowTrendingUpIcon,
} from '@heroicons/react/24/outline';

export default function UploadDetailPage({ params }: { params: Promise<{ log_id: string }> }) {
  const { log_id } = use(params);
  const router = useRouter();
  const [detail, setDetail] = useState<UploadDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const loadDetail = () => {
    setLoading(true);
    setError(null);
    api.getUploadDetail(Number(log_id))
      .then(setDetail)
      .catch((err: ApiError) => setError(err.message || 'Erro ao carregar detalhes'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadDetail();
  }, [log_id]);

  const handleDownloadReport = async () => {
    setDownloading(true);
    setDownloadError(null);
    try {
      const blob = await api.downloadUploadReport(Number(log_id));
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `relatorio_upload_${log_id}_${new Date().toISOString().slice(0, 10)}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      setDownloadError(err.message || 'Erro ao gerar relatório');
    } finally {
      setDownloading(false);
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getSexLabel = (s: string | null) => {
    if (s === 'M') return 'Macho';
    if (s === 'F') return 'Fêmea';
    return '—';
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="w-8 h-8 border-2 border-cyan-glow border-t-transparent rounded-full animate-spin" />
        </div>
      </DashboardLayout>
    );
  }

  if (error || !detail) {
    return (
      <DashboardLayout>
        <div className="space-y-6">
          <Link href="/history" className="inline-flex items-center gap-2 text-text-secondary hover:text-white transition-colors">
            <ArrowLeftIcon className="w-5 h-5" />
            Voltar ao Histórico
          </Link>
          <div className="p-6 rounded-xl bg-rose-neon/[0.08] border border-rose-neon/20">
            <p className="text-rose-neon-400 font-medium">Erro ao carregar detalhes</p>
            <p className="text-text-muted text-sm mt-1">{error || 'Upload não encontrado'}</p>
            <button
              onClick={loadDetail}
              className="mt-4 px-4 py-2 rounded-lg bg-rose-neon/10 border border-rose-neon/20 text-rose-neon-400 text-sm hover:bg-rose-neon/20 transition-all"
            >
              Tentar novamente
            </button>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  const { log, animals_preview, total_count } = detail;

  return (
    <DashboardLayout>
      <div className="space-y-8 animate-in fade-in duration-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link
              href="/history"
              className="p-2 rounded-lg border border-white/[0.06] bg-white/[0.02] hover:bg-white/[0.04] transition-all"
            >
              <ArrowLeftIcon className="w-5 h-5 text-text-secondary" />
            </Link>
            <div>
              <h1 className="text-3xl font-bold text-white tracking-tight">
                Detalhes do Upload
              </h1>
              <p className="text-text-secondary text-sm mt-1">
                {log.source_system} • {log.filename || 'Arquivo sem nome'}
              </p>
            </div>
          </div>
          <GlowButton onClick={handleDownloadReport} loading={downloading}>
            <DocumentArrowDownIcon className="w-5 h-5 mr-2" />
            Baixar Relatório PDF
          </GlowButton>
        </div>

        {downloadError && (
          <div className="p-4 rounded-xl bg-rose-neon/[0.08] border border-rose-neon/20">
            <p className="text-rose-neon-400 text-sm">{downloadError}</p>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <GlassCard glow="cyan" className="p-6 space-y-6">
              <h2 className="text-xl font-bold text-white">Informações do Processamento</h2>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.04]">
                  <div className="flex items-center gap-2 text-text-muted text-xs mb-2">
                    <ClockIcon className="w-4 h-4" />
                    Data
                  </div>
                  <p className="text-white font-bold">{formatDate(log.started_at)}</p>
                </div>
                <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.04]">
                  <div className="flex items-center gap-2 text-text-muted text-xs mb-2">
                    <CubeIcon className="w-4 h-4" />
                    Total Linhas
                  </div>
                  <p className="text-white font-bold">{log.total_rows?.toLocaleString() || 0}</p>
                </div>
                <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.04]">
                  <div className="flex items-center gap-2 text-text-muted text-xs mb-2">
                    <CheckCircleIcon className="w-4 h-4 text-emerald-400" />
                    Inseridos
                  </div>
                  <p className="text-emerald-400 font-bold">{log.rows_inserted?.toLocaleString() || 0}</p>
                </div>
                <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.04]">
                  <div className="flex items-center gap-2 text-text-muted text-xs mb-2">
                    <ArrowTrendingUpIcon className="w-4 h-4 text-amber-400" />
                    Atualizados
                  </div>
                  <p className="text-amber-400 font-bold">{log.rows_updated?.toLocaleString() || 0}</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="flex justify-between p-3 rounded-lg bg-white/[0.02]">
                  <span className="text-text-muted">Status</span>
                  <span className={`font-medium ${log.status === 'completed' ? 'text-emerald-400' : log.status === 'failed' ? 'text-rose-neon-400' : 'text-amber-400'}`}>
                    {log.status === 'completed' ? 'Concluído' : log.status === 'failed' ? 'Falhou' : 'Processando'}
                  </span>
                </div>
                <div className="flex justify-between p-3 rounded-lg bg-white/[0.02]">
                  <span className="text-text-muted">Falhas</span>
                  <span className="text-rose-neon-400 font-medium">{log.rows_failed || 0}</span>
                </div>
                <div className="flex justify-between p-3 rounded-lg bg-white/[0.02]">
                  <span className="text-text-muted">Plataforma</span>
                  <span className="text-white font-medium">{log.source_system}</span>
                </div>
                <div className="flex justify-between p-3 rounded-lg bg-white/[0.02]">
                  <span className="text-text-muted">Total Animais</span>
                  <span className="text-white font-medium">{total_count}</span>
                </div>
              </div>

              {log.error_message && (
                <div className="p-4 rounded-lg bg-rose-neon/[0.06] border border-rose-neon/20">
                  <p className="text-rose-neon-400 text-sm font-medium mb-1">Mensagem de Erro</p>
                  <p className="text-text-muted text-xs">{log.error_message}</p>
                </div>
              )}
            </GlassCard>

            <GlassCard glow="cyan" className="p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold text-white">Animais Processados</h2>
                <span className="text-xs text-text-muted">Mostrando {animals_preview.length} de {total_count}</span>
              </div>

              {animals_preview.length === 0 ? (
                <p className="text-text-muted text-center py-8">Nenhum animal encontrado.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-white/[0.04]">
                        <th className="text-left px-3 py-2 text-[10px] text-text-muted uppercase tracking-wider font-semibold">RGN</th>
                        <th className="text-left px-3 py-2 text-[10px] text-text-muted uppercase tracking-wider font-semibold">Nome</th>
                        <th className="text-left px-3 py-2 text-[10px] text-text-muted uppercase tracking-wider font-semibold">Sexo</th>
                        <th className="text-left px-3 py-2 text-[10px] text-text-muted uppercase tracking-wider font-semibold">Raça</th>
                        <th className="text-right px-3 py-2 text-[10px] text-text-muted uppercase tracking-wider font-semibold">P210</th>
                        <th className="text-right px-3 py-2 text-[10px] text-text-muted uppercase tracking-wider font-semibold">P365</th>
                        <th className="text-left px-3 py-2 text-[10px] text-text-muted uppercase tracking-wider font-semibold">Ações</th>
                      </tr>
                    </thead>
                    <tbody>
                      {animals_preview.map((animal: Animal) => (
                        <tr key={animal.id_animal} className="border-b border-white/[0.02] hover:bg-white/[0.02] transition-colors">
                          <td className="px-3 py-3 font-mono text-sm text-cyan-glow-400">{animal.rgn_animal}</td>
                          <td className="px-3 py-3 text-sm text-text-primary">{animal.nome_animal || '—'}</td>
                          <td className="px-3 py-3">
                            <span className={`text-xs px-2 py-0.5 rounded-full ${animal.sexo === 'M' ? 'bg-blue-500/10 text-blue-400' : 'bg-pink-500/10 text-pink-400'}`}>
                              {getSexLabel(animal.sexo)}
                            </span>
                          </td>
                          <td className="px-3 py-3 text-sm text-text-secondary">{animal.raca || '—'}</td>
                          <td className="px-3 py-3 text-sm text-right font-mono">{animal.p210_peso_desmama?.toFixed(1) || '—'}</td>
                          <td className="px-3 py-3 text-sm text-right font-mono">{animal.p365_peso_ano?.toFixed(1) || '—'}</td>
                          <td className="px-3 py-3">
                            <Link href={`/animals/${animal.id_animal}`} className="text-xs text-cyan-glow-400 hover:text-cyan-glow-300 transition-colors">
                              Ver detalhes
                            </Link>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </GlassCard>
          </div>

          <div className="space-y-6">
            <GlassCard glow="violet" className="p-6 space-y-4">
              <h3 className="text-lg font-bold text-white">Resumo</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-text-muted text-sm">Arquivo</span>
                  <span className="text-white text-sm text-right max-w-[180px] truncate">{log.filename || '—'}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-text-muted text-sm">Plataforma</span>
                  <span className="text-white text-sm">{log.source_system}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-text-muted text-sm">Total Linhas</span>
                  <span className="text-white text-sm font-bold">{log.total_rows?.toLocaleString() || 0}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-text-muted text-sm">Taxa de Sucesso</span>
                  <span className={`text-sm font-bold ${log.total_rows > 0 && log.rows_failed === 0 ? 'text-emerald-400' : log.rows_failed > log.total_rows / 2 ? 'text-rose-neon-400' : 'text-amber-400'}`}>
                    {log.total_rows > 0 ? ((1 - (log.rows_failed || 0) / log.total_rows) * 100).toFixed(1) : 0}%
                  </span>
                </div>
              </div>
            </GlassCard>

            <GlassCard glow="cyan" className="p-6 space-y-4">
              <h3 className="text-lg font-bold text-white">Ações Rápidas</h3>
              <div className="space-y-2">
                <button
                  onClick={handleDownloadReport}
                  disabled={downloading}
                  className="w-full flex items-center justify-between p-3 rounded-lg bg-white/[0.02] border border-white/[0.04] hover:border-cyan-glow/30 hover:bg-white/[0.04] transition-all text-left"
                >
                  <span className="text-sm text-text-primary">Baixar Relatório PDF</span>
                  <DocumentArrowDownIcon className="w-5 h-5 text-cyan-glow-400" />
                </button>
                <Link
                  href="/history"
                  className="w-full flex items-center justify-between p-3 rounded-lg bg-white/[0.02] border border-white/[0.04] hover:border-white/[0.08] hover:bg-white/[0.04] transition-all"
                >
                  <span className="text-sm text-text-primary">Ver Histórico</span>
                  <ArrowLeftIcon className="w-5 h-5 text-text-muted" />
                </Link>
              </div>
            </GlassCard>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
