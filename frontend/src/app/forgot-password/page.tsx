"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  EnvelopeIcon,
  ArrowLeftIcon,
  SparklesIcon,
  CheckCircleIcon,
} from "@heroicons/react/24/outline";
import { GlowButton } from "@/components/ui/glow-button";
import { AnimatedInput } from "@/components/ui/animated-input";
import { GlassCard } from "@/components/ui/glass-card";
import { BorderBeam } from "@/components/ui/border-beam";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      setError("E-mail é obrigatório");
      return;
    }
    if (!/\S+@\S+\.\S+/.test(email)) {
      setError("E-mail inválido");
      return;
    }

    setIsLoading(true);
    setError("");

    try {
      await fetch(`${API_BASE}/auth/forgot-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      // Always show success (backend doesn't reveal if email exists)
      setSent(true);
    } catch {
      setSent(true); // Don't reveal errors
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen flex items-center justify-center bg-deep-dark p-8">
      {/* Ambient */}
      <div className="absolute top-0 left-1/3 w-[600px] h-[600px] bg-emerald-glow/[0.04] rounded-full blur-[120px]" />
      <div className="absolute bottom-0 right-1/3 w-[500px] h-[500px] bg-cyan-glow/[0.03] rounded-full blur-[120px]" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="w-full max-w-md relative z-10"
      >
        {/* Brand */}
        <div className="flex items-center justify-center gap-3 mb-10">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-glow-deep to-emerald-glow flex items-center justify-center glow-green">
            <SparklesIcon className="w-5 h-5 text-white" />
          </div>
          <span className="text-xl font-bold text-white">
            Melhora<span className="text-emerald-glow-400">+</span>
          </span>
        </div>

        <div className="relative">
          <GlassCard glow="green" className="p-10">
            <BorderBeam
              size={150}
              duration={12}
              colorFrom="#10b981"
              colorTo="#06b6d4"
            />

            <div className="relative z-10 space-y-8">
              {sent ? (
                <>
                  <div className="text-center space-y-4">
                    <div className="w-16 h-16 rounded-full bg-emerald-glow/10 flex items-center justify-center mx-auto">
                      <CheckCircleIcon className="w-8 h-8 text-emerald-glow-400" />
                    </div>
                    <h2 className="text-2xl font-bold text-white">
                      Verifique seu e-mail
                    </h2>
                    <p className="text-text-secondary text-sm">
                      Se <span className="text-cyan-glow-400 font-semibold">{email}</span>{" "}
                      estiver cadastrado, você receberá um link para redefinir sua senha.
                    </p>
                  </div>

                  <Link
                    href="/login"
                    className="flex items-center justify-center gap-2 text-sm text-text-muted hover:text-text-secondary transition-colors"
                  >
                    <ArrowLeftIcon className="w-4 h-4" />
                    Voltar para o login
                  </Link>
                </>
              ) : (
                <>
                  <div className="space-y-2">
                    <h2 className="text-3xl font-bold text-white tracking-tight">
                      Recuperar senha
                    </h2>
                    <p className="text-text-secondary text-sm">
                      Informe seu e-mail e enviaremos um link para redefinir sua senha.
                    </p>
                  </div>

                  <form onSubmit={handleSubmit} className="space-y-5" noValidate>
                    <AnimatedInput
                      label="Seu E-mail"
                      placeholder="nome@empresa.com"
                      type="email"
                      icon={<EnvelopeIcon className="w-5 h-5" />}
                      value={email}
                      onChange={(e) => {
                        setEmail(e.target.value);
                        setError("");
                      }}
                      error={error}
                    />

                    <GlowButton
                      type="submit"
                      size="lg"
                      className="w-full"
                      loading={isLoading}
                    >
                      {isLoading ? "Enviando..." : "Enviar Link de Recuperação"}
                    </GlowButton>
                  </form>

                  <div className="text-center">
                    <Link
                      href="/login"
                      className="flex items-center justify-center gap-2 text-sm text-text-muted hover:text-text-secondary transition-colors"
                    >
                      <ArrowLeftIcon className="w-4 h-4" />
                      Voltar para o login
                    </Link>
                  </div>
                </>
              )}
            </div>
          </GlassCard>
        </div>
      </motion.div>
    </main>
  );
}
