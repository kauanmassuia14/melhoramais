"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowLeftIcon, ArrowPathIcon, ExclamationTriangleIcon } from "@heroicons/react/24/outline";
import { api } from "@/lib/api";
import DashboardLayout from "@/components/DashboardLayout";
import GlassCard from "@/components/GlassCard";
import StatCard from "@/components/StatCard";

interface EvaluationMetric {
  dep: number | null;
  ac: number | null;
  deca: number | null;
  p_percent: number | null;
}

interface Evaluation {
  id: string;
  safra: number;
  fonte_origem: string;
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
  nome: string | null;
  sexo: string | null;
  nascimento: string | null;
  genotipado: boolean | null;
  csg: boolean | null;
  farm_id: string | null;
  evaluations: Evaluation[];
}

export default function AnimalDetailPage({ params }: { params: { id: string } }) {
  const [animal, setAnimal] = useState<AnimalV2 | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnimal = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getAnimalV2(params.id);
      setAnimal(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erro ao carregar animal");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (params.id) fetchAnimal();
  }, [params.id]);

  const getSexLabel = (s: string | null) => {
    if (s === "M") return "Macho";
    if (s === "F") return "Fêmea";
    return "—";
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "—";
    try {
      return new Date(dateStr).toLocaleDateString("pt-BR");
    } catch {
      return dateStr;
    }
  };

  const getLatestEvaluation = () => {
    if (!animal?.evaluations?.length) return null;
    return animal.evaluations[0];
  };

  const eval_ = getLatestEvaluation();

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
                  <span className="font-mono text-cyan-glow-400">
                    {animal.rgn || "—"}
                  </span>
                  {animal.nome && (
                    <span className="text-text-secondary ml-3 text-2xl">
                      — {animal.nome}
                    </span>
                  )}
                </>
              ) : (
                "Animal não encontrado"
              )}
            </h1>
            {animal && (
              <p className="text-text-secondary text-sm mt-1">
                {getSexLabel(animal.sexo)} · {animal.genotipado ? "Genotipado" : "Não genotipado"} ·{" "}
                Fonte: {eval_?.fonte_origem || "—"}
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
          <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-rose-neon/[0.06] border border-rose-neon/20">
            <ExclamationTriangleIcon className="w-5 h-5 text-rose-neon-400 flex-shrink-0" />
            <span className="text-sm text-rose-neon-400">{error}</span>
          </div>
        )}

        {animal && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            {/* Identification */}
            <GlassCard className="p-6">
              <h2 className="text-sm font-semibold text-text-muted uppercase tracking-wider mb-4">
                Identificação
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <StatCard label="RGN" value={animal.rgn} />
                <StatCard label="Nome" value={animal.nome} />
                <StatCard label="Sexo" value={getSexLabel(animal.sexo)} />
                <StatCard label="Data Nascimento" value={formatDate(animal.nascimento)} />
                <StatCard 
                  label="Genotipado" 
                  value={animal.genotipado === true ? "Sim" : animal.genotipado === false ? "Não" : "—"} 
                />
                <StatCard 
                  label="CSG" 
                  value={animal.csg === true ? "Sim" : animal.csg === false ? "Não" : "—"} 
                />
                <StatCard label="Fonte" value={eval_?.fonte_origem || "—"} />
                <StatCard label="Safra" value={eval_?.safra?.toString() || "—"} />
              </div>
            </GlassCard>

            {/* Genetic Indices */}
            {eval_ && (
              <GlassCard className="p-6">
                <h2 className="text-sm font-semibold text-text-muted uppercase tracking-wider mb-4">
                  Índices Genéticos
                </h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <StatCard
                    label="iABCZ — Índice ABCZ"
                    value={eval_.iabczg?.toFixed(2) ?? null}
                  />
                  <StatCard
                    label="DECA"
                    value={eval_.deca_index?.toString() ?? null}
                  />
                  
                  {/* PN - Peso Nascimento */}
                  <StatCard
                    label="PN-EDg — Peso Nascimento"
                    value={eval_.pn?.dep?.toFixed(2) ?? null}
                  />
                  <StatCard
                    label="PN-EDg — AC%"
                    value={eval_.pn?.ac?.toString() ?? null}
                    unit="%"
                  />
                  <StatCard
                    label="PN-EDg — DECA"
                    value={eval_.pn?.deca?.toString() ?? null}
                  />
                  <StatCard
                    label="PN-EDg — P%"
                    value={eval_.pn?.p_percent?.toFixed(1) ?? null}
                    unit="%"
                  />

                  {/* PD - Peso Desmama */}
                  <StatCard
                    label="PD-EDg — Peso Desmama"
                    value={eval_.pd?.dep?.toFixed(2) ?? null}
                  />
                  <StatCard
                    label="PD-EDg — AC%"
                    value={eval_.pd?.ac?.toString() ?? null}
                    unit="%"
                  />
                  <StatCard
                    label="PD-EDg — DECA"
                    value={eval_.pd?.deca?.toString() ?? null}
                  />
                  <StatCard
                    label="PD-EDg — P%"
                    value={eval_.pd?.p_percent?.toFixed(1) ?? null}
                    unit="%"
                  />

                  {/* PA - Peso Ano */}
                  <StatCard
                    label="PA-EDg — Peso Ano"
                    value={eval_.pa?.dep?.toFixed(2) ?? null}
                  />
                  <StatCard
                    label="PA-EDg — AC%"
                    value={eval_.pa?.ac?.toString() ?? null}
                    unit="%"
                  />

                  {/* PS - Peso Sobreano */}
                  <StatCard
                    label="PS-EDg — Peso Sobreano"
                    value={eval_.ps?.dep?.toFixed(2) ?? null}
                  />
                  <StatCard
                    label="PS-EDg — AC%"
                    value={eval_.ps?.ac?.toString() ?? null}
                    unit="%"
                  />

                  {/* PM - Peso Materno */}
                  <StatCard
                    label="PM-EMg — Peso Materno"
                    value={eval_.pm?.dep?.toFixed(2) ?? null}
                  />
                  <StatCard
                    label="PM-EMg — AC%"
                    value={eval_.pm?.ac?.toString() ?? null}
                    unit="%"
                  />

                  {/* IPP */}
                  <StatCard
                    label="IPP — Idade Primeiro Parto"
                    value={eval_.ipp?.dep?.toFixed(2) ?? null}
                  />
                  <StatCard
                    label="IPP — AC%"
                    value={eval_.ipp?.ac?.toString() ?? null}
                    unit="%"
                  />

                  {/* Stayability */}
                  <StatCard
                    label="STAYg — Stayability"
                    value={eval_.stay?.dep?.toFixed(2) ?? null}
                  />
                  <StatCard
                    label="STAYg — AC%"
                    value={eval_.stay?.ac?.toString() ?? null}
                    unit="%"
                  />

                  {/* PE 365 */}
                  <StatCard
                    label="PE-365g — Perímetro Escrotal"
                    value={eval_.pe_365?.dep?.toFixed(2) ?? null}
                  />
                  <StatCard
                    label="PE-365g — AC%"
                    value={eval_.pe_365?.ac?.toString() ?? null}
                    unit="%"
                  />

                  {/* AOL - Área Olho de Lombo */}
                  <StatCard
                    label="AOLg — Área Olho de Lombo"
                    value={eval_.aol?.dep?.toFixed(2) ?? null}
                    unit="cm²"
                  />
                  <StatCard
                    label="AOLg — AC%"
                    value={eval_.aol?.ac?.toString() ?? null}
                    unit="%"
                  />

                  {/* ACAB - Acabamento */}
                  <StatCard
                    label="ACABg — Acabamento"
                    value={eval_.acab?.dep?.toFixed(2) ?? null}
                    unit="mm"
                  />
                  <StatCard
                    label="ACABg — AC%"
                    value={eval_.acab?.ac?.toString() ?? null}
                    unit="%"
                  />

                  {/* Marmoreio */}
                  <StatCard
                    label="MARg — Marmoreio"
                    value={eval_.marmoreio?.dep?.toFixed(2) ?? null}
                  />
                  <StatCard
                    label="MARg — AC%"
                    value={eval_.marmoreio?.ac?.toString() ?? null}
                    unit="%"
                  />

                  {/* EG - Estrutura Corporal */}
                  <StatCard
                    label="Eg — Estrutura"
                    value={eval_.eg?.dep?.toFixed(2) ?? null}
                  />
                  <StatCard
                    label="Eg — AC%"
                    value={eval_.eg?.ac?.toString() ?? null}
                    unit="%"
                  />

                  {/* PG - Precocidade */}
                  <StatCard
                    label="Pg — Precocidade"
                    value={eval_.pg?.dep?.toFixed(2) ?? null}
                  />
                  <StatCard
                    label="Pg — AC%"
                    value={eval_.pg?.ac?.toString() ?? null}
                    unit="%"
                  />

                  {/* MG - Musculosidade */}
                  <StatCard
                    label="Mg — Musculosidade"
                    value={eval_.mg?.dep?.toFixed(2) ?? null}
                  />
                  <StatCard
                    label="Mg — AC%"
                    value={eval_.mg?.ac?.toString() ?? null}
                    unit="%"
                  />
                </div>
              </GlassCard>
            )}
          </motion.div>
        )}
      </div>
    </DashboardLayout>
  );
}