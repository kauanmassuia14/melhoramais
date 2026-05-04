"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  EnvelopeIcon,
  LockClosedIcon,
  EyeIcon,
  EyeSlashIcon,
  ArrowRightIcon,
} from "@heroicons/react/24/outline";
import { GlowButton } from "@/components/ui/glow-button";
import { AnimatedInput } from "@/components/ui/animated-input";
import { GlassCard } from "@/components/ui/glass-card";
import { BorderBeam } from "@/components/ui/border-beam";
import { useAuth } from "@/lib/auth-context";

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
    <main className="min-h-screen flex items-center justify-center bg-deep-dark overflow-hidden">
      <div className="absolute top-[-20%] left-[-10%] w-[700px] h-[700px] bg-emerald-glow/[0.06] rounded-full blur-[150px] animate-pulse" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[600px] h-[600px] bg-cyan-glow/[0.04] rounded-full blur-[150px] animate-pulse" />
      <div className="absolute inset-0 bg-grid opacity-30" />

      <motion.div
        initial={{ opacity: 0, x: 30 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.8 }}
        className="w-full max-w-md relative z-10 px-4"
      >
        <div className="flex justify-center mb-8">
          <img
            src="/assets/images/logomelhoramais.png"
            alt="Melhora+"
            className="h-20 object-contain"
          />
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
              <div className="space-y-2">
                <h2 className="text-3xl font-bold text-white tracking-tight">
                  Acesse sua conta
                </h2>
                <p className="text-text-secondary">
                  Entre com suas credenciais para continuar.
                </p>
              </div>

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
            </div>
          </GlassCard>
        </div>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.2 }}
          className="mt-8 text-center text-xs text-text-muted"
        >
          Protegido por criptografia de ponta a ponta
        </motion.p>
      </motion.div>
    </main>
  );
}
