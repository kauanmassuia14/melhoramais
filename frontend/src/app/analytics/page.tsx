'use client';

import { useState, useEffect } from 'react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Card } from '@/components/ui/Card';
import { api, type DashboardStats } from '@/lib/api';
import {
  ChartBarSquareIcon,
  CubeTransparentIcon,
  ArrowTrendingUpIcon,
  BeakerIcon,
} from '@heroicons/react/24/outline';

export default function AnalyticsPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getStats()
      .then(setStats)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const sourceTotal = stats
    ? Object.values(stats.animals_by_source).reduce((a, b) => a + b, 0)
    : 0;

  return (
    <DashboardLayout>
      <div className="space-y-8 animate-in fade-in duration-700">
        <section className="space-y-2">
          <h1 className="text-4xl font-bold text-white tracking-tight">Análises Genéticas</h1>
          <p className="text-slate-400 text-lg">Insights avançados sobre o seu rebanho e performance de dados.</p>
        </section>

        {loading && <p className="text-slate-400">Carregando estatísticas...</p>}
        {error && <p className="text-red-400">Erro: {error}</p>}

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
                    return (
                      <div key={source} className="flex-1 flex flex-col items-center gap-2">
                        <span className="text-xs text-slate-400 font-bold">{count}</span>
                        <div className="w-full bg-slate-800/50 rounded-t-xl overflow-hidden" style={{ height: '200px' }}>
                          <div
                            className="w-full bg-gradient-to-t from-blue-600 to-blue-400 transition-all duration-1000"
                            style={{ height: `${height}%`, marginTop: 'auto', display: 'flex', alignItems: 'flex-end' }}
                          ></div>
                        </div>
                        <span className="text-xs text-slate-500 font-medium">{source}</span>
                      </div>
                    );
                  })}
                </div>
              </Card>

              <Card variant="bento" className="lg:col-span-4 space-y-6">
                <h3 className="text-xl font-bold text-white">Distribuição por Plataforma</h3>
                <div className="space-y-4">
                  {Object.entries(stats.animals_by_source).map(([source, count]) => {
                    const pct = sourceTotal > 0 ? Math.round((count / sourceTotal) * 100) : 0;
                    const colors: Record<string, string> = {
                      ANCP: 'bg-blue-500',
                      PMGZ: 'bg-emerald-500',
                      Geneplus: 'bg-amber-500',
                    };
                    return (
                      <DistributionRow
                        key={source}
                        label={source}
                        percentage={pct}
                        color={colors[source] || 'bg-slate-500'}
                      />
                    );
                  })}
                </div>
              </Card>
            </div>
          </>
        )}
      </div>
    </DashboardLayout>
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
