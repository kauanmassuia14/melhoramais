// ─── Mock Data: Comparação de Plataformas Genéticas ──────────────────────────
// Dados realistas que simulam a resposta dos endpoints que serão criados na Fase 2.
// Quando o backend estiver pronto, estes mocks serão substituídos por chamadas reais.

export interface PlatformMetric {
  dep: number | null;
  acc: number | null;
  deca: number | null;
  p_percent: number | null;
}

export interface PlatformData {
  fonte: string;
  safra: number;
  indice_principal: number | null;
  rank: number | null;
  metrics: Record<string, PlatformMetric>;
}

export interface AnimalComparisonData {
  animal: { id: string; rgn: string; nome: string };
  platforms: Record<string, PlatformData | null>;
  available_metrics: string[];
}

export interface DashboardPlatformData {
  metrics: string[];
  platforms: Record<string, {
    total_animals: number;
    averages: Record<string, { avg: number; min: number; max: number }>;
  }>;
}

// ─── Nomes amigáveis das métricas ────────────────────────────────────────────
export const METRIC_LABELS: Record<string, { name: string; unit: string; fullName: string }> = {
  pn:    { name: "PN",     unit: "kg",    fullName: "Peso Nascimento" },
  pd:    { name: "PD",     unit: "kg",    fullName: "Peso Desmama" },
  pa:    { name: "PA",     unit: "kg",    fullName: "Peso Ano" },
  ps:    { name: "PS",     unit: "kg",    fullName: "Peso Sobreano" },
  pm:    { name: "PM",     unit: "kg",    fullName: "Peso Materno" },
  ipp:   { name: "IPP",    unit: "dias",  fullName: "Idade 1º Parto" },
  stay:  { name: "STAY",   unit: "%",     fullName: "Stayability" },
  pe365: { name: "PE365",  unit: "cm",    fullName: "Perímetro Escrotal" },
  aol:   { name: "AOL",    unit: "cm²",   fullName: "Área Olho Lombo" },
  acab:  { name: "ACAB",   unit: "mm",    fullName: "Acabamento" },
  mar:   { name: "MAR",    unit: "",      fullName: "Marmoreio" },
  eg:    { name: "EG",     unit: "pts",   fullName: "Estrutura Corporal" },
  pg:    { name: "PG",     unit: "pts",   fullName: "Precocidade" },
  mg:    { name: "MG",     unit: "pts",   fullName: "Musculosidade" },
};

// ─── Cores por plataforma ────────────────────────────────────────────────────
export const PLATFORM_COLORS: Record<string, { primary: string; bg: string; border: string; fill: string; text: string }> = {
  PMGZ:         { primary: "#22d3ee", bg: "bg-cyan-500/10",    border: "border-cyan-500/30",    fill: "#22d3ee", text: "text-cyan-400" },
  pmgz:         { primary: "#22d3ee", bg: "bg-cyan-500/10",    border: "border-cyan-500/30",    fill: "#22d3ee", text: "text-cyan-400" },
  ANCP:         { primary: "#34d399", bg: "bg-emerald-500/10", border: "border-emerald-500/30", fill: "#34d399", text: "text-emerald-400" },
  ancp:         { primary: "#34d399", bg: "bg-emerald-500/10", border: "border-emerald-500/30", fill: "#34d399", text: "text-emerald-400" },
  GENEPLUS:     { primary: "#fbbf24", bg: "bg-amber-500/10",   border: "border-amber-500/30",   fill: "#fbbf24", text: "text-amber-400" },
  Geneplus:     { primary: "#fbbf24", bg: "bg-amber-500/10",   border: "border-amber-500/30",   fill: "#fbbf24", text: "text-amber-400" },
  geneplus:     { primary: "#fbbf24", bg: "bg-amber-500/10",   border: "border-amber-500/30",   fill: "#fbbf24", text: "text-amber-400" },
  MELHORA_PLUS: { primary: "#a78bfa", bg: "bg-violet-500/10",  border: "border-violet-500/30",  fill: "#a78bfa", text: "text-violet-400" },
  melhora_plus: { primary: "#a78bfa", bg: "bg-violet-500/10",  border: "border-violet-500/30",  fill: "#a78bfa", text: "text-violet-400" },
};

export const PLATFORM_LABELS: Record<string, string> = {
  PMGZ: "PMGZ",
  pmgz: "PMGZ",
  ANCP: "ANCP",
  ancp: "ANCP",
  GENEPLUS: "Geneplus",
  Geneplus: "Geneplus",
  geneplus: "Geneplus",
  MELHORA_PLUS: "Melhora+",
  melhora_plus: "Melhora+",
};

// ─── Mock: Comparação de um animal específico ────────────────────────────────
export const MOCK_ANIMAL_COMPARISON: AnimalComparisonData = {
  animal: { id: "mock-uuid-001", rgn: "ABC1234", nome: "TORO ELITE JR" },
  platforms: {
    PMGZ: {
      fonte: "PMGZ",
      safra: 2026,
      indice_principal: 14.82,
      rank: 3,
      metrics: {
        pn:    { dep: 0.87,  acc: 42, deca: 3,  p_percent: 2.5 },
        pd:    { dep: 15.20, acc: 51, deca: 2,  p_percent: 8.3 },
        pa:    { dep: 18.40, acc: 38, deca: 4,  p_percent: 15.0 },
        ps:    { dep: 22.10, acc: 45, deca: 2,  p_percent: 6.1 },
        pm:    { dep: 8.30,  acc: 36, deca: 5,  p_percent: 22.0 },
        ipp:   { dep: -4.20, acc: 28, deca: 4,  p_percent: 18.0 },
        stay:  { dep: 6.80,  acc: 22, deca: 3,  p_percent: 12.5 },
        pe365: { dep: 1.42,  acc: 55, deca: 2,  p_percent: 5.0 },
        aol:   { dep: 0.65,  acc: 30, deca: 4,  p_percent: 20.0 },
        acab:  { dep: 0.18,  acc: 25, deca: 5,  p_percent: 30.0 },
        mar:   { dep: 0.08,  acc: 20, deca: 6,  p_percent: 40.0 },
        eg:    { dep: 0.45,  acc: 32, deca: 3,  p_percent: 10.0 },
        pg:    { dep: 0.52,  acc: 35, deca: 2,  p_percent: 7.0 },
        mg:    { dep: 0.38,  acc: 30, deca: 4,  p_percent: 18.0 },
      },
    },
    ANCP: {
      fonte: "ANCP",
      safra: 2026,
      indice_principal: 126.40,
      rank: null,
      metrics: {
        pn:    { dep: 0.92,  acc: 38, deca: null, p_percent: null },
        pd:    { dep: 13.80, acc: 47, deca: null, p_percent: null },
        pa:    { dep: 16.50, acc: 35, deca: null, p_percent: null },
        ps:    { dep: 20.40, acc: 41, deca: null, p_percent: null },
        pm:    { dep: 7.60,  acc: 30, deca: null, p_percent: null },
        ipp:   { dep: -5.10, acc: 25, deca: null, p_percent: null },
        stay:  { dep: 5.90,  acc: 18, deca: null, p_percent: null },
        pe365: { dep: 1.28,  acc: 50, deca: null, p_percent: null },
        aol:   { dep: 0.58,  acc: 26, deca: null, p_percent: null },
        acab:  { dep: 0.22,  acc: 22, deca: null, p_percent: null },
        mar:   { dep: 0.06,  acc: 16, deca: null, p_percent: null },
        eg:    { dep: null,  acc: null, deca: null, p_percent: null },
        pg:    { dep: null,  acc: null, deca: null, p_percent: null },
        mg:    { dep: null,  acc: null, deca: null, p_percent: null },
      },
    },
    GENEPLUS: {
      fonte: "GENEPLUS",
      safra: 2026,
      indice_principal: 98.70,
      rank: null,
      metrics: {
        pn:    { dep: 0.78,  acc: 35, deca: null, p_percent: null },
        pd:    { dep: 12.40, acc: 42, deca: null, p_percent: null },
        pa:    { dep: null,  acc: null, deca: null, p_percent: null },
        ps:    { dep: 19.80, acc: 38, deca: null, p_percent: null },
        pm:    { dep: 6.90,  acc: 28, deca: null, p_percent: null },
        ipp:   { dep: -3.80, acc: 22, deca: null, p_percent: null },
        stay:  { dep: 7.20,  acc: 20, deca: null, p_percent: null },
        pe365: { dep: null,  acc: null, deca: null, p_percent: null },
        aol:   { dep: 0.72,  acc: 28, deca: null, p_percent: null },
        acab:  { dep: 0.15,  acc: 20, deca: null, p_percent: null },
        mar:   { dep: null,  acc: null, deca: null, p_percent: null },
        eg:    { dep: null,  acc: null, deca: null, p_percent: null },
        pg:    { dep: null,  acc: null, deca: null, p_percent: null },
        mg:    { dep: null,  acc: null, deca: null, p_percent: null },
      },
    },
    MELHORA_PLUS: null, // sem dados manuais inseridos ainda
  },
  available_metrics: ["pn", "pd", "pa", "ps", "pm", "ipp", "stay", "pe365", "aol", "acab", "mar", "eg", "pg", "mg"],
};

// ─── Mock: Visão geral do dashboard ──────────────────────────────────────────
export const MOCK_PLATFORM_OVERVIEW: DashboardPlatformData = {
  metrics: ["pn", "pd", "ps", "pm", "ipp", "stay", "pe365", "aol", "acab", "mar"],
  platforms: {
    PMGZ: {
      total_animals: 152,
      averages: {
        pn:    { avg: 0.72,  min: -1.80, max: 3.20 },
        pd:    { avg: 11.80, min: -4.50, max: 28.60 },
        ps:    { avg: 18.40, min: -6.20, max: 38.90 },
        pm:    { avg: 6.50,  min: -2.10, max: 15.40 },
        ipp:   { avg: -3.20, min: -12.50, max: 4.80 },
        stay:  { avg: 5.40,  min: -1.80, max: 14.20 },
        pe365: { avg: 1.15,  min: -0.80, max: 3.60 },
        aol:   { avg: 0.48,  min: -0.30, max: 1.80 },
        acab:  { avg: 0.14,  min: -0.10, max: 0.65 },
        mar:   { avg: 0.05,  min: -0.02, max: 0.18 },
      },
    },
    ANCP: {
      total_animals: 89,
      averages: {
        pn:    { avg: 0.65,  min: -2.10, max: 2.80 },
        pd:    { avg: 10.20, min: -5.80, max: 25.40 },
        ps:    { avg: 16.80, min: -7.40, max: 35.20 },
        pm:    { avg: 5.80,  min: -3.20, max: 14.00 },
        ipp:   { avg: -2.80, min: -10.20, max: 5.40 },
        stay:  { avg: 4.60,  min: -2.50, max: 12.80 },
        pe365: { avg: 1.02,  min: -1.10, max: 3.20 },
        aol:   { avg: 0.42,  min: -0.40, max: 1.60 },
        acab:  { avg: 0.16,  min: -0.12, max: 0.58 },
        mar:   { avg: 0.04,  min: -0.03, max: 0.15 },
      },
    },
    GENEPLUS: {
      total_animals: 47,
      averages: {
        pn:    { avg: 0.58,  min: -1.50, max: 2.40 },
        pd:    { avg: 9.80,  min: -3.60, max: 22.10 },
        ps:    { avg: 15.90, min: -5.80, max: 32.40 },
        pm:    { avg: 5.20,  min: -2.80, max: 12.60 },
        ipp:   { avg: -2.40, min: -9.80, max: 4.20 },
        stay:  { avg: 5.10,  min: -1.60, max: 13.40 },
        pe365: { avg: 0.95,  min: -0.90, max: 2.80 },
        aol:   { avg: 0.55,  min: -0.20, max: 1.90 },
        acab:  { avg: 0.12,  min: -0.08, max: 0.50 },
        mar:   { avg: 0.03,  min: -0.01, max: 0.12 },
      },
    },
  },
};
