'use client';

import { useState, useEffect, Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Card } from '@/components/ui/Card';
import { api, type DashboardStats, type GeneticsFarm as Farm } from '@/lib/api';
import {
  ChartBarSquareIcon,
  CubeTransparentIcon,
  ArrowTrendingUpIcon,
  BeakerIcon,
  ArrowRightIcon,
  SparklesIcon,
  CheckBadgeIcon,
} from '@heroicons/react/24/outline';

function AnalyticsContent() {
  const searchParams = useSearchParams();
  const farmIdParam = searchParams.get('farm_id');
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedFarm, setSelectedFarm] = useState<Farm | null>(null);
  const [farms, setFarms] = useState<Farm[]>([]);

  useEffect(() => {
    if (typeof window !== 'undefined' && localStorage.getItem('access_token')) {
      const farmId = farmIdParam || undefined;
      api.getStatsV2(farmId)
        .then(setStats)
        .catch((e) => setError(e.message))
        .finally(() => setLoading(false));
    }
  }, [farmIdParam]);

  useEffect(() => {
    if (typeof window !== 'undefined' && localStorage.getItem('access_token')) {
      api.getGeneticsFarms()
        .then((data) => {
          setFarms(data);
          if (farmIdParam) {
            const farm = data.find((f) => String(f.id) === farmIdParam);
            if (farm) setSelectedFarm(farm);
          }
        })
        .catch(console.error);
    }
  }, [farmIdParam]);

  const sourceTotal = stats
    ? Object.values(stats.animals_by_source).reduce((a, b) => a + b, 0)
    : 0;

  return (
    <DashboardLayout>
      <div className="space-y-8 animate-in fade-in duration-700">
        <section className="flex items-start justify-between">
          <div className="space-y-2">
            <h1 className="text-4xl font-bold text-white tracking-tight">Análises Genéticas</h1>
            {selectedFarm && (
              <p className="text-cyan-400 text-lg">
                Fazenda: {selectedFarm.nome}
              </p>
            )}
            <p className="text-slate-400 text-lg">Insights avançados sobre o seu rebanho e performance de dados.</p>
          </div>
          {selectedFarm && (
            <Link
              href={`/benchmarking?farm_id=${selectedFarm.id}`}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-violet-glow/10 border border-violet-glow/20 text-violet-glow-400 text-sm font-medium hover:bg-violet-glow/20 transition-all"
            >
              <SparklesIcon className="w-5 h-5" />
              Benchmarking
              <ArrowRightIcon className="w-4 h-4" />
            </Link>
          )}
        </section>

        {farms.length > 0 && (
          <Card variant="bento" className="p-4">
            <div className="flex items-center gap-4">
              <span className="text-sm text-slate-400">Filtrar por fazenda:</span>
              <select
                value={farmIdParam || ''}
                onChange={(e) => {
                  const id = e.target.value;
                  window.location.href = id ? `/analytics?farm_id=${id}` : '/analytics';
                }}
                className="px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-white text-sm"
              >
                <option value="">Todas as fazendas</option>
                {farms.map((farm) => (
                  <option key={farm.id} value={farm.id}>
                    {farm.nome}
                  </option>
                ))}
              </select>
            </div>
          </Card>
        )}

        {loading && <p className="text-slate-400">Carregando estatísticas...</p>}
        {error && <p className="text-red-400">Erro: {typeof error === 'string' ? error : JSON.stringify(error)}</p>}

        {stats && (
          <>
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <StatCard
                title="Total Animais"
                value={stats.total_animals.toLocaleString()}
                trend={`${stats.recent_uploads} uploads/30d`}
                icon={<CubeTransparentIcon className="w-6 h-6" />}
                color="blue"
              />
              <StatCard
                title="Média P210"
                value={stats.avg_p210 ? stats.avg_p210.toFixed(1) : '-'}
                trend="Peso Desmama"
                icon={<ArrowTrendingUpIcon className="w-6 h-6" />}
                color="emerald"
              />
              <StatCard
                title="Fazendas"
                value={String(stats.total_farms)}
                trend="Multi-tenant"
                icon={<BeakerIcon className="w-6 h-6" />}
                color="purple"
              />
              <StatCard
                title="Média P450"
                value={stats.avg_p450 ? stats.avg_p450.toFixed(1) : '-'}
                trend="Peso Sobreano"
                icon={<ChartBarSquareIcon className="w-6 h-6" />}
                color="amber"
              />
            </div>

            {/* Distribution */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
              <Card variant="bento" className="lg:col-span-8 h-96 flex flex-col justify-between">
                <div>
                  <h3 className="text-xl font-bold text-white">Distribuição por Fonte</h3>
                  <p className="text-slate-500 text-sm">Animais por sistema genético</p>
                </div>
                <div className="flex-1 flex items-end gap-2 pt-8">
                  {Object.entries(stats.animals_by_source).map(([source, count], i) => {
                    const maxCount = Math.max(...Object.values(stats.animals_by_source));
                    const height = maxCount > 0 ? (count / maxCount) * 100 : 0;
                    const colors = ['from-blue-600 to-blue-400', 'from-emerald-600 to-emerald-400', 'from-violet-600 to-violet-400', 'from-amber-600 to-amber-400'];
                    return (
                      <div key={source} className="flex-1 flex flex-col items-center gap-2">
                        <span className="text-xs text-slate-400 font-bold">{count}</span>
                        <div className="w-full bg-slate-800/50 rounded-t-xl overflow-hidden relative group" style={{ height: '200px' }}>
                          <div
                            className={`w-full bg-gradient-to-t ${colors[i % colors.length]} transition-all duration-1000 group-hover:brightness-125`}
                            style={{ height: `${height}%`, marginTop: 'auto', display: 'flex', alignItems: 'flex-end' }}
                          >
                            <div className="w-full h-full absolute top-0 left-0 bg-white/5 opacity-0 group-hover:opacity-100 transition-opacity" />
                          </div>
                        </div>
                        <span className="text-xs text-slate-500 font-medium">{source}</span>
                      </div>
                    );
                  })}
                </div>
              </Card>

              <Card variant="bento" className="lg:col-span-4 flex flex-col justify-between">
                <div>
                  <h3 className="text-xl font-bold text-white">Distribuição por Sexo</h3>
                  <p className="text-slate-500 text-sm">Composição do rebanho</p>
                </div>
                
                <div className="flex-1 flex items-center justify-center py-6">
                  <div className="relative w-40 h-40">
                    <svg className="w-full h-full" viewBox="0 0 36 36">
                      {(() => {
                        let offset = 0;
                        const total = Object.values(stats.animals_by_sex).reduce((a, b) => a + b, 0);
                        const colors = ['#3b82f6', '#10b981', '#8b5cf6'];
                        return Object.entries(stats.animals_by_sex).map(([sex, count], i) => {
                          const pct = total > 0 ? (count / total) * 100 : 0;
                          const strokeDash = `${pct} ${100 - pct}`;
                          const strokeOffset = -offset;
                          offset += pct;
                          return (
                            <circle
                              key={sex}
                              cx="18" cy="18" r="16"
                              fill="none"
                              stroke={colors[i % colors.length]}
                              strokeWidth="3.5"
                              strokeDasharray={strokeDash}
                              strokeDashoffset={strokeOffset}
                              className="transition-all duration-1000"
                            />
                          );
                        });
                      })()}
                    </svg>
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                      <span className="text-2xl font-bold text-white">{stats.total_animals}</span>
                      <span className="text-[10px] text-slate-500 uppercase tracking-widest">Total</span>
                    </div>
                  </div>
                </div>

                <div className="space-y-2 pt-4">
                  {Object.entries(stats.animals_by_sex).map(([sex, count], i) => {
                    const total = Object.values(stats.animals_by_sex).reduce((a, b) => a + b, 0);
                    const pct = total > 0 ? Math.round((count / total) * 100) : 0;
                    const colors = ['bg-blue-500', 'bg-emerald-500', 'bg-violet-500'];
                    return (
                      <div key={sex} className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div className={`w-2 h-2 rounded-full ${colors[i % colors.length]}`} />
                          <span className="text-xs text-slate-400">{sex}</span>
                        </div>
                        <span className="text-xs font-bold text-white">{count} ({pct}%)</span>
                      </div>
                    );
                  })}
                </div>
              </Card>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <Card variant="bento" className="p-6">
                 <h4 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-4">Métricas de Peso</h4>
                 <div className="space-y-6">
                    <MetricRow label="Desmama (210d)" value={stats.avg_p210} color="text-blue-400" bg="bg-blue-400/10" />
                    <MetricRow label="Ano (365d)" value={stats.avg_p365} color="text-emerald-400" bg="bg-emerald-400/10" />
                    <MetricRow label="Sobreano (450d)" value={stats.avg_p450} color="text-violet-400" bg="bg-violet-400/10" />
                 </div>
              </Card>
              
              <Card variant="bento" className="lg:col-span-2 p-6">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h3 className="text-lg font-bold text-white">Performance de Dados</h3>
                    <p className="text-slate-500 text-sm">Uploads recentes e integridade</p>
                  </div>
                  <div className="text-right">
                    <span className="text-2xl font-bold text-emerald-400">{stats.recent_uploads}</span>
                    <p className="text-[10px] text-slate-500 uppercase tracking-widest">Uploads / 30d</p>
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <div className="space-y-4">
                    <p className="text-xs font-bold text-slate-500 uppercase tracking-widest">Top Fontes</p>
                    {Object.entries(stats.animals_by_source).sort((a,b) => b[1] - a[1]).slice(0, 3).map(([source, count]) => (
                      <div key={source} className="flex items-center justify-between p-3 rounded-xl bg-slate-800/40 border border-white/5">
                        <span className="text-sm text-white font-medium">{source}</span>
                        <span className="text-sm font-bold text-cyan-400">{count}</span>
                      </div>
                    ))}
                  </div>
                  <div className="flex items-center justify-center p-6 bg-slate-800/20 rounded-2xl border border-dashed border-slate-700">
                    <div className="text-center">
                       <CheckBadgeIcon className="w-12 h-12 text-emerald-500/20 mx-auto mb-2" />
                       <p className="text-xs text-slate-500 italic">"Sincronização ativa e dados validados para o ciclo 2026."</p>
                    </div>
                  </div>
                </div>
              </Card>
            </div>
          </>
        )}
      </div>
    </DashboardLayout>
  );
}

export default function AnalyticsPage() {
  return (
    <Suspense fallback={<p className="text-slate-400 p-8">Carregando análises...</p>}>
      <AnalyticsContent />
    </Suspense>
  );
}

function StatCard({ title, value, trend, icon, color }: any) {
  const colors: Record<string, string> = {
    blue: 'bg-blue-600/10 text-blue-400 border-blue-500/20',
    emerald: 'bg-emerald-600/10 text-emerald-400 border-emerald-500/20',
    purple: 'bg-purple-600/10 text-purple-400 border-purple-500/20',
    amber: 'bg-amber-600/10 text-amber-400 border-amber-500/20',
  };

  return (
    <Card variant="bento" className="p-6">
      <div className="flex justify-between items-start mb-4">
        <div className={`w-12 h-12 rounded-2xl flex items-center justify-center border ${colors[color]}`}>
          {icon}
        </div>
        <span className="text-xs font-bold px-2 py-1 rounded-md bg-slate-800 text-slate-400">
          {trend}
        </span>
      </div>
      <div className="space-y-1">
        <p className="text-slate-500 text-sm font-medium uppercase tracking-widest">{title}</p>
        <p className="text-3xl font-bold text-white tracking-tight">{value}</p>
      </div>
    </Card>
  );
}

function DistributionRow({ label, percentage, color }: any) {
  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center text-sm">
        <span className="text-slate-300 font-medium">{label}</span>
        <span className="text-white font-bold">{percentage}%</span>
      </div>
      <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${percentage}%` }}></div>
      </div>
    </div>
  );
}

function MetricRow({ label, value, color, bg }: any) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs text-slate-500 font-medium">{label}</span>
      <div className={`px-3 py-1 rounded-lg ${bg} border border-white/5`}>
        <span className={`text-sm font-bold ${color}`}>
          {value ? `${value.toFixed(1)} kg` : '—'}
        </span>
      </div>
    </div>
  );
}