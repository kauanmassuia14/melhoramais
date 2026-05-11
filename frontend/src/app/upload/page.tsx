"use client";

import { useState, useEffect } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { GlassCard } from "@/components/ui/glass-card";
import { GlowButton } from "@/components/ui/glow-button";
import { motion, AnimatePresence } from "framer-motion";
import { api, GeneticsFarm as Farm, Upload } from "@/lib/api";
import {
  DocumentArrowUpIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  PlusIcon,
  BuildingOfficeIcon,
  ChevronDownIcon,
  ChevronUpIcon,
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

interface CreateFarmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (farm: Farm) => void;
}

function CreateFarmModal({ isOpen, onClose, onSuccess }: CreateFarmModalProps) {
  const [nomeFarm, setNomeFarm] = useState("");
  const [cnpj, setCnpj] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const farmResponse = await api.createFarm({
        nome_farm: nomeFarm,
        cnpj: cnpj || undefined,
      });
      // Convert legacy Farm response to GeneticsFarm format
      const farm: Farm = {
        id: farmResponse.id_farm,
        nome: farmResponse.nome_farm,
        dono_fazenda: farmResponse.responsavel || null,
        cnpj: farmResponse.cnpj || null,
        created_at: farmResponse.created_at
      };
      onSuccess(farm);
      setNomeFarm("");
      setCnpj("");
    } catch (err: any) {
      setError(err.message || "Erro ao criar fazenda");
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-surface-1 border border-white/[0.08] rounded-2xl p-6 w-full max-w-md"
      >
        <h3 className="text-xl font-bold text-white mb-4">Nova Fazenda</h3>
        
        {error && (
          <div className="mb-4 p-3 rounded-lg bg-rose-neon/[0.08] border border-rose-neon/20 text-rose-neon-400 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-text-secondary mb-1">Nome da Fazenda *</label>
            <input
              type="text"
              value={nomeFarm}
              onChange={(e) => setNomeFarm(e.target.value)}
              className="w-full bg-white/10 border border-white/10 rounded-lg px-4 py-2.5 text-white placeholder:text-text-muted focus:outline-none focus:border-emerald-glow/40"
              placeholder="Ex: Fazenda São João"
              required
            />
          </div>

          <div>
            <label className="block text-sm text-text-secondary mb-1">CNPJ (opcional)</label>
            <input
              type="text"
              value={cnpj}
              onChange={(e) => setCnpj(e.target.value)}
              className="w-full bg-white/10 border border-white/10 rounded-lg px-4 py-2.5 text-white placeholder:text-text-muted focus:outline-none focus:border-emerald-glow/40"
              placeholder="00.000.000/0000-00"
            />
          </div>

          <div className="flex gap-3 pt-4">
            <GlowButton
              type="button"
              variant="ghost"
              onClick={onClose}
              className="flex-1"
            >
              Cancelar
            </GlowButton>
            <GlowButton
              type="submit"
              disabled={loading || !nomeFarm.trim()}
              className="flex-1"
            >
              {loading ? "Criando..." : "Criar Fazenda"}
            </GlowButton>
          </div>
        </form>
      </motion.div>
    </div>
  );
}

export default function UploadPage() {
  const [farms, setFarms] = useState<Farm[]>([]);
  const [selectedFarm, setSelectedFarm] = useState<Farm | null>(null);
  const [farmDropdownOpen, setFarmDropdownOpen] = useState(false);
  const [createFarmModalOpen, setCreateFarmModalOpen] = useState(false);
  const [platform, setPlatform] = useState("");
  const [uploadName, setUploadName] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [fileHash, setFileHash] = useState<string>("");
  const [existingUploads, setExistingUploads] = useState<{ arquivo_hash: string; arquivo_nome_original: string }[]>([]);
  const [status, setStatus] = useState<"idle" | "creating-upload" | "processing" | "success" | "error">("idle");
  const [errorMsg, setErrorMsg] = useState("");
  const [currentUpload, setCurrentUpload] = useState<Upload | null>(null);

  useEffect(() => {
    loadFarms();
    loadExistingUploads();
  }, []);

  const loadFarms = async () => {
    try {
      const farmsData = await api.getGeneticsFarms();
      setFarms(farmsData);
      if (farmsData.length > 0 && !selectedFarm) {
        setSelectedFarm(farmsData[0]);
      }
    } catch (err) {
      console.error("Erro ao carregar fazendas:", err);
    }
  };

  const loadExistingUploads = async () => {
    try {
      const uploads = await api.getUploads({ limit: 100 });
      setExistingUploads(uploads.map(u => ({ arquivo_hash: u.arquivo_hash || "", arquivo_nome_original: u.arquivo_nome_original || "" })));
    } catch (err) {
      console.error("Erro ao carregar uploads:", err);
    }
  };

  const calculateFileHash = async (file: File): Promise<string> => {
    const buffer = await file.arrayBuffer();
    const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  };

  const handleFileChange = async (newFile: File | null) => {
    setFile(newFile);
    if (newFile) {
      const hash = await calculateFileHash(newFile);
      setFileHash(hash);
    } else {
      setFileHash("");
    }
  };

  const checkDuplicate = (): boolean => {
    return existingUploads.some(u => u.arquivo_hash === fileHash);
  };

  const handleFarmCreated = (farm: Farm) => {
    setFarms([...farms, farm]);
    setSelectedFarm(farm);
    setCreateFarmModalOpen(false);
  };

  const handleUpload = async () => {
    if (!file || !platform || !selectedFarm || !uploadName.trim()) return;

    setStatus("creating-upload");

    try {
      // Step 1: Create upload record
      const upload = await api.createUpload({
        nome: uploadName.trim(),
        id_farm: selectedFarm.id,
        fonte_origem: platform,
        arquivo_nome_original: file.name,
        arquivo_hash: fileHash,
      });

      setCurrentUpload(upload);
      setStatus("processing");

      // Step 2: Process file with upload_id
      const blob = await api.uploadFileWithUpload(file, platform, selectedFarm.id, upload.upload_id);
      
      // Arquivo processado — não baixar automaticamente
      // O upload foi salvo no banco e pode ser acessado via histórico
      setStatus("success");
      
      try {
        await api.createNotification({
          title: "Upload concluído",
          message: `"${uploadName}" - ${file.name} processado com sucesso na fazenda ${selectedFarm.nome}.`,
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
          message: `Falha ao processar "${uploadName}": ${err.message || "Erro desconhecido"}`,
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
    setCurrentUpload(null);
    setUploadName("");
  };

  const canProceed = selectedFarm && platform && file && uploadName.trim();

  return (
    <DashboardLayout>
      <CreateFarmModal
        isOpen={createFarmModalOpen}
        onClose={() => setCreateFarmModalOpen(false)}
        onSuccess={handleFarmCreated}
      />

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
            Selecione a fazenda, dê um nome ao upload, escolha a plataforma e envie o arquivo.
          </p>
        </section>

        {/* Step 1: Select Farm */}
        <GlassCard glow="green" className="p-8 space-y-6">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-emerald-glow/10 border border-emerald-glow/20 flex items-center justify-center">
              <span className="text-emerald-glow-400 font-bold text-sm">01</span>
            </div>
            <h2 className="text-xl font-bold text-white">Selecione a Fazenda</h2>
          </div>

          <div className="relative">
            <button
              onClick={() => setFarmDropdownOpen(!farmDropdownOpen)}
              className="w-full bg-white/10 border border-white/10 rounded-xl px-4 py-3.5 text-left flex items-center justify-between hover:bg-white/15 hover:border-white/20 transition-colors focus:outline-none focus:border-emerald-glow/50 focus:ring-2 focus:ring-emerald-glow/10"
            >
              <div className="flex items-center gap-3">
                <BuildingOfficeIcon className="w-5 h-5 text-text-muted" />
                <span className="text-white">
                  {selectedFarm ? selectedFarm.nome : "Selecione uma fazenda..."}
                </span>
              </div>
              {farmDropdownOpen ? (
                <ChevronUpIcon className="w-5 h-5 text-text-muted" />
              ) : (
                <ChevronDownIcon className="w-5 h-5 text-text-muted" />
              )}
            </button>

            <AnimatePresence>
              {farmDropdownOpen && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="absolute top-full left-0 right-0 mt-2 bg-deep-dark border border-white/10 rounded-xl overflow-hidden z-10 shadow-xl"
                >
                  <div className="max-h-60 overflow-y-auto py-1">
                    {farms.map((farm) => (
                      <button
                        key={farm.id}
                        onClick={() => {
                          setSelectedFarm(farm);
                          setFarmDropdownOpen(false);
                        }}
                        className="w-full px-4 py-3 text-left hover:bg-white/5 transition-colors flex items-center gap-3"
                      >
                        <BuildingOfficeIcon className="w-4 h-4 text-text-muted" />
                        <span className="text-white">{farm.nome}</span>
                        {farm.cnpj && (
                          <span className="text-xs text-text-muted">{farm.cnpj}</span>
                        )}
                      </button>
                    ))}
                  </div>
                  <div className="border-t border-white/10 p-2">
                    <button
                      onClick={() => {
                        setFarmDropdownOpen(false);
                        setCreateFarmModalOpen(true);
                      }}
                      className="w-full px-4 py-2.5 rounded-lg bg-emerald-glow/10 border border-emerald-glow/20 text-emerald-glow-400 text-sm font-medium flex items-center justify-center gap-2 hover:bg-emerald-glow/15 transition-colors"
                    >
                      <PlusIcon className="w-4 h-4" />
                      Criar Nova Fazenda
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </GlassCard>

        {/* Step 2: Platform */}
        <GlassCard 
          glow="green" 
          className={`p-8 space-y-6 transition-all duration-500 ${
            !selectedFarm ? "opacity-40 pointer-events-none" : ""
          }`}
        >
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-emerald-glow/10 border border-emerald-glow/20 flex items-center justify-center">
              <span className="text-emerald-glow-400 font-bold text-sm">02</span>
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

        {/* Step 3: Upload Name */}
        <GlassCard
          glow="green"
          className={`p-8 space-y-6 transition-all duration-500 ${
            !platform ? "opacity-40 pointer-events-none" : ""
          }`}
        >
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-emerald-glow/10 border border-emerald-glow/20 flex items-center justify-center">
              <span className="text-emerald-glow-400 font-bold text-sm">03</span>
            </div>
            <h2 className="text-xl font-bold text-white">Nome do Upload</h2>
          </div>

          <div>
            <input
              type="text"
              value={uploadName}
              onChange={(e) => setUploadName(e.target.value)}
              placeholder="Ex: Importação ANCP Janeiro 2026"
              className="w-full bg-white/10 border border-white/10 rounded-xl px-4 py-3.5 text-white placeholder:text-text-muted focus:outline-none focus:border-emerald-glow/40 transition-colors"
            />
            <p className="text-xs text-text-muted mt-2">
              Dê um nome descritivo para identificar este upload no histórico
            </p>
          </div>
        </GlassCard>

        {/* Step 4: File */}
        <GlassCard
          glow="green"
          className={`p-8 space-y-6 transition-all duration-500 ${
            !uploadName.trim() ? "opacity-40 pointer-events-none" : ""
          }`}
        >
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-emerald-glow/10 border border-emerald-glow/20 flex items-center justify-center">
              <span className="text-emerald-glow-400 font-bold text-sm">04</span>
            </div>
            <h2 className="text-xl font-bold text-white">Upload do Arquivo</h2>
          </div>

          <div
            className="border-2 border-dashed border-white/10 rounded-xl p-12 text-center hover:border-emerald-glow/30 transition-all cursor-pointer"
            onClick={() => document.getElementById("file-input")?.click()}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              const dropped = e.dataTransfer.files[0];
              if (dropped) handleFileChange(dropped);
            }}
          >
            <input
              id="file-input"
              type="file"
              accept=".xlsx,.xls,.csv,.PAG"
              className="hidden"
              onChange={(e) => handleFileChange(e.target.files?.[0] || null)}
            />
            <DocumentArrowUpIcon className="w-12 h-12 text-text-muted mx-auto mb-4" />
            {file ? (
              <div>
                <p className="text-white font-medium">{file.name}</p>
                <p className="text-xs text-text-muted mt-1">
                  {(file.size / 1024).toFixed(1)} KB
                </p>
                {checkDuplicate() && (
                  <p className="text-xs text-amber-glow-400 mt-2 flex items-center justify-center gap-1">
                    <ExclamationTriangleIcon className="w-3 h-3" />
                    Este arquivo já foi processado anteriormente
                  </p>
                )}
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

        {/* Step 5: Execute */}
        <GlassCard
          glow="green"
          className={`p-8 space-y-6 transition-all duration-500 ${
            !canProceed ? "opacity-40 pointer-events-none" : ""
          }`}
        >
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-emerald-glow/10 border border-emerald-glow/20 flex items-center justify-center">
              <span className="text-emerald-glow-400 font-bold text-sm">05</span>
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
                  {selectedFarm?.nome} · {platform} · {uploadName}
                </p>
              </div>
              <GlowButton onClick={handleUpload}>Processar Dados</GlowButton>
            </div>
          )}

          {status === "creating-upload" && (
            <div className="p-4 rounded-xl bg-emerald-glow/10 border border-emerald-glow/20">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-5 h-5 border-2 border-emerald-glow border-t-transparent rounded-full animate-spin" />
                <span className="text-sm text-emerald-glow-400 font-medium">
                  Criando registro do upload...
                </span>
              </div>
              <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: "0%" }}
                  animate={{ width: "30%" }}
                  transition={{ duration: 1, ease: "linear" }}
                  className="h-full bg-gradient-to-r from-emerald-glow-deep to-emerald-glow rounded-full"
                />
              </div>
            </div>
          )}

          {status === "processing" && (
            <div className="p-4 rounded-xl bg-emerald-glow/10 border border-emerald-glow/20">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-5 h-5 border-2 border-emerald-glow border-t-transparent rounded-full animate-spin" />
                <span className="text-sm text-emerald-glow-400 font-medium">
                  Processando arquivo...
                </span>
              </div>
              <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: "30%" }}
                  animate={{ width: "100%" }}
                  transition={{ duration: 3, ease: "linear" }}
                  className="h-full bg-gradient-to-r from-emerald-glow-deep to-emerald-glow rounded-full"
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
                  <p className="text-xs text-text-muted">
                    Download iniciado automaticamente
                  </p>
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
