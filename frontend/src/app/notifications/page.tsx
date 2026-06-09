"use client";

import { useState, useEffect } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { GlassCard } from "@/components/ui/glass-card";
import { GlowButton } from "@/components/ui/glow-button";
import { useToast } from "@/components/ui/Toast";
import { useConfirm } from "@/components/ui/ConfirmDialog";
import { motion, AnimatePresence } from "framer-motion";
import { api, Notification } from "@/lib/api";
import {
  BellIcon,
  CheckIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  TrashIcon,
  MagnifyingGlassIcon,
  ArrowRightIcon,
} from "@heroicons/react/24/outline";

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [activeTab, setActiveTab] = useState<"all" | "unread" | "read">("all");
  const { showToast } = useToast();
  const { confirm, dialog } = useConfirm();

  useEffect(() => {
    loadNotifications();
  }, []);

  const loadNotifications = async () => {
    setLoading(true);
    try {
      const data = await api.getNotifications(false);
      setNotifications(data);
    } catch (err) {
      showToast("Erro ao carregar notificações", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAsRead = async (id: number) => {
    try {
      await api.markAsRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
      showToast("Notificação marcada como lida", "success");
    } catch {
      showToast("Erro ao marcar notificação", "error");
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await api.markAllAsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      showToast("Todas marcadas como lidas", "success");
    } catch {
      showToast("Erro ao marcar notificações", "error");
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await api.deleteNotification(id);
      setNotifications((prev) => prev.filter((n) => n.id !== id));
      showToast("Notificação excluída", "success");
    } catch {
      showToast("Erro ao excluir notificação", "error");
    }
  };

  const handleClearRead = async () => {
    const confirmed = await confirm({
      title: "Limpar notificações lidas",
      message: "Tem certeza que deseja apagar todas as notificações lidas? Esta ação não pode ser desfeita.",
      type: "danger",
    });

    if (!confirmed) return;

    try {
      await api.clearReadNotifications();
      setNotifications((prev) => prev.filter((n) => !n.is_read));
      showToast("Notificações lidas limpas com sucesso", "success");
    } catch {
      showToast("Erro ao limpar notificações", "error");
    }
  };

  const formatTime = (dateStr: string | null) => {
    if (!dateStr) return "";
    const cleanDateStr = dateStr.includes("Z") || dateStr.includes("+") || (dateStr.includes("-") && dateStr.lastIndexOf("-") > 7)
      ? dateStr
      : `${dateStr}Z`;
    const date = new Date(cleanDateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    
    const diffMins = Math.floor(diffMs / 60000);
    if (diffMins < 1) return "agora";
    if (diffMins < 60) return `${diffMins}m atrás`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h atrás`;
    
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays < 7) return `${diffDays}d atrás`;
    
    return date.toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getIcon = (type: string) => {
    switch (type) {
      case "success":
        return <CheckCircleIcon className="w-5 h-5 text-emerald-400" />;
      case "error":
        return <ExclamationTriangleIcon className="w-5 h-5 text-rose-500" />;
      case "warning":
        return <ExclamationTriangleIcon className="w-5 h-5 text-amber-500" />;
      default:
        return <InformationCircleIcon className="w-5 h-5 text-cyan-400" />;
    }
  };

  const getCardStyles = (type: string, isRead: boolean) => {
    const base = "p-5 border hover:border-white/[0.1] transition-all duration-300 relative overflow-hidden";
    if (!isRead) {
      switch (type) {
        case "success":
          return `${base} border-emerald-glow/20 bg-emerald-glow/[0.02] shadow-[inset_0_0_15px_rgba(16,185,129,0.02)]`;
        case "error":
          return `${base} border-rose-neon/20 bg-rose-neon/[0.02] shadow-[inset_0_0_15px_rgba(244,63,94,0.02)]`;
        case "warning":
          return `${base} border-amber-500/20 bg-amber-500/[0.02] shadow-[inset_0_0_15px_rgba(245,158,11,0.02)]`;
        default:
          return `${base} border-cyan-glow/20 bg-cyan-glow/[0.02] shadow-[inset_0_0_15px_rgba(6,182,212,0.02)]`;
      }
    }
    return `${base} border-white/[0.06] bg-white/[0.01] opacity-75`;
  };

  const filtered = notifications.filter((n) => {
    // Tab filter
    if (activeTab === "unread" && n.is_read) return false;
    if (activeTab === "read" && !n.is_read) return false;
    
    // Search filter
    if (search.trim()) {
      const query = search.toLowerCase();
      return (
        n.title.toLowerCase().includes(query) ||
        n.message.toLowerCase().includes(query)
      );
    }
    return true;
  });

  const unreadExist = notifications.some((n) => !n.is_read);
  const readExist = notifications.some((n) => n.is_read);

  return (
    <DashboardLayout>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-8 max-w-5xl mx-auto"
      >
        {/* Header */}
        <section className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-4xl font-bold text-white tracking-tight">
              Central de Notificações
            </h1>
            <p className="text-text-secondary mt-1">
              Acompanhe alertas, logs de processamento e atualizações de sistema.
            </p>
          </div>
          <div className="flex gap-2">
            {unreadExist && (
              <GlowButton variant="ghost" size="sm" onClick={handleMarkAllRead}>
                <CheckIcon className="w-4 h-4" />
                Marcar todas como lidas
              </GlowButton>
            )}
            {readExist && (
              <GlowButton
                variant="ghost"
                size="sm"
                onClick={handleClearRead}
                className="text-rose-neon-400 hover:text-rose-neon"
              >
                <TrashIcon className="w-4 h-4" />
                Limpar lidas
              </GlowButton>
            )}
          </div>
        </section>

        {/* Filters and Search */}
        <GlassCard glow="cyan" className="p-6">
          <div className="flex flex-col md:flex-row items-center gap-4 justify-between">
            {/* Tabs */}
            <div className="flex gap-2 w-full md:w-auto">
              {(["all", "unread", "read"] as const).map((tab) => {
                const labels = { all: "Todas", unread: "Não lidas", read: "Lidas" };
                const count =
                  tab === "all"
                    ? notifications.length
                    : tab === "unread"
                    ? notifications.filter((n) => !n.is_read).length
                    : notifications.filter((n) => n.is_read).length;

                return (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`px-4 py-2 rounded-xl text-sm font-medium transition-all flex items-center gap-2 border ${
                      activeTab === tab
                        ? "bg-cyan-glow/10 text-cyan-glow-400 border-cyan-glow/20 glow-cyan"
                        : "text-text-muted hover:text-text-primary hover:bg-white/[0.02] border-transparent"
                    }`}
                  >
                    <span>{labels[tab]}</span>
                    <span className={`text-[11px] px-1.5 py-0.5 rounded-full ${
                      activeTab === tab ? "bg-cyan-glow/20 text-cyan-glow-300" : "bg-white/5 text-text-muted"
                    }`}>
                      {count}
                    </span>
                  </button>
                );
              })}
            </div>

            {/* Search Input */}
            <div className="relative w-full md:w-80 group">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted group-focus-within:text-cyan-glow transition-colors" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Buscar notificações..."
                className="w-full bg-white/5 border border-white/10 rounded-xl py-2 pl-10 pr-4 text-sm text-text-primary placeholder:text-text-muted outline-none focus:border-cyan-glow/40 focus:ring-2 focus:ring-cyan-glow/10 transition-all"
              />
            </div>
          </div>
        </GlassCard>

        {/* Notifications list */}
        <div className="space-y-4">
          {loading ? (
            <GlassCard className="p-12 text-center">
              <div className="w-8 h-8 border-2 border-cyan-glow border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <p className="text-text-secondary">Carregando notificações...</p>
            </GlassCard>
          ) : filtered.length === 0 ? (
            <GlassCard className="p-12 text-center">
              <BellIcon className="w-12 h-12 text-text-muted mx-auto mb-4 opacity-50" />
              <p className="text-text-primary font-medium mb-1">Nenhuma notificação</p>
              <p className="text-text-secondary text-sm">
                {search.trim()
                  ? "Nenhuma correspondência encontrada para a busca."
                  : activeTab === "unread"
                  ? "Excelente! Você não tem nenhuma notificação não lida."
                  : "Nenhuma notificação nesta categoria."}
              </p>
            </GlassCard>
          ) : (
            <div className="flex flex-col gap-3">
              <AnimatePresence initial={false}>
                {filtered.map((notif) => (
                  <motion.div
                    key={notif.id}
                    initial={{ opacity: 0, y: 15 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, x: 50 }}
                    layout
                  >
                    <GlassCard className={getCardStyles(notif.type, notif.is_read)}>
                      <div className="flex items-start gap-4">
                        {/* Icon */}
                        <div className="mt-1 flex-shrink-0">
                          {getIcon(notif.type)}
                        </div>

                        {/* Content */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between gap-4">
                            <div>
                              <h4 className="text-sm font-bold text-white flex items-center gap-2">
                                {notif.title}
                                {!notif.is_read && (
                                  <span className="w-2 h-2 rounded-full bg-cyan-glow glow-cyan" />
                                )}
                              </h4>
                              <p className="text-xs text-text-secondary mt-1 leading-relaxed">
                                {notif.message}
                              </p>
                            </div>
                            <span className="text-[10px] text-text-muted/70 font-mono whitespace-nowrap">
                              {formatTime(notif.created_at)}
                            </span>
                          </div>

                          {/* Action Link */}
                          {notif.link && (
                            <div className="mt-3">
                              <a
                                href={notif.link}
                                className="inline-flex items-center gap-1.5 text-xs text-cyan-glow-400 hover:text-cyan-glow-300 font-semibold transition-all group"
                              >
                                Ir para link
                                <ArrowRightIcon className="w-3.5 h-3.5 transform group-hover:translate-x-0.5 transition-transform" />
                              </a>
                            </div>
                          )}
                        </div>

                        {/* Actions buttons */}
                        <div className="flex items-center gap-2 ml-4 self-center">
                          {!notif.is_read && (
                            <button
                              onClick={() => handleMarkAsRead(notif.id)}
                              className="p-2 rounded-lg text-text-muted hover:text-emerald-glow hover:bg-white/5 transition-all"
                              title="Marcar como lida"
                            >
                              <CheckIcon className="w-4 h-4" />
                            </button>
                          )}
                          <button
                            onClick={() => handleDelete(notif.id)}
                            className="p-2 rounded-lg text-text-muted hover:text-rose-neon hover:bg-white/5 transition-all"
                            title="Excluir"
                          >
                            <TrashIcon className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    </GlassCard>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          )}
        </div>
      </motion.div>
      {dialog}
    </DashboardLayout>
  );
}
