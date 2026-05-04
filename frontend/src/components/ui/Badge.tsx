"use client";

interface BadgeProps {
  variant?: "green" | "cyan" | "rose" | "violet" | "neutral";
  children: React.ReactNode;
  className?: string;
}

const variants = {
  green: "bg-emerald-glow/10 text-emerald-glow-400 border-emerald-glow/20",
  cyan: "bg-cyan-glow/10 text-cyan-glow-400 border-cyan-glow/20",
  rose: "bg-rose-neon/10 text-rose-neon-400 border-rose-neon/20",
  violet: "bg-violet-glow/10 text-violet-glow-400 border-violet-glow/20",
  neutral: "bg-white/5 text-text-secondary border-white/10",
};

export function Badge({
  variant = "neutral",
  children,
  className = "",
}: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${variants[variant]} ${className}`}
    >
      {children}
    </span>
  );
}