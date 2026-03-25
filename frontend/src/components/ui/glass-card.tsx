"use client";

import { motion, type HTMLMotionProps } from "framer-motion";
import { forwardRef } from "react";

interface GlassCardProps extends HTMLMotionProps<"div"> {
  glow?: "cyan" | "rose" | "violet" | "none";
  beam?: boolean;
  children: React.ReactNode;
}

const glowStyles = {
  cyan:
    "hover:shadow-[0_0_30px_rgba(6,182,212,0.08),0_20px_60px_rgba(0,0,0,0.3)]",
  rose:
    "hover:shadow-[0_0_30px_rgba(244,63,94,0.08),0_20px_60px_rgba(0,0,0,0.3)]",
  violet:
    "hover:shadow-[0_0_30px_rgba(139,92,246,0.08),0_20px_60px_rgba(0,0,0,0.3)]",
  none: "",
};

export const GlassCard = forwardRef<HTMLDivElement, GlassCardProps>(
  (
    {
      glow = "none",
      beam = false,
      children,
      className = "",
      ...props
    },
    ref
  ) => {
    const base = beam ? "glass-card border-beam" : "glass-card";

    return (
      <motion.div
        ref={ref}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.4, 0, 0.2, 1] }}
        className={`${base} ${glowStyles[glow]} ${className}`}
        {...props}
      >
        {children}
      </motion.div>
    );
  }
);

GlassCard.displayName = "GlassCard";
