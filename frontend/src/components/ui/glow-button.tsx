"use client";

import { motion, type HTMLMotionProps } from "framer-motion";
import { forwardRef } from "react";

interface GlowButtonProps extends HTMLMotionProps<"button"> {
  variant?: "primary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
  children: React.ReactNode;
}

const sizes = {
  sm: "px-4 py-2 text-sm rounded-lg",
  md: "px-6 py-3 text-sm rounded-xl",
  lg: "px-8 py-4 text-base rounded-xl",
};

export const GlowButton = forwardRef<HTMLButtonElement, GlowButtonProps>(
  (
    {
      variant = "primary",
      size = "md",
      loading = false,
      children,
      className = "",
      disabled,
      ...props
    },
    ref
  ) => {
    const base =
      "relative inline-flex items-center justify-center font-semibold overflow-hidden transition-all duration-300";

    const variants = {
      primary:
        "bg-gradient-to-r from-cyan-glow-deep to-cyan-glow text-white " +
        "hover:shadow-[0_0_30px_rgba(6,182,212,0.4),0_0_60px_rgba(6,182,212,0.2)] " +
        "active:scale-[0.97] disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:shadow-none",
      ghost:
        "bg-transparent text-text-secondary border border-white/[0.06] " +
        "hover:bg-white/[0.04] hover:border-white/[0.1] hover:text-text-primary",
      danger:
        "bg-gradient-to-r from-rose-neon-deep to-rose-neon text-white " +
        "hover:shadow-[0_0_30px_rgba(244,63,94,0.4)] " +
        "active:scale-[0.97]",
    };

    return (
      <motion.button
        ref={ref}
        whileHover={{ y: -1 }}
        whileTap={{ scale: 0.97 }}
        className={`${base} ${variants[variant]} ${sizes[size]} ${className}`}
        disabled={disabled || loading}
        {...props}
      >
        {/* Shimmer overlay */}
        {variant === "primary" && (
          <span className="absolute inset-0 bg-gradient-to-r from-transparent via-white/[0.1] to-transparent -translate-x-full hover:translate-x-full transition-transform duration-700" />
        )}
        {loading ? (
          <svg
            className="animate-spin h-5 w-5"
            viewBox="0 0 24 24"
            fill="none"
          >
            <circle
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="3"
              className="opacity-20"
            />
            <path
              d="M12 2a10 10 0 0 1 10 10"
              stroke="currentColor"
              strokeWidth="3"
              strokeLinecap="round"
            />
          </svg>
        ) : (
          children
        )}
      </motion.button>
    );
  }
);

GlowButton.displayName = "GlowButton";
