"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  XMarkIcon,
  SparklesIcon,
  CheckIcon,
  ExclamationTriangleIcon,
} from "@heroicons/react/24/outline";
import { METRIC_LABELS } from "@/lib/mock-comparison-data";

interface MelhoraPlusFormProps {
  isOpen: boolean;
  onClose: () => void;
  animalName: string;
  animalRgn: string;
  existingData?: Record<string, { dep: number | null; acc: number | null }>;
  onSave: (data: { metrics: Record<string, { dep: number | null; acc: number | null }>; notas: string }) => void;
}

// ─── Metric Input Row ────────────────────────────────────────────────────────
function MetricInput({
  metricKey,
  dep,
  acc,
  onDepChange,
  onAccChange,
}: {
  metricKey: string;
  dep: string;
  acc: string;
  onDepChange: (v: string) => void;
  onAccChange: (v: string) => void;
}) {
  const info = METRIC_LABELS[metricKey];
  if (!info) return null;

  return (
    <div className="grid grid-cols-12 gap-3 items-center py-2.5 border-b border-white/[0.04] last:border-0">
      {/* Label */}
      <div className="col-span-5 sm:col-span-4">
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-bold font-mono text-cyan-400 w-8">
            {info.name}
          </span>
          <span className="text-xs text-slate-400 truncate">{info.fullName}</span>
        </div>
      </div>

      {/* DEP Input */}
      <div className="col-span-4 sm:col-span-4">
        <div className="relative">
          <input
            type="number"
            step="0.01"
            value={dep}
            onChange={(e) => onDepChange(e.target.value)}
            placeholder="DEP"
            className="w-full bg-white/[0.03] border border-white/10 rounded-lg px-3 py-2 text-sm text-white font-mono placeholder:text-slate-600 focus:outline-none focus:border-violet-500/50 focus:ring-1 focus:ring-violet-500/20 transition-all"
          />
          {info.unit && (
            <span className="absolute right-2 top-1/2 -translate-y-1/2 text-[9px] text-slate-600">
              {info.unit}
            </span>
          )}
        </div>
      </div>

      {/* Accuracy Input */}
      <div className="col-span-3 sm:col-span-4">
        <div className="relative">
          <input
            type="number"
            min="0"
            max="100"
            step="1"
            value={acc}
            onChange={(e) => onAccChange(e.target.value)}
            placeholder="AC%"
            className="w-full bg-white/[0.03] border border-white/10 rounded-lg px-3 py-2 text-sm text-white font-mono placeholder:text-slate-600 focus:outline-none focus:border-violet-500/50 focus:ring-1 focus:ring-violet-500/20 transition-all"
          />
          <span className="absolute right-2 top-1/2 -translate-y-1/2 text-[9px] text-slate-600">
            %
          </span>
        </div>
      </div>
    </div>
  );
}

// ─── Main Component ──────────────────────────────────────────────────────────
export function MelhoraPlusForm({
  isOpen,
  onClose,
  animalName,
  animalRgn,
  existingData,
  onSave,
}: MelhoraPlusFormProps) {
  const metricKeys = Object.keys(METRIC_LABELS);

  // Initialize form state
  const [formData, setFormData] = useState<Record<string, { dep: string; acc: string }>>({});
  const [notas, setNotas] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  // Reset form when opening
  useEffect(() => {
    if (isOpen) {
      const initial: Record<string, { dep: string; acc: string }> = {};
      metricKeys.forEach((key) => {
        const existing = existingData?.[key];
        initial[key] = {
          dep: existing?.dep != null ? String(existing.dep) : "",
          acc: existing?.acc != null ? String(existing.acc) : "",
        };
      });
      setFormData(initial);
      setSaved(false);
    }
  }, [isOpen]);

  // Close on ESC
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  const updateDep = useCallback((key: string, value: string) => {
    setFormData((prev) => ({
      ...prev,
      [key]: { ...prev[key], dep: value },
    }));
  }, []);

  const updateAcc = useCallback((key: string, value: string) => {
    setFormData((prev) => ({
      ...prev,
      [key]: { ...prev[key], acc: value },
    }));
  }, []);

  const filledCount = Object.values(formData).filter(
    (v) => v.dep !== ""
  ).length;

  const handleSave = async () => {
    setSaving(true);

    // Convert to proper types
    const metricsPayload: Record<string, { dep: number | null; acc: number | null }> = {};
    Object.entries(formData).forEach(([key, val]) => {
      if (val.dep !== "") {
        metricsPayload[key] = {
          dep: parseFloat(val.dep),
          acc: val.acc !== "" ? parseFloat(val.acc) : null,
        };
      }
    });

    // Simulate API call (mock phase)
    await new Promise((r) => setTimeout(r, 800));
    onSave({ metrics: metricsPayload, notas });

    setSaving(false);
    setSaved(true);
    setTimeout(() => onClose(), 1200);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/70 backdrop-blur-sm"
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.92, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.92, y: 20 }}
            transition={{ type: "spring", bounce: 0.2, duration: 0.5 }}
            className="relative z-10 w-full max-w-2xl max-h-[85vh] overflow-hidden rounded-2xl border border-violet-500/20 bg-slate-900/98 backdrop-blur-xl shadow-2xl flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-white/[0.06]">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500/20 to-fuchsia-500/20 border border-violet-500/30 flex items-center justify-center">
                  <SparklesIcon className="w-5 h-5 text-violet-400" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-white">
                    Dados Melhora+
                  </h2>
                  <p className="text-xs text-slate-500">
                    <span className="text-cyan-400 font-mono">{animalRgn}</span>
                    {animalName && (
                      <span className="text-slate-400"> — {animalName}</span>
                    )}
                  </p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-2 rounded-xl hover:bg-white/[0.05] text-slate-400 hover:text-white transition-all"
              >
                <XMarkIcon className="w-5 h-5" />
              </button>
            </div>

            {/* Column Headers */}
            <div className="grid grid-cols-12 gap-3 px-6 pt-4 pb-2">
              <div className="col-span-5 sm:col-span-4">
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                  Característica
                </span>
              </div>
              <div className="col-span-4 sm:col-span-4">
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                  DEP (valor)
                </span>
              </div>
              <div className="col-span-3 sm:col-span-4">
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                  Acurácia
                </span>
              </div>
            </div>

            {/* Form Body */}
            <div className="flex-1 overflow-y-auto px-6 pb-2">
              {/* Pesos */}
              <div className="mb-4">
                <span className="text-[9px] font-bold text-violet-400/60 uppercase tracking-widest">
                  Pesos
                </span>
                {["pn", "pd", "pa", "ps", "pm"].map((key) => (
                  <MetricInput
                    key={key}
                    metricKey={key}
                    dep={formData[key]?.dep ?? ""}
                    acc={formData[key]?.acc ?? ""}
                    onDepChange={(v) => updateDep(key, v)}
                    onAccChange={(v) => updateAcc(key, v)}
                  />
                ))}
              </div>

              {/* Reprodução */}
              <div className="mb-4">
                <span className="text-[9px] font-bold text-violet-400/60 uppercase tracking-widest">
                  Reprodução
                </span>
                {["ipp", "stay", "pe365"].map((key) => (
                  <MetricInput
                    key={key}
                    metricKey={key}
                    dep={formData[key]?.dep ?? ""}
                    acc={formData[key]?.acc ?? ""}
                    onDepChange={(v) => updateDep(key, v)}
                    onAccChange={(v) => updateAcc(key, v)}
                  />
                ))}
              </div>

              {/* Carcaça */}
              <div className="mb-4">
                <span className="text-[9px] font-bold text-violet-400/60 uppercase tracking-widest">
                  Carcaça
                </span>
                {["aol", "acab", "mar"].map((key) => (
                  <MetricInput
                    key={key}
                    metricKey={key}
                    dep={formData[key]?.dep ?? ""}
                    acc={formData[key]?.acc ?? ""}
                    onDepChange={(v) => updateDep(key, v)}
                    onAccChange={(v) => updateAcc(key, v)}
                  />
                ))}
              </div>

              {/* Conformação */}
              <div className="mb-4">
                <span className="text-[9px] font-bold text-violet-400/60 uppercase tracking-widest">
                  Conformação
                </span>
                {["eg", "pg", "mg"].map((key) => (
                  <MetricInput
                    key={key}
                    metricKey={key}
                    dep={formData[key]?.dep ?? ""}
                    acc={formData[key]?.acc ?? ""}
                    onDepChange={(v) => updateDep(key, v)}
                    onAccChange={(v) => updateAcc(key, v)}
                  />
                ))}
              </div>

              {/* Notes */}
              <div className="mt-4">
                <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-2">
                  Observações
                </label>
                <textarea
                  value={notas}
                  onChange={(e) => setNotas(e.target.value)}
                  placeholder="Notas sobre os dados inseridos..."
                  rows={2}
                  className="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:border-violet-500/50 focus:ring-1 focus:ring-violet-500/20 transition-all resize-none"
                />
              </div>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between p-6 border-t border-white/[0.06]">
              <div className="flex items-center gap-2">
                {filledCount > 0 ? (
                  <span className="text-xs text-slate-400">
                    <span className="text-violet-400 font-bold">{filledCount}</span> de{" "}
                    {metricKeys.length} preenchidas
                  </span>
                ) : (
                  <span className="flex items-center gap-1.5 text-xs text-amber-400/60">
                    <ExclamationTriangleIcon className="w-3.5 h-3.5" />
                    Preencha ao menos uma métrica
                  </span>
                )}
              </div>

              <div className="flex gap-3">
                <button
                  onClick={onClose}
                  className="px-4 py-2.5 rounded-xl border border-white/10 text-sm text-slate-400 hover:text-white hover:bg-white/[0.04] transition-all"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleSave}
                  disabled={filledCount === 0 || saving || saved}
                  className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all ${
                    saved
                      ? "bg-emerald-500/20 border border-emerald-500/30 text-emerald-400"
                      : "bg-violet-500/20 border border-violet-500/30 text-violet-300 hover:bg-violet-500/30 disabled:opacity-40 disabled:cursor-not-allowed"
                  }`}
                >
                  {saved ? (
                    <>
                      <CheckIcon className="w-4 h-4" />
                      Salvo!
                    </>
                  ) : saving ? (
                    <>
                      <div className="w-4 h-4 border-2 border-violet-400/30 border-t-violet-400 rounded-full animate-spin" />
                      Salvando...
                    </>
                  ) : (
                    <>
                      <SparklesIcon className="w-4 h-4" />
                      Salvar Dados
                    </>
                  )}
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
