"use client";

import { ReactNode } from "react";
import { GlowButton } from "./glow-button";

interface EmptyStateProps {
  icon: ReactNode;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      <div className="w-16 h-16 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center mb-4">
        <div className="text-text-muted">{icon}</div>
      </div>
      <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
      {description && (
        <p className="text-text-secondary text-sm text-center max-w-md mb-6">
          {description}
        </p>
      )}
      {action && (
        <GlowButton size="sm" onClick={action.onClick}>
          {action.label}
        </GlowButton>
      )}
    </div>
  );
}