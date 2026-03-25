"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  PlusIcon,
  BuildingOffice2Icon,
  UserIcon,
  EnvelopeIcon,
  IdentificationIcon,
  ExclamationTriangleIcon,
  XMarkIcon,
} from "@heroicons/react/24/outline";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { GlassCard } from "@/components/ui/glass-card";
import { GlowButton } from "@/components/ui/glow-button";
import { AnimatedInput } from "@/components/ui/animated-input";
import { api, Farm } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export default function FarmsPage() {
  const { user } = useAuth();
  const [farms, setFarms] = useState<Farm[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({
    nome_farm: "",
    cnpj: "",
    responsavel: "",
    email: "",
  });
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  const fetchFarms = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getFarms();
      setFarms(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erro ao carregar fazendas");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFarms();
  }, []);

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

  const isAdmin = user?.role === "admin";

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
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

        {/* Create Modal */}
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

        {/* Error */}
        {error && (
          <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-rose-neon/[0.06] border border-rose-neon/20">
            <ExclamationTriangleIcon className="w-5 h-5 text-rose-neon-400 flex-shrink-0" />
            <span className="text-sm text-rose-neon-400">{error}</span>
          </div>
        )}

        {/* Farms Grid */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-40 bg-white/[0.02] rounded-2xl animate-pulse" />
            ))}
          </div>
        ) : farms.length === 0 ? (
          <GlassCard className="p-12 text-center">
            <BuildingOffice2Icon className="w-12 h-12 text-text-muted mx-auto mb-4" />
            <p className="text-text-secondary text-sm">
              Nenhuma fazenda cadastrada
            </p>
            {isAdmin && (
              <p className="text-text-muted text-xs mt-2">
                Clique em &quot;Nova Fazenda&quot; para começar
              </p>
            )}
          </GlassCard>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {farms.map((farm, i) => (
              <motion.div
                key={farm.id_farm}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
              >
                <GlassCard className="p-6 hover:border-cyan-glow/20 transition-colors">
                  <div className="flex items-start justify-between mb-4">
                    <div className="w-10 h-10 rounded-xl bg-cyan-glow/10 flex items-center justify-center">
                      <BuildingOffice2Icon className="w-5 h-5 text-cyan-glow-400" />
                    </div>
                    <span className="text-[10px] text-text-muted font-mono">
                      #{farm.id_farm}
                    </span>
                  </div>

                  <h3 className="text-lg font-bold text-white mb-2">
                    {farm.nome_farm}
                  </h3>

                  <div className="space-y-1.5">
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

                  {farm.created_at && (
                    <p className="text-[10px] text-text-muted mt-4">
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
