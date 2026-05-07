"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowLeftIcon,
  ArrowPathIcon,
  ExclamationTriangleIcon,
  CheckBadgeIcon,
  BeakerIcon,
} from "@heroicons/react/24/outline";
import { api } from "@/lib/api";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { GlassCard } from "@/components/ui/glass-card";
import { MetricCard } from "@/components/ui/MetricCard";

interface EvaluationMetric {
  dep: number | null;
  ac: number | null;
  deca: number | null;
  p_percent: number | null;
}

interface Evaluation {
  id: string;
  safra: number | null;
  fonte_origem: string | null;
  iabczg: number | null;
  deca_index: number | null;
  pn: EvaluationMetric | null;
  pd: EvaluationMetric | null;
  pa: EvaluationMetric | null;
  ps: EvaluationMetric | null;
  pm: EvaluationMetric | null;
  ipp: EvaluationMetric | null;
  stay: EvaluationMetric | null;
  pe_365: EvaluationMetric | null;
  psn: EvaluationMetric | null;
  aol: EvaluationMetric | null;
  acab: EvaluationMetric | null;
  marmoreio: EvaluationMetric | null;
  eg: EvaluationMetric | null;
  pg: EvaluationMetric | null;
  mg: EvaluationMetric | null;
}

interface AnimalV2 {
  id: string;
  rgn: string | null;
  serie: string | null;
  nome: string | null;
  sexo: string | null;
  nascimento: string | null;
  genotipado: boolean | null;
  csg: boolean | null;
  farm_id: string | null;
  evaluations: Evaluation[];
}

const fmt = (v: number | null | undefined, d = 2) =>
  v != null ? Number(v).toFixed(d) : null;

const fmtDate = (d: string | null) => {
  if (!d) return null;
  return new Date(d).toLocaleDateString("pt-BR");
};

export default function AnimalDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [animal, setAnimal] = useState<AnimalV2 | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnimal = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getAnimalV2(id);
      setAnimal(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erro ao carregar animal");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id && typeof window !== "undefined" && localStorage.getItem("access_token")) {
      fetchAnimal();
    }
  }, [id]);

  const ev = animal?.evaluations?.[0] ?? null;
  const decanil = ev?.deca_index ?? ev?.pd?.deca ?? ev?.pn?.deca;

  const getSexLabel = (s: string | null) => {
    if (s === "M") return "Macho";
    if (s === "F") return "Fêmea";
    return "—";
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Back + Header */}
        <div className="flex items-center gap-4">
          <Link
            href="/animals"
            className="p-2 rounded-xl border border-white/[0.06] text-text-muted hover:text-text-primary hover:bg-white/[0.03] transition-all"
          >
            <ArrowLeftIcon className="w-5 h-5" />
          </Link>
          <div className="flex-1">
            <h1 className="text-3xl font-bold text-white tracking-tight">
              {loading ? (
                <span className="inline-block w-48 h-8 bg-white/[0.04] rounded animate-pulse" />
              ) : animal ? (
                <>
                  <span className="font-mono text-cyan-400">{animal.rgn || "—"}</span>
                  {animal.nome && (
                    <span className="text-text-secondary ml-3 text-2xl">— {animal.nome}</span>
                  )}
                </>
              ) : (
                "Animal não encontrado"
              )}
            </h1>
            {animal && (
              <p className="text-text-secondary text-sm mt-1">
                {getSexLabel(animal.sexo)}
                {animal.nascimento && ` · Nascido em ${fmtDate(animal.nascimento)}`}
                {ev?.fonte_origem && ` · Fonte: ${ev.fonte_origem}`}
                {ev?.safra && ` · Safra ${ev.safra}`}
              </p>
            )}
          </div>
          <button
            onClick={fetchAnimal}
            className="flex items-center gap-2 px-4 py-2 rounded-xl border border-white/[0.06] bg-white/[0.02] text-sm text-text-secondary hover:bg-white/[0.04] transition-all"
          >
            <ArrowPathIcon className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            Atualizar
          </button>
        </div>

        {/* Error */}
        {error && (
          <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-rose-500/[0.06] border border-rose-500/20">
            <ExclamationTriangleIcon className="w-5 h-5 text-rose-400 flex-shrink-0" />
            <span className="text-sm text-rose-400">{error}</span>
          </div>
        )}

        {/* Loading skeleton */}
        {loading && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="h-20 rounded-xl bg-white/[0.04] animate-pulse" />
            ))}
          </div>
        )}

        {animal && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-8"
          >
            {/* ── Identificação ─────────────────────────────────────────── */}
            <GlassCard className="p-6">
              <h2 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-5">
                Identificação
              </h2>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
                {/* RGN */}
                <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                  <span className="text-[10px] text-text-muted uppercase tracking-wider block mb-1">RGN</span>
                  <span className="font-mono text-lg font-bold text-emerald-400">{animal.rgn || "—"}</span>
                </div>
                {/* Série */}
                {animal.serie && (
                  <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                    <span className="text-[10px] text-text-muted uppercase tracking-wider block mb-1">Série</span>
                    <span className="font-mono text-lg font-bold text-white">{animal.serie}</span>
                  </div>
                )}
                {/* Nome */}
                <div className="rounded-xl border border-white/10 bg-white/5 p-4 col-span-2">
                  <span className="text-[10px] text-text-muted uppercase tracking-wider block mb-1">Nome</span>
                  <span className="text-base font-semibold text-white">{animal.nome || "—"}</span>
                </div>
                {/* Sexo */}
                <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                  <span className="text-[10px] text-text-muted uppercase tracking-wider block mb-1">Sexo</span>
                  <span className={`text-sm font-semibold ${animal.sexo === "M" ? "text-blue-400" : animal.sexo === "F" ? "text-pink-400" : "text-text-muted"}`}>
                    {getSexLabel(animal.sexo)}
                  </span>
                </div>
                {/* Nascimento */}
                <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                  <span className="text-[10px] text-text-muted uppercase tracking-wider block mb-1">Nascimento</span>
                  <span className="text-sm font-semibold text-white">{fmtDate(animal.nascimento) || "—"}</span>
                </div>
                {/* Genotipado */}
                <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                  <span className="text-[10px] text-text-muted uppercase tracking-wider block mb-1">Genotipado</span>
                  {animal.genotipado ? (
                    <span className="flex items-center gap-1 text-sm font-semibold text-emerald-400">
                      <CheckBadgeIcon className="w-4 h-4" /> Sim
                    </span>
                  ) : animal.genotipado === false ? (
                    <span className="text-sm font-semibold text-text-muted">Não</span>
                  ) : (
                    <span className="text-sm text-text-muted">—</span>
                  )}
                </div>
                {/* CSG */}
                <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                  <span className="text-[10px] text-text-muted uppercase tracking-wider block mb-1">CSG</span>
                  {animal.csg ? (
                    <span className="flex items-center gap-1 text-sm font-semibold text-violet-400">
                      <BeakerIcon className="w-4 h-4" /> Sim
                    </span>
                  ) : animal.csg === false ? (
                    <span className="text-sm font-semibold text-text-muted">Não</span>
                  ) : (
                    <span className="text-sm text-text-muted">—</span>
                  )}
                </div>
              </div>
            </GlassCard>

            {/* ── Índices Genéticos ──────────────────────────────────────── */}
            {ev && (
              <GlassCard className="p-6">
                <div className="flex items-center justify-between mb-5">
                  <h2 className="text-xs font-semibold text-text-muted uppercase tracking-wider">
                    Índices Genéticos
                  </h2>
                  <span className="text-xs text-text-muted">
                    Fonte: <span className="text-white font-medium">{ev.fonte_origem || "—"}</span>
                    {ev.safra && <> · Safra <span className="text-white font-medium">{ev.safra}</span></>}
                  </span>
                </div>

                {/* Global */}
                <div className="grid grid-cols-2 gap-4 mb-6">
                  <MetricCard metricKey="iabczg" label="iABCZ — Índice Global" value={fmt(ev.iabczg)} />
                  <MetricCard metricKey="deca" label="DECA — Decil" value={decanil?.toString()} />
                </div>

                {/* Pesos */}
                <h3 className="text-[10px] text-text-muted uppercase tracking-wider mb-3 mt-2">Pesos (DEP)</h3>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4 mb-6">
                  <MetricCard metricKey="pn" label="PN — Peso Nascimento" value={fmt(ev.pn?.dep)} unit="kg" />
                  <MetricCard metricKey="pd" label="PD — Peso Desmama" value={fmt(ev.pd?.dep)} unit="kg" />
                  <MetricCard metricKey="pa" label="PA — Peso Ano" value={fmt(ev.pa?.dep)} unit="kg" />
                  <MetricCard metricKey="ps" label="PS — Peso Sobreano" value={fmt(ev.ps?.dep)} unit="kg" />
                  <MetricCard metricKey="pm" label="PM — Peso Materno" value={fmt(ev.pm?.dep)} unit="kg" />
                </div>

                {/* Acurácias */}
                {(ev.pn?.ac || ev.pd?.ac || ev.ps?.ac) && (
                  <>
                    <h3 className="text-[10px] text-text-muted uppercase tracking-wider mb-3 mt-2">Acurácias (%)</h3>
                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4 mb-6">
                      {ev.pn?.ac != null && <MetricCard metricKey="pn" label="AC% — PN" value={`${ev.pn.ac}`} unit="%" />}
                      {ev.pd?.ac != null && <MetricCard metricKey="pd" label="AC% — PD" value={`${ev.pd.ac}`} unit="%" />}
                      {ev.pa?.ac != null && <MetricCard metricKey="pa" label="AC% — PA" value={`${ev.pa.ac}`} unit="%" />}
                      {ev.ps?.ac != null && <MetricCard metricKey="ps" label="AC% — PS" value={`${ev.ps.ac}`} unit="%" />}
                      {ev.pm?.ac != null && <MetricCard metricKey="pm" label="AC% — PM" value={`${ev.pm.ac}`} unit="%" />}
                    </div>
                  </>
                )}

                {/* Reprodução */}
                <h3 className="text-[10px] text-text-muted uppercase tracking-wider mb-3 mt-2">Reprodução</h3>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4 mb-6">
                  <MetricCard metricKey="ipp" label="IPP — Idade 1º Parto" value={fmt(ev.ipp?.dep)} unit="dias" />
                  <MetricCard metricKey="stay" label="STAY — Stayability" value={fmt(ev.stay?.dep)} unit="%" />
                  <MetricCard metricKey="pe_365" label="PE-365 — Perímetro Escrotal" value={fmt(ev.pe_365?.dep)} unit="cm" />
                </div>

                {/* Carcaça */}
                <h3 className="text-[10px] text-text-muted uppercase tracking-wider mb-3 mt-2">Carcaça e Qualidade</h3>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4 mb-6">
                  <MetricCard metricKey="aol" label="AOL — Área Olho de Lombo" value={fmt(ev.aol?.dep)} unit="cm²" />
                  <MetricCard metricKey="acab" label="ACAB — Acabamento" value={fmt(ev.acab?.dep)} unit="mm" />
                  <MetricCard metricKey="marmoreio" label="MAR — Marmoreio" value={fmt(ev.marmoreio?.dep)} />
                </div>

                {/* Conformação */}
                <h3 className="text-[10px] text-text-muted uppercase tracking-wider mb-3 mt-2">Conformação</h3>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
                  <MetricCard metricKey="eg" label="E — Estrutura Corporal" value={fmt(ev.eg?.dep)} />
                  <MetricCard metricKey="pg" label="P — Precocidade" value={fmt(ev.pg?.dep)} />
                  <MetricCard metricKey="mg" label="M — Musculosidade" value={fmt(ev.mg?.dep)} />
                </div>
              </GlassCard>
            )}

            {/* Sem avaliações */}
            {!ev && (
              <GlassCard className="p-12 text-center">
                <p className="text-text-muted text-sm">
                  Nenhuma avaliação genética encontrada para este animal.
                </p>
              </GlassCard>
            )}
          </motion.div>
        )}
      </div>
    </DashboardLayout>
  );
}