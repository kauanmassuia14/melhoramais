"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  MagnifyingGlassIcon,
  FunnelIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  ArrowPathIcon,
  ExclamationTriangleIcon,
  CheckBadgeIcon,
  BeakerIcon,
} from "@heroicons/react/24/outline";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { GlassCard } from "@/components/ui/glass-card";
import { api } from "@/lib/api";

interface MetricBlock {
  dep: number | null;
  ac: number | null;
  deca: number | null;
  p_percent: number | null;
}

interface Evaluation {
  iabczg: number | null;
  deca_index: number | null;
  fonte_origem: string | null;
  pd: MetricBlock | null;   // DEP Desmama (~P210)
  ps: MetricBlock | null;   // DEP Sobreano (~P450)
  pn: MetricBlock | null;   // DEP Nascimento
}

interface AnimalV2 {
  id: string;
  rgn: string;
  serie: string | null;
  nome: string | null;
  sexo: string | null;
  nascimento: string | null;
  genotipado: boolean | null;
  csg: boolean | null;
  farm_id: string | null;
  evaluations: Evaluation[];
}

const PAGE_SIZE = 20;

const fmt = (v: number | null | undefined, decimals = 2) =>
  v != null ? v.toFixed(decimals) : "—";

const fmtDate = (d: string | null) => {
  if (!d) return "—";
  return new Date(d).toLocaleDateString("pt-BR", { year: "numeric", month: "2-digit", day: "2-digit" });
};

export default function AnimalsPage() {
  const [animals, setAnimals] = useState<AnimalV2[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [sexo, setSexo] = useState("");
  const [page, setPage] = useState(0);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(true);

  const fetchAnimals = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getAnimalsV2({
        search: search || undefined,
        sexo: sexo || undefined,
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
      });
      setAnimals(data.data);
      setTotal(data.total);
      setHasMore(data.data.length === PAGE_SIZE);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erro ao carregar animais");
    } finally {
      setLoading(false);
    }
  }, [search, sexo, page]);

  useEffect(() => {
    if (typeof window !== "undefined" && localStorage.getItem("access_token")) {
      fetchAnimals();
    }
  }, [page, sexo]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(0);
    fetchAnimals();
  };

  const getSexBadge = (s: string | null) => {
    if (s === "M") return <span className="text-xs px-2 py-0.5 rounded-full font-medium text-blue-400 bg-blue-400/10">Macho</span>;
    if (s === "F") return <span className="text-xs px-2 py-0.5 rounded-full font-medium text-pink-400 bg-pink-400/10">Fêmea</span>;
    return <span className="text-text-muted text-xs">—</span>;
  };

  const getDecaBadge = (deca: number | null | undefined) => {
    if (deca == null) return <span className="text-text-muted text-xs">—</span>;
    const colors = [
      "bg-emerald-500/20 text-emerald-400",
      "bg-cyan-500/20 text-cyan-400",
      "bg-blue-500/20 text-blue-400",
      "bg-violet-500/20 text-violet-400",
      "bg-yellow-500/20 text-yellow-400",
      "bg-orange-500/20 text-orange-400",
      "bg-rose-500/20 text-rose-400",
    ];
    const colorClass = colors[Math.min(deca - 1, colors.length - 1)] ?? colors[colors.length - 1];
    return (
      <span className={`text-xs px-2 py-0.5 rounded-full font-bold ${colorClass}`}>
        D{deca}
      </span>
    );
  };

  const columns = [
    "RGN", "Nome", "Sexo", "Nascimento", "Genotipado", "CSG",
    "Índice (IABCZG)", "Deca", "DEP Desmama", "DEP Sobreano", "Fonte", "",
  ];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white tracking-tight">Animais</h1>
            <p className="text-text-secondary text-sm mt-1">
              {total > 0 ? `${total.toLocaleString("pt-BR")} animais encontrados` : "Busque e visualize os dados genéticos dos animais"}
            </p>
          </div>
          <button
            onClick={fetchAnimals}
            className="flex items-center gap-2 px-4 py-2 rounded-xl border border-white/10 bg-white/5 text-sm text-text-secondary hover:bg-white/10 transition-all"
          >
            <ArrowPathIcon className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            Atualizar
          </button>
        </div>

        {/* Filters */}
        <GlassCard className="p-4">
          <form onSubmit={handleSearch} className="flex flex-wrap gap-3 items-end">
            <div className="flex-1 min-w-[200px]">
              <label className="text-[10px] text-text-muted uppercase tracking-wider mb-1 block">Buscar</label>
              <div className="relative">
                <MagnifyingGlassIcon className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
                <input
                  type="text"
                  placeholder="RGN ou nome do animal..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-sm text-text-primary placeholder:text-text-muted focus:border-emerald-glow/30 focus:outline-none transition-colors"
                />
              </div>
            </div>

            <div className="w-28">
              <label className="text-[10px] text-text-muted uppercase tracking-wider mb-1 block">Sexo</label>
              <div className="relative">
                <select
                  value={sexo}
                  onChange={(e) => { setSexo(e.target.value); setPage(0); }}
                  className="w-full px-3 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white text-sm focus:border-emerald-glow/30 focus:outline-none transition-colors appearance-none cursor-pointer"
                >
                  <option value="" className="bg-deep-dark text-white">Todos</option>
                  <option value="M" className="bg-deep-dark text-white">Macho</option>
                  <option value="F" className="bg-deep-dark text-white">Fêmea</option>
                </select>
                <svg className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>

            <button
              type="submit"
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-glow/10 border border-emerald-glow/20 text-emerald-glow-400 text-sm font-medium hover:bg-emerald-glow/20 transition-all"
            >
              <FunnelIcon className="w-4 h-4" />
              Filtrar
            </button>
          </form>
        </GlassCard>

        {/* Error */}
        {error && (
          <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-rose-neon/[0.06] border border-rose-neon/20">
            <ExclamationTriangleIcon className="w-5 h-5 text-rose-neon-400 flex-shrink-0" />
            <span className="text-sm text-rose-neon-400">{error}</span>
          </div>
        )}

        {/* Table */}
        <GlassCard className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/[0.04]">
                  {columns.map((col) => (
                    <th
                      key={col}
                      className={`px-4 py-3 text-[10px] text-text-muted uppercase tracking-wider font-semibold ${
                        ["Índice (IABCZG)", "DEP Desmama", "DEP Sobreano"].includes(col)
                          ? "text-right"
                          : "text-left"
                      }`}
                    >
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  Array.from({ length: 8 }).map((_, i) => (
                    <tr key={i} className="border-b border-white/[0.02]">
                      {Array.from({ length: 12 }).map((_, j) => (
                        <td key={j} className="px-4 py-3">
                          <div className="h-4 bg-white/[0.04] rounded animate-pulse" />
                        </td>
                      ))}
                    </tr>
                  ))
                ) : animals.length === 0 ? (
                  <tr>
                    <td colSpan={12} className="px-4 py-12 text-center">
                      <p className="text-text-muted text-sm">Nenhum animal encontrado</p>
                    </td>
                  </tr>
                ) : (
                  animals.map((animal, i) => {
                    const ev = animal.evaluations?.[0];
                    return (
                      <motion.tr
                        key={animal.id}
                        initial={{ opacity: 0, y: 4 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.015 }}
                        className="border-b border-white/[0.02] hover:bg-white/[0.025] transition-colors group"
                      >
                        {/* RGN */}
                        <td className="px-4 py-3">
                          <span className="font-mono text-sm font-semibold text-emerald-glow-400">
                            {animal.rgn}
                          </span>
                          {animal.serie && (
                            <span className="text-[10px] text-text-muted block">{animal.serie}</span>
                          )}
                        </td>

                        {/* Nome */}
                        <td className="px-4 py-3 text-sm text-text-primary max-w-[180px]">
                          <span className="truncate block">{animal.nome || "—"}</span>
                        </td>

                        {/* Sexo */}
                        <td className="px-4 py-3">{getSexBadge(animal.sexo)}</td>

                        {/* Nascimento */}
                        <td className="px-4 py-3 text-xs text-text-secondary font-mono">
                          {fmtDate(animal.nascimento)}
                        </td>

                        {/* Genotipado */}
                        <td className="px-4 py-3">
                          {animal.genotipado ? (
                            <span className="flex items-center gap-1 text-xs text-emerald-400">
                              <CheckBadgeIcon className="w-4 h-4" />
                              Sim
                            </span>
                          ) : (
                            <span className="text-xs text-text-muted">Não</span>
                          )}
                        </td>

                        {/* CSG */}
                        <td className="px-4 py-3">
                          {animal.csg ? (
                            <span className="flex items-center gap-1 text-xs text-violet-400">
                              <BeakerIcon className="w-4 h-4" />
                              Sim
                            </span>
                          ) : (
                            <span className="text-xs text-text-muted">Não</span>
                          )}
                        </td>

                        {/* IABCZG */}
                        <td className="px-4 py-3 text-right">
                          {ev?.iabczg != null ? (
                            <span className="font-mono text-sm font-semibold text-cyan-400">
                              {Number(ev.iabczg).toFixed(2)}
                            </span>
                          ) : (
                            <span className="text-text-muted text-xs">—</span>
                          )}
                        </td>

                        {/* Deca */}
                        <td className="px-4 py-3">
                          {getDecaBadge(ev?.deca_index)}
                        </td>

                        {/* DEP Desmama (pd) */}
                        <td className="px-4 py-3 text-right">
                          {ev?.pd?.dep != null ? (
                            <span className="font-mono text-sm text-amber-400">
                              {fmt(ev.pd.dep)}
                            </span>
                          ) : (
                            <span className="text-text-muted text-xs">—</span>
                          )}
                        </td>

                        {/* DEP Sobreano (ps) */}
                        <td className="px-4 py-3 text-right">
                          {ev?.ps?.dep != null ? (
                            <span className="font-mono text-sm text-orange-400">
                              {fmt(ev.ps.dep)}
                            </span>
                          ) : (
                            <span className="text-text-muted text-xs">—</span>
                          )}
                        </td>

                        {/* Fonte */}
                        <td className="px-4 py-3">
                          {ev?.fonte_origem ? (
                            <span className="text-xs px-2 py-0.5 rounded-full bg-white/5 border border-white/10 text-text-secondary">
                              {ev.fonte_origem}
                            </span>
                          ) : (
                            <span className="text-text-muted text-xs">—</span>
                          )}
                        </td>

                        {/* Link */}
                        <td className="px-4 py-3">
                          <Link
                            href={`/animals/${animal.id}`}
                            className="text-xs text-emerald-glow-400 opacity-0 group-hover:opacity-100 hover:text-emerald-glow-300 transition-all"
                          >
                            Detalhes →
                          </Link>
                        </td>
                      </motion.tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {!loading && animals.length > 0 && (
            <div className="flex items-center justify-between px-4 py-3 border-t border-white/[0.04]">
              <p className="text-xs text-text-muted">
                Página {page + 1} · {animals.length} de {total.toLocaleString("pt-BR")} animais
              </p>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                  disabled={page === 0}
                  className="p-2 rounded-lg border border-white/[0.06] text-text-muted hover:text-text-primary hover:bg-white/[0.03] disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                >
                  <ChevronLeftIcon className="w-4 h-4" />
                </button>
                <span className="text-xs text-text-muted px-2">{page + 1}</span>
                <button
                  onClick={() => setPage((p) => p + 1)}
                  disabled={!hasMore}
                  className="p-2 rounded-lg border border-white/[0.06] text-text-muted hover:text-text-primary hover:bg-white/[0.03] disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                >
                  <ChevronRightIcon className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </GlassCard>
      </div>
    </DashboardLayout>
  );
}
