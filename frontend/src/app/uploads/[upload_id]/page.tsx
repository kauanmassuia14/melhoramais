"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { GlassCard } from "@/components/ui/glass-card";
import { GlowButton } from "@/components/ui/glow-button";
import { useToast } from "@/components/ui/Toast";
import { useConfirm } from "@/components/ui/ConfirmDialog";
import { motion } from "framer-motion";
import { api, UploadWithAnimals, Farm, Animal } from "@/lib/api";
import {
  ArrowLeftIcon,
  BuildingOfficeIcon,
  ArrowUpTrayIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  DocumentTextIcon,
  TrashIcon,
} from "@heroicons/react/24/outline";
import Link from "next/link";

const STATUS_CONFIG: Record<string, { bg: string; text: string; icon: any; label: string }> = {
  completed: {
    bg: "bg-emerald-glow/[0.08]",
    text: "text-emerald-glow-400",
    icon: CheckCircleIcon,
    label: "Concluído",
  },
  processing: {
    bg: "bg-cyan-glow/[0.08]",
    text: "text-cyan-glow-400",
    icon: ClockIcon,
    label: "Processando",
  },
  failed: {
    bg: "bg-rose-neon/[0.08]",
    text: "text-rose-neon-400",
    icon: XCircleIcon,
    label: "Falhou",
  },
};

export default function UploadDetailPage() {
  const params = useParams();
  const uploadId = params.upload_id as string;
  
  const [data, setData] = useState<UploadWithAnimals | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const { showToast } = useToast();
  const { confirm, dialog } = useConfirm();

  useEffect(() => {
    if (uploadId) {
      loadData();
    }
  }, [uploadId]);

  const loadData = async () => {
    setIsLoading(true);
    setError("");
    try {
      const uploadData = await api.getUpload(uploadId);
      setData(uploadData);
    } catch (err: any) {
      setError(err.message || "Erro ao carregar detalhes do upload");
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    const confirmed = await confirm({
      title: "Excluir upload",
      message: "Tem certeza que deseja excluir este upload? Todos os animais associados serão removidos permanentemente.",
      type: "danger",
    });

    if (!confirmed) return;

    try {
      await api.deleteUpload(uploadId);
      showToast("Upload excluído com sucesso", "success");
      window.location.href = "/uploads";
    } catch (err: any) {
      showToast(err.message || "Erro ao excluir upload", "error");
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "-";
    const date = new Date(dateStr);
    return date.toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-[60vh]">
          <div className="w-8 h-8 border-2 border-cyan-glow border-t-transparent rounded-full animate-spin" />
        </div>
      </DashboardLayout>
    );
  }

  if (error || !data) {
    return (
      <DashboardLayout>
        <GlassCard className="p-12 text-center">
          <XCircleIcon className="w-12 h-12 text-rose-neon-400 mx-auto mb-4" />
          <p className="text-text-primary font-medium mb-2">{error || "Upload não encontrado"}</p>
          <Link href="/uploads">
            <GlowButton className="mt-4">
              <ArrowLeftIcon className="w-4 h-4" />
              Voltar para Uploads
            </GlowButton>
          </Link>
        </GlassCard>
      </DashboardLayout>
    );
  }

  const { upload, farm_nome, animais_preview, total_animais } = data;
  const statusConfig = STATUS_CONFIG[upload.status] || STATUS_CONFIG.processing;
  const StatusIcon = statusConfig.icon;

  return (
    <DashboardLayout>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-8"
      >
        {/* Header */}
        <section className="flex items-start justify-between">
          <div>
            <Link href="/uploads" className="inline-flex items-center gap-1 text-text-secondary hover:text-white transition-colors mb-2">
              <ArrowLeftIcon className="w-4 h-4" />
              Voltar para Uploads
            </Link>
            <h1 className="text-4xl font-bold text-white tracking-tight">
              {upload.nome}
            </h1>
            <div className="flex items-center gap-4 mt-2">
              <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium ${statusConfig.bg} ${statusConfig.text} border border-white/[0.08]`}>
                <StatusIcon className="w-4 h-4" />
                {statusConfig.label}
              </span>
              <span className="text-text-secondary text-sm">
                ID: {upload.upload_id}
              </span>
            </div>
          </div>
          <GlowButton variant="ghost" onClick={handleDelete} className="text-rose-neon-400 hover:text-rose-neon">
            <TrashIcon className="w-4 h-4" />
            Excluir Upload
          </GlowButton>
        </section>

        {/* Info Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <GlassCard className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-cyan-glow/[0.08] border border-cyan-glow/20 flex items-center justify-center">
                <BuildingOfficeIcon className="w-5 h-5 text-cyan-glow-400" />
              </div>
              <div>
                <p className="text-xs text-text-muted">Fazenda</p>
                <p className="text-white font-medium">{farm_nome}</p>
              </div>
            </div>
          </GlassCard>

          <GlassCard className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-emerald-glow/[0.08] border border-emerald-glow/20 flex items-center justify-center">
                <ArrowUpTrayIcon className="w-5 h-5 text-emerald-glow-400" />
              </div>
              <div>
                <p className="text-xs text-text-muted">Plataforma</p>
                <p className="text-white font-medium">{upload.fonte_origem}</p>
              </div>
            </div>
          </GlassCard>

          <GlassCard className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-violet-glow/[0.08] border border-violet-glow/20 flex items-center justify-center">
                <DocumentTextIcon className="w-5 h-5 text-violet-glow-400" />
              </div>
              <div>
                <p className="text-xs text-text-muted">Total de Animais</p>
                <p className="text-white font-medium">{total_animais}</p>
              </div>
            </div>
          </GlassCard>

          <GlassCard className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-amber-glow/[0.08] border border-amber-glow/20 flex items-center justify-center">
                <ClockIcon className="w-5 h-5 text-amber-glow-400" />
              </div>
              <div>
                <p className="text-xs text-text-muted">Data do Upload</p>
                <p className="text-white font-medium">{formatDate(upload.data_upload)}</p>
              </div>
            </div>
          </GlassCard>
        </div>

        {/* Processing Details */}
        {upload.status === "completed" && (
          <GlassCard glow="cyan" className="p-6">
            <h2 className="text-lg font-bold text-white mb-4">Detalhes do Processamento</h2>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-4 bg-white/[0.02] rounded-xl border border-white/[0.04]">
                <p className="text-3xl font-bold text-white">{upload.total_registros}</p>
                <p className="text-sm text-text-secondary mt-1">Total de Registros</p>
              </div>
              <div className="text-center p-4 bg-emerald-glow/[0.04] rounded-xl border border-emerald-glow/10">
                <p className="text-3xl font-bold text-emerald-glow-400">{upload.rows_inserted}</p>
                <p className="text-sm text-text-secondary mt-1">Inseridos</p>
              </div>
              <div className="text-center p-4 bg-cyan-glow/[0.04] rounded-xl border border-cyan-glow/10">
                <p className="text-3xl font-bold text-cyan-glow-400">{upload.rows_updated}</p>
                <p className="text-sm text-text-secondary mt-1">Atualizados</p>
              </div>
            </div>
          </GlassCard>
        )}

        {upload.status === "failed" && upload.error_message && (
          <GlassCard glow="rose" className="p-6">
            <h2 className="text-lg font-bold text-rose-neon-400 mb-2">Erro no Processamento</h2>
            <div className="bg-rose-neon/[0.04] border border-rose-neon/20 rounded-lg p-4">
              <p className="text-rose-neon-400 text-sm">{upload.error_message}</p>
            </div>
          </GlassCard>
        )}

        {/* Animals Preview */}
        {animais_preview.length > 0 && (
          <div>
            <h2 className="text-lg font-bold text-white mb-4">Animais Importados</h2>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-white/[0.08]">
                    <th className="text-left py-3 px-4 text-text-secondary font-medium">RGN</th>
                    <th className="text-left py-3 px-4 text-text-secondary font-medium">Nome</th>
                    <th className="text-left py-3 px-4 text-text-secondary font-medium">Sexo</th>
                    <th className="text-left py-3 px-4 text-text-secondary font-medium">Raça</th>
                    <th className="text-left py-3 px-4 text-text-secondary font-medium">Nascimento</th>
                  </tr>
                </thead>
                <tbody>
                  {animais_preview.slice(0, 20).map((animal) => (
                    <tr key={animal.id_animal} className="border-b border-white/[0.04] hover:bg-white/[0.02]">
                      <td className="py-3 px-4 text-white font-medium">{animal.rgn_animal}</td>
                      <td className="py-3 px-4 text-text-primary">{animal.nome_animal || "-"}</td>
                      <td className="py-3 px-4">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                          animal.sexo === "M" 
                            ? "bg-cyan-glow/[0.08] text-cyan-glow-400" 
                            : animal.sexo === "F"
                            ? "bg-rose-glow/[0.08] text-rose-glow-400"
                            : "bg-white/[0.04] text-text-secondary"
                        }`}>
                          {animal.sexo === "M" ? "Macho" : animal.sexo === "F" ? "Fêmea" : "-"}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-text-secondary">{animal.raca || "-"}</td>
                      <td className="py-3 px-4 text-text-secondary">
                        {animal.data_nascimento 
                          ? new Date(animal.data_nascimento).toLocaleDateString("pt-BR")
                          : "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {total_animais > 20 && (
                <p className="text-center text-text-muted text-sm py-4">
                  Mostrando 20 de {total_animais} animais
                </p>
              )}
            </div>
          </div>
        )}
      </motion.div>
      {dialog}
    </DashboardLayout>
  );
}
