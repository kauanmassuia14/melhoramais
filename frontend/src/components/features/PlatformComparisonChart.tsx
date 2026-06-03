"use client";

import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from "recharts";
import {
  ChevronDownIcon,
  PencilSquareIcon,
  InformationCircleIcon,
} from "@heroicons/react/24/outline";
import {
  type AnimalComparisonData,
  type PlatformMetric,
  PLATFORM_COLORS,
  PLATFORM_LABELS,
  METRIC_LABELS,
} from "@/lib/mock-comparison-data";

interface PlatformComparisonChartProps {
  data: AnimalComparisonData;
  onOpenMelhoraForm?: () => void;
}

// ─── Custom Tooltip ──────────────────────────────────────────────────────────
function CustomTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  const item = payload[0]?.payload;
  if (!item) return null;

  return (
    <div className="rounded-xl border border-white/10 bg-slate-900/95 backdrop-blur-xl p-4 shadow-2xl min-w-[200px]">
      <div className="flex items-center gap-2 mb-3">
        <div
          className="w-3 h-3 rounded-full"
          style={{ backgroundColor: item.color }}
        />
        <span className="text-sm font-bold text-white">{item.label}</span>
      </div>
      <div className="space-y-2">
        <div className="flex justify-between">
          <span className="text-xs text-slate-400">DEP</span>
          <span className="text-sm font-bold text-white font-mono">
            {item.dep != null ? item.dep.toFixed(2) : "—"}
          </span>
        </div>
        {item.acc != null && (
          <div className="flex justify-between">
            <span className="text-xs text-slate-400">Acurácia</span>
            <span className="text-sm font-medium text-slate-300 font-mono">
              {item.acc}%
            </span>
          </div>
        )}
        {item.deca != null && (
          <div className="flex justify-between">
            <span className="text-xs text-slate-400">DECA/TOP</span>
            <span className="text-sm font-medium text-slate-300 font-mono">
              {item.deca}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Metric Selector Dropdown ────────────────────────────────────────────────
function MetricSelector({
  selected,
  options,
  onChange,
}: {
  selected: string;
  options: string[];
  onChange: (v: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const info = METRIC_LABELS[selected];

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-white/10 bg-white/[0.03] hover:bg-white/[0.06] transition-all text-sm"
      >
        <span className="text-white font-semibold">{info?.name}</span>
        <span className="text-slate-400 hidden sm:inline">
          — {info?.fullName}
        </span>
        <ChevronDownIcon
          className={`w-4 h-4 text-slate-400 transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -8, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.96 }}
            transition={{ duration: 0.15 }}
            className="absolute top-full left-0 mt-2 z-50 w-72 max-h-80 overflow-y-auto rounded-xl border border-white/10 bg-slate-900/98 backdrop-blur-xl shadow-2xl"
          >
            {options.map((key) => {
              const m = METRIC_LABELS[key];
              return (
                <button
                  key={key}
                  onClick={() => {
                    onChange(key);
                    setOpen(false);
                  }}
                  className={`w-full text-left px-4 py-3 flex items-center gap-3 hover:bg-white/[0.04] transition-colors ${
                    selected === key ? "bg-white/[0.06]" : ""
                  }`}
                >
                  <span
                    className={`text-xs font-bold font-mono w-10 ${
                      selected === key ? "text-cyan-400" : "text-slate-500"
                    }`}
                  >
                    {m?.name}
                  </span>
                  <span
                    className={`text-sm ${selected === key ? "text-white font-medium" : "text-slate-400"}`}
                  >
                    {m?.fullName}
                  </span>
                  {m?.unit && (
                    <span className="text-[10px] text-slate-600 ml-auto">
                      {m.unit}
                    </span>
                  )}
                </button>
              );
            })}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ─── Platform Value Cards ────────────────────────────────────────────────────
function PlatformValueCard({
  platform,
  metric,
  isMelhoraPlus,
  onOpenForm,
}: {
  platform: string;
  metric: PlatformMetric | null;
  isMelhoraPlus: boolean;
  onOpenForm?: () => void;
}) {
  const colors = PLATFORM_COLORS[platform];
  const label = PLATFORM_LABELS[platform];
  const hasDep = metric?.dep != null;

  return (
    <motion.div
      whileHover={{ y: -2, scale: 1.01 }}
      className={`rounded-xl border p-4 transition-all ${colors?.border} ${colors?.bg}`}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <div
            className="w-2.5 h-2.5 rounded-full"
            style={{ backgroundColor: colors?.primary }}
          />
          <span className={`text-xs font-bold uppercase tracking-wider ${colors?.text}`}>
            {label}
          </span>
        </div>
        {isMelhoraPlus && (
          <button
            onClick={onOpenForm}
            className="p-1 rounded-lg hover:bg-white/10 transition-colors"
            title="Inserir dados"
          >
            <PencilSquareIcon className="w-4 h-4 text-violet-400" />
          </button>
        )}
      </div>

      {hasDep ? (
        <div className="space-y-1.5">
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-bold text-white font-mono">
              {metric!.dep!.toFixed(2)}
            </span>
            <span className="text-xs text-slate-500">DEP</span>
          </div>
          <div className="flex gap-3 text-[11px]">
            {metric!.acc != null && (
              <span className="text-slate-400">
                AC: <span className="text-white font-medium">{metric!.acc}%</span>
              </span>
            )}
            {metric!.deca != null && (
              <span className="text-slate-400">
                DECA: <span className="text-white font-medium">{metric!.deca}</span>
              </span>
            )}
          </div>
        </div>
      ) : (
        <div className="flex flex-col items-center py-2">
          <span className="text-slate-600 text-sm">—</span>
          {isMelhoraPlus && (
            <button
              onClick={onOpenForm}
              className="mt-1 text-[10px] text-violet-400 hover:underline"
            >
              Inserir dados
            </button>
          )}
        </div>
      )}
    </motion.div>
  );
}

// ─── Main Component ──────────────────────────────────────────────────────────
export function PlatformComparisonChart({
  data,
  onOpenMelhoraForm,
}: PlatformComparisonChartProps) {
  const [selectedMetric, setSelectedMetric] = useState("pd");

  // Build chart data
  const chartData = useMemo(() => {
    const platformOrder = ["PMGZ", "ANCP", "GENEPLUS", "MELHORA_PLUS"];
    return platformOrder
      .map((key) => {
        const platform = data.platforms[key];
        const metric = platform?.metrics?.[selectedMetric];
        const colors = PLATFORM_COLORS[key];
        return {
          name: PLATFORM_LABELS[key],
          dep: metric?.dep ?? null,
          acc: metric?.acc ?? null,
          deca: metric?.deca ?? null,
          color: colors?.primary ?? "#666",
          label: PLATFORM_LABELS[key],
          platform: key,
        };
      })
      .filter((d) => d.dep != null);
  }, [data, selectedMetric]);

  // Calculate average for reference line
  const avgDep = useMemo(() => {
    const validDeps = chartData.filter((d) => d.dep != null).map((d) => d.dep!);
    if (validDeps.length === 0) return 0;
    return validDeps.reduce((a, b) => a + b, 0) / validDeps.length;
  }, [chartData]);

  const metricInfo = METRIC_LABELS[selectedMetric];
  const platformOrder = ["PMGZ", "ANCP", "GENEPLUS", "MELHORA_PLUS"];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500/20 to-violet-500/20 border border-white/10 flex items-center justify-center">
            <InformationCircleIcon className="w-5 h-5 text-cyan-400" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">
              Comparação DEP entre Plataformas
            </h3>
            <p className="text-[11px] text-slate-500">
              Selecione uma característica para comparar
            </p>
          </div>
        </div>

        <MetricSelector
          selected={selectedMetric}
          options={data.available_metrics}
          onChange={setSelectedMetric}
        />
      </div>

      {/* Chart */}
      <motion.div
        key={selectedMetric}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="h-72 w-full"
      >
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              margin={{ top: 20, right: 20, bottom: 20, left: 10 }}
              barCategoryGap="25%"
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="rgba(255,255,255,0.04)"
                vertical={false}
              />
              <XAxis
                dataKey="name"
                stroke="rgba(255,255,255,0.2)"
                tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 12, fontWeight: 600 }}
                axisLine={{ stroke: "rgba(255,255,255,0.06)" }}
              />
              <YAxis
                stroke="rgba(255,255,255,0.2)"
                tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }}
                axisLine={{ stroke: "rgba(255,255,255,0.06)" }}
                tickFormatter={(v) => `${v}`}
                label={{
                  value: metricInfo?.unit || "DEP",
                  angle: -90,
                  position: "insideLeft",
                  style: { fill: "rgba(255,255,255,0.3)", fontSize: 11 },
                }}
              />
              <Tooltip
                content={<CustomTooltip />}
                cursor={{ fill: "rgba(255,255,255,0.02)" }}
              />
              <ReferenceLine
                y={avgDep}
                stroke="rgba(255,255,255,0.15)"
                strokeDasharray="4 4"
                label={{
                  value: `Média: ${avgDep.toFixed(2)}`,
                  position: "right",
                  style: { fill: "rgba(255,255,255,0.3)", fontSize: 10 },
                }}
              />
              <Bar dataKey="dep" radius={[8, 8, 0, 0]} maxBarSize={64}>
                {chartData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.color}
                    fillOpacity={0.85}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-full flex items-center justify-center">
            <p className="text-sm text-slate-500">
              Nenhuma plataforma possui dados para{" "}
              <span className="text-white font-medium">{metricInfo?.fullName}</span>
            </p>
          </div>
        )}
      </motion.div>

      {/* Platform Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {platformOrder.map((key) => {
          const platform = data.platforms[key];
          const metric = platform?.metrics?.[selectedMetric] ?? null;
          return (
            <PlatformValueCard
              key={key}
              platform={key}
              metric={metric}
              isMelhoraPlus={key === "MELHORA_PLUS"}
              onOpenForm={onOpenMelhoraForm}
            />
          );
        })}
      </div>
    </div>
  );
}
