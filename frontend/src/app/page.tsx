"use client";

import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { GlassCard } from "@/components/ui/glass-card";
import { api, DashboardStats } from "@/lib/api";
import {
  Squares2X2Icon,
  DocumentArrowUpIcon,
  BuildingOffice2Icon,
  SparklesIcon,
  ArrowRightIcon,
  ArrowUpTrayIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
} from "@heroicons/react/24/outline";
import { GlowButton } from "@/components/ui/glow-button";
import { motion } from "framer-motion";
import Link from "next/link";

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window !== "undefined" && localStorage.getItem("access_token")) {
      loadStats();
    }
  }, []);

  const loadStats = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getStatsV2();
      setStats(data);
    } catch (err: any) {
      try {
        const data = await api.getStats();
        setStats(data);
      } catch (err2: any) {
        setError(err2.message || "Erro ao carregar estatísticas");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <DashboardLayout>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-8"
      >
        {/* Welcome Section */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-4xl font-bold text-white tracking-tight">
              Olá, Kauan
            </h1>
            <p className="text-text-secondary mt-1">
              Bem-vindo ao Melhora+. Aqui está o que está acontecendo hoje.
            </p>
          </div>
          <div className="flex gap-3">
             <Link href="/upload">
                <GlowButton variant="secondary" size="sm">
                  <ArrowUpTrayIcon className="w-4 h-4" />
                  Importar Dados
                </GlowButton>
             </Link>
             <Link href="/analytics">
                <GlowButton size="sm">
                  <ChartBarIcon className="w-4 h-4" />
                  Ver Análises
                </GlowButton>
             </Link>
          </div>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[1, 2, 3, 4].map((i) => (
              <GlassCard key={i} className="p-6 animate-pulse">
                <div className="h-20 bg-white/[0.04] rounded" />
              </GlassCard>
            ))}
          </div>
        ) : stats ? (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <StatCard
                icon={Squares2X2Icon}
                label="Total de Animais"
                value={stats.total_animals.toLocaleString("pt-BR")}
                color="cyan"
              />
              <StatCard
                icon={BuildingOffice2Icon}
                label="Fazendas"
                value={stats.total_farms.toString()}
                color="emerald"
              />
              <StatCard
                icon={DocumentArrowUpIcon}
                label="Uploads (30 dias)"
                value={stats.recent_uploads.toString()}
                color="violet"
              />
              <StatCard
                icon={SparklesIcon}
                label="Peso Médio Desmama"
                value={stats.avg_p210 ? `${stats.avg_p210.toFixed(1)} kg` : "N/A"}
                color="amber"
              />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <GlassCard className="lg:col-span-2 p-6 overflow-hidden relative group">
                <div className="absolute top-0 right-0 -mt-8 -mr-8 w-40 h-40 bg-emerald-glow/10 rounded-full blur-3xl group-hover:bg-emerald-glow/20 transition-all duration-500" />
                
                <div className="flex items-center justify-between mb-6">
                   <h3 className="text-xl font-bold text-white">Estatísticas de Peso</h3>
                   <Link href="/analytics" className="text-sm text-cyan-glow-400 hover:underline flex items-center gap-1">
                      Ver tudo <ArrowRightIcon className="w-4 h-4" />
                   </Link>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                  <WeightMetric 
                    label="Desmama (210d)" 
                    value={stats.avg_p210} 
                    color="cyan"
                    subtitle="Performance inicial" 
                  />
                  <WeightMetric 
                    label="Ano (365d)" 
                    value={stats.avg_p365} 
                    color="emerald"
                    subtitle="Crescimento anual" 
                  />
                  <WeightMetric 
                    label="Sobreano (450d)" 
                    value={stats.avg_p450} 
                    color="violet"
                    subtitle="Potencial final" 
                  />
                </div>
              </GlassCard>

              <GlassCard className="p-6">
                 <h3 className="text-lg font-bold text-white mb-6">Distribuição por Sexo</h3>
                 <div className="space-y-6">
                    {Object.entries(stats.animals_by_sex).map(([sex, count], i) => {
                       const total = Object.values(stats.animals_by_sex).reduce((a, b) => a + b, 0);
                       const pct = total > 0 ? (count / total) * 100 : 0;
                       const label = sex === "Macho" || sex === "M" ? "Machos" : sex === "Fêmea" || sex === "F" ? "Fêmeas" : "Outros";
                       const colors = ['bg-cyan-glow-400', 'bg-rose-neon-400', 'bg-violet-glow-400'];
                       
                       return (
                         <div key={sex} className="space-y-2">
                           <div className="flex justify-between text-sm">
                             <span className="text-text-secondary">{label}</span>
                             <span className="text-white font-bold">{count.toLocaleString("pt-BR")}</span>
                           </div>
                           <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
                             <motion.div 
                               initial={{ width: 0 }}
                               animate={{ width: `${pct}%` }}
                               className={`h-full ${colors[i % colors.length]}`} 
                             />
                           </div>
                         </div>
                       );
                    })}
                 </div>
              </GlassCard>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
               <GlassCard className="p-6">
                  <h3 className="text-lg font-bold text-white mb-4">Top Fontes de Dados</h3>
                  <div className="grid grid-cols-2 gap-4">
                     {Object.entries(stats.animals_by_source).sort((a,b) => b[1] - a[1]).slice(0, 4).map(([source, count]) => (
                       <div key={source} className="p-4 rounded-xl bg-white/[0.02] border border-white/5 flex flex-col gap-1">
                          <span className="text-xs text-text-muted uppercase tracking-wider">{source}</span>
                          <span className="text-xl font-bold text-white">{count.toLocaleString("pt-BR")}</span>
                       </div>
                     ))}
                  </div>
               </GlassCard>
               
               <GlassCard className="p-6 flex flex-col justify-between">
                  <div>
                    <h3 className="text-lg font-bold text-white">Próximos Passos</h3>
                    <p className="text-sm text-text-secondary mt-1">Sugestões baseadas no seu rebanho</p>
                  </div>
                  
                  <div className="mt-6 space-y-3">
                    <SuggestionItem icon={ArrowUpTrayIcon} text="Importe novos dados da safra 2026" />
                    <SuggestionItem icon={ChartBarIcon} text="Analise o desvio padrão de peso desmama" />
                  </div>
               </GlassCard>
            </div>
          </>
        ) : error ? (
          <GlassCard className="p-8 text-center border-rose-neon/20">
            <ExclamationTriangleIcon className="w-12 h-12 text-rose-neon-400 mx-auto mb-4" />
            <p className="text-text-primary font-medium mb-2">Erro ao carregar dados</p>
            <p className="text-text-secondary text-sm mb-6">{error}</p>
            <GlowButton onClick={loadStats} variant="ghost" size="sm">
              Tentar Novamente
            </GlowButton>
          </GlassCard>
        ) : (
          <GlassCard className="p-12 text-center">
            <Squares2X2Icon className="w-12 h-12 text-text-muted mx-auto mb-4 animate-pulse" />
            <p className="text-text-muted">
              Nenhum dado disponível no momento.
            </p>
          </GlassCard>
        )}
      </motion.div>
    </DashboardLayout>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: React.ElementType;
  label: string;
  value: string;
  color: "cyan" | "emerald" | "violet" | "amber";
}) {
  const colorMap = {
    cyan: "text-cyan-glow-400 bg-cyan-glow/[0.08] border-cyan-glow/20",
    emerald: "text-emerald-glow-400 bg-emerald-glow/[0.08] border-emerald-glow/20",
    violet: "text-violet-glow-400 bg-violet-glow/[0.08] border-violet-glow/20",
    amber: "text-amber-400 bg-amber-400/[0.08] border-amber-400/20",
  };

  return (
    <GlassCard className="p-6 hover:translate-y-[-4px] transition-all duration-300">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-text-muted text-[10px] uppercase tracking-widest mb-1 font-bold">
            {label}
          </p>
          <p className="text-3xl font-bold text-white">{value}</p>
        </div>
        <div
          className={`w-12 h-12 rounded-xl flex items-center justify-center border ${colorMap[color]}`}
        >
          <Icon className="w-6 h-6" />
        </div>
      </div>
    </GlassCard>
  );
}

function WeightMetric({ label, value, color, subtitle }: any) {
  const colorMap: any = {
    cyan: "text-cyan-glow-400",
    emerald: "text-emerald-glow-400",
    violet: "text-violet-glow-400",
  };
  
  return (
    <div className="relative">
      <p className="text-text-muted text-[10px] uppercase tracking-widest mb-1 font-bold">{label}</p>
      <div className="flex items-baseline gap-1">
        <span className={`text-3xl font-bold ${colorMap[color] || 'text-white'}`}>
           {value ? value.toFixed(1) : "—"}
        </span>
        <span className="text-xs text-text-muted font-medium">kg</span>
      </div>
      <p className="text-[10px] text-text-muted mt-1 italic">{subtitle}</p>
    </div>
  );
}

function SuggestionItem({ icon: Icon, text }: any) {
  return (
    <div className="flex items-center gap-3 p-3 rounded-xl bg-white/[0.02] border border-white/5 hover:bg-white/[0.05] transition-colors cursor-pointer group">
       <div className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center group-hover:scale-110 transition-transform">
          <Icon className="w-4 h-4 text-text-secondary" />
       </div>
       <span className="text-sm text-text-secondary group-hover:text-white transition-colors">{text}</span>
    </div>
  );
}
