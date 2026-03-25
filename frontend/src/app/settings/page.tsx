"use client";

import { useState } from "react";
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
} from "@heroicons/react/24/outline";

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
  const [activeTab, setActiveTab] = useState("integrations");

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
              {activeTab === "integrations" && (
                <motion.div
                  key="integrations"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="space-y-6"
                >
                  {/* Integrations Header */}
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
                        <span className="text-xs text-emerald-glow-400 font-mono">
                          2/3 CONECTADOS
                        </span>
                      </div>
                    </div>

                    {/* Integration Cards */}
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
                          {/* HUD corner indicators */}
                          <div className="absolute top-0 left-0 w-4 h-4 border-t border-l rounded-tl-xl border-cyan-glow/30" />
                          <div className="absolute top-0 right-0 w-4 h-4 border-t border-r rounded-tr-xl border-cyan-glow/30" />
                          <div className="absolute bottom-0 left-0 w-4 h-4 border-b border-l rounded-bl-xl border-cyan-glow/30" />
                          <div className="absolute bottom-0 right-0 w-4 h-4 border-b border-r rounded-br-xl border-cyan-glow/30" />

                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                              <div
                                className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                                  integration.status === "connected"
                                    ? "bg-cyan-glow/[0.08] border border-cyan-glow/20"
                                    : "bg-rose-neon/[0.08] border border-rose-neon/20"
                                }`}
                              >
                                <span className="text-lg font-bold text-white">
                                  {integration.name.charAt(0)}
                                </span>
                              </div>

                              <div>
                                <div className="flex items-center gap-2">
                                  <h3 className="text-base font-bold text-white">
                                    {integration.name}
                                  </h3>
                                  {integration.status === "connected" ? (
                                    <span className="flex items-center gap-1 text-[10px] text-emerald-glow-400 bg-emerald-glow/[0.06] px-2 py-0.5 rounded-full border border-emerald-glow/20 font-mono">
                                      <CheckCircleIcon className="w-3 h-3" />
                                      ONLINE
                                    </span>
                                  ) : (
                                    <span className="flex items-center gap-1 text-[10px] text-rose-neon-400 bg-rose-neon/[0.06] px-2 py-0.5 rounded-full border border-rose-neon/20 font-mono">
                                      <ExclamationTriangleIcon className="w-3 h-3" />
                                      OFFLINE
                                    </span>
                                  )}
                                </div>
                                <p className="text-xs text-text-muted">
                                  {integration.description}
                                </p>
                              </div>
                            </div>

                            <div className="flex items-center gap-3">
                              {integration.status === "connected" ? (
                                <>
                                  <div className="text-right hidden sm:block">
                                    <p className="text-xs text-text-muted">
                                      Última sync
                                    </p>
                                    <p className="text-xs text-text-secondary font-mono">
                                      {integration.lastSync}
                                    </p>
                                  </div>
                                  <GlowButton variant="ghost" size="sm">
                                    <KeyIcon className="w-4 h-4 mr-1.5" />
                                    Rotacionar
                                  </GlowButton>
                                </>
                              ) : (
                                <GlowButton size="sm">
                                  <LinkIcon className="w-4 h-4 mr-1.5" />
                                  Conectar
                                </GlowButton>
                              )}
                            </div>
                          </div>

                          {/* API Key display (connected only) */}
                          {integration.status === "connected" && (
                            <div className="mt-4 pt-4 border-t border-white/[0.04]">
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                  <span className="text-xs text-text-muted">
                                    API Key:
                                  </span>
                                  <code className="text-xs text-cyan-glow-400 font-mono bg-white/[0.02] px-2 py-1 rounded">
                                    {integration.apiKey}
                                  </code>
                                </div>
                                <button className="text-xs text-text-muted hover:text-rose-neon-400 transition-colors flex items-center gap-1">
                                  <TrashIcon className="w-3 h-3" />
                                  Desconectar
                                </button>
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </GlassCard>
                </motion.div>
              )}

              {activeTab === "profile" && (
                <motion.div
                  key="profile"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                >
                  <GlassCard glow="cyan" className="p-8 space-y-8">
                    <div className="border-b border-white/[0.06] pb-6">
                      <h2 className="text-2xl font-bold text-white">
                        Informações do Perfil
                      </h2>
                      <p className="text-sm text-text-muted">
                        Atualize seus dados pessoais.
                      </p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <AnimatedInput
                        label="Nome"
                        defaultValue="Administrador"
                        icon={<UserIcon className="w-5 h-5" />}
                      />
                      <AnimatedInput
                        label="E-mail"
                        defaultValue="admin@geneticasolutions.com"
                        type="email"
                        icon={<UserIcon className="w-5 h-5" />}
                      />
                      <AnimatedInput
                        label="Organização"
                        defaultValue="Genética Solutions Ltda."
                      />
                      <AnimatedInput
                        label="Cargo"
                        defaultValue="Diretor Técnico"
                      />
                    </div>

                    <div className="pt-4 flex gap-4">
                      <GlowButton>Salvar Alterações</GlowButton>
                      <GlowButton variant="ghost">Cancelar</GlowButton>
                    </div>
                  </GlassCard>
                </motion.div>
              )}

              {activeTab !== "integrations" && activeTab !== "profile" && (
                <motion.div
                  key={activeTab}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                >
                  <GlassCard glow="cyan" className="p-12 text-center">
                    <p className="text-text-muted text-lg">
                      Seção "{NAV_ITEMS.find((i) => i.id === activeTab)?.label}" em desenvolvimento.
                    </p>
                    <p className="text-text-muted text-sm mt-2">
                      Disponível na próxima sprint.
                    </p>
                  </GlassCard>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
