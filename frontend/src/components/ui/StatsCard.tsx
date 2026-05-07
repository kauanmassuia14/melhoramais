"use client";

import { ReactNode } from "react";

interface StatsCardProps {
  label: string;
  value: string | number | null | undefined;
  icon?: ReactNode;
  unit?: string;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  className?: string;
}

export function StatsCard({
  label,
  value,
  icon,
  unit,
  trend,
  className = "",
}: StatsCardProps) {
  return (
    <div
      className={`bg-white/5 border border-white/10 rounded-xl p-5 ${className}`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-text-secondary mb-1">{label}</p>
          <p className="text-2xl font-bold text-white">
            {value ?? '—'}{unit && <span className="text-lg ml-1 text-text-secondary">{unit}</span>}
          </p>
        </div>
        {icon && (
          <div className="w-10 h-10 rounded-lg bg-emerald-glow/10 flex items-center justify-center text-emerald-glow-400">
            {icon}
          </div>
        )}
      </div>
      {trend && (
        <div className="mt-3 flex items-center gap-1.5">
          <span
            className={`text-sm font-medium ${
              trend.isPositive ? "text-emerald-glow-400" : "text-rose-neon-400"
            }`}
          >
            {trend.isPositive ? "+" : "-"}
            {Math.abs(trend.value)}%
          </span>
          <span className="text-xs text-text-muted">vs período anterior</span>
        </div>
      )}
    </div>
  );
}