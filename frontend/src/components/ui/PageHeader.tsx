"use client";

import { ReactNode } from "react";
import { ArrowUpTrayIcon } from "@heroicons/react/24/outline";
import Link from "next/link";
import { GlowButton } from "./glow-button";

interface PageHeaderProps {
  title: string;
  description?: string;
  action?: {
    label: string;
    href: string;
    icon?: ReactNode;
  };
  children?: ReactNode;
}

export function PageHeader({
  title,
  description,
  action,
  children,
}: PageHeaderProps) {
  return (
    <div className="flex items-center justify-between mb-8">
      <div>
        <h1 className="text-3xl font-bold text-white tracking-tight">{title}</h1>
        {description && (
          <p className="text-text-secondary mt-1">{description}</p>
        )}
      </div>
      {action && (
        <Link href={action.href}>
          <GlowButton>
            {action.icon || <ArrowUpTrayIcon className="w-5 h-5" />}
            {action.label}
          </GlowButton>
        </Link>
      )}
    </div>
  );
}