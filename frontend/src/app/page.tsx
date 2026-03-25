"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { GlassCard } from "@/components/ui/glass-card";
import { GlowButton } from "@/components/ui/glow-button";
import { motion } from "framer-motion";
import { api, type DashboardStats } from "@/lib/api";
import {
  DocumentArrowUpIcon,
  ChartBarIcon,
  CubeIcon,
  ArrowTrendingUpIcon,
  ClockIcon,
  SparklesIcon,
  ArrowRightIcon,
} from "@heroicons/react/24/outline";

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.08 },
  },
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" as const } },
};

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getStats()
      .then(setStats)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <DashboardLayout>
      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="space-y-8"
      >
        {/* Header */}
        <motion.div variants={item} className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-white tracking-tight">
              Dashboard Genética
            </h1>
            <p className="text-text-secondary mt-1">
              Visão geral do seu rebanho e performance de dados.
            </p>
          </div>
          <Link href="/upload">
            <GlowButton>
              <DocumentArrowUpIcon className="w-5 h-5 mr-2" />
              Novo Upload
            </GlowButton>
          </Link>
        </motion.div>

        {/* KPI Bento Grid */}
        <motion.div variants={item} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          <KpiCard
            title="Total de Animais"
            value={stats?.total_animals.toLocaleString() ?? "—"}
            subtitle="animais unificados"
            icon={<CubeIcon className="w-6 h-6" />}
            color="cyan"
            trend="+12%"
          />
          <KpiCard
            title="Fazendas Ativas"
            value={String(stats?.total_farms ?? "—")}
            subtitle="multi-tenant"
            icon={<ChartBarIcon className="w-6 h-6" />}
            color="violet"
            trend="Estável"
          />
          <KpiCard
            title="Média P210"
            value={stats?.avg_p210?.toFixed(1) ?? "—"}
            subtitle="peso desmama"
            icon={<ArrowTrendingUpIcon className="w-6 h-6" />}
            color="emerald"
            trend="+3.2%"
          />
          <KpiCard
            title="Uploads (30d)"
            value={String(stats?.recent_uploads ?? "—")}
            subtitle="processamentos"
            icon={<ClockIcon className="w-6 h-6" />}
            color="rose"
            trend="+5%"
          />
        </motion.div>

        {/* Main Content: Charts + Recent Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Distribution Chart */}
          <motion.div variants={item} className="lg:col-span-2">
            <GlassCard glow="cyan" className="p-8 h-[380px] flex flex-col">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-lg font-bold text-white">
                    Distribuição por Fonte
                  </h3>
                  <p className="text-xs text-text-muted">
                    Animais por sistema genético
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-cyan-glow animate-pulse" />
                  <span className="text-[10px] text-text-muted font-mono">
                    LIVE
                  </span>
                </div>
              </div>

              <div className="flex-1 flex items-end gap-4">
                {stats ? (
                  Object.entries(stats.animals_by_source).map(
                    ([source, count], i) => {
                      const max = Math.max(
                        ...Object.values(stats.animals_by_source)
                      );
                      const h = max > 0 ? (count / max) * 100 : 0;
                      const colors: Record<string, string> = {
                        ANCP: "from-cyan-glow-deep to-cyan-glow",
                        PMGZ: "from-emerald-glow/60 to-emerald-glow-400",
                        Geneplus: "from-violet-glow-deep to-violet-glow-400",
                      };
                      return (
                        <motion.div
                          key={source}
                          initial={{ height: 0 }}
                          animate={{ height: `${h}%` }}
                          transition={{
                            duration: 0.8,
                            delay: i * 0.15,
                            ease: [0.4, 0, 0.2, 1],
                          }}
                          className="flex-1 rounded-t-xl bg-gradient-to-t relative group cursor-pointer"
                          style={{
                            backgroundImage: `linear-gradient(to top, var(--tw-gradient-stops))`,
                          }}
                        >
                          <div
                            className={`absolute inset-0 rounded-t-xl bg-gradient-to-t ${
                              colors[source] || "from-slate-700 to-slate-500"
                            }`}
                          />
                          <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-deep-dark-800 border border-white/[0.08] px-2 py-1 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                            <span className="text-xs text-white font-bold">
                              {count.toLocaleString()}
                            </span>
                          </div>
                          <div className="absolute -bottom-6 left-1/2 -translate-x-1/2">
                            <span className="text-xs text-text-muted font-medium">
                              {source}
                            </span>
                          </div>
                        </motion.div>
                      );
                    }
                  )
                ) : (
                  <div className="flex-1 flex items-center justify-center">
                    <p className="text-text-muted text-sm">
                      {loading ? "Carregando..." : "Sem dados disponíveis"}
                    </p>
                  </div>
                )}
              </div>
            </GlassCard>
          </motion.div>

          {/* Quick Actions + Sources */}
          <motion.div variants={item} className="space-y-5">
            <GlassCard glow="violet" className="p-6 space-y-5">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <SparklesIcon className="w-5 h-5 text-violet-glow-400" />
                Ações Rápidas
              </h3>
              <div className="space-y-3">
                {[
                  {
                    label: "Upload ANCP",
                    desc: "Processar relatório genético",
                    href: "/",
                    color: "cyan",
                  },
                  {
                    label: "Ver Análises",
                    desc: "KPIs e distribuição",
                    href: "/analytics",
                    color: "violet",
                  },
                  {
                    label: "Histórico",
                    desc: "Últimos processamentos",
                    href: "/history",
                    color: "emerald",
                  },
                ].map((action) => (
                  <Link key={action.label} href={action.href} className="block">
                    <div className="flex items-center justify-between p-3 rounded-xl bg-white/[0.02] border border-white/[0.04] hover:border-white/[0.08] hover:bg-white/[0.04] transition-all group">
                      <div>
                        <p className="text-sm font-medium text-text-primary">
                          {action.label}
                        </p>
                        <p className="text-xs text-text-muted">{action.desc}</p>
                      </div>
                      <ArrowRightIcon className="w-4 h-4 text-text-muted group-hover:text-cyan-glow-400 group-hover:translate-x-1 transition-all" />
                    </div>
                  </Link>
                ))}
              </div>
            </GlassCard>

            {/* Source breakdown */}
            <GlassCard className="p-6 space-y-4">
              <h3 className="text-sm font-bold text-text-primary uppercase tracking-wider">
                Distribuição
              </h3>
              {stats
                ? Object.entries(stats.animals_by_source).map(
                    ([source, count]) => {
                      const total = Object.values(
                        stats.animals_by_source
                      ).reduce((a, b) => a + b, 0);
                      const pct =
                        total > 0 ? Math.round((count / total) * 100) : 0;
                      const barColors: Record<string, string> = {
                        ANCP: "bg-cyan-glow",
                        PMGZ: "bg-emerald-glow-400",
                        Geneplus: "bg-violet-glow-400",
                      };
                      return (
                        <div key={source} className="space-y-1.5">
                          <div className="flex justify-between text-xs">
                            <span className="text-text-secondary">{source}</span>
                            <span className="text-white font-bold">{pct}%</span>
                          </div>
                          <div className="h-1.5 bg-white/[0.04] rounded-full overflow-hidden">
                            <motion.div
                              initial={{ width: 0 }}
                              animate={{ width: `${pct}%` }}
                              transition={{ duration: 1, delay: 0.5 }}
                              className={`h-full rounded-full ${
                                barColors[source] || "bg-slate-500"
                              }`}
                            />
                          </div>
                        </div>
                      );
                    }
                  )
                : null}
            </GlassCard>
          </motion.div>
        </div>
      </motion.div>
    </DashboardLayout>
  );
}

function KpiCard({
  title,
  value,
  subtitle,
  icon,
  color,
  trend,
}: {
  title: string;
  value: string;
  subtitle: string;
  icon: React.ReactNode;
  color: "cyan" | "violet" | "emerald" | "rose";
  trend: string;
}) {
  const colors: Record<string, { bg: string; border: string; text: string; glow: string }> = {
    cyan: {
      bg: "bg-cyan-glow/[0.06]",
      border: "border-cyan-glow/20",
      text: "text-cyan-glow-400",
      glow: "hover:shadow-[0_0_30px_rgba(6,182,212,0.08)]",
    },
    violet: {
      bg: "bg-violet-glow/[0.06]",
      border: "border-violet-glow/20",
      text: "text-violet-glow-400",
      glow: "hover:shadow-[0_0_30px_rgba(139,92,246,0.08)]",
    },
    emerald: {
      bg: "bg-emerald-glow/[0.06]",
      border: "border-emerald-glow/20",
      text: "text-emerald-glow-400",
      glow: "hover:shadow-[0_0_30px_rgba(16,185,129,0.08)]",
    },
    rose: {
      bg: "bg-rose-neon/[0.06]",
      border: "border-rose-neon/20",
      text: "text-rose-neon-400",
      glow: "hover:shadow-[0_0_30px_rgba(244,63,94,0.08)]",
    },
  };
  const c = colors[color];

  return (
    <motion.div
      whileHover={{ y: -2, scale: 1.01 }}
      className={`glass-card p-6 ${c.glow} transition-shadow duration-300`}
    >
      <div className="flex items-center justify-between mb-4">
        <div
          className={`w-11 h-11 rounded-xl ${c.bg} border ${c.border} flex items-center justify-center ${c.text}`}
        >
          {icon}
        </div>
        <span className="text-[11px] font-mono text-text-muted bg-white/[0.03] px-2 py-1 rounded-md">
          {trend}
        </span>
      </div>
      <p className="text-[11px] text-text-muted uppercase tracking-widest font-medium">
        {title}
      </p>
      <p className="text-2xl font-bold text-white mt-1">{value}</p>
      <p className="text-xs text-text-muted mt-0.5">{subtitle}</p>
    </motion.div>
  );
}
