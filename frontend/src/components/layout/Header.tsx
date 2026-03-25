"use client";

import { BellIcon, MagnifyingGlassIcon } from "@heroicons/react/24/outline";
import { motion } from "framer-motion";

export const Header = () => {
  return (
    <header className="h-[64px] border-b border-white/[0.04] flex items-center justify-between px-8 bg-deep-dark/80 backdrop-blur-xl sticky top-0 z-20 w-full">
      {/* Search */}
      <div className="relative w-96 group">
        <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted group-focus-within:text-cyan-glow transition-colors" />
        <input
          type="text"
          placeholder="Buscar animais, relatórios..."
          className="w-full bg-white/[0.02] border border-white/[0.06] rounded-xl py-2 pl-10 pr-4 text-sm text-text-primary placeholder:text-text-muted outline-none focus:border-cyan-glow/40 focus:shadow-[0_0_0_3px_rgba(6,182,212,0.08)] transition-all"
        />
        <kbd className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] text-text-muted border border-white/[0.08] rounded px-1.5 py-0.5 font-mono">
          ⌘K
        </kbd>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-4">
        {/* Notification */}
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="relative p-2.5 rounded-xl text-text-muted hover:text-text-primary hover:bg-white/[0.04] transition-all"
        >
          <BellIcon className="w-5 h-5" />
          <span className="absolute top-2 right-2 w-2 h-2 bg-cyan-glow rounded-full glow-cyan animate-pulse" />
        </motion.button>

        {/* Divider */}
        <div className="h-8 w-px bg-white/[0.06]" />

        {/* Profile */}
        <div className="flex items-center gap-3">
          <div className="text-right hidden sm:block">
            <p className="text-sm font-medium text-text-primary">Genética Ltda.</p>
            <p className="text-[11px] text-text-muted">Administrador</p>
          </div>
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-glow-deep to-violet-glow flex items-center justify-center text-white text-sm font-bold">
            GL
          </div>
        </div>
      </div>
    </header>
  );
};
