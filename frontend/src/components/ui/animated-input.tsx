"use client";

import { motion, type HTMLMotionProps } from "framer-motion";
import { forwardRef } from "react";

interface AnimatedInputProps
  extends Omit<HTMLMotionProps<"input">, "children"> {
  label?: string;
  icon?: React.ReactNode;
  error?: string;
}

export const AnimatedInput = forwardRef<HTMLInputElement, AnimatedInputProps>(
  ({ label, icon, error, className = "", ...props }, ref) => {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-2"
      >
        {label && (
          <label className="block text-sm font-medium text-text-secondary">
            {label}
          </label>
        )}

        <div className="relative group">
          {icon && (
            <div className="absolute left-4 top-1/2 -translate-y-1/2 text-text-muted group-focus-within:text-cyan-glow transition-colors">
              {icon}
            </div>
          )}

          <motion.input
            ref={ref}
            whileFocus={{ scale: 1.01 }}
            className={`
              glass-input w-full py-3.5 text-[15px]
              ${icon ? "pl-12 pr-4" : "px-4"}
              ${error ? "border-rose-neon! shadow-[0_0_0_3px_rgba(244,63,94,0.1)]!" : ""}
              ${className}
            `}
            {...props}
          />
        </div>

        {error && (
          <motion.p
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-sm text-rose-neon-400"
          >
            {error}
          </motion.p>
        )}
      </motion.div>
    );
  }
);

AnimatedInput.displayName = "AnimatedInput";
