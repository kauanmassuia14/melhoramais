"use client";

import { useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { GlassCard } from "@/components/ui/glass-card";
import { GlowButton } from "@/components/ui/glow-button";
import { motion } from "framer-motion";
import { api } from "@/lib/api";
import {
  DocumentArrowUpIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ArrowDownTrayIcon,
} from "@heroicons/react/24/outline";

const PLATFORMS = [
  {
    id: "ANCP",
    name: "ANCP",
    description: "Associação Nacional de Criadores e Pesquisadores",
    color: "cyan",
  },
  {
    id: "PMGZ",
    name: "PMGZ",
    description: "Programa de Melhoramento Genético Zebuíno",
    color: "emerald",
  },
  {
    id: "Geneplus",
    name: "Geneplus",
    description: "Programa Embrapa Geneplus",
    color: "violet",
  },
];

export default function UploadPage() {
  const [platform, setPlatform] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<"idle" | "processing" | "success" | "error">("idle");
  const [errorMsg, setErrorMsg] = useState("");

  const handleUpload = async () => {
    if (!file || !platform) return;
    setStatus("processing");

    try {
      const blob = await api.uploadFile(file, platform, 1);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `melhora_plus_tratado_${platform}.xlsx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setStatus("success");
      
      try {
        await api.createNotification({
          title: "Upload concluído",
          message: `Arquivo "${file.name}" processado com sucesso na plataforma ${platform}.`,
          type: "success",
        });
      } catch {
        // notification failed silently
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Erro no processamento");
      setStatus("error");
      
      try {
        await api.createNotification({
          title: "Erro no upload",
          message: `Falha ao processar "${file?.name}": ${err.message || "Erro desconhecido"}`,
          type: "error",
        });
      } catch {
        // notification failed silently
      }
    }
  };

  const handleReset = () => {
    setStatus("idle");
    setFile(null);
    setErrorMsg("");
  };

  return (
    <DashboardLayout>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-8 max-w-5xl mx-auto"
      >
        <section>
          <h1 className="text-4xl font-bold text-white tracking-tight">
            Upload de Dados Genéticos
          </h1>
          <p className="text-text-secondary mt-1">
            Selecione a plataforma, envie o arquivo e processe automaticamente.
          </p>
        </section>

        {/* Step 1: Platform */}
        <GlassCard glow="cyan" className="p-8 space-y-6">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-cyan-glow/[0.08] border border-cyan-glow/20 flex items-center justify-center">
              <span className="text-cyan-glow-400 font-bold text-sm">01</span>
            </div>
            <h2 className="text-xl font-bold text-white">Selecione a Plataforma</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {PLATFORMS.map((p) => {
              const isSelected = platform === p.id;
              const colorMap: Record<string, string> = {
                cyan: "border-cyan-glow/40 bg-cyan-glow/[0.04] shadow-[0_0_30px_rgba(6,182,212,0.08)]",
                emerald: "border-emerald-glow/40 bg-emerald-glow/[0.04] shadow-[0_0_30px_rgba(16,185,129,0.08)]",
                violet: "border-violet-glow/40 bg-violet-glow/[0.04] shadow-[0_0_30px_rgba(139,92,246,0.08)]",
              };
              return (
                <motion.button
                  key={p.id}
                  whileHover={{ y: -2 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => setPlatform(p.id)}
                  className={`p-5 rounded-xl border text-left transition-all duration-300 ${
                    isSelected
                      ? colorMap[p.color]
                      : "border-white/[0.06] bg-white/[0.02] hover:border-white/[0.1]"
                  }`}
                >
                  <p className="text-lg font-bold text-white">{p.name}</p>
                  <p className="text-xs text-text-muted mt-1">{p.description}</p>
                </motion.button>
              );
            })}
          </div>
        </GlassCard>

        {/* Step 2: File */}
        <GlassCard
          glow="cyan"
          className={`p-8 space-y-6 transition-all duration-500 ${
            !platform ? "opacity-40 pointer-events-none" : ""
          }`}
        >
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-emerald-glow/[0.08] border border-emerald-glow/20 flex items-center justify-center">
              <span className="text-emerald-glow-400 font-bold text-sm">02</span>
            </div>
            <h2 className="text-xl font-bold text-white">Upload do Arquivo</h2>
          </div>

          <div
            className="border-2 border-dashed border-white/[0.08] rounded-xl p-12 text-center hover:border-cyan-glow/30 transition-all cursor-pointer"
            onClick={() => document.getElementById("file-input")?.click()}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              const dropped = e.dataTransfer.files[0];
              if (dropped) setFile(dropped);
            }}
          >
            <input
              id="file-input"
              type="file"
              accept=".xlsx,.xls,.csv,.PAG"
              className="hidden"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
            />
            <DocumentArrowUpIcon className="w-12 h-12 text-text-muted mx-auto mb-4" />
            {file ? (
              <div>
                <p className="text-white font-medium">{file.name}</p>
                <p className="text-xs text-text-muted mt-1">
                  {(file.size / 1024).toFixed(1)} KB
                </p>
              </div>
            ) : (
              <div>
                <p className="text-text-secondary">
                  Arraste o arquivo ou clique para selecionar
                </p>
                <p className="text-xs text-text-muted mt-2">
                  .xlsx, .xls, .csv, .PAG
                </p>
              </div>
            )}
          </div>
        </GlassCard>

        {/* Step 3: Execute */}
        <GlassCard
          glow="cyan"
          className={`p-8 space-y-6 transition-all duration-500 ${
            !file ? "opacity-40 pointer-events-none" : ""
          }`}
        >
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-violet-glow/[0.08] border border-violet-glow/20 flex items-center justify-center">
              <span className="text-violet-glow-400 font-bold text-sm">03</span>
            </div>
            <h2 className="text-xl font-bold text-white">Execução</h2>
          </div>

          {status === "idle" && (
            <div className="flex items-center justify-between p-4 rounded-xl bg-white/[0.02] border border-white/[0.04]">
              <div>
                <p className="text-sm text-text-primary font-medium">
                  Pronto para processar
                </p>
                <p className="text-xs text-text-muted">
                  {platform} · {file?.name}
                </p>
              </div>
              <GlowButton onClick={handleUpload}>Processar Dados</GlowButton>
            </div>
          )}

          {status === "processing" && (
            <div className="p-4 rounded-xl bg-cyan-glow/[0.04] border border-cyan-glow/20">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-5 h-5 border-2 border-cyan-glow border-t-transparent rounded-full animate-spin" />
                <span className="text-sm text-cyan-glow-400 font-medium">
                  Processando...
                </span>
              </div>
              <div className="h-1.5 bg-white/[0.04] rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: "0%" }}
                  animate={{ width: "100%" }}
                  transition={{ duration: 3, ease: "linear" }}
                  className="h-full bg-gradient-to-r from-cyan-glow-deep to-cyan-glow rounded-full"
                />
              </div>
            </div>
          )}

          {status === "success" && (
            <div className="p-4 rounded-xl bg-emerald-glow/[0.04] border border-emerald-glow/20 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <CheckCircleIcon className="w-6 h-6 text-emerald-glow-400" />
                <div>
                  <p className="text-sm text-emerald-glow-400 font-medium">
                    Processamento concluído
                  </p>
                  <p className="text-xs text-text-muted">Download iniciado automaticamente</p>
                </div>
              </div>
              <GlowButton variant="ghost" size="sm" onClick={handleReset}>
                Novo Upload
              </GlowButton>
            </div>
          )}

          {status === "error" && (
            <div className="p-4 rounded-xl bg-rose-neon/[0.04] border border-rose-neon/20 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <ExclamationTriangleIcon className="w-6 h-6 text-rose-neon-400" />
                <div>
                  <p className="text-sm text-rose-neon-400 font-medium">Erro</p>
                  <p className="text-xs text-text-muted">{errorMsg}</p>
                </div>
              </div>
              <GlowButton variant="ghost" size="sm" onClick={handleReset}>
                Tentar Novamente
              </GlowButton>
            </div>
          )}
        </GlassCard>
      </motion.div>
    </DashboardLayout>
  );
}
