"use client";

import { useState, useEffect } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { GlassCard } from "@/components/ui/glass-card";
import { GlowButton } from "@/components/ui/glow-button";
import { AnimatedInput } from "@/components/ui/animated-input";
import { motion, AnimatePresence } from "framer-motion";
import {
  UserIcon,
  ShieldCheckIcon,
  BellAlertIcon,
  KeyIcon,
  AdjustmentsHorizontalIcon,
  LinkIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  GlobeAltIcon,
  SignalIcon,
  TrashIcon,
  LockClosedIcon,
  PlusIcon,
  XMarkIcon,
} from "@heroicons/react/24/outline";
import { useAuth } from "@/lib/auth-context";
import { api, ColumnMapping } from "@/lib/api";

const NAV_ITEMS = [
  { id: "profile", label: "Perfil", icon: UserIcon },
  { id: "security", label: "Segurança", icon: ShieldCheckIcon },
  { id: "mappings", label: "Mapeamentos", icon: AdjustmentsHorizontalIcon },
  { id: "integrations", label: "Integrações", icon: LinkIcon },
  { id: "notifications", label: "Notificações", icon: BellAlertIcon },
];

const INTEGRATIONS = [
  {
    id: "ancp",
    name: "ANCP",
    description: "Associação Nacional de Criadores e Pesquisadores",
    status: "connected",
    color: "cyan",
    lastSync: "2 min atrás",
    apiKey: "ancp_live_****_x7k2",
  },
  {
    id: "pmgz",
    name: "PMGZ",
    description: "Programa de Melhoramento Genético Zebuíno",
    status: "connected",
    color: "emerald",
    lastSync: "15 min atrás",
    apiKey: "pmgz_prod_****_m9q1",
  },
  {
    id: "geneplus",
    name: "Geneplus",
    description: "Programa Embrapa Geneplus",
    status: "disconnected",
    color: "rose",
    lastSync: "Nunca",
    apiKey: "",
  },
];

export default function SettingsPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState("profile");

  return (
    <DashboardLayout>
      <div className="space-y-8 animate-in fade-in duration-700">
        <section className="space-y-2">
          <h1 className="text-4xl font-bold text-white tracking-tight">
            Configurações
          </h1>
          <p className="text-text-secondary text-lg">
            Gerencie seu perfil, integrações e parâmetros do sistema.
          </p>
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Settings Nav */}
          <aside className="lg:col-span-1 space-y-1">
            {NAV_ITEMS.map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 text-left ${
                  activeTab === item.id
                    ? "bg-cyan-glow/[0.06] text-cyan-glow-400 border border-cyan-glow/20 glow-cyan"
                    : "text-text-muted hover:text-text-primary hover:bg-white/[0.03] border border-transparent"
                }`}
              >
                <item.icon className="w-5 h-5 flex-shrink-0" />
                <span className="text-sm font-medium">{item.label}</span>
              </button>
            ))}
          </aside>

          {/* Content */}
          <div className="lg:col-span-3">
            <AnimatePresence mode="wait">
              {activeTab === "profile" && <ProfileTab key="profile" />}
              {activeTab === "security" && <SecurityTab key="security" />}
              {activeTab === "mappings" && <MappingsTab key="mappings" />}
              {activeTab === "integrations" && <IntegrationsTab key="integrations" />}
              {activeTab === "notifications" && <NotificationsTab key="notifications" />}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

// ============================================
// Profile Tab
// ============================================
function ProfileTab() {
  const { user } = useAuth();
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
    >
      <GlassCard glow="cyan" className="p-8 space-y-8">
        <div className="border-b border-white/[0.06] pb-6">
          <h2 className="text-2xl font-bold text-white">Informações do Perfil</h2>
          <p className="text-sm text-text-muted">Seus dados pessoais.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="text-[10px] text-text-muted uppercase tracking-wider mb-1 block">Nome</label>
            <div className="px-4 py-3 rounded-xl bg-white/[0.03] border border-white/[0.06] text-sm text-text-primary">
              {user?.nome || "—"}
            </div>
          </div>
          <div>
            <label className="text-[10px] text-text-muted uppercase tracking-wider mb-1 block">E-mail</label>
            <div className="px-4 py-3 rounded-xl bg-white/[0.03] border border-white/[0.06] text-sm text-text-primary">
              {user?.email || "—"}
            </div>
          </div>
          <div>
            <label className="text-[10px] text-text-muted uppercase tracking-wider mb-1 block">Role</label>
            <div className="px-4 py-3 rounded-xl bg-white/[0.03] border border-white/[0.06] text-sm">
              <span className={`px-2 py-0.5 rounded-full text-xs ${
                user?.role === "admin" ? "bg-cyan-glow/10 text-cyan-glow-400" : "bg-violet-glow/10 text-violet-glow-400"
              }`}>
                {user?.role?.toUpperCase() || "—"}
              </span>
            </div>
          </div>
          <div>
            <label className="text-[10px] text-text-muted uppercase tracking-wider mb-1 block">Fazenda ID</label>
            <div className="px-4 py-3 rounded-xl bg-white/[0.03] border border-white/[0.06] text-sm text-text-primary">
              {user?.id_farm || "Não vinculada"}
            </div>
          </div>
        </div>
      </GlassCard>
    </motion.div>
  );
}

// ============================================
// Security Tab — Change Password
// ============================================
function SecurityTab() {
  const [form, setForm] = useState({ current: "", newPw: "", confirm: "" });
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess(false);

    if (form.newPw.length < 6) {
      setError("Nova senha deve ter pelo menos 6 caracteres");
      return;
    }
    if (form.newPw !== form.confirm) {
      setError("Senhas não coincidem");
      return;
    }

    setLoading(true);
    try {
      await api.changePassword(form.current, form.newPw);
      setSuccess(true);
      setForm({ current: "", newPw: "", confirm: "" });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erro ao alterar senha");
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
    >
      <GlassCard glow="cyan" className="p-8 space-y-8">
        <div className="border-b border-white/[0.06] pb-6">
          <h2 className="text-2xl font-bold text-white flex items-center gap-3">
            <ShieldCheckIcon className="w-6 h-6 text-cyan-glow-400" />
            Segurança
          </h2>
          <p className="text-sm text-text-muted">Altere sua senha de acesso.</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5 max-w-md">
          <AnimatedInput
            label="Senha Atual"
            type="password"
            icon={<LockClosedIcon className="w-5 h-5" />}
            value={form.current}
            onChange={(e) => setForm((p) => ({ ...p, current: e.target.value }))}
          />
          <AnimatedInput
            label="Nova Senha"
            type="password"
            placeholder="Mínimo 6 caracteres"
            icon={<KeyIcon className="w-5 h-5" />}
            value={form.newPw}
            onChange={(e) => setForm((p) => ({ ...p, newPw: e.target.value }))}
          />
          <AnimatedInput
            label="Confirmar Nova Senha"
            type="password"
            icon={<KeyIcon className="w-5 h-5" />}
            value={form.confirm}
            onChange={(e) => setForm((p) => ({ ...p, confirm: e.target.value }))}
          />

          {error && (
            <div className="flex items-center gap-2 text-sm text-rose-neon-400">
              <ExclamationTriangleIcon className="w-4 h-4" />
              {error}
            </div>
          )}
          {success && (
            <div className="flex items-center gap-2 text-sm text-emerald-glow-400">
              <CheckCircleIcon className="w-4 h-4" />
              Senha alterada com sucesso!
            </div>
          )}

          <GlowButton type="submit" loading={loading}>
            Alterar Senha
          </GlowButton>
        </form>
      </GlassCard>
    </motion.div>
  );
}

// ============================================
// Mappings Tab
// ============================================
function MappingsTab() {
  const [mappings, setMappings] = useState<ColumnMapping[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({
    source_system: "ANCP",
    source_column: "",
    target_column: "",
    data_type: "string",
    is_required: false,
  });
  const [error, setError] = useState("");

  const fetchMappings = async () => {
    setLoading(true);
    try {
      const data = await api.getMappings(filter || undefined);
      setMappings(data);
    } catch {
      setError("Erro ao carregar mapeamentos");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMappings();
  }, [filter]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.source_column.trim() || !form.target_column.trim()) {
      setError("Colunas são obrigatórias");
      return;
    }
    setCreating(true);
    setError("");
    try {
      await api.createMapping(form);
      setShowCreate(false);
      setForm({ source_system: "ANCP", source_column: "", target_column: "", data_type: "string", is_required: false });
      fetchMappings();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erro ao criar mapeamento");
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await api.deleteMapping(id);
      fetchMappings();
    } catch {
      setError("Erro ao deletar mapeamento");
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="space-y-6"
    >
      <GlassCard glow="cyan" className="p-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-white flex items-center gap-3">
              <AdjustmentsHorizontalIcon className="w-6 h-6 text-cyan-glow-400" />
              Mapeamentos de Colunas
            </h2>
            <p className="text-sm text-text-muted">
              Configure como as colunas dos arquivos são mapeadas para o modelo padrão.
            </p>
          </div>
          <GlowButton onClick={() => setShowCreate(true)} size="sm">
            <PlusIcon className="w-4 h-4 mr-1" />
            Novo
          </GlowButton>
        </div>

        {/* Filter */}
        <div className="flex gap-3 mb-4">
          {["", "ANCP", "PMGZ", "Geneplus"].map((s) => (
            <button
              key={s}
              onClick={() => setFilter(s)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                filter === s
                  ? "bg-cyan-glow/10 text-cyan-glow-400 border border-cyan-glow/20"
                  : "text-text-muted hover:text-text-primary border border-white/[0.06]"
              }`}
            >
              {s || "Todos"}
            </button>
          ))}
        </div>

        {/* Create Form */}
        {showCreate && (
          <div className="mb-6 p-4 rounded-xl bg-white/[0.02] border border-white/[0.06]">
            <form onSubmit={handleCreate} className="grid grid-cols-2 md:grid-cols-5 gap-3 items-end">
              <div>
                <label className="text-[10px] text-text-muted uppercase tracking-wider mb-1 block">Sistema</label>
                <select
                  value={form.source_system}
                  onChange={(e) => setForm((p) => ({ ...p, source_system: e.target.value }))}
                  className="w-full px-3 py-2 rounded-xl bg-white/[0.03] border border-white/[0.06] text-sm text-text-primary appearance-none"
                >
                  <option value="ANCP">ANCP</option>
                  <option value="PMGZ">PMGZ</option>
                  <option value="Geneplus">Geneplus</option>
                </select>
              </div>
              <div>
                <label className="text-[10px] text-text-muted uppercase tracking-wider mb-1 block">Coluna Origem</label>
                <input
                  type="text"
                  placeholder="Ex: RGN"
                  value={form.source_column}
                  onChange={(e) => setForm((p) => ({ ...p, source_column: e.target.value }))}
                  className="w-full px-3 py-2 rounded-xl bg-white/[0.03] border border-white/[0.06] text-sm text-text-primary"
                />
              </div>
              <div>
                <label className="text-[10px] text-text-muted uppercase tracking-wider mb-1 block">Coluna Destino</label>
                <input
                  type="text"
                  placeholder="Ex: rgn_animal"
                  value={form.target_column}
                  onChange={(e) => setForm((p) => ({ ...p, target_column: e.target.value }))}
                  className="w-full px-3 py-2 rounded-xl bg-white/[0.03] border border-white/[0.06] text-sm text-text-primary"
                />
              </div>
              <div>
                <label className="text-[10px] text-text-muted uppercase tracking-wider mb-1 block">Tipo</label>
                <select
                  value={form.data_type}
                  onChange={(e) => setForm((p) => ({ ...p, data_type: e.target.value }))}
                  className="w-full px-3 py-2 rounded-xl bg-white/[0.03] border border-white/[0.06] text-sm text-text-primary appearance-none"
                >
                  <option value="string">String</option>
                  <option value="float">Float</option>
                  <option value="date">Date</option>
                </select>
              </div>
              <div className="flex gap-2">
                <button
                  type="submit"
                  disabled={creating}
                  className="px-4 py-2 rounded-xl bg-cyan-glow/10 border border-cyan-glow/20 text-cyan-glow-400 text-sm font-medium hover:bg-cyan-glow/20 transition-all"
                >
                  {creating ? "..." : "Criar"}
                </button>
                <button
                  type="button"
                  onClick={() => setShowCreate(false)}
                  className="p-2 rounded-xl border border-white/[0.06] text-text-muted hover:text-text-primary transition-all"
                >
                  <XMarkIcon className="w-4 h-4" />
                </button>
              </div>
            </form>
            {error && <p className="text-xs text-rose-neon-400 mt-2">{error}</p>}
          </div>
        )}

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/[0.04]">
                <th className="text-left px-3 py-2 text-[10px] text-text-muted uppercase tracking-wider">Sistema</th>
                <th className="text-left px-3 py-2 text-[10px] text-text-muted uppercase tracking-wider">Coluna Origem</th>
                <th className="text-left px-3 py-2 text-[10px] text-text-muted uppercase tracking-wider">Coluna Destino</th>
                <th className="text-left px-3 py-2 text-[10px] text-text-muted uppercase tracking-wider">Tipo</th>
                <th className="text-left px-3 py-2 text-[10px] text-text-muted uppercase tracking-wider">Obrigatório</th>
                <th className="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i} className="border-b border-white/[0.02]">
                    {Array.from({ length: 6 }).map((_, j) => (
                      <td key={j} className="px-3 py-2">
                        <div className="h-4 bg-white/[0.04] rounded animate-pulse" />
                      </td>
                    ))}
                  </tr>
                ))
              ) : mappings.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-3 py-8 text-center text-text-muted text-sm">
                    Nenhum mapeamento encontrado
                  </td>
                </tr>
              ) : (
                mappings.map((m) => (
                  <tr key={m.id} className="border-b border-white/[0.02] hover:bg-white/[0.02] transition-colors">
                    <td className="px-3 py-2">
                      <span className="text-xs px-2 py-0.5 rounded-full bg-white/[0.04] text-text-muted">{m.source_system}</span>
                    </td>
                    <td className="px-3 py-2 text-sm text-cyan-glow-400 font-mono">{m.source_column}</td>
                    <td className="px-3 py-2 text-sm text-text-primary font-mono">{m.target_column}</td>
                    <td className="px-3 py-2 text-xs text-text-muted">{m.data_type}</td>
                    <td className="px-3 py-2">
                      {m.is_required && <span className="text-[10px] text-rose-neon-400">Sim</span>}
                    </td>
                    <td className="px-3 py-2">
                      <button
                        onClick={() => handleDelete(m.id)}
                        className="p-1 rounded text-text-muted hover:text-rose-neon-400 transition-colors"
                      >
                        <TrashIcon className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </GlassCard>
    </motion.div>
  );
}

// ============================================
// Integrations Tab
// ============================================
function IntegrationsTab() {
  return (
    <motion.div
      key="integrations"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="space-y-6"
    >
      <GlassCard glow="cyan" className="p-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-white flex items-center gap-3">
              <GlobeAltIcon className="w-6 h-6 text-cyan-glow-400" />
              Integrações de Plataformas
            </h2>
            <p className="text-sm text-text-muted mt-1">
              Conecte suas chaves de API das plataformas genéticas.
            </p>
          </div>
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-glow/[0.06] border border-emerald-glow/20">
            <SignalIcon className="w-4 h-4 text-emerald-glow-400" />
            <span className="text-xs text-emerald-glow-400 font-mono">2/3 CONECTADOS</span>
          </div>
        </div>

        <div className="space-y-4">
          {INTEGRATIONS.map((integration) => (
            <div
              key={integration.id}
              className={`relative p-5 rounded-xl border transition-all duration-300 ${
                integration.status === "connected"
                  ? "bg-white/[0.02] border-white/[0.06] hover:border-white/[0.1]"
                  : "bg-rose-neon/[0.02] border-rose-neon/10 hover:border-rose-neon/20"
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div
                    className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                      integration.status === "connected"
                        ? "bg-cyan-glow/[0.08] border border-cyan-glow/20"
                        : "bg-rose-neon/[0.08] border border-rose-neon/20"
                    }`}
                  >
                    <span className="text-lg font-bold text-white">{integration.name.charAt(0)}</span>
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-base font-bold text-white">{integration.name}</h3>
                      {integration.status === "connected" ? (
                        <span className="flex items-center gap-1 text-[10px] text-emerald-glow-400 bg-emerald-glow/[0.06] px-2 py-0.5 rounded-full border border-emerald-glow/20 font-mono">
                          <CheckCircleIcon className="w-3 h-3" /> ONLINE
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-[10px] text-rose-neon-400 bg-rose-neon/[0.06] px-2 py-0.5 rounded-full border border-rose-neon/20 font-mono">
                          <ExclamationTriangleIcon className="w-3 h-3" /> OFFLINE
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-text-muted">{integration.description}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {integration.status === "connected" ? (
                    <>
                      <div className="text-right hidden sm:block">
                        <p className="text-xs text-text-muted">Última sync</p>
                        <p className="text-xs text-text-secondary font-mono">{integration.lastSync}</p>
                      </div>
                      <GlowButton variant="ghost" size="sm">
                        <KeyIcon className="w-4 h-4 mr-1.5" /> Rotacionar
                      </GlowButton>
                    </>
                  ) : (
                    <GlowButton size="sm">
                      <LinkIcon className="w-4 h-4 mr-1.5" /> Conectar
                    </GlowButton>
                  )}
                </div>
              </div>
              {integration.status === "connected" && integration.apiKey && (
                <div className="mt-4 pt-4 border-t border-white/[0.04]">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-text-muted">API Key:</span>
                      <code className="text-xs text-cyan-glow-400 font-mono bg-white/[0.02] px-2 py-1 rounded">{integration.apiKey}</code>
                    </div>
                    <button className="text-xs text-text-muted hover:text-rose-neon-400 transition-colors flex items-center gap-1">
                      <TrashIcon className="w-3 h-3" /> Desconectar
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </GlassCard>
    </motion.div>
  );
}

// ============================================
// Notifications Tab
// ============================================
function NotificationsTab() {
  const [settings, setSettings] = useState({
    email_uploads: true,
    email_errors: true,
    email_weekly_report: false,
    push_uploads: false,
    push_errors: true,
  });

  const toggle = (key: keyof typeof settings) => {
    setSettings((p) => ({ ...p, [key]: !p[key] }));
  };

  const items = [
    { key: "email_uploads" as const, label: "E-mail: Uploads concluídos", desc: "Receba um e-mail quando um upload for processado com sucesso." },
    { key: "email_errors" as const, label: "E-mail: Erros de processamento", desc: "Receba um e-mail quando houver falhas no processamento." },
    { key: "email_weekly_report" as const, label: "E-mail: Relatório semanal", desc: "Resumo semanal com estatísticas de uso e KPIs." },
    { key: "push_uploads" as const, label: "Push: Uploads concluídos", desc: "Notificação no navegador quando uploads terminarem." },
    { key: "push_errors" as const, label: "Push: Erros críticos", desc: "Notificação imediata para erros que precisam de atenção." },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
    >
      <GlassCard glow="cyan" className="p-8 space-y-6">
        <div className="border-b border-white/[0.06] pb-6">
          <h2 className="text-2xl font-bold text-white flex items-center gap-3">
            <BellAlertIcon className="w-6 h-6 text-cyan-glow-400" />
            Notificações
          </h2>
          <p className="text-sm text-text-muted">Configure como deseja ser notificado.</p>
        </div>

        <div className="space-y-4">
          {items.map((item) => (
            <div key={item.key} className="flex items-center justify-between py-3 border-b border-white/[0.04] last:border-0">
              <div>
                <p className="text-sm text-text-primary font-medium">{item.label}</p>
                <p className="text-xs text-text-muted mt-0.5">{item.desc}</p>
              </div>
              <button
                onClick={() => toggle(item.key)}
                className={`relative w-11 h-6 rounded-full transition-colors ${
                  settings[item.key] ? "bg-cyan-glow" : "bg-white/[0.1]"
                }`}
              >
                <div
                  className={`absolute top-0.5 w-5 h-5 rounded-full bg-white transition-transform ${
                    settings[item.key] ? "translate-x-[22px]" : "translate-x-0.5"
                  }`}
                />
              </button>
            </div>
          ))}
        </div>
      </GlassCard>
    </motion.div>
  );
}
