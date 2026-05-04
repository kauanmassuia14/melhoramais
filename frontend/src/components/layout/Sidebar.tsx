"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { useState } from "react";
import {
  HomeIcon,
  ClockIcon,
  ChartBarIcon,
  Cog6ToothIcon,
  ArrowRightOnRectangleIcon,
  DocumentArrowUpIcon,
  CpuChipIcon,
  Squares2X2Icon,
  BuildingOffice2Icon,
  SparklesIcon,
} from "@heroicons/react/24/outline";
import { Logo } from "@/components/ui/logo";
import { useAuth } from "@/lib/auth-context";

const MENU_ITEMS = [
  { id: "dashboard", label: "Dashboard", icon: HomeIcon, href: "/" },
  { id: "upload", label: "Upload", icon: DocumentArrowUpIcon, href: "/upload" },
  { id: "animals", label: "Animais", icon: Squares2X2Icon, href: "/animals" },
  { id: "farms", label: "Fazendas", icon: BuildingOffice2Icon, href: "/farms" },
  { id: "history", label: "Logs de Processamento", icon: ClockIcon, href: "/history" },
  { id: "benchmarking", label: "Benchmarking", icon: SparklesIcon, href: "/benchmarking" },
  { id: "analytics", label: "Análises", icon: ChartBarIcon, href: "/analytics" },
  { id: "settings", label: "Configurações", icon: Cog6ToothIcon, href: "/settings" },
];

export const Sidebar = () => {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [isHovered, setIsHovered] = useState(false);

  return (
    <motion.aside
      initial={false}
      animate={{ width: isHovered ? 260 : 72 }}
      transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
      className="border-r border-white/5 bg-deep-dark-900 flex flex-col sticky top-0 h-screen overflow-hidden"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="flex flex-col h-full">
        <div className={`py-6 ${isHovered ? "px-6" : "px-3"}`}>
          <Logo size="md" showText={isHovered} />
        </div>

        <div className={`mx-4 mb-4 px-3 py-2.5 rounded-xl glass ${isHovered ? "" : "justify-center flex"}`}>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-emerald-glow animate-pulse" />
            {isHovered && (
              <span className="text-[11px] text-text-muted font-mono">
                SYSTEM ONLINE
              </span>
            )}
          </div>
        </div>

        <nav className="flex-1 px-3 space-y-1 overflow-y-auto overflow-x-hidden">
          {isHovered && (
            <p className="px-3 py-2 text-[10px] text-text-muted font-semibold tracking-[0.2em] uppercase">
              Navegação
            </p>
          )}
          {MENU_ITEMS.map((item) => {
            const isActive =
              pathname === item.href ||
              (item.href !== "/" && pathname.startsWith(item.href));
            return (
              <Link key={item.id} href={item.href} className="block relative">
<motion.div
                  whileHover={{ x: 2 }}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-300 relative ${
                    isActive
                      ? "text-emerald-glow-400"
                      : "text-text-secondary hover:text-text-primary hover:bg-white/[0.03]"
                  }`}
                >
                  {isActive && (
                    <motion.div
                      layoutId="sidebar-active"
                      className="absolute inset-0 rounded-xl bg-emerald-glow/10 border border-emerald-glow/20"
                      transition={{ type: "spring", bounce: 0.2, duration: 0.5 }}
                    />
                  )}
                  <item.icon className="w-5 h-5 relative z-10 flex-shrink-0" />
                  {isHovered && (
                    <span className="text-sm font-medium relative z-10 whitespace-nowrap">
                      {item.label}
                    </span>
                  )}
                  {isActive && (
                    <div className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-1 w-1 h-5 bg-emerald-glow rounded-r-full glow-green-strong" />
                  )}
                </motion.div>
              </Link>
            );
          })}
        </nav>

        <div className="p-4 space-y-3">
          {user && isHovered && (
            <div className="px-3 py-2 rounded-xl bg-white/[0.02] border border-white/[0.04]">
              <p className="text-xs text-text-primary font-medium truncate">{user.nome}</p>
              <p className="text-[10px] text-text-muted truncate">{user.email}</p>
              <span className={`inline-block mt-1 text-[9px] px-1.5 py-0.5 rounded-full ${
                user.role === "admin"
                  ? "bg-emerald-glow/10 text-emerald-glow-400"
                  : "bg-violet-glow/10 text-violet-glow-400"
              }`}>
                {user.role.toUpperCase()}
              </span>
            </div>
          )}

          <div className={`px-3 py-2 rounded-xl bg-white/[0.02] border border-white/[0.04] ${isHovered ? "" : "justify-center flex"}`}>
            <div className="flex items-center gap-2">
              <CpuChipIcon className="w-4 h-4 text-violet-glow-400 flex-shrink-0" />
              {isHovered && (
                <span className="text-[11px] text-text-muted font-mono">
                  v2.0.0-beta
                </span>
              )}
            </div>
          </div>

          <button
            onClick={logout}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-text-muted hover:text-rose-neon-400 hover:bg-rose-neon/[0.04] transition-all group ${
              isHovered ? "" : "justify-center"
            }`}
          >
            <ArrowRightOnRectangleIcon className="w-5 h-5 group-hover:translate-x-0.5 transition-transform flex-shrink-0" />
            {isHovered && (
              <span className="text-sm font-medium">Sair</span>
            )}
          </button>
        </div>
      </div>
    </motion.aside>
  );
};