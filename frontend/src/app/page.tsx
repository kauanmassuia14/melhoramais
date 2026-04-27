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
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ExclamationTriangleIcon,
} from "@heroicons/react/24/outline";
import { GlowButton } from "@/components/ui/glow-button";
import { motion } from "framer-motion";

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
      const data = await api.getStats();
      setStats(data);
    } catch (err: any) {
      setError(err.message || "Erro ao carregar estatísticas");
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
        <div>
          <h1 className="text-4xl font-bold text-white tracking-tight">
            Dashboard
          </h1>
          <p className="text-text-secondary mt-1">
            Visão geral do sistema Melhora+
          </p>
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

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <GlassCard className="p-6">
                <h3 className="text-lg font-semibold text-white mb-4">
                  Animais por Fonte
                </h3>
                <div className="space-y-3">
                  {Object.entries(stats.animals_by_source).map(([source, count]) => (
                    <div key={source} className="flex items-center justify-between">
                      <span className="text-sm text-text-secondary">{source}</span>
                      <span className="text-sm font-mono text-cyan-glow-400">
                        {count.toLocaleString("pt-BR")}
                      </span>
                    </div>
                  ))}
                  {Object.keys(stats.animals_by_source).length === 0 && (
                    <p className="text-text-muted text-sm">Nenhum dado disponível</p>
                  )}
                </div>
              </GlassCard>

              <GlassCard className="p-6">
                <h3 className="text-lg font-semibold text-white mb-4">
                  Animais por Sexo
                </h3>
                <div className="space-y-3">
                  {Object.entries(stats.animals_by_sex).map(([sex, count]) => (
                    <div key={sex} className="flex items-center justify-between">
                      <span className="text-sm text-text-secondary">
                        {sex === "M" ? "Macho" : sex === "F" ? "Fêmea" : sex}
                      </span>
                      <span className="text-sm font-mono text-cyan-glow-400">
                        {count.toLocaleString("pt-BR")}
                      </span>
                    </div>
                  ))}
                  {Object.keys(stats.animals_by_sex).length === 0 && (
                    <p className="text-text-muted text-sm">Nenhum dado disponível</p>
                  )}
                </div>
              </GlassCard>
            </div>

            <GlassCard className="p-6">
              <h3 className="text-lg font-semibold text-white mb-4">
                Estatísticas de Peso
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <p className="text-text-muted text-xs uppercase tracking-wider mb-1">
                    Peso Desmama (210d)
                  </p>
                  <p className="text-2xl font-bold text-cyan-glow-400">
                    {stats.avg_p210 ? `${stats.avg_p210.toFixed(1)} kg` : "N/A"}
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-text-muted text-xs uppercase tracking-wider mb-1">
                    Peso Ano (365d)
                  </p>
                  <p className="text-2xl font-bold text-emerald-glow-400">
                    {stats.avg_p365 ? `${stats.avg_p365.toFixed(1)} kg` : "N/A"}
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-text-muted text-xs uppercase tracking-wider mb-1">
                    Peso Sobreano (450d)
                  </p>
                  <p className="text-2xl font-bold text-violet-glow-400">
                    {stats.avg_p450 ? `${stats.avg_p450.toFixed(1)} kg` : "N/A"}
                  </p>
                </div>
              </div>
            </GlassCard>
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
    <GlassCard className="p-6">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-text-muted text-xs uppercase tracking-wider mb-1">
            {label}
          </p>
          <p className="text-2xl font-bold text-white">{value}</p>
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
