"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  EnvelopeIcon,
  LockClosedIcon,
  EyeIcon,
  EyeSlashIcon,
  ArrowRightIcon,
  SparklesIcon,
} from "@heroicons/react/24/outline";
import { GlowButton } from "@/components/ui/glow-button";
import { AnimatedInput } from "@/components/ui/animated-input";
import { GlassCard } from "@/components/ui/glass-card";
import { BorderBeam } from "@/components/ui/border-beam";
import { useAuth } from "@/lib/auth-context";

const DNA_HELIX = [
  { x: 0, delay: 0 },
  { x: 1, delay: 0.1 },
  { x: 2, delay: 0.2 },
  { x: 3, delay: 0.3 },
  { x: 4, delay: 0.4 },
  { x: 5, delay: 0.5 },
  { x: 6, delay: 0.6 },
  { x: 7, delay: 0.7 },
];

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<{ email?: string; password?: string }>(
    {}
  );

  const validate = () => {
    const newErrors: typeof errors = {};
    if (!email) newErrors.email = "E-mail é obrigatório";
    else if (!/\S+@\S+\.\S+/.test(email))
      newErrors.email = "E-mail inválido";
    if (!password) newErrors.password = "Senha é obrigatória";
    else if (password.length < 6)
      newErrors.password = "Mínimo de 6 caracteres";
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    setIsLoading(true);
    setErrors({});
    try {
      await login(email, password);
      window.location.href = "/";
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Erro ao autenticar";
      setErrors({ password: message });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen flex bg-deep-dark overflow-hidden">
      {/* ============================================
          LEFT: Immersive Visual Panel
          ============================================ */}
      <section className="hidden lg:flex lg:w-[55%] relative flex-col justify-between p-16 overflow-hidden">
        {/* Animated Background Orbs */}
        <div className="absolute top-[-20%] left-[-10%] w-[700px] h-[700px] bg-cyan-glow/[0.06] rounded-full blur-[150px] animate-pulse" />
        <div className="absolute bottom-[-20%] right-[-10%] w-[600px] h-[600px] bg-violet-glow/[0.04] rounded-full blur-[150px] animate-pulse" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[400px] h-[400px] bg-rose-neon/[0.03] rounded-full blur-[100px]" />

        {/* Grid overlay */}
        <div className="absolute inset-0 bg-grid opacity-30" />

        {/* Top: Brand */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: [0.4, 0, 0.2, 1] }}
          className="relative z-10 flex items-center gap-4"
        >
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-cyan-glow-deep to-cyan-glow flex items-center justify-center glow-cyan">
            <SparklesIcon className="w-6 h-6 text-white" />
          </div>
          <div>
            <span className="text-2xl font-bold text-white tracking-tight">
              Melhora<span className="text-cyan-glow-400">+</span>
            </span>
            <p className="text-[11px] text-text-muted tracking-[0.2em] uppercase">
              Biotecnologia & Genética
            </p>
          </div>
        </motion.div>

        {/* Center: Hero */}
        <div className="relative z-10 space-y-8">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
          >
            <h1 className="text-6xl xl:text-7xl font-bold text-white leading-[1.05] tracking-tight">
              A nova era do
              <br />
              <span className="text-gradient-cyan italic">
                Melhoramento Genético.
              </span>
            </h1>
          </motion.div>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="text-lg text-text-secondary max-w-lg leading-relaxed"
          >
            Unifique dados de{" "}
            <span className="text-cyan-glow-400 font-semibold">ANCP</span>,{" "}
            <span className="text-emerald-glow-400 font-semibold">PMGZ</span> e{" "}
            <span className="text-violet-glow-400 font-semibold">Geneplus</span>{" "}
            em uma única visão do animal.
          </motion.p>

          {/* DNA Helix Animation */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 1, delay: 0.6 }}
            className="flex items-center gap-3 pt-4"
          >
            {DNA_HELIX.map((_, i) => (
              <motion.div
                key={i}
                initial={{ scaleY: 0 }}
                animate={{ scaleY: 1 }}
                transition={{
                  duration: 0.5,
                  delay: 0.6 + i * 0.08,
                  repeat: Infinity,
                  repeatType: "reverse",
                  repeatDelay: 2,
                }}
                className="w-1 bg-gradient-to-t from-cyan-glow/40 to-cyan-glow-400 rounded-full"
                style={{ height: 20 + Math.sin(i * 0.8) * 15 }}
              />
            ))}
            <span className="text-xs text-text-muted font-mono ml-2">
              GENOME_ENGINE v3.2
            </span>
          </motion.div>
        </div>

        {/* Bottom: Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.8 }}
          className="relative z-10 flex items-center gap-10"
        >
          {[
            { label: "Animais Unificados", value: "2.4M+" },
            { label: "Fazendas Ativas", value: "580" },
            { label: "Precisão de Mapeamento", value: "99.7%" },
          ].map((stat) => (
            <div key={stat.label} className="space-y-1">
              <p className="text-2xl font-bold text-white">{stat.value}</p>
              <p className="text-xs text-text-muted tracking-wide uppercase">
                {stat.label}
              </p>
            </div>
          ))}
        </motion.div>
      </section>

      {/* ============================================
          RIGHT: Login Form
          ============================================ */}
      <section className="w-full lg:w-[45%] flex items-center justify-center p-8 relative">
        {/* Subtle border glow */}
        <div className="absolute left-0 top-0 bottom-0 w-px bg-gradient-to-b from-transparent via-cyan-glow/20 to-transparent" />

        <motion.div
          initial={{ opacity: 0, x: 30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="w-full max-w-md"
        >
          {/* Mobile brand */}
          <div className="lg:hidden flex items-center gap-3 mb-12">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-glow-deep to-cyan-glow flex items-center justify-center glow-cyan">
              <SparklesIcon className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-white">
              Melhora<span className="text-cyan-glow-400">+</span>
            </span>
          </div>

          {/* Form Card */}
          <div className="relative">
            <GlassCard glow="cyan" className="p-10">
              <BorderBeam
                size={150}
                duration={12}
                colorFrom="#06b6d4"
                colorTo="#8b5cf6"
              />

              <div className="relative z-10 space-y-8">
                {/* Header */}
                <div className="space-y-2">
                  <h2 className="text-3xl font-bold text-white tracking-tight">
                    Acesse sua conta
                  </h2>
                  <p className="text-text-secondary">
                    Entre com suas credenciais para continuar.
                  </p>
                </div>

                {/* Form */}
                <form
                  onSubmit={handleSubmit}
                  className="space-y-5"
                  noValidate
                >
                  <AnimatedInput
                    label="Endereço de E-mail"
                    placeholder="nome@empresa.com"
                    type="email"
                    icon={<EnvelopeIcon className="w-5 h-5" />}
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value);
                      setErrors((prev) => ({ ...prev, email: undefined }));
                    }}
                    error={errors.email}
                  />

                  <div className="space-y-2">
                    <AnimatedInput
                      label="Sua Senha"
                      placeholder="••••••••"
                      type={showPassword ? "text" : "password"}
                      icon={<LockClosedIcon className="w-5 h-5" />}
                      value={password}
                      onChange={(e) => {
                        setPassword(e.target.value);
                        setErrors((prev) => ({
                          ...prev,
                          password: undefined,
                        }));
                      }}
                      error={errors.password}
                    />
                    <div className="flex justify-between items-center">
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="flex items-center gap-1.5 text-xs text-text-muted hover:text-text-secondary transition-colors"
                      >
                        {showPassword ? (
                          <EyeSlashIcon className="w-4 h-4" />
                        ) : (
                          <EyeIcon className="w-4 h-4" />
                        )}
                        {showPassword ? "Ocultar" : "Mostrar"}
                      </button>
                      <Link
                        href="/forgot-password"
                        className="text-xs text-cyan-glow-400 hover:text-cyan-glow-300 transition-colors font-medium"
                      >
                        Esqueceu a senha?
                      </Link>
                    </div>
                  </div>

                  <GlowButton
                    type="submit"
                    size="lg"
                    className="w-full"
                    loading={isLoading}
                  >
                    {isLoading ? (
                      "Autenticando..."
                    ) : (
                      <>
                        Fazer Login
                        <ArrowRightIcon className="w-5 h-5 ml-2" />
                      </>
                    )}
                  </GlowButton>
                </form>

                {/* Divider */}
                <div className="relative">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-white/[0.06]" />
                  </div>
                  <div className="relative flex justify-center">
                    <span className="bg-transparent px-4 text-xs text-text-muted">
                      ou continue com
                    </span>
                  </div>
                </div>

                {/* Social login placeholder */}
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    className="flex items-center justify-center gap-2 py-3 rounded-xl border border-white/[0.06] bg-white/[0.02] text-sm text-text-secondary hover:bg-white/[0.04] hover:border-white/[0.1] transition-all"
                  >
                    <svg className="w-5 h-5" viewBox="0 0 24 24">
                      <path
                        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
                        fill="#4285F4"
                      />
                      <path
                        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                        fill="#34A853"
                      />
                      <path
                        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                        fill="#FBBC05"
                      />
                      <path
                        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                        fill="#EA4335"
                      />
                    </svg>
                    Google
                  </button>
                  <button
                    type="button"
                    className="flex items-center justify-center gap-2 py-3 rounded-xl border border-white/[0.06] bg-white/[0.02] text-sm text-text-secondary hover:bg-white/[0.04] hover:border-white/[0.1] transition-all"
                  >
                    <svg
                      className="w-5 h-5"
                      fill="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                    </svg>
                    GitHub
                  </button>
                </div>

                {/* Register link */}
                <div className="pt-4 text-center">
                  <p className="text-text-muted text-sm">
                    Ainda não tem acesso?{" "}
                    <Link
                      href="/register"
                      className="text-cyan-glow-400 hover:text-cyan-glow-300 font-semibold transition-colors"
                    >
                      Crie uma conta
                    </Link>
                  </p>
                </div>
              </div>
            </GlassCard>
          </div>

          {/* Bottom hint */}
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.2 }}
            className="mt-8 text-center text-xs text-text-muted"
          >
            Protegido por criptografia de ponta a ponta
          </motion.p>
        </motion.div>
      </section>
    </main>
  );
}
