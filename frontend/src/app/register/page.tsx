"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  EnvelopeIcon,
  LockClosedIcon,
  UserIcon,
  EyeIcon,
  EyeSlashIcon,
  ArrowRightIcon,
  SparklesIcon,
  BuildingOfficeIcon,
} from "@heroicons/react/24/outline";
import { GlowButton } from "@/components/ui/glow-button";
import { AnimatedInput } from "@/components/ui/animated-input";
import { GlassCard } from "@/components/ui/glass-card";
import { BorderBeam } from "@/components/ui/border-beam";
import { useAuth } from "@/lib/auth-context";

export default function RegisterPage() {
  const { register } = useAuth();
  const [form, setForm] = useState({
    name: "",
    email: "",
    organization: "",
    password: "",
    confirmPassword: "",
  });
  const [showPw, setShowPw] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const set = (key: string, value: string) => {
    setForm((p) => ({ ...p, [key]: value }));
    setErrors((p) => ({ ...p, [key]: "" }));
  };

  const validate = () => {
    const e: Record<string, string> = {};
    if (!form.name) e.name = "Nome é obrigatório";
    if (!form.email) e.email = "E-mail é obrigatório";
    else if (!/\S+@\S+\.\S+/.test(form.email)) e.email = "E-mail inválido";
    if (!form.password) e.password = "Senha é obrigatória";
    else if (form.password.length < 8) e.password = "Mínimo de 8 caracteres";
    if (form.password !== form.confirmPassword)
      e.confirmPassword = "Senhas não coincidem";
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    setIsLoading(true);
    setErrors({});
    try {
      await register({
        nome: form.name,
        email: form.email,
        senha: form.password,
      });
      window.location.href = "/";
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Erro ao criar conta";
      setErrors({ email: message });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen flex bg-deep-dark overflow-hidden">
      {/* LEFT: Visual Panel */}
      <section className="hidden lg:flex lg:w-[55%] relative flex-col justify-between p-16 overflow-hidden">
        <div className="absolute top-[-20%] right-[-10%] w-[700px] h-[700px] bg-violet-glow/[0.06] rounded-full blur-[150px] animate-pulse" />
        <div className="absolute bottom-[-20%] left-[-10%] w-[600px] h-[600px] bg-emerald-glow/[0.04] rounded-full blur-[150px] animate-pulse" />
        <div className="absolute inset-0 bg-grid opacity-30" />

        {/* Brand */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="relative z-10 flex items-center gap-4"
        >
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-violet-glow-deep to-violet-glow flex items-center justify-center glow-violet">
            <SparklesIcon className="w-6 h-6 text-white" />
          </div>
          <div>
            <span className="text-2xl font-bold text-white tracking-tight">
              Melhora<span className="text-emerald-glow-400">+</span>
            </span>
            <p className="text-[11px] text-text-muted tracking-[0.2em] uppercase">
              Biotecnologia & Genética
            </p>
          </div>
        </motion.div>

        {/* Hero */}
        <div className="relative z-10 space-y-8">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
          >
            <h1 className="text-6xl xl:text-7xl font-bold text-white leading-[1.05] tracking-tight">
              Crie sua conta
              <br />
              <span className="text-gradient-cyan italic">
                Acelere seu sucesso.
              </span>
            </h1>
          </motion.div>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="text-lg text-text-secondary max-w-lg leading-relaxed"
          >
            Junte-se a{" "}
            <span className="text-emerald-glow-400 font-semibold">580+ fazendas</span>{" "}
            que já transformaram seus dados genéticos em decisões inteligentes.
          </motion.p>

          {/* Features list */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.6 }}
            className="space-y-3 pt-2"
          >
            {[
              "Unificação automática ANCP + PMGZ + Geneplus",
              "Dashboard em tempo real com KPIs genéticos",
              "Relatórios PDF com identidade visual personalizada",
            ].map((feat, i) => (
              <div key={i} className="flex items-center gap-3">
                <div className="w-5 h-5 rounded-full bg-emerald-glow/10 flex items-center justify-center flex-shrink-0">
                  <div className="w-2 h-2 rounded-full bg-cyan-glow" />
                </div>
                <span className="text-sm text-text-secondary">{feat}</span>
              </div>
            ))}
          </motion.div>
        </div>

        {/* Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.8 }}
          className="relative z-10 flex items-center gap-10"
        >
          {[
            { label: "Animais Unificados", value: "2.4M+" },
            { label: "Precisão", value: "99.7%" },
            { label: "Uptime", value: "99.99%" },
          ].map((s) => (
            <div key={s.label} className="space-y-1">
              <p className="text-2xl font-bold text-white">{s.value}</p>
              <p className="text-xs text-text-muted tracking-wide uppercase">
                {s.label}
              </p>
            </div>
          ))}
        </motion.div>
      </section>

      {/* RIGHT: Register Form */}
      <section className="w-full lg:w-[45%] flex items-center justify-center p-8 relative">
        <div className="absolute left-0 top-0 bottom-0 w-px bg-gradient-to-b from-transparent via-violet-glow/20 to-transparent" />

        <motion.div
          initial={{ opacity: 0, x: 30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="w-full max-w-md"
        >
          {/* Mobile brand */}
          <div className="lg:hidden flex items-center gap-3 mb-12">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-glow-deep to-violet-glow flex items-center justify-center glow-violet">
              <SparklesIcon className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-white">
              Melhora<span className="text-emerald-glow-400">+</span>
            </span>
          </div>

          <div className="relative">
            <GlassCard glow="violet" className="p-10">
              <BorderBeam
                size={150}
                duration={12}
                colorFrom="#8b5cf6"
                colorTo="#10b981"
              />

              <div className="relative z-10 space-y-8">
                <div className="space-y-2">
                  <h2 className="text-3xl font-bold text-white tracking-tight">
                    Comece sua jornada
                  </h2>
                  <p className="text-text-secondary">
                    Preencha os dados abaixo para criar seu perfil.
                  </p>
                </div>

                <form
                  onSubmit={handleSubmit}
                  className="space-y-5"
                  noValidate
                >
                  <AnimatedInput
                    label="Nome Completo"
                    placeholder="Ex: João da Silva"
                    icon={<UserIcon className="w-5 h-5" />}
                    value={form.name}
                    onChange={(e) => set("name", e.target.value)}
                    error={errors.name}
                  />

                  <AnimatedInput
                    label="E-mail Profissional"
                    placeholder="nome@empresa.com"
                    type="email"
                    icon={<EnvelopeIcon className="w-5 h-5" />}
                    value={form.email}
                    onChange={(e) => set("email", e.target.value)}
                    error={errors.email}
                  />

                  <AnimatedInput
                    label="Organização / Fazenda"
                    placeholder="Nome da sua empresa"
                    icon={<BuildingOfficeIcon className="w-5 h-5" />}
                    value={form.organization}
                    onChange={(e) => set("organization", e.target.value)}
                  />

                  <AnimatedInput
                    label="Senha"
                    placeholder="Mínimo 8 caracteres"
                    type={showPw ? "text" : "password"}
                    icon={<LockClosedIcon className="w-5 h-5" />}
                    value={form.password}
                    onChange={(e) => set("password", e.target.value)}
                    error={errors.password}
                  />

                  <div className="space-y-2">
                    <AnimatedInput
                      label="Confirmar Senha"
                      placeholder="Repita a senha"
                      type={showPw ? "text" : "password"}
                      icon={<LockClosedIcon className="w-5 h-5" />}
                      value={form.confirmPassword}
                      onChange={(e) => set("confirmPassword", e.target.value)}
                      error={errors.confirmPassword}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPw(!showPw)}
                      className="flex items-center gap-1.5 text-xs text-text-muted hover:text-text-secondary transition-colors"
                    >
                      {showPw ? (
                        <EyeSlashIcon className="w-4 h-4" />
                      ) : (
                        <EyeIcon className="w-4 h-4" />
                      )}
                      {showPw ? "Ocultar senhas" : "Mostrar senhas"}
                    </button>
                  </div>

                  <GlowButton
                    type="submit"
                    size="lg"
                    className="w-full"
                    loading={isLoading}
                  >
                    {isLoading ? (
                      "Criando conta..."
                    ) : (
                      <>
                        Criar Conta Gratuita
                        <ArrowRightIcon className="w-5 h-5 ml-2" />
                      </>
                    )}
                  </GlowButton>
                </form>

                <div className="pt-4 text-center">
                  <p className="text-text-muted text-sm">
                    Já possui uma conta?{" "}
                    <Link
                      href="/login"
                      className="text-emerald-glow-400 hover:text-cyan-glow-300 font-semibold transition-colors"
                    >
                      Fazer Login
                    </Link>
                  </p>
                </div>
              </div>
            </GlassCard>
          </div>

          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.2 }}
            className="mt-8 text-center text-xs text-text-muted"
          >
            Ao criar uma conta, você concorda com nossos Termos de Serviço
          </motion.p>
        </motion.div>
      </section>
    </main>
  );
}
