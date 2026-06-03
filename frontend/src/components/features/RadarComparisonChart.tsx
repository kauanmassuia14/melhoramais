"use client";

import { useState, useMemo } from "react";
import { motion } from "framer-motion";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from "recharts";
import {
  type AnimalComparisonData,
  PLATFORM_COLORS,
  PLATFORM_LABELS,
  METRIC_LABELS,
} from "@/lib/mock-comparison-data";

interface RadarComparisonChartProps {
  data: AnimalComparisonData;
}

// ─── Custom Tooltip ──────────────────────────────────────────────────────────
function CustomRadarTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;

  return (
    <div className="rounded-xl border border-white/10 bg-slate-900/95 backdrop-blur-xl p-3 shadow-2xl min-w-[180px]">
      <p className="text-xs font-bold text-white mb-2">
        {METRIC_LABELS[label]?.fullName || label}
      </p>
      <div className="space-y-1.5">
        {payload.map((entry: any) => (
          <div key={entry.dataKey} className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-1.5">
              <div
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: entry.color }}
              />
              <span className="text-[11px] text-slate-400">{entry.name}</span>
            </div>
            <span className="text-xs font-bold text-white font-mono">
              {entry.value != null ? entry.value.toFixed(1) : "—"}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Custom Legend ────────────────────────────────────────────────────────────
function CustomLegend({
  platforms,
  visible,
  onToggle,
}: {
  platforms: string[];
  visible: Set<string>;
  onToggle: (key: string) => void;
}) {
  return (
    <div className="flex flex-wrap justify-center gap-3 mt-4">
      {platforms.map((key) => {
        const colors = PLATFORM_COLORS[key];
        const isVisible = visible.has(key);
        return (
          <button
            key={key}
            onClick={() => onToggle(key)}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-medium transition-all ${
              isVisible
                ? `${colors?.border} ${colors?.bg} text-white`
                : "border-white/5 bg-transparent text-slate-600 hover:text-slate-400"
            }`}
          >
            <div
              className={`w-2 h-2 rounded-full transition-opacity ${isVisible ? "opacity-100" : "opacity-30"}`}
              style={{ backgroundColor: colors?.primary }}
            />
            {PLATFORM_LABELS[key]}
          </button>
        );
      })}
    </div>
  );
}

// ─── Main Component ──────────────────────────────────────────────────────────
export function RadarComparisonChart({ data }: RadarComparisonChartProps) {
  const platformKeys = Object.keys(data.platforms).filter(
    (k) => data.platforms[k] != null
  );
  const [visiblePlatforms, setVisiblePlatforms] = useState<Set<string>>(
    new Set(platformKeys)
  );

  const togglePlatform = (key: string) => {
    setVisiblePlatforms((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        if (next.size > 1) next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  };

  // Build radar data — normalize DEPs to 0-100 scale for fair comparison
  const radarData = useMemo(() => {
    // Find min/max DEP per metric across all platforms to normalize
    const ranges: Record<string, { min: number; max: number }> = {};

    // First pass: collect all DEP values per metric
    data.available_metrics.forEach((metricKey) => {
      const deps: number[] = [];
      Object.values(data.platforms).forEach((platform) => {
        if (platform?.metrics?.[metricKey]?.dep != null) {
          deps.push(platform.metrics[metricKey].dep!);
        }
      });
      if (deps.length > 0) {
        const min = Math.min(...deps);
        const max = Math.max(...deps);
        // Add some padding
        const pad = Math.max((max - min) * 0.1, 0.1);
        ranges[metricKey] = { min: min - pad, max: max + pad };
      }
    });

    // Second pass: build normalized radar data
    return data.available_metrics
      .filter((key) => ranges[key])
      .map((metricKey) => {
        const label = METRIC_LABELS[metricKey]?.name || metricKey;
        const range = ranges[metricKey];
        const row: any = { metric: label, metricKey };

        Object.keys(data.platforms).forEach((platformKey) => {
          const platform = data.platforms[platformKey];
          const dep = platform?.metrics?.[metricKey]?.dep;
          if (dep != null && range.max !== range.min) {
            // Normalize to 0-100 scale
            row[platformKey] = Math.round(
              ((dep - range.min) / (range.max - range.min)) * 100
            );
          } else {
            row[platformKey] = null;
          }
        });

        return row;
      });
  }, [data]);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4 }}
      className="space-y-4"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-white">Radar Comparativo</h3>
          <p className="text-[11px] text-slate-500">
            Valores normalizados (0–100) para comparação visual
          </p>
        </div>
      </div>

      {/* Radar Chart */}
      <div className="h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart
            cx="50%"
            cy="50%"
            outerRadius="72%"
            data={radarData}
          >
            <PolarGrid
              stroke="rgba(255,255,255,0.06)"
              gridType="polygon"
            />
            <PolarAngleAxis
              dataKey="metric"
              tick={{
                fill: "rgba(255,255,255,0.5)",
                fontSize: 10,
                fontWeight: 600,
              }}
            />
            <PolarRadiusAxis
              angle={90}
              domain={[0, 100]}
              tick={{ fill: "rgba(255,255,255,0.2)", fontSize: 9 }}
              axisLine={false}
            />
            <Tooltip content={<CustomRadarTooltip />} />

            {platformKeys.map((key) => {
              const colors = PLATFORM_COLORS[key];
              if (!visiblePlatforms.has(key)) return null;
              return (
                <Radar
                  key={key}
                  name={PLATFORM_LABELS[key]}
                  dataKey={key}
                  stroke={colors?.primary}
                  fill={colors?.primary}
                  fillOpacity={0.08}
                  strokeWidth={2}
                  dot={{
                    r: 3,
                    fill: colors?.primary,
                    fillOpacity: 1,
                    strokeWidth: 0,
                  }}
                  activeDot={{
                    r: 5,
                    fill: colors?.primary,
                    strokeWidth: 2,
                    stroke: "#fff",
                  }}
                  connectNulls
                />
              );
            })}
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* Legend with toggles */}
      <CustomLegend
        platforms={[...platformKeys, ...(!platformKeys.includes("MELHORA_PLUS") ? ["MELHORA_PLUS"] : [])]}
        visible={visiblePlatforms}
        onToggle={togglePlatform}
      />
    </motion.div>
  );
}
