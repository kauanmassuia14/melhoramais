"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowLeftIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
} from "@heroicons/react/24/outline";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { GlassCard } from "@/components/ui/glass-card";
import { api, Animal } from "@/lib/api";

interface StatCardProps {
  label: string;
  value: string | number | null;
  unit?: string;
}

function StatCard({ label, value, unit }: StatCardProps) {
  return (
    <div className="px-4 py-3 rounded-xl bg-white/[0.02] border border-white/[0.04]">
      <p className="text-[10px] text-text-muted uppercase tracking-wider mb-1">
        {label}
      </p>
      <p className="text-lg font-bold text-text-primary font-mono">
        {value !== null && value !== undefined ? value : "—"}
        {unit && value !== null && value !== undefined && (
          <span className="text-xs text-text-muted ml-1">{unit}</span>
        )}
      </p>
    </div>
  );
}

export default function AnimalDetailPage() {
  const params = useParams();
  const id = Number(params.id);
  const [animal, setAnimal] = useState<Animal | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnimal = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getAnimal(id);
      setAnimal(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erro ao carregar animal");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id) fetchAnimal();
  }, [id]);

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
                  <span className="font-mono text-cyan-glow-400">
                    {animal.rgn_animal}
                  </span>
                  {animal.nome_animal && (
                    <span className="text-text-secondary ml-3 text-2xl">
                      — {animal.nome_animal}
                    </span>
                  )}
                </>
              ) : (
                "Animal não encontrado"
              )}
            </h1>
            {animal && (
              <p className="text-text-secondary text-sm mt-1">
                {getSexLabel(animal.sexo)} · {animal.raca || "Raça não informada"} ·{" "}
                Fonte: {animal.fonte_origem || "—"}
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
                <StatCard label="RGN" value={animal.rgn_animal} />
                <StatCard label="Nome" value={animal.nome_animal} />
                <StatCard label="Sexo" value={getSexLabel(animal.sexo)} />
                <StatCard label="Raça" value={animal.raca} />
                <StatCard label="Data Nascimento" value={animal.data_nascimento || "—"} />
                <StatCard label="Mãe (RGN)" value={animal.mae_rgn} />
                <StatCard label="Pai (RGN)" value={animal.pai_rgn} />
                <StatCard label="Fonte" value={animal.fonte_origem} />
              </div>
            </GlassCard>

            {/* Genetic Indices */}
            <GlassCard className="p-6">
              <h2 className="text-sm font-semibold text-text-muted uppercase tracking-wider mb-4">
                Índices Genéticos
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <StatCard
                  label="P210 — Peso Desmama"
                  value={animal.p210_peso_desmama?.toFixed(2) ?? null}
                  unit="%"
                />
                <StatCard
                  label="P365 — Peso Ano"
                  value={animal.p365_peso_ano?.toFixed(2) ?? null}
                  unit="%"
                />
                <StatCard
                  label="P450 — Peso Sobreano"
                  value={animal.p450_peso_sobreano?.toFixed(2) ?? null}
                  unit="%"
                />
                <StatCard
                  label="PE — Perímetro Escrotal"
                  value={animal.pe_perimetro_escrotal?.toFixed(2) ?? null}
                  unit="cm"
                />
                <StatCard
                  label="AOL — Área Olho de Lombo"
                  value={animal.a_area_olho_lombo?.toFixed(2) ?? null}
                  unit="cm²"
                />
                <StatCard
                  label="EGP — Espessura Gordura"
                  value={animal.eg_espessura_gordura?.toFixed(2) ?? null}
                  unit="mm"
                />
                <StatCard
                  label="IM — Idade 1º Parto"
                  value={animal.im_idade_primeiro_parto?.toFixed(2) ?? null}
                  unit="meses"
                />
                <StatCard
                  label="Processado em"
                  value={
                    animal.data_processamento
                      ? new Date(animal.data_processamento).toLocaleDateString("pt-BR")
                      : "—"
                  }
                />
              </div>
            </GlassCard>
          </motion.div>
        )}

        {/* Loading skeleton */}
        {loading && (
          <div className="space-y-6">
            <GlassCard className="p-6">
              <div className="h-4 w-24 bg-white/[0.04] rounded animate-pulse mb-4" />
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Array.from({ length: 8 }).map((_, i) => (
                  <div key={i} className="h-16 bg-white/[0.02] rounded-xl animate-pulse" />
                ))}
              </div>
            </GlassCard>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
