"use client";

import { useState, useMemo } from "react";
import { motion } from "framer-motion";
import {
  BarChart,
  Bar,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import {
  ChevronDownIcon,
  ArrowRightIcon,
  BuildingOffice2Icon,
} from "@heroicons/react/24/outline";
import Link from "next/link";
import {
  type DashboardPlatformData,
  PLATFORM_COLORS,
  PLATFORM_LABELS,
  METRIC_LABELS,
} from "@/lib/mock-comparison-data";

interface DashboardPlatformChartProps {
  data: DashboardPlatformData;
}

// ─── Custom Tooltip ──────────────────────────────────────────────────────────
function DashTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;

  return (
    <div className="rounded-xl border border-white/10 bg-slate-900/95 backdrop-blur-xl p-3 shadow-2xl min-w-[180px]">
      {payload.map((entry: any) => (
        <div
          key={entry.dataKey}
          className="flex items-center justify-between gap-4 py-1"
        >
          <div className="flex items-center gap-2">
            <div
              className="w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: entry.fill }}
            />
            <span className="text-xs text-slate-300">{entry.name}</span>
          </div>
          <span className="text-sm font-bold text-white font-mono">
            {entry.value?.toFixed(2)}
          </span>
        </div>
      ))}
    </div>
  );
}

// ─── Main Component ──────────────────────────────────────────────────────────
export function DashboardPlatformChart({
  data,
}: DashboardPlatformChartProps) {
  const [selectedMetric, setSelectedMetric] = useState("pd");
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const metricInfo = METRIC_LABELS[selectedMetric];
  const platformKeys = Object.keys(data.platforms);

  // Build chart data for grouped bars
  const chartData = useMemo(() => {
    return platformKeys.map((key) => {
      const platform = data.platforms[key];
      const avg = platform?.averages?.[selectedMetric]?.avg ?? null;
      return {
        name: PLATFORM_LABELS[key] || key,
        avg: avg,
        color: PLATFORM_COLORS[key]?.primary ?? "#666",
        platform: key,
        min: platform?.averages?.[selectedMetric]?.min ?? null,
        max: platform?.averages?.[selectedMetric]?.max ?? null,
      };
    });
  }, [data, selectedMetric, platformKeys]);

  // Global average
  const globalAvg = useMemo(() => {
    const vals = chartData.filter((d) => d.avg != null).map((d) => d.avg!);
    return vals.length > 0 ? vals.reduce((a, b) => a + b, 0) / vals.length : 0;
  }, [chartData]);

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-lg font-bold text-white">
            Plataformas Genéticas
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Média DEP por plataforma na sua fazenda
          </p>
        </div>

        {/* Metric Dropdown */}
        <div className="relative">
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-2 px-3 py-2 rounded-xl border border-white/10 bg-white/[0.03] hover:bg-white/[0.06] transition-all text-sm"
          >
            <span className="text-cyan-400 font-bold text-xs font-mono">
              {metricInfo?.name}
            </span>
            <ChevronDownIcon
              className={`w-3.5 h-3.5 text-slate-400 transition-transform ${dropdownOpen ? "rotate-180" : ""}`}
            />
          </button>

          {dropdownOpen && (
            <motion.div
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              className="absolute top-full right-0 mt-1 z-50 w-56 max-h-64 overflow-y-auto rounded-xl border border-white/10 bg-slate-900/98 backdrop-blur-xl shadow-2xl"
            >
              {data.metrics.map((key) => {
                const m = METRIC_LABELS[key];
                return (
                  <button
                    key={key}
                    onClick={() => {
                      setSelectedMetric(key);
                      setDropdownOpen(false);
                    }}
                    className={`w-full text-left px-3 py-2.5 flex items-center gap-2 hover:bg-white/[0.04] transition-colors text-xs ${
                      selectedMetric === key
                        ? "bg-white/[0.06] text-cyan-400"
                        : "text-slate-400"
                    }`}
                  >
                    <span className="font-bold font-mono w-8">{m?.name}</span>
                    <span>{m?.fullName}</span>
                  </button>
                );
              })}
            </motion.div>
          )}
        </div>
      </div>

      {/* Chart */}
      <motion.div
        key={selectedMetric}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="h-56"
      >
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            margin={{ top: 10, right: 10, bottom: 10, left: 0 }}
            barCategoryGap="20%"
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgba(255,255,255,0.04)"
              vertical={false}
            />
            <XAxis
              dataKey="name"
              stroke="rgba(255,255,255,0.15)"
              tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 11, fontWeight: 600 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              stroke="rgba(255,255,255,0.15)"
              tick={{ fill: "rgba(255,255,255,0.3)", fontSize: 10 }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip content={<DashTooltip />} cursor={{ fill: "rgba(255,255,255,0.02)" }} />
            <ReferenceLine
              y={globalAvg}
              stroke="rgba(255,255,255,0.12)"
              strokeDasharray="4 4"
            />
            <Bar
              dataKey="avg"
              name="Média DEP"
              radius={[6, 6, 0, 0]}
              maxBarSize={56}
            >
              {chartData.map((entry, i) => (
                <Cell
                  key={`bar-${i}`}
                  fill={entry.color}
                  fillOpacity={0.85}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </motion.div>

      {/* Platform badges */}
      <div className="flex flex-wrap gap-2">
        {platformKeys.map((key) => {
          const colors = PLATFORM_COLORS[key];
          const platform = data.platforms[key];
          return (
            <div
              key={key}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border ${colors?.border} ${colors?.bg}`}
            >
              <BuildingOffice2Icon className={`w-3.5 h-3.5 ${colors?.text}`} />
              <span className="text-[11px] text-slate-300 font-medium">
                {PLATFORM_LABELS[key]}
              </span>
              <span className={`text-[11px] font-bold ${colors?.text}`}>
                {platform?.total_animals ?? 0}
              </span>
            </div>
          );
        })}
      </div>

      {/* Link */}
      <Link
        href="/analytics"
        className="flex items-center gap-1.5 text-xs text-cyan-400 hover:text-cyan-300 transition-colors font-medium group"
      >
        Ver análise completa
        <ArrowRightIcon className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
      </Link>
    </div>
  );
}
