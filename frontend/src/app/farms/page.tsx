"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  PlusIcon,
  BuildingOffice2Icon,
  UserIcon,
  EnvelopeIcon,
  IdentificationIcon,
  ExclamationTriangleIcon,
  XMarkIcon,
  PencilIcon,
  MagnifyingGlassIcon,
  CheckIcon,
  Squares2X2Icon,
  ArrowTrendingUpIcon,
  ClockIcon,
  TrashIcon,
} from "@heroicons/react/24/outline";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { GlassCard } from "@/components/ui/glass-card";
import { GlowButton } from "@/components/ui/glow-button";
import { AnimatedInput } from "@/components/ui/animated-input";
import { useToast } from "@/components/ui/Toast";
import { api, Farm, DashboardStats, Upload } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

interface FarmWithStats extends Farm {
  stats?: DashboardStats;
  lastUpload?: Upload;
}

export default function FarmsPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [farms, setFarms] = useState<FarmWithStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [search, setSearch] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editName, setEditName] = useState("");
  const [savingEdit, setSavingEdit] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [form, setForm] = useState({
    nome_farm: "",
    cnpj: "",
    responsavel: "",
    email: "",
  });
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const { showToast } = useToast();

  const fetchFarms = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getFarms();
      const farmsWithStats = await Promise.all(
        data.map(async (farm) => {
          try {
            const [stats, uploads] = await Promise.all([
              api.getStats(farm.id_farm),
              api.getUploads({ farmId: farm.id_farm, limit: 1 })
            ]);
            return { 
              ...farm, 
              stats, 
              lastUpload: uploads.length > 0 ? uploads[0] : undefined 
            };
          } catch {
            return { ...farm, stats: undefined, lastUpload: undefined };
          }
        })
      );
      setFarms(farmsWithStats);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erro ao carregar fazendas");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFarms();
  }, []);

  const filteredFarms = farms.filter((farm) => {
    if (!search) return true;
    const s = search.toLowerCase();
    return (
      farm.nome_farm.toLowerCase().includes(s) ||
      farm.responsavel?.toLowerCase().includes(s) ||
      farm.email?.toLowerCase().includes(s) ||
      farm.cnpj?.toLowerCase().includes(s)
    );
  });

  const validateForm = () => {
    const e: Record<string, string> = {};
    if (!form.nome_farm.trim()) e.nome_farm = "Nome é obrigatório";
    setFormErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;
    setCreating(true);
    try {
      await api.createFarm({
        nome_farm: form.nome_farm,
        cnpj: form.cnpj || undefined,
        responsavel: form.responsavel || undefined,
        email: form.email || undefined,
      });
      setShowCreate(false);
      setForm({ nome_farm: "", cnpj: "", responsavel: "", email: "" });
      fetchFarms();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Erro ao criar fazenda";
      setFormErrors({ nome_farm: msg });
    } finally {
      setCreating(false);
    }
  };

  const startEdit = (farm: Farm) => {
    setEditingId(farm.id_farm);
    setEditName(farm.nome_farm);
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditName("");
  };

  const saveEdit = async () => {
    if (!editName.trim() || editingId === null) return;
    setSavingEdit(true);
    try {
      await api.updateFarm(editingId, { nome_farm: editName.trim() });
      setEditingId(null);
      setEditName("");
      fetchFarms();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Erro ao editar fazenda";
      setError(msg);
    } finally {
      setSavingEdit(false);
    }
  };

  const handleDelete = async (farmId: number) => {
    if (!confirm("Tem certeza que deseja excluir esta fazenda? Todos os animais, uploads e processamentos serão removidos.")) return;
    setDeletingId(farmId);
    try {
      await api.deleteFarm(farmId);
      fetchFarms();
      showToast("Fazenda excluída com sucesso", "success");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Erro ao excluir fazenda";
      showToast(msg, "error");
    } finally {
      setDeletingId(null);
    }
  };

  const handleFarmClick = (farmId: number) => {
    router.push(`/analytics?farm_id=${farmId}`);
  };

  const isAdmin = user?.role === "admin";

  const formatNumber = (num: number | null | undefined) => {
    if (num === null || num === undefined) return "—";
    return num.toLocaleString();
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white tracking-tight">
              Fazendas
            </h1>
            <p className="text-text-secondary text-sm mt-1">
              Gerencie as fazendas cadastradas na plataforma
            </p>
          </div>
          {isAdmin && (
            <GlowButton
              onClick={() => setShowCreate(true)}
              className="flex items-center gap-2"
            >
              <PlusIcon className="w-4 h-4" />
              Nova Fazenda
            </GlowButton>
          )}
        </div>

        <GlassCard className="p-4">
          <div className="relative max-w-md">
            <MagnifyingGlassIcon className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
            <input
              type="text"
              placeholder="Buscar fazendas..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-sm text-text-primary placeholder:text-text-muted focus:border-emerald-glow/30 focus:outline-none transition-colors"
            />
          </div>
        </GlassCard>

        {showCreate && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="w-full max-w-md"
            >
              <GlassCard glow="cyan" className="p-8">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-bold text-white">Nova Fazenda</h2>
                  <button
                    onClick={() => setShowCreate(false)}
                    className="p-1 rounded-lg text-text-muted hover:text-text-primary transition-colors"
                  >
                    <XMarkIcon className="w-5 h-5" />
                  </button>
                </div>

                <form onSubmit={handleCreate} className="space-y-4" noValidate>
                  <AnimatedInput
                    label="Nome da Fazenda"
                    placeholder="Ex: Fazenda Santa Maria"
                    icon={<BuildingOffice2Icon className="w-5 h-5" />}
                    value={form.nome_farm}
                    onChange={(e) => {
                      setForm((p) => ({ ...p, nome_farm: e.target.value }));
                      setFormErrors((p) => ({ ...p, nome_farm: "" }));
                    }}
                    error={formErrors.nome_farm}
                  />

                  <AnimatedInput
                    label="CNPJ"
                    placeholder="00.000.000/0000-00"
                    icon={<IdentificationIcon className="w-5 h-5" />}
                    value={form.cnpj}
                    onChange={(e) => setForm((p) => ({ ...p, cnpj: e.target.value }))}
                  />

                  <AnimatedInput
                    label="Responsável"
                    placeholder="Nome do responsável"
                    icon={<UserIcon className="w-5 h-5" />}
                    value={form.responsavel}
                    onChange={(e) =>
                      setForm((p) => ({ ...p, responsavel: e.target.value }))
                    }
                  />

                  <AnimatedInput
                    label="E-mail"
                    placeholder="contato@fazenda.com"
                    type="email"
                    icon={<EnvelopeIcon className="w-5 h-5" />}
                    value={form.email}
                    onChange={(e) => setForm((p) => ({ ...p, email: e.target.value }))}
                  />

                  <GlowButton
                    type="submit"
                    size="lg"
                    className="w-full"
                    loading={creating}
                  >
                    {creating ? "Criando..." : "Criar Fazenda"}
                  </GlowButton>
                </form>
              </GlassCard>
            </motion.div>
          </div>
        )}

        {error && (
          <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-rose-neon/[0.06] border border-rose-neon/20">
            <ExclamationTriangleIcon className="w-5 h-5 text-rose-neon-400 flex-shrink-0" />
            <span className="text-sm text-rose-neon-400">{error}</span>
          </div>
        )}

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-56 bg-white/[0.02] rounded-2xl animate-pulse" />
            ))}
          </div>
        ) : filteredFarms.length === 0 ? (
          <GlassCard className="p-12 text-center">
            <BuildingOffice2Icon className="w-12 h-12 text-text-muted mx-auto mb-4" />
            <p className="text-text-secondary text-sm">
              {search ? "Nenhuma fazenda encontrada" : "Nenhuma fazenda cadastrada"}
            </p>
            {isAdmin && !search && (
              <p className="text-text-muted text-xs mt-2">
                Clique em "Nova Fazenda" para começar
              </p>
            )}
          </GlassCard>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredFarms.map((farm, i) => (
              <motion.div
                key={farm.id_farm}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
              >
                <GlassCard
                  className="p-6 hover:border-cyan-glow/20 transition-colors cursor-pointer group"
                  onClick={() => handleFarmClick(farm.id_farm)}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="w-10 h-10 rounded-xl bg-cyan-glow/10 flex items-center justify-center">
                      <BuildingOffice2Icon className="w-5 h-5 text-cyan-glow-400" />
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="text-[10px] text-text-muted font-mono">
                        #{farm.id_farm}
                      </span>
                      {(isAdmin || user?.id_farm === farm.id_farm) && (
                        <>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              startEdit(farm);
                            }}
                            className="p-1 rounded-lg text-text-muted hover:text-cyan-glow-400 hover:bg-cyan-glow/10 opacity-0 group-hover:opacity-100 transition-all"
                          >
                            <PencilIcon className="w-3.5 h-3.5" />
                          </button>
                          {isAdmin && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDelete(farm.id_farm);
                              }}
                              disabled={deletingId === farm.id_farm}
                              className="p-1 rounded-lg text-text-muted hover:text-rose-neon-400 hover:bg-rose-neon/10 opacity-0 group-hover:opacity-100 transition-all disabled:opacity-50"
                            >
                              <TrashIcon className="w-3.5 h-3.5" />
                            </button>
                          )}
                        </>
                      )}
                    </div>
                  </div>

                  {editingId === farm.id_farm ? (
                    <div className="flex items-center gap-2 mb-3" onClick={(e) => e.stopPropagation()}>
                      <input
                        type="text"
                        value={editName}
                        onChange={(e) => setEditName(e.target.value)}
                        className="flex-1 px-3 py-2 rounded-xl bg-white/[0.05] border border-cyan-glow/30 text-white text-lg font-bold focus:outline-none focus:border-cyan-glow/50"
                        autoFocus
                      />
                      <button
                        onClick={saveEdit}
                        disabled={savingEdit || !editName.trim()}
                        className="p-2 rounded-xl bg-emerald-glow/20 text-emerald-glow-400 hover:bg-emerald-glow/30 disabled:opacity-50"
                      >
                        <CheckIcon className="w-5 h-5" />
                      </button>
                      <button
                        onClick={cancelEdit}
                        className="p-2 rounded-xl bg-rose-neon/10 text-rose-neon-400 hover:bg-rose-neon/20"
                      >
                        <XMarkIcon className="w-5 h-5" />
                      </button>
                    </div>
                  ) : (
                    <h3 className="text-lg font-bold text-white mb-2">
                      {farm.nome_farm}
                    </h3>
                  )}

                  <div className="space-y-1 mb-3">
                    {farm.responsavel && (
                      <div className="flex items-center gap-2 text-sm text-text-secondary">
                        <UserIcon className="w-3.5 h-3.5 text-text-muted" />
                        {farm.responsavel}
                      </div>
                    )}
                    {farm.email && (
                      <div className="flex items-center gap-2 text-sm text-text-secondary">
                        <EnvelopeIcon className="w-3.5 h-3.5 text-text-muted" />
                        {farm.email}
                      </div>
                    )}
                    {farm.cnpj && (
                      <div className="flex items-center gap-2 text-sm text-text-secondary font-mono">
                        <IdentificationIcon className="w-3.5 h-3.5 text-text-muted" />
                        {farm.cnpj}
                      </div>
                    )}
                  </div>

                  {farm.stats && (
                    <div className="pt-3 mt-3 border-t border-white/[0.06]">
                      <div className="grid grid-cols-2 gap-2">
                        <div className="flex items-center gap-1.5 text-xs">
                          <Squares2X2Icon className="w-3.5 h-3.5 text-cyan-glow-400" />
                          <span className="text-text-secondary">
                            {formatNumber(farm.stats.total_animals)} animais
                          </span>
                        </div>
                        {farm.lastUpload ? (
                          <div className="flex items-center gap-1.5 text-xs">
                            <ClockIcon className="w-3.5 h-3.5 text-emerald-glow-400" />
                            <span className="text-text-muted">
                              Upload: {new Date(farm.lastUpload.data_upload!).toLocaleDateString("pt-BR")}
                            </span>
                          </div>
                        ) : (
                          <div className="flex items-center gap-1.5 text-xs">
                            <ClockIcon className="w-3.5 h-3.5 text-text-muted" />
                            <span className="text-text-muted">Sem uploads</span>
                          </div>
                        )}
                        {farm.stats.avg_p210 && (
                          <div className="flex items-center gap-1.5 text-xs">
                            <span className="text-text-muted">P210:</span>
                            <span className="text-text-primary font-mono font-medium">
                              {farm.stats.avg_p210.toFixed(1)}
                            </span>
                          </div>
                        )}
                        {farm.stats.avg_p365 && (
                          <div className="flex items-center gap-1.5 text-xs">
                            <span className="text-text-muted">P365:</span>
                            <span className="text-text-primary font-mono font-medium">
                              {farm.stats.avg_p365.toFixed(1)}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {!farm.stats && (
                    <div className="pt-3 mt-3 border-t border-white/[0.06]">
                      <div className="flex items-center gap-1.5 text-xs text-text-muted">
                        <ClockIcon className="w-3.5 h-3.5" />
                        <span>Sem dados carregados</span>
                      </div>
                    </div>
                  )}

                  {farm.created_at && (
                    <p className="text-[10px] text-text-muted mt-3">
                      Criada em{" "}
                      {new Date(farm.created_at).toLocaleDateString("pt-BR")}
                    </p>
                  )}
                </GlassCard>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}