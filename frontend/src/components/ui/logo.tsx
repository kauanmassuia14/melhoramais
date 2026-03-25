"use client";

import Image from "next/image";

interface LogoProps {
  size?: "sm" | "md" | "lg";
  showText?: boolean;
  className?: string;
}

const sizes = {
  sm: { icon: 32, text: "text-lg" },
  md: { icon: 40, text: "text-xl" },
  lg: { icon: 48, text: "text-2xl" },
};

export function Logo({ size = "md", showText = true, className = "" }: LogoProps) {
  const s = sizes[size];

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {/*
        ============================================
        TO CHANGE THE LOGO:
        1. Put your logo file in: frontend/public/logo.png
        2. Uncomment the <Image> below
        3. Comment out or remove the placeholder div
        ============================================
      */}
      {/* <Image src="/logo.png" alt="Melhora+" width={s.icon} height={s.icon} className="rounded-xl" /> */}

      {/* Placeholder icon — remove when you add your logo */}
      <div
        className="rounded-xl bg-gradient-to-br from-cyan-glow-deep to-cyan-glow flex items-center justify-center glow-cyan"
        style={{ width: s.icon, height: s.icon }}
      >
        <span className="text-white font-bold" style={{ fontSize: s.icon * 0.5 }}>
          M+
        </span>
      </div>

      {showText && (
        <div>
          <span className={`${s.text} font-bold text-white tracking-tight`}>
            Melhora<span className="text-cyan-glow-400">+</span>
          </span>
          <p className="text-[10px] text-text-muted tracking-[0.15em] uppercase">
            Genética Platform
          </p>
        </div>
      )}
    </div>
  );
}
