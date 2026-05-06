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
} from "@heroicons/react/24/outline";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { GlassCard } from "@/components/ui/glass-card";
import { api } from "@/lib/api";

interface AnimalV2 {
  id: string;
  rgn: string;
  nome: string | null;
  sexo: string | null;
  nascimento: string | null;
  genotipado: boolean | null;
  csg: boolean | null;
  evaluations: Array<{
    iabczg: number | null;
    fonte_origem: string | null;
  }>;
}

const PAGE_SIZE = 20;

export default function AnimalsPage() {
  const [animals, setAnimals] = useState<AnimalV2[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [source, setSource] = useState("");
  const [sexo, setSexo] = useState("");
  const [genotipado, setGenotipado] = useState("");
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
  }, [page, source, sexo]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(0);
    fetchAnimals();
  };

  const getSexLabel = (s: string | null) => {
    if (s === "M") return "Macho";
    if (s === "F") return "Fêmea";
    return "—";
  };

  const getSexColor = (s: string | null) => {
    if (s === "M") return "text-blue-400 bg-blue-400/10";
    if (s === "F") return "text-pink-400 bg-pink-400/10";
    return "text-text-muted bg-white/5";
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white tracking-tight">
              Animais
            </h1>
            <p className="text-text-secondary text-sm mt-1">
              Busque e visualize os dados genéticos dos animais
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
              <label className="text-[10px] text-text-muted uppercase tracking-wider mb-1 block">
                Buscar
              </label>
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

            <div className="w-36">
              <label className="text-[10px] text-text-muted uppercase tracking-wider mb-1 block">
                Fonte
              </label>
              <div className="relative">
                <select
                  value={source}
                  onChange={(e) => { setSource(e.target.value); setPage(0); }}
                  className="w-full px-3 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white text-sm focus:border-emerald-glow/30 focus:outline-none transition-colors appearance-none cursor-pointer"
                >
                  <option value="" className="bg-deep-dark text-white">Todas</option>
                  <option value="ANCP" className="bg-deep-dark text-white">ANCP</option>
                  <option value="PMGZ" className="bg-deep-dark text-white">PMGZ</option>
                  <option value="Geneplus" className="bg-deep-dark text-white">Geneplus</option>
                </select>
                <svg className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>

            <div className="w-28">
              <label className="text-[10px] text-text-muted uppercase tracking-wider mb-1 block">
                Sexo
              </label>
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

            <div className="w-28">
              <label className="text-[10px] text-text-muted uppercase tracking-wider mb-1 block">
                Genotipado
              </label>
              <div className="relative">
                <select
                  value={source}
                  onChange={(e) => { setSource(e.target.value); setPage(0); }}
                  className="w-full px-3 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white text-sm focus:border-emerald-glow/30 focus:outline-none transition-colors appearance-none cursor-pointer"
                >
                  <option value="" className="bg-deep-dark text-white">Todos</option>
                  <option value="sim" className="bg-deep-dark text-white">Sim</option>
                  <option value="nao" className="bg-deep-dark text-white">Não</option>
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

        {/* Error state */}
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
                  <th className="text-left px-4 py-3 text-[10px] text-text-muted uppercase tracking-wider font-semibold">
                    RGN
                  </th>
                  <th className="text-left px-4 py-3 text-[10px] text-text-muted uppercase tracking-wider font-semibold">
                    Nome
                  </th>
                  <th className="text-left px-4 py-3 text-[10px] text-text-muted uppercase tracking-wider font-semibold">
                    Sexo
                  </th>
                  <th className="text-left px-4 py-3 text-[10px] text-text-muted uppercase tracking-wider font-semibold">
                    Raça
                  </th>
                  <th className="text-right px-4 py-3 text-[10px] text-text-muted uppercase tracking-wider font-semibold">
                    P210
                  </th>
                  <th className="text-right px-4 py-3 text-[10px] text-text-muted uppercase tracking-wider font-semibold">
                    P365
                  </th>
                  <th className="text-right px-4 py-3 text-[10px] text-text-muted uppercase tracking-wider font-semibold">
                    P450
                  </th>
                  <th className="text-left px-4 py-3 text-[10px] text-text-muted uppercase tracking-wider font-semibold">
                    Fonte
                  </th>
                  <th className="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  Array.from({ length: 8 }).map((_, i) => (
                    <tr key={i} className="border-b border-white/[0.02]">
                      {Array.from({ length: 8 }).map((_, j) => (
                        <td key={j} className="px-4 py-3">
                          <div className="h-4 bg-white/[0.04] rounded animate-pulse" />
                        </td>
                      ))}
                    </tr>
                  ))
                ) : animals.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="px-4 py-12 text-center">
                      <p className="text-text-muted text-sm">
                        Nenhum animal encontrado
                      </p>
                    </td>
                  </tr>
                ) : (
                  animals.map((animal, i) => {
                    const latestEval = animal.evaluations?.[0];
                    return (
                      <motion.tr
                        key={animal.id}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: i * 0.02 }}
                        className="border-b border-white/[0.02] hover:bg-white/[0.02] transition-colors"
                      >
                        <td className="px-4 py-3">
                          <span className="font-mono text-sm text-emerald-glow-400">
                            {animal.rgn}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-text-primary">
                          {animal.nome || "—"}
                        </td>
                        <td className="px-4 py-3">
                          <span
                            className={`text-xs px-2 py-0.5 rounded-full font-medium ${getSexColor(
                              animal.sexo
                            )}`}
                          >
                            {getSexLabel(animal.sexo)}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-text-secondary">
                          {animal.nascimento ? new Date(animal.nascimento).toLocaleDateString('pt-BR') : "—"}
                        </td>
                        <td className="px-4 py-3 text-sm text-text-primary text-right font-mono">
                          {latestEval?.iabczg?.toFixed(2) || "—"}
                        </td>
                        <td className="px-4 py-3">
                          <span className={`text-xs px-2 py-0.5 rounded-full ${animal.genotipado ? 'bg-emerald-glow/10 text-emerald-glow-400' : 'bg-white/[0.04] text-text-muted'}`}>
                            {animal.genotipado ? 'Sim' : 'Não'}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <span className="text-xs px-2 py-0.5 rounded-full bg-white/[0.04] text-text-muted">
                            {latestEval?.fonte_origem || "—"}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <Link
                            href={`/animals/${animal.id}`}
                            className="text-xs text-emerald-glow-400 hover:text-emerald-glow-300 transition-colors"
                          >
                            Detalhes
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
                Página {page + 1} · {animals.length} resultados
              </p>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                  disabled={page === 0}
                  className="p-2 rounded-lg border border-white/[0.06] text-text-muted hover:text-text-primary hover:bg-white/[0.03] disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                >
                  <ChevronLeftIcon className="w-4 h-4" />
                </button>
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
