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
      <Image
        src="/assets/images/logomelhoramais.png"
        alt="Melhora+"
        width={s.icon}
        height={s.icon}
        className="rounded-xl"
      />

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
