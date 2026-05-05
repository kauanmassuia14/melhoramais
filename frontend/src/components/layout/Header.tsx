"use client";

import { BellIcon, MagnifyingGlassIcon } from "@heroicons/react/24/outline";
import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect, useRef } from "react";
import { useAuth } from "@/lib/auth-context";
import { api, Notification } from "@/lib/api";
import { CheckIcon } from "@heroicons/react/24/outline";
import { useToast } from "@/components/ui/Toast";

export const Header = () => {
  const { user } = useAuth();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showDropdown, setShowDropdown] = useState(false);
  const [loading, setLoading] = useState(false);
  const [initialLoadDone, setInitialLoadDone] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const { showToast } = useToast();

  // Only fetch on first load and when dropdown opens
  const fetchNotifications = async () => {
    try {
      const [notifs, count] = await Promise.all([
        api.getNotifications(true),
        api.getUnreadCount(),
      ]);
      setNotifications(notifs);
      setUnreadCount(count.count);
      setInitialLoadDone(true);
    } catch {
      // silently fail
    }
  };

  useEffect(() => {
    if (!initialLoadDone) {
      fetchNotifications();
    }
  }, [initialLoadDone]);

  useEffect(() => {
    if (showDropdown && initialLoadDone) {
      fetchNotifications();
    }
  }, [showDropdown, initialLoadDone]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleMarkAsRead = async (id: number) => {
    try {
      await api.markAsRead(id);
      setUnreadCount((prev) => Math.max(0, prev - 1));
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
      showToast("Notificação marcada como lida", "success");
    } catch {
      showToast("Erro ao marcar notificação", "error");
    }
  };

  const handleMarkAllRead = async () => {
    setLoading(true);
    try {
      await api.markAllAsRead();
      setUnreadCount(0);
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      showToast("Todas marcadas como lidas", "success");
    } catch {
      showToast("Erro ao marcar notificações", "error");
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (dateStr: string | null) => {
    if (!dateStr) return "";
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    if (diffMins < 1) return "agora";
    if (diffMins < 60) return `${diffMins}m atrás`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h atrás`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d atrás`;
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case "success": return "text-emerald-600";
      case "error": return "text-red-500";
      case "warning": return "text-yellow-500";
      default: return "text-emerald-600";
    }
  };

  return (
    <header className="h-[64px] border-b border-white/[0.06] flex items-center justify-between px-8 bg-deep-dark-900 sticky top-0 z-20 w-full">
      {/* Search */}
      <div className="relative w-96 group">
        <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted group-focus-within:text-emerald-glow transition-colors" />
        <input
          type="text"
          placeholder="Buscar animais, relatórios..."
          className="w-full bg-white/5 border border-white/10 rounded-xl py-2 pl-10 pr-4 text-sm text-text-primary placeholder:text-text-muted outline-none focus:border-emerald-glow/40 focus:ring-2 focus:ring-emerald-glow/10 transition-all"
        />
        <kbd className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] text-text-muted border border-white/[0.08] rounded px-1.5 py-0.5 font-mono">
          ⌘K
        </kbd>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-4">
        {/* Notification */}
        <div className="relative" ref={dropdownRef}>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setShowDropdown(!showDropdown)}
            className="relative p-2.5 rounded-xl text-text-muted hover:text-text-primary hover:bg-white/[0.04] transition-all"
          >
            <BellIcon className="w-5 h-5" />
            {unreadCount > 0 && (
              <span className="absolute top-2 right-2 min-w-[16px] h-4 flex items-center justify-center bg-emerald-glow rounded-full text-[10px] text-white font-bold px-1 glow-green animate-pulse">
                {unreadCount > 9 ? "9+" : unreadCount}
              </span>
            )}
          </motion.button>

          <AnimatePresence>
            {showDropdown && (
              <motion.div
                initial={{ opacity: 0, y: 8, scale: 0.96 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 8, scale: 0.96 }}
                transition={{ duration: 0.15 }}
                className="absolute right-0 top-full mt-2 w-96 max-h-[480px] overflow-hidden rounded-2xl bg-deep-dark border border-white/[0.08] shadow-2xl"
              >
                <div className="flex items-center justify-between px-4 py-3 border-b border-white/[0.06]">
                  <h3 className="text-sm font-semibold text-text-primary">Notificações</h3>
                  {unreadCount > 0 && (
                    <button
                      onClick={handleMarkAllRead}
                      disabled={loading}
                      className="text-xs text-emerald-glow-400 hover:text-emerald-glow-300 transition-colors"
                    >
                      {loading ? "..." : "Marcar todas como lidas"}
                    </button>
                  )}
                </div>

                <div className="overflow-y-auto max-h-[400px]">
                  {notifications.length === 0 ? (
                    <div className="py-12 text-center">
                      <BellIcon className="w-8 h-8 text-text-muted mx-auto mb-2 opacity-50" />
                      <p className="text-sm text-text-muted">Nenhuma notificação</p>
                    </div>
                  ) : (
                    notifications.map((notif) => (
                      <div
                        key={notif.id}
                        className={`relative px-4 py-3 border-b border-white/[0.04] hover:bg-white/[0.02] transition-colors ${
                          !notif.is_read ? "bg-emerald-glow/[0.03]" : ""
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          <div className={`mt-0.5 w-2 h-2 rounded-full flex-shrink-0 ${
                            notif.type === "success" ? "bg-emerald-glow" :
                            notif.type === "error" ? "bg-rose-neon" :
                            notif.type === "warning" ? "bg-yellow-400" :
                            "bg-emerald-glow"
                          }`} />
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-text-primary truncate">{notif.title}</p>
                            <p className="text-xs text-text-muted mt-0.5 line-clamp-2">{notif.message}</p>
                            <p className="text-[10px] text-text-muted/60 mt-1 font-mono">
                              {formatTime(notif.created_at)}
                            </p>
                          </div>
                          {!notif.is_read && (
                            <button
                              onClick={() => handleMarkAsRead(notif.id)}
                              className="flex-shrink-0 p-1 rounded-lg text-text-muted hover:text-emerald-glow-400 hover:bg-white/[0.04] transition-all"
                              title="Marcar como lida"
                            >
                              <CheckIcon className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Divider */}
        <div className="h-8 w-px bg-white/[0.06]" />

        {/* Profile */}
        <div className="flex items-center gap-3">
          <div className="text-right hidden sm:block">
            <p className="text-sm font-medium text-text-primary">{user?.nome || "Usuário"}</p>
            <p className="text-[11px] text-text-muted capitalize">{user?.role || "Usuário"}</p>
          </div>
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-600 to-emerald-500 flex items-center justify-center text-white text-sm font-bold">
            {user?.nome ? user.nome.charAt(0).toUpperCase() : "U"}
          </div>
        </div>
      </div>
    </header>
  );
};
