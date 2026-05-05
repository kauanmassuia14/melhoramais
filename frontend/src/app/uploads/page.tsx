"use client";

import { useState, useEffect } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { GlassCard } from "@/components/ui/glass-card";
import { GlowButton } from "@/components/ui/glow-button";
import { useToast } from "@/components/ui/Toast";
import { motion } from "framer-motion";
import { api, Upload, Farm } from "@/lib/api";
import {
  ArrowUpTrayIcon,
  DocumentTextIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  BuildingOfficeIcon,
  ArrowRightIcon,
  TrashIcon,
} from "@heroicons/react/24/outline";
import Link from "next/link";

const STATUS_COLORS: Record<string, { bg: string; text: string; icon: any }> = {
  completed: {
    bg: "bg-emerald-glow/10",
    text: "text-emerald-glow-400",
    icon: CheckCircleIcon,
  },
  processing: {
    bg: "bg-emerald-glow/10",
    text: "text-emerald-glow-400",
    icon: ClockIcon,
  },
  failed: {
    bg: "bg-rose-neon/10",
    text: "text-rose-neon-400",
    icon: XCircleIcon,
  },
};

const PLATFORM_NAMES: Record<string, string> = {
  ANCP: "ANCP",
  PMGZ: "PMGZ",
  Geneplus: "Geneplus",
  PMG: "PMGZ",
};

export default function UploadsPage() {
  const [uploads, setUploads] = useState<Upload[]>([]);
  const [farms, setFarms] = useState<Record<number, Farm>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [filterFarm, setFilterFarm] = useState<number | null>(null);
  const [filterStatus, setFilterStatus] = useState<string | null>(null);
  const { showToast } = useToast();

  useEffect(() => {
    loadData();
  }, [filterFarm, filterStatus]);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [uploadsData, farmsData] = await Promise.all([
        api.getUploads({
          farmId: filterFarm || undefined,
          status: filterStatus || undefined,
          limit: 100,
        }),
        api.getFarms(),
      ]);

      setUploads(uploadsData);
      
      const farmsMap: Record<number, Farm> = {};
      farmsData.forEach((farm) => {
        farmsMap[farm.id_farm] = farm;
      });
      setFarms(farmsMap);
    } catch (err) {
      console.error("Erro ao carregar uploads:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteUpload = async (uploadId: string) => {
    if (!confirm("Tem certeza que deseja excluir este upload? Todos os animais associados serão removidos.")) {
      return;
    }

    try {
      await api.deleteUpload(uploadId);
      setUploads(uploads.filter((u) => u.upload_id !== uploadId));
      showToast("Upload excluído com sucesso", "success");
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

  return (
    <DashboardLayout>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-8"
      >
        {/* Header */}
        <section className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-white tracking-tight">
              Histórico de Uploads
            </h1>
            <p className="text-text-secondary mt-1">
              Visualize e gerencie todos os uploads de dados genéticos
            </p>
          </div>
          <Link href="/upload">
            <GlowButton>
              <ArrowUpTrayIcon className="w-5 h-5" />
              Novo Upload
            </GlowButton>
          </Link>
        </section>

        {/* Filters */}
        <GlassCard glow="green" className="p-6">
          <div className="flex flex-wrap gap-4">
            <div>
              <label className="block text-sm text-text-secondary mb-2">Fazenda</label>
              <select
                value={filterFarm || ""}
                onChange={(e) => setFilterFarm(e.target.value ? Number(e.target.value) : null)}
                className="bg-white/10 border border-white/10 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-emerald-glow/50 focus:ring-2 focus:ring-emerald-glow/10 transition-all"
              >
                <option value="">Todas as fazendas</option>
                {Object.values(farms).map((farm) => (
                  <option key={farm.id_farm} value={farm.id_farm}>
                    {farm.nome_farm}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm text-text-secondary mb-2">Status</label>
              <select
                value={filterStatus || ""}
                onChange={(e) => setFilterStatus(e.target.value || null)}
                className="bg-white/10 border border-white/10 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-emerald-glow/50 focus:ring-2 focus:ring-emerald-glow/10 transition-all"
              >
                <option value="">Todos os status</option>
                <option value="completed">Concluído</option>
                <option value="processing">Processando</option>
                <option value="failed">Falhou</option>
              </select>
            </div>

            <div className="flex items-end">
              <GlowButton
                variant="ghost"
                onClick={() => {
                  setFilterFarm(null);
                  setFilterStatus(null);
                }}
              >
                Limpar Filtros
              </GlowButton>
            </div>
          </div>
        </GlassCard>

        {/* Uploads List */}
        <div className="space-y-4">
          {isLoading ? (
            <GlassCard className="p-12 text-center">
              <div className="w-8 h-8 border-2 border-cyan-glow border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <p className="text-text-secondary">Carregando uploads...</p>
            </GlassCard>
          ) : uploads.length === 0 ? (
            <GlassCard className="p-12 text-center">
              <DocumentTextIcon className="w-12 h-12 text-text-muted mx-auto mb-4" />
              <p className="text-text-primary font-medium mb-2">Nenhum upload encontrado</p>
              <p className="text-text-secondary text-sm mb-4">
                Comece fazendo o upload de seus dados genéticos
              </p>
              <Link href="/upload">
                <GlowButton size="sm">Fazer Upload</GlowButton>
              </Link>
            </GlassCard>
          ) : (
            uploads.map((upload, index) => {
              const statusConfig = STATUS_COLORS[upload.status] || STATUS_COLORS.processing;
              const StatusIcon = statusConfig.icon;
              const farm = farms[upload.id_farm];

              return (
                <motion.div
                  key={upload.upload_id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <GlassCard className="p-6 hover:border-white/[0.1] transition-colors">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-4">
                        {/* Status Icon */}
                        <div className={`w-12 h-12 rounded-xl ${statusConfig.bg} border border-white/[0.08] flex items-center justify-center flex-shrink-0`}>
                          <StatusIcon className={`w-6 h-6 ${statusConfig.text}`} />
                        </div>

                        {/* Info */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-3 mb-1">
                            <h3 className="text-lg font-bold text-white truncate">
                              {upload.nome}
                            </h3>
                            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusConfig.bg} ${statusConfig.text} border border-white/[0.08]`}>
                              {upload.status === "completed" ? "Concluído" : 
                               upload.status === "processing" ? "Processando" : "Falhou"}
                            </span>
                          </div>

                          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-text-secondary">
                            <span className="flex items-center gap-1">
                              <BuildingOfficeIcon className="w-4 h-4" />
                              {farm?.nome_farm || `Fazenda ${upload.id_farm}`}
                            </span>
                            <span className="flex items-center gap-1">
                              <ArrowUpTrayIcon className="w-4 h-4" />
                              {PLATFORM_NAMES[upload.fonte_origem] || upload.fonte_origem}
                            </span>
                            <span className="flex items-center gap-1">
                              <ClockIcon className="w-4 h-4" />
                              {formatDate(upload.data_upload)}
                            </span>
                          </div>

                          {upload.arquivo_nome_original && (
                            <p className="text-xs text-text-muted mt-2">
                              Arquivo: {upload.arquivo_nome_original}
                            </p>
                          )}

                          {upload.status === "completed" && (
                            <div className="flex items-center gap-4 mt-3 text-sm">
                              <span className="text-text-secondary">
                                <span className="text-white font-medium">{upload.total_registros}</span> registros
                              </span>
                              <span className="text-emerald-glow-400">
                                <span className="font-medium">{upload.rows_inserted}</span> inseridos
                              </span>
                              {upload.rows_updated > 0 && (
                                <span className="text-cyan-glow-400">
                                  <span className="font-medium">{upload.rows_updated}</span> atualizados
                                </span>
                              )}
                            </div>
                          )}

                          {upload.status === "failed" && upload.error_message && (
                            <p className="text-xs text-rose-neon-400 mt-2 bg-rose-neon/[0.04] p-2 rounded">
                              {upload.error_message}
                            </p>
                          )}
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex items-center gap-2">
                        <Link href={`/uploads/${upload.upload_id}`}>
                          <GlowButton variant="ghost" size="sm">
                            Detalhes
                            <ArrowRightIcon className="w-4 h-4" />
                          </GlowButton>
                        </Link>
                        <GlowButton
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteUpload(upload.upload_id)}
                          className="text-rose-neon-400 hover:text-rose-neon"
                        >
                          <TrashIcon className="w-4 h-4" />
                        </GlowButton>
                      </div>
                    </div>
                  </GlassCard>
                </motion.div>
              );
            })
          )}
        </div>
      </motion.div>
    </DashboardLayout>
  );
}
