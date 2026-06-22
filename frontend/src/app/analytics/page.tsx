'use client';

import { useState, useEffect, Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { GlassCard } from '@/components/ui/glass-card';
import { api, type AnalyticsStats, type AncpComparisonData, type DepPerformanceData, type GeneticsFarm as Farm } from '@/lib/api';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ChartBarIcon,
  SparklesIcon,
  ArrowRightIcon,
  BeakerIcon,
  IdentificationIcon,
  GlobeAltIcon,
  ServerIcon,
  ArrowUpTrayIcon,
  UserGroupIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  XMarkIcon,
  ChevronDownIcon
} from '@heroicons/react/24/outline';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend
} from 'recharts';

function AnalyticsContent() {
  const searchParams = useSearchParams();
  const { user } = useAuth();
  const farmIdParam = searchParams.get('farm_id');
  const [stats, setStats] = useState<AnalyticsStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedFarm, setSelectedFarm] = useState<Farm | null>(null);
  const [farms, setFarms] = useState<Farm[]>([]);
  const [isBreedModalOpen, setIsBreedModalOpen] = useState(false);
  const [breedPage, setBreedPage] = useState(1);

  // DEP Performance & ANCP Comparison state
  const [depPerf, setDepPerf] = useState<DepPerformanceData | null>(null);
  const [ancpComp, setAncpComp] = useState<AncpComparisonData | null>(null);
  const [depPlatformFilter, setDepPlatformFilter] = useState<string>('');
  const [ancpPlatformFilter, setAncpPlatformFilter] = useState<string>('');
  const [ancpSafra, setAncpSafra] = useState<number | undefined>(undefined);
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc'); // 'asc' = best to worst (TOP 0.1% first)
  const [isSafraOpen, setIsSafraOpen] = useState(false);
  const [isPlatformOpen, setIsPlatformOpen] = useState(false);

  useEffect(() => {
    if (typeof window !== 'undefined' && localStorage.getItem('access_token')) {
      const farmId = farmIdParam || undefined;
      setLoading(true);
      Promise.all([
        api.getAnalyticsStats(farmId),
        api.getDepPerformance({ farmId, fonteOrigem: depPlatformFilter || undefined }),
        api.getAncpComparison({ farmId, safra: ancpSafra, fonteOrigem: ancpPlatformFilter || undefined }),
      ])
        .then(([statsData, depData, ancpData]) => {
          setStats(statsData);
          setDepPerf(depData);
          setAncpComp(ancpData);
        })
        .catch((e) => setError(e.message))
        .finally(() => setLoading(false));
    }
  }, [farmIdParam, depPlatformFilter, ancpPlatformFilter, ancpSafra]);

  useEffect(() => {
    if (typeof window !== 'undefined' && localStorage.getItem('access_token')) {
      api.getGeneticsFarms()
        .then((data) => {
          setFarms(data);
          const effectiveId = farmIdParam || (user && user.role !== 'admin' && user.id_farm ? String(user.id_farm) : 'all');
          if (effectiveId && effectiveId !== 'all') {
            const farm = data.find((f) => String(f.id) === effectiveId);
            if (farm) setSelectedFarm(farm);
          } else {
            setSelectedFarm(null);
          }
        })
        .catch(console.error);
    }
  }, [farmIdParam, user]);

  // Color mappings
  const COLORS = ['#06b6d4', '#10b981', '#8b5cf6', '#f59e0b', '#ec4899', '#6366f1'];

  // Breed distribution data format
  const breedData = stats
    ? Object.entries(stats.breed_distribution).map(([name, value]) => ({ name, value }))
    : [];

  // Weight metrics chart data format
  const weightData = stats
    ? Object.entries(stats.weight_metrics).map(([key, data]) => ({
        name: key === 'p210' ? 'Desmama (210d)' : key === 'p365' ? 'Ano (365d)' : 'Sobreano (450d)',
        avg: data.avg || 0,
        min: data.min || 0,
        max: data.max || 0,
      }))
    : [];

  return (
    <DashboardLayout>
      <div className="space-y-8 animate-in fade-in duration-700">
        
        {/* ─── Page Title / Header ────────────────────────────────────────── */}
        <section className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-2">
            <h1 className="text-4xl font-bold text-white tracking-tight flex items-center gap-3">
              <ChartBarIcon className="w-9 h-9 text-cyan-400" />
              Inteligência Genética
            </h1>
            <p className="text-slate-400 text-lg">
              {selectedFarm 
                ? `Insights profundos e comparativos para a fazenda ${selectedFarm.nome}` 
                : 'Métricas globais consolidadas de todas as fazendas registradas'}
            </p>
          </div>
        </section>

        {/* ─── Farm Selector Dropdown ────────────────────────────────────── */}
        {farms.length > 0 && (
          <GlassCard className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <span className="text-sm font-semibold text-slate-300">Selecionar Fazenda:</span>
              <select
                value={farmIdParam || (user && user.role !== 'admin' && user.id_farm ? String(user.id_farm) : 'all')}
                onChange={(e) => {
                  const id = e.target.value;
                  window.location.href = `/analytics?farm_id=${id}`;
                }}
                className="bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-sm text-white focus:outline-none focus:border-cyan-glow/50 focus:ring-2 focus:ring-cyan-glow/10 transition-all cursor-pointer hover:bg-white/10 font-medium"
              >
                <option value="all" className="bg-slate-900 text-white">Todas as fazendas</option>
                {farms.map((farm) => (
                  <option key={farm.id} value={farm.id} className="bg-slate-900 text-white">
                    {farm.nome}
                  </option>
                ))}
              </select>
            </div>
            {stats && (
              <span className="text-xs text-slate-500 font-mono">
                Dados consolidados de {stats.summary.total_evaluations} avaliações
              </span>
            )}
          </GlassCard>
        )}

        {/* ─── Loading / Error states ─────────────────────────────────────── */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-24 text-center space-y-4">
            <div className="relative w-16 h-16 flex items-center justify-center">
              <div className="absolute inset-0 rounded-full border-4 border-cyan-500/10 border-t-cyan-500 animate-spin" />
              <BeakerIcon className="w-6 h-6 text-cyan-400 animate-pulse" />
            </div>
            <div>
              <h4 className="text-base font-bold text-white">Consolidando análises complexas...</h4>
              <p className="text-sm text-slate-500 mt-1 max-w-sm">Processando estatísticas, distribuições raciais e índices de DEPs.</p>
            </div>
          </div>
        )}

        {error && (
          <GlassCard className="p-8 border-rose-500/20 text-center max-w-lg mx-auto space-y-4">
            <div className="w-12 h-12 rounded-full bg-rose-500/10 border border-rose-500/20 flex items-center justify-center mx-auto">
              <span className="text-rose-500 font-bold text-xl">!</span>
            </div>
            <h3 className="text-lg font-bold text-white">Erro ao carregar dados</h3>
            <p className="text-slate-400 text-sm">{error}</p>
          </GlassCard>
        )}

        {/* ─── Dashboard Stats ────────────────────────────────────────────── */}
        {!loading && !error && stats && (
          <div className="space-y-8">
            
            {/* Hero KPIs */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              
              <GlassCard className="p-6 relative overflow-hidden group">
                <div className="absolute top-0 right-0 -mt-4 -mr-4 w-24 h-24 bg-cyan-glow/10 rounded-full blur-2xl group-hover:bg-cyan-glow/20 transition-all pointer-events-none" />
                <div className="flex justify-between items-start mb-4">
                  <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
                    <UserGroupIcon className="w-5 h-5" />
                  </div>
                  <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider bg-slate-800 px-2 py-1 rounded">
                    Rebanho
                  </span>
                </div>
                <div className="space-y-1">
                  <p className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Total Animais</p>
                  <p className="text-3xl font-extrabold text-white tracking-tight">{stats.summary.total_animals.toLocaleString("pt-BR")}</p>
                </div>
              </GlassCard>

              <GlassCard className="p-6 relative overflow-hidden group">
                <div className="absolute top-0 right-0 -mt-4 -mr-4 w-24 h-24 bg-emerald-glow/10 rounded-full blur-2xl group-hover:bg-emerald-glow/20 transition-all pointer-events-none" />
                <div className="flex justify-between items-start mb-4">
                  <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                    <IdentificationIcon className="w-5 h-5" />
                  </div>
                  <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider bg-slate-800 px-2 py-1 rounded">
                    Identificação
                  </span>
                </div>
                <div className="space-y-1">
                  <p className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Genotipados</p>
                  <div className="flex items-baseline gap-2">
                    <p className="text-3xl font-extrabold text-white tracking-tight">{stats.summary.genotyping_rate}%</p>
                    <span className="text-xs text-emerald-400 font-medium">taxa</span>
                  </div>
                </div>
              </GlassCard>

              <GlassCard className="p-6 relative overflow-hidden group">
                <div className="absolute top-0 right-0 -mt-4 -mr-4 w-24 h-24 bg-violet-glow/10 rounded-full blur-2xl group-hover:bg-violet-glow/20 transition-all pointer-events-none" />
                <div className="flex justify-between items-start mb-4">
                  <div className="w-10 h-10 rounded-xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center text-violet-400">
                    <GlobeAltIcon className="w-5 h-5" />
                  </div>
                  <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider bg-slate-800 px-2 py-1 rounded">
                    Plataformas
                  </span>
                </div>
                <div className="space-y-1">
                  <p className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Ativas</p>
                  <p className="text-3xl font-extrabold text-white tracking-tight">{stats.summary.platforms.join(' / ') || '—'}</p>
                </div>
              </GlassCard>

              <GlassCard className="p-6 relative overflow-hidden group">
                <div className="absolute top-0 right-0 -mt-4 -mr-4 w-24 h-24 bg-amber-glow/10 rounded-full blur-2xl group-hover:bg-amber-glow/20 transition-all pointer-events-none" />
                <div className="flex justify-between items-start mb-4">
                  <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
                    <ServerIcon className="w-5 h-5" />
                  </div>
                  <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider bg-slate-800 px-2 py-1 rounded">
                    Raças
                  </span>
                </div>
                <div className="space-y-1">
                  <p className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Diversidade</p>
                  <div className="flex items-baseline gap-2">
                    <p className="text-3xl font-extrabold text-white tracking-tight">{stats.summary.total_breeds}</p>
                    <span className="text-xs text-slate-400">racas</span>
                  </div>
                </div>
              </GlassCard>

            </div>

            {/* Distribution Charts Block */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
              
              {/* Donut Chart: Breed Distribution */}
              <GlassCard className="lg:col-span-5 p-6 flex flex-col justify-between min-h-[380px]">
                <div>
                  <h3 className="text-lg font-bold text-white">Composição de Raças</h3>
                  <p className="text-slate-500 text-xs">Percentual de raças no rebanho</p>
                </div>
                
                {breedData.length > 0 ? (
                  <div className="flex-1 flex flex-col sm:flex-row items-center justify-center gap-6 py-6">
                    <div className="relative w-44 h-44">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={breedData}
                            cx="50%"
                            cy="50%"
                            innerRadius={55}
                            outerRadius={75}
                            paddingAngle={4}
                            dataKey="value"
                          >
                            {breedData.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                          </Pie>
                        </PieChart>
                      </ResponsiveContainer>
                      <div className="absolute inset-0 flex flex-col items-center justify-center">
                        <span className="text-3xl font-black text-white">{stats.summary.total_animals}</span>
                        <span className="text-[9px] text-slate-500 uppercase tracking-widest">Animais</span>
                      </div>
                    </div>
                    
                    <div className="flex-1 space-y-2.5 w-full">
                      {breedData.slice(0, 5).map((b, idx) => {
                        const total = stats.summary.total_animals;
                        const pct = total > 0 ? ((b.value / total) * 100).toFixed(1) : 0;
                        return (
                          <div key={b.name} className="flex items-center justify-between text-xs">
                            <div className="flex items-center gap-2">
                              <div className="w-2.5 h-2.5 rounded" style={{ backgroundColor: COLORS[idx % COLORS.length] }} />
                              <span className="text-slate-300 font-semibold">{b.name}</span>
                            </div>
                            <span className="text-white font-bold">{b.value.toLocaleString("pt-BR")} ({pct}%)</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ) : (
                  <div className="flex-1 flex items-center justify-center">
                    <p className="text-slate-500 text-sm">Nenhum dado de raça disponível</p>
                  </div>
                )}
              </GlassCard>

              {/* Weight Performance Metrics Range */}
              <GlassCard className="lg:col-span-7 p-6 flex flex-col justify-between min-h-[380px]">
                <div>
                  <h3 className="text-lg font-bold text-white">Desempenho de DEPs de Peso</h3>
                  <p className="text-slate-500 text-xs">Média, valor mínimo e valor máximo de peso estimado (DEP) por período</p>
                </div>
                
                {weightData.length > 0 ? (
                  <div className="flex-1 w-full h-64 pt-6">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={weightData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" vertical={false} />
                        <XAxis dataKey="name" tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 11 }} axisLine={{ stroke: 'rgba(255,255,255,0.05)' }} />
                        <YAxis tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 10 }} axisLine={{ stroke: 'rgba(255,255,255,0.05)' }} />
                        <Tooltip
                          contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.95)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' }}
                          labelStyle={{ color: '#fff', fontWeight: 'bold', fontSize: '12px' }}
                        />
                        <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                        <Bar dataKey="min" name="Min DEP" fill="#f43f5e" radius={[4, 4, 0, 0]} maxBarSize={40} />
                        <Bar dataKey="avg" name="Média DEP" fill="#06b6d4" radius={[4, 4, 0, 0]} maxBarSize={40} />
                        <Bar dataKey="max" name="Max DEP" fill="#10b981" radius={[4, 4, 0, 0]} maxBarSize={40} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="flex-1 flex items-center justify-center">
                    <p className="text-slate-500 text-sm">Nenhum dado de avaliação de peso disponível</p>
                  </div>
                )}
              </GlassCard>

            </div>

            {/* ─── DEP Performance Section ──────────────────────────────────── */}
            {depPerf && Object.keys(depPerf.dep_metrics).length > 0 && (() => {
              // Sorting logic
              const sortedDeps = Object.entries(depPerf.dep_metrics).sort(([aKey, aM], [bKey, bM]) => {
                const aTop = aM.top;
                const bTop = bM.top;
                if (aTop === null || aTop === undefined) return 1;
                if (bTop === null || bTop === undefined) return -1;
                return sortOrder === 'asc' ? aTop - bTop : bTop - aTop;
              });

              return (
                <div className="space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div>
                      <h3 className="text-xl font-bold text-white">Desempenho de DEPs</h3>
                      <p className="text-slate-500 text-xs">Média e percentil TOP de cada DEP do rebanho</p>
                    </div>
                    <div className="flex items-center gap-3">
                      {/* Sort toggle */}
                      <button
                        onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                        className="bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-xs text-white hover:bg-white/10 transition-all font-medium flex items-center gap-2"
                      >
                        Ordenação: <span className="text-cyan-400 font-bold">{sortOrder === 'asc' ? 'Melhor ao Pior' : 'Pior ao Melhor'}</span>
                      </button>

                      {/* Platform filter */}
                      <select
                        value={depPlatformFilter}
                        onChange={(e) => setDepPlatformFilter(e.target.value)}
                        className="bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-sm text-white focus:outline-none focus:border-cyan-glow/50 transition-all cursor-pointer hover:bg-white/10 font-medium w-fit"
                      >
                        <option value="" className="bg-slate-900 text-white">Todas Plataformas</option>
                        <option value="ANCP" className="bg-slate-900 text-white">ANCP</option>
                        <option value="PMGZ" className="bg-slate-900 text-white">PMGZ</option>
                        <option value="GENEPLUS" className="bg-slate-900 text-white">GENEPLUS</option>
                      </select>
                    </div>
                  </div>

                  <GlassCard className="p-6 overflow-hidden">
                    <div className="overflow-x-auto w-full">
                      <table className="w-full text-left text-xs border-collapse">
                        <thead>
                          <tr className="border-b border-white/5 text-slate-400 font-bold">
                            <th className="py-3 px-2">DEP</th>
                            <th className="py-3 px-2">Descrição</th>
                            <th className="py-3 px-2 text-right">Média</th>
                            <th className="py-3 px-2 text-right">N</th>
                            <th className="py-3 px-2 text-center">TOP %</th>
                          </tr>
                        </thead>
                        <tbody>
                          {sortedDeps.map(([key, m]) => (
                            <tr key={key} className="border-b border-white/[0.02] hover:bg-white/[0.02] transition-colors">
                              <td className="py-3 px-2 font-bold text-cyan-400 font-mono">{key}</td>
                              <td className="py-3 px-2 text-slate-400 max-w-[160px] truncate">{m.label}</td>
                              <td className="py-3 px-2 text-right font-black text-white font-mono">{m.avg?.toFixed(2) ?? '—'}</td>
                              <td className="py-3 px-2 text-right text-slate-500 font-mono">{m.count}</td>
                              <td className="py-3 px-2 text-center">
                                {m.top !== null && m.top !== undefined ? (
                                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-extrabold ${
                                    m.top <= 5 ? 'bg-emerald-500/20 text-emerald-400' :
                                    m.top <= 20 ? 'bg-cyan-500/20 text-cyan-400' :
                                    m.top <= 50 ? 'bg-amber-500/20 text-amber-400' :
                                    'bg-rose-500/20 text-rose-400'
                                  }`}>
                                    TOP {m.top}%
                                  </span>
                                ) : '—'}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </GlassCard>
                </div>
              );
            })()}

            {/* ─── ANCP Comparison Section ──────────────────────────────────── */}
            {ancpComp && Object.keys(ancpComp.comparisons).length > 0 && (() => {
              // Sorting logic
              const sortedComparisons = Object.entries(ancpComp.comparisons).sort(([aKey, aData], [bKey, bData]) => {
                const aTop = aData.top;
                const bTop = bData.top;
                if (aTop === null || aTop === undefined) return 1;
                if (bTop === null || bTop === undefined) return -1;
                return sortOrder === 'asc' ? aTop - bTop : bTop - aTop;
              });

              return (
                <div className="space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div>
                      <h3 className="text-xl font-bold text-white">Comparação com ANCP Top 10</h3>
                      <p className="text-slate-500 text-xs">Média da fazenda vs média ANCP Top 10 por safra</p>
                    </div>
                    <div className="flex items-center gap-3">
                      {/* Platform Filter Custom */}
                      <div className="relative">
                        <button
                          type="button"
                          onClick={() => setIsPlatformOpen(!isPlatformOpen)}
                          className="bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-sm text-white focus:outline-none focus:border-cyan-glow/50 transition-all cursor-pointer hover:bg-white/10 font-medium w-64 flex items-center justify-between gap-2"
                        >
                          <span className="truncate">
                            {ancpPlatformFilter === "" ? "Todas Plataformas (Dados Fazenda)" : ancpPlatformFilter}
                          </span>
                          <ChevronDownIcon className={`w-4 h-4 text-slate-400 transition-transform duration-200 shrink-0 ${isPlatformOpen ? 'rotate-180' : ''}`} />
                        </button>
                        {isPlatformOpen && (
                          <>
                            <div className="fixed inset-0 z-10" onClick={() => setIsPlatformOpen(false)} />
                            <div className="absolute right-0 mt-2 w-64 bg-slate-900/95 border border-white/10 rounded-xl shadow-2xl overflow-hidden z-20 backdrop-blur-md">
                              {[
                                { val: "", label: "Todas Plataformas (Dados Fazenda)" },
                                { val: "ANCP", label: "ANCP" },
                                { val: "PMGZ", label: "PMGZ" },
                                { val: "GENEPLUS", label: "GENEPLUS" }
                              ].map((opt) => (
                                <button
                                  type="button"
                                  key={opt.val}
                                  onClick={() => {
                                    setAncpPlatformFilter(opt.val);
                                    setIsPlatformOpen(false);
                                  }}
                                  className={`w-full px-4 py-2.5 text-left text-sm hover:bg-white/10 transition-colors ${
                                    ancpPlatformFilter === opt.val ? 'text-cyan-400 bg-white/5 font-bold' : 'text-slate-300'
                                  }`}
                                >
                                  {opt.label}
                                </button>
                              ))}
                            </div>
                          </>
                        )}
                      </div>

                      {/* Safra Picker Custom */}
                      <div className="relative">
                        <button
                          type="button"
                          onClick={() => setIsSafraOpen(!isSafraOpen)}
                          className="bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-sm text-white focus:outline-none focus:border-cyan-glow/50 transition-all cursor-pointer hover:bg-white/10 font-medium w-36 flex items-center justify-between gap-2"
                        >
                          <span>Safra {ancpComp.safra}</span>
                          <ChevronDownIcon className={`w-4 h-4 text-slate-400 transition-transform duration-200 shrink-0 ${isSafraOpen ? 'rotate-180' : ''}`} />
                        </button>
                        {isSafraOpen && (
                          <>
                            <div className="fixed inset-0 z-10" onClick={() => setIsSafraOpen(false)} />
                            <div className="absolute right-0 mt-2 w-36 bg-slate-900/95 border border-white/10 rounded-xl shadow-2xl z-20 max-h-60 overflow-y-auto backdrop-blur-md">
                              {ancpComp.available_safras.map((s) => (
                                <button
                                  type="button"
                                  key={s}
                                  onClick={() => {
                                    setAncpSafra(s);
                                    setIsSafraOpen(false);
                                  }}
                                  className={`w-full px-4 py-2.5 text-left text-sm hover:bg-white/10 transition-colors ${
                                    ancpComp.safra === s ? 'text-cyan-400 bg-white/5 font-bold' : 'text-slate-300'
                                  }`}
                                >
                                  Safra {s}
                                </button>
                              ))}
                            </div>
                          </>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {sortedComparisons.map(([dep, data]) => {
                      const isAbove = data.diff_pct !== null && data.diff_pct >= 0;
                      const hasBothValues = data.fazenda_avg !== null && data.ancp_top10 !== null;
                      const maxBarVal = hasBothValues ? Math.max(Math.abs(data.fazenda_avg!), Math.abs(data.ancp_top10!)) : 1;

                      return (
                        <GlassCard key={dep} className="p-4 relative overflow-hidden group">
                          <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-bold text-white">{dep}</span>
                              {data.lower_is_better && (
                                <span className="text-[8px] px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400 font-bold uppercase tracking-wider">↓ menor = melhor</span>
                              )}
                            </div>
                            {data.diff_pct !== null && (
                              <span className={`text-lg font-black ${
                                isAbove ? 'text-emerald-400' : 'text-rose-400'
                              }`}>
                                {isAbove ? '+' : ''}{data.diff_pct.toFixed(1)}%
                              </span>
                            )}
                          </div>

                          {/* Fazenda bar */}
                          <div className="space-y-2">
                            <div className="flex items-center gap-2">
                              <span className="text-[10px] text-slate-400 w-20 shrink-0 font-semibold">Sua Fazenda</span>
                              <div className="flex-1 h-6 bg-white/5 rounded-full overflow-hidden relative">
                                <motion.div
                                  initial={{ width: 0 }}
                                  animate={{ width: hasBothValues ? `${Math.max(5, (Math.abs(data.fazenda_avg!) / maxBarVal) * 100)}%` : '0%' }}
                                  transition={{ duration: 0.8, ease: 'easeOut' }}
                                  className={`h-full rounded-full ${isAbove ? 'bg-gradient-to-r from-emerald-600 to-emerald-400' : 'bg-gradient-to-r from-rose-600 to-rose-400'}`}
                                />
                                <span className="absolute right-2 top-1/2 -translate-y-1/2 text-[10px] font-bold text-white font-mono">
                                  {data.fazenda_avg?.toFixed(2) ?? '—'}
                                </span>
                              </div>
                            </div>

                            {/* ANCP Top 10 bar */}
                            <div className="flex items-center gap-2">
                              <span className="text-[10px] text-slate-400 w-20 shrink-0 font-semibold">ANCP Top 10</span>
                              <div className="flex-1 h-6 bg-white/5 rounded-full overflow-hidden relative">
                                <motion.div
                                  initial={{ width: 0 }}
                                  animate={{ width: hasBothValues ? `${Math.max(5, (Math.abs(data.ancp_top10!) / maxBarVal) * 100)}%` : '0%' }}
                                  transition={{ duration: 0.8, ease: 'easeOut', delay: 0.1 }}
                                  className="h-full rounded-full bg-gradient-to-r from-amber-600 to-amber-400"
                                />
                                <span className="absolute right-2 top-1/2 -translate-y-1/2 text-[10px] font-bold text-white font-mono">
                                  {data.ancp_top10?.toFixed(2) ?? '—'}
                                </span>
                              </div>
                            </div>
                          </div>

                          {data.top !== null && data.top !== undefined && (
                            <div className="mt-2 text-right">
                              <span className={`px-2 py-0.5 rounded-full text-[9px] font-extrabold ${
                                data.top <= 5 ? 'bg-emerald-500/20 text-emerald-400' :
                                data.top <= 20 ? 'bg-cyan-500/20 text-cyan-400' :
                                data.top <= 50 ? 'bg-amber-500/20 text-amber-400' :
                                'bg-rose-500/20 text-rose-400'
                              }`}>
                                TOP {data.top}%
                              </span>
                            </div>
                          )}
                        </GlassCard>
                      );
                    })}
                  </div>
                </div>
              );
            })()}

            {/* Platform Genetic Indices Detailed Info */}
            <div className="space-y-4">
              <h3 className="text-xl font-bold text-white">Índices Genéticos por Plataforma</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                
                {['ANCP', 'PMGZ', 'GENEPLUS'].map((platform) => {
                  const info = stats.index_by_platform[platform];
                  const colors = {
                    ANCP: { text: 'text-cyan-400', bg: 'bg-cyan-500/10', border: 'border-cyan-500/20' },
                    PMGZ: { text: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20' },
                    GENEPLUS: { text: 'text-violet-400', bg: 'bg-violet-500/10', border: 'border-violet-500/20' }
                  }[platform as 'ANCP' | 'PMGZ' | 'GENEPLUS'] || { text: 'text-slate-400', bg: 'bg-slate-500/10', border: 'border-slate-500/20' };

                  return (
                    <GlassCard key={platform} className={`p-6 border ${colors.border}`}>
                      <div className="flex justify-between items-center mb-4">
                        <span className="text-sm font-bold text-white tracking-widest">{platform}</span>
                        <span className={`text-[10px] font-extrabold px-2 py-0.5 rounded uppercase ${colors.bg} ${colors.text}`}>
                          {info?.label || 'DEP'}
                        </span>
                      </div>
                      
                      {info ? (
                        <div className="space-y-4">
                          <div className="flex items-baseline gap-1">
                            <span className="text-3xl font-black text-white font-mono">{info.avg?.toFixed(2)}</span>
                            <span className="text-xs text-slate-500">Média</span>
                          </div>
                          
                          <div className="grid grid-cols-2 gap-4 text-xs pt-3 border-t border-white/5">
                            <div>
                              <p className="text-slate-500">Mínimo</p>
                              <p className="text-slate-300 font-bold font-mono">{info.min?.toFixed(2) ?? '—'}</p>
                            </div>
                            <div>
                              <p className="text-slate-500">Máximo</p>
                              <p className="text-slate-300 font-bold font-mono">{info.max?.toFixed(2) ?? '—'}</p>
                            </div>
                          </div>
                          
                          <div className="text-[10px] text-slate-500 pt-1">
                            {info.count} animais avaliados
                          </div>
                        </div>
                      ) : (
                        <div className="py-8 text-center text-xs text-slate-600">
                          Sem avaliações nesta plataforma
                        </div>
                      )}
                    </GlassCard>
                  );
                })}

              </div>
            </div>

            {/* Top Animals & Breed Averages Block */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
              
              {/* Top 10 Best Animals Table */}
              <GlassCard className="lg:col-span-7 p-6 overflow-hidden">
                <div className="mb-4">
                  <h3 className="text-lg font-bold text-white">Top 10 Animais do Rebanho</h3>
                  <p className="text-slate-500 text-xs">Melhores pontuações por Índice Principal</p>
                </div>
                
                {stats.top_animals.length > 0 ? (
                  <div className="overflow-x-auto w-full">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead>
                        <tr className="border-b border-white/5 text-slate-400 font-bold">
                          <th className="py-3 px-2">Rank</th>
                          <th className="py-3 px-2">RGN</th>
                          <th className="py-3 px-2">Nome</th>
                          <th className="py-3 px-2 text-center">Sexo</th>
                          <th className="py-3 px-2">Plataforma</th>
                          <th className="py-3 px-2 text-right">Índice</th>
                        </tr>
                      </thead>
                      <tbody>
                        {stats.top_animals.map((an, idx) => (
                          <tr key={an.rgn + idx} className="border-b border-white/[0.02] hover:bg-white/[0.02] transition-colors">
                            <td className="py-3 px-2 font-bold text-cyan-400">#{idx + 1}</td>
                            <td className="py-3 px-2 font-mono text-slate-200">{an.rgn}</td>
                            <td className="py-3 px-2 font-semibold text-white max-w-[120px] truncate">{an.nome}</td>
                            <td className="py-3 px-2 text-center">
                              <span className={`px-1.5 py-0.5 rounded font-bold text-[10px] ${an.sexo === 'M' ? 'bg-cyan-500/10 text-cyan-400' : 'bg-rose-500/10 text-rose-400'}`}>
                                {an.sexo}
                              </span>
                            </td>
                            <td className="py-3 px-2 text-slate-400">{an.fonte}</td>
                            <td className="py-3 px-2 text-right font-black text-white font-mono">
                              {an.indice?.toFixed(2)} <span className="text-[9px] text-slate-500 font-normal">{an.indice_label}</span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="py-12 text-center text-slate-500">
                    Nenhum animal qualificado com índice principal encontrado
                  </div>
                )}
              </GlassCard>

              {/* Breed Averages Comparison Table */}
              <GlassCard className="lg:col-span-5 p-6">
                <div className="mb-4 flex justify-between items-start">
                  <div>
                    <h3 className="text-lg font-bold text-white">Médias por Raça</h3>
                    <p className="text-slate-500 text-xs">Média geral das avaliações de peso por raça</p>
                  </div>
                  {Object.keys(stats.breed_averages).length > 10 && (
                    <button
                      onClick={() => {
                        setBreedPage(1);
                        setIsBreedModalOpen(true);
                      }}
                      className="text-[11px] bg-white/5 hover:bg-white/10 text-cyan-400 border border-cyan-500/10 hover:border-cyan-500/20 px-2.5 py-1.5 rounded-lg flex items-center gap-1 font-semibold transition-all shadow-md"
                    >
                      Expandir
                      <ArrowRightIcon className="w-3 h-3" />
                    </button>
                  )}
                </div>
                
                {Object.keys(stats.breed_averages).length > 0 ? (
                  <div className="overflow-x-auto w-full">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead>
                        <tr className="border-b border-white/5 text-slate-400 font-bold">
                          <th className="py-3 px-2">Raça</th>
                          <th className="py-3 px-2 text-right">P210 (Desmama)</th>
                          <th className="py-3 px-2 text-right">P450 (Sobreano)</th>
                          <th className="py-3 px-2 text-right">Índice</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(stats.breed_averages).slice(0, 10).map(([breed, val]) => (
                          <tr key={breed} className="border-b border-white/[0.02] hover:bg-white/[0.02] transition-colors">
                            <td className="py-3 px-2 font-bold text-white">{breed}</td>
                            <td className="py-3 px-2 text-right font-mono text-slate-300">
                              {val.p210 ? `${val.p210.toFixed(2)} kg` : '—'}
                            </td>
                            <td className="py-3 px-2 text-right font-mono text-slate-300">
                              {val.p450 ? `${val.p450.toFixed(2)} kg` : '—'}
                            </td>
                            <td className="py-3 px-2 text-right font-black text-emerald-400 font-mono">
                              {val.indice ? val.indice.toFixed(2) : '—'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="py-12 text-center text-slate-500">
                    Nenhum dado por raça disponível
                  </div>
                )}
              </GlassCard>

            </div>

            {/* Auxiliary status cards (Genotyping / CSG / Recent Uploads activity) */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              
              <GlassCard className="p-6 flex flex-col justify-between">
                <div className="space-y-2">
                  <h4 className="text-sm font-bold text-white">CSG (Certificado Superior de Genética)</h4>
                  <p className="text-slate-500 text-xs">Percentual de animais certificados no rebanho</p>
                </div>
                <div className="flex items-center gap-6 pt-4">
                  <div className="text-3xl font-black text-cyan-400 font-mono">{stats.summary.csg_rate}%</div>
                  <div className="h-2 flex-1 bg-white/5 rounded-full overflow-hidden">
                    <div className="h-full bg-cyan-500 rounded-full" style={{ width: `${stats.summary.csg_rate}%` }} />
                  </div>
                </div>
              </GlassCard>

              <GlassCard className="p-6 flex flex-col justify-between">
                <div className="space-y-2">
                  <h4 className="text-sm font-bold text-white">Genotipagem Completa</h4>
                  <p className="text-slate-500 text-xs">Taxa de animais genotipados para análises avançadas</p>
                </div>
                <div className="flex items-center gap-6 pt-4">
                  <div className="text-3xl font-black text-emerald-400 font-mono">{stats.summary.genotyping_rate}%</div>
                  <div className="h-2 flex-1 bg-white/5 rounded-full overflow-hidden">
                    <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${stats.summary.genotyping_rate}%` }} />
                  </div>
                </div>
              </GlassCard>

              <GlassCard className="p-6 flex flex-col justify-between">
                <div className="space-y-2">
                  <h4 className="text-sm font-bold text-white">Atividade Recente de Dados</h4>
                  <p className="text-slate-500 text-xs">Lotes de planilhas integradas à plataforma</p>
                </div>
                <div className="flex justify-between gap-2 text-center pt-4 text-xs">
                  <div className="flex-1 bg-white/[0.02] border border-white/5 p-2 rounded-xl">
                    <p className="text-slate-500 text-[10px] uppercase">30d</p>
                    <p className="text-base font-extrabold text-white font-mono">{stats.upload_activity.last_30d}</p>
                  </div>
                  <div className="flex-1 bg-white/[0.02] border border-white/5 p-2 rounded-xl">
                    <p className="text-slate-500 text-[10px] uppercase">60d</p>
                    <p className="text-base font-extrabold text-white font-mono">{stats.upload_activity.last_60d}</p>
                  </div>
                  <div className="flex-1 bg-white/[0.02] border border-white/5 p-2 rounded-xl">
                    <p className="text-slate-500 text-[10px] uppercase">90d</p>
                    <p className="text-base font-extrabold text-white font-mono">{stats.upload_activity.last_90d}</p>
                  </div>
                </div>
              </GlassCard>

            </div>

            {/* Modal de Médias por Raça Expandido */}
            <AnimatePresence>
              {isBreedModalOpen && (
                <div
                  className="fixed inset-0 z-[100] flex items-center justify-center p-4"
                  onClick={() => setIsBreedModalOpen(false)}
                >
                  {/* Backdrop */}
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="absolute inset-0 bg-black/80 backdrop-blur-sm"
                  />

                  {/* Modal Content */}
                  <motion.div
                    initial={{ scale: 0.95, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0.95, opacity: 0 }}
                    className="relative z-10 w-full max-w-2xl rounded-2xl border border-white/10 bg-slate-950/95 backdrop-blur-xl p-6 shadow-2xl flex flex-col max-h-[90vh]"
                    onClick={(e) => e.stopPropagation()}
                  >
                    {/* Header */}
                    <div className="flex items-start justify-between gap-4 mb-5">
                      <div>
                        <h2 className="text-xl font-bold text-white flex items-center gap-2">
                          <GlobeAltIcon className="w-5 h-5 text-cyan-400" />
                          Médias por Raça Completo
                        </h2>
                        <p className="text-xs text-slate-400 mt-1">
                          Lista completa com paginação e médias gerais de desempenho
                        </p>
                      </div>
                      <button
                        onClick={() => setIsBreedModalOpen(false)}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-all flex-shrink-0"
                      >
                        <XMarkIcon className="w-5 h-5" />
                      </button>
                    </div>

                    {/* Table Area (scrollable) */}
                    <div className="overflow-y-auto flex-1 w-full pr-1">
                      <table className="w-full text-left text-xs border-collapse">
                        <thead>
                          <tr className="border-b border-white/5 text-slate-400 font-bold sticky top-0 bg-slate-950/95 z-10">
                            <th className="py-3 px-2">Raça</th>
                            <th className="py-3 px-2 text-right">P210 (Desmama)</th>
                            <th className="py-3 px-2 text-right">P450 (Sobreano)</th>
                            <th className="py-3 px-2 text-right">Índice</th>
                          </tr>
                        </thead>
                        <tbody>
                          {Object.entries(stats.breed_averages)
                            .slice((breedPage - 1) * 10, breedPage * 10)
                            .map(([breed, val]) => (
                              <tr key={'modal-' + breed} className="border-b border-white/[0.02] hover:bg-white/[0.02] transition-colors">
                                <td className="py-3 px-2 font-bold text-white text-sm">{breed}</td>
                                <td className="py-3 px-2 text-right font-mono text-slate-300 text-sm">
                                  {val.p210 ? `${val.p210.toFixed(2)} kg` : '—'}
                                </td>
                                <td className="py-3 px-2 text-right font-mono text-slate-300 text-sm">
                                  {val.p450 ? `${val.p450.toFixed(2)} kg` : '—'}
                                </td>
                                <td className="py-3 px-2 text-right font-black text-emerald-400 font-mono text-sm">
                                  {val.indice ? val.indice.toFixed(2) : '—'}
                                </td>
                              </tr>
                            ))}
                        </tbody>
                      </table>
                    </div>

                    {/* Footer / Pagination */}
                    <div className="border-t border-white/5 mt-5 pt-4 flex items-center justify-between">
                      <span className="text-xs text-slate-400">
                        Mostrando {(breedPage - 1) * 10 + 1} a {Math.min(breedPage * 10, Object.keys(stats.breed_averages).length)} de {Object.keys(stats.breed_averages).length} raças
                      </span>

                      <div className="flex items-center gap-2">
                        <button
                          disabled={breedPage === 1}
                          onClick={() => setBreedPage((p) => Math.max(1, p - 1))}
                          className="p-1.5 rounded-lg border border-white/10 text-slate-400 hover:text-white hover:bg-white/5 disabled:opacity-30 disabled:pointer-events-none transition-all"
                        >
                          <ChevronLeftIcon className="w-4 h-4" />
                        </button>
                        <span className="text-xs text-white font-semibold px-2">
                          {breedPage} / {Math.ceil(Object.keys(stats.breed_averages).length / 10)}
                        </span>
                        <button
                          disabled={breedPage >= Math.ceil(Object.keys(stats.breed_averages).length / 10)}
                          onClick={() => setBreedPage((p) => p + 1)}
                          className="p-1.5 rounded-lg border border-white/10 text-slate-400 hover:text-white hover:bg-white/5 disabled:opacity-30 disabled:pointer-events-none transition-all"
                        >
                          <ChevronRightIcon className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </motion.div>
                </div>
              )}
            </AnimatePresence>

          </div>
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