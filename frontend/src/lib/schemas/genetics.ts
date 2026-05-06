import { z } from 'zod';

// ============================================
// ENUMS
// ============================================

export const AnimalSexEnum = z.enum(['M', 'F']);
export type AnimalSex = z.infer<typeof AnimalSexEnum>;

export const BooleanStatusEnum = z.enum(['SIM', 'NÃO']);
export type BooleanStatus = z.infer<typeof BooleanStatusEnum>;

export const FonteOrigemEnum = z.enum(['PMGZ', 'ANCP', 'GENEPLUS']);
export type FonteOrigem = z.infer<typeof FonteOrigemEnum>;

// ============================================
// COMPOSITE TYPES (como objetos TypeScript)
// ============================================

export const MetricBlockSchema = z.object({
  dep: z.number().nullable(),
  ac: z.number().nullable(),
  deca: z.number().nullable(),
  p_percent: z.number().nullable(),
});
export type MetricBlock = z.infer<typeof MetricBlockSchema>;

export const ProgenyInfoSchema = z.object({
  filhos: z.number().nullable(),
  rebanhos: z.number().nullable(),
});
export type ProgenyInfo = z.infer<typeof ProgenyInfoSchema>;

// ============================================
// ANIMAL
// ============================================

export const AnimalSchema = z.object({
  id: z.string().uuid(),
  nome: z.string().nullable(),
  serie: z.string().nullable(),
  rgn: z.string(),
  sexo: AnimalSexEnum,
  nascimento: z.string().date().nullable(),
  genotipado: BooleanStatusEnum.nullable(),
  csg: BooleanStatusEnum.nullable(),
  sire_id: z.string().uuid().nullable(),
  dam_id: z.string().uuid().nullable(),
  created_at: z.string().datetime().optional(),
  updated_at: z.string().datetime().optional(),
});

export type Animal = z.infer<typeof AnimalSchema>;

export const AnimalCreateSchema = AnimalSchema.omit({
  id: true,
  created_at: true,
  updated_at: true,
}).partial({
  nome: true,
  serie: true,
  nascimento: true,
  genotipado: true,
  csg: true,
  sire_id: true,
  dam_id: true,
});

export type AnimalCreate = z.infer<typeof AnimalCreateSchema>;

export const AnimalUpdateSchema = AnimalCreateSchema;
export type AnimalUpdate = z.infer<typeof AnimalUpdateSchema>;

// ============================================
// GENETIC EVALUATION
// ============================================

export const GeneticEvaluationSchema = z.object({
  id: z.string().uuid(),
  animal_id: z.string().uuid(),
  safra: z.number(),
  fonte_origem: FonteOrigemEnum,

  // Campos globais de avaliação
  iabczg: z.number().nullable(),
  deca_index: z.number().nullable(),

  // Crescimento (metric_block)
  pn_ed: MetricBlockSchema,
  pd_ed: MetricBlockSchema,
  pa_ed: MetricBlockSchema,
  ps_ed: MetricBlockSchema,
  pm_em: MetricBlockSchema,

  // Reprodutivas/Maternas (metric_block)
  ipp: MetricBlockSchema,
  stay: MetricBlockSchema,
  pe_365: MetricBlockSchema,
  psn: MetricBlockSchema,

  // Carcaça (metric_block)
  aol: MetricBlockSchema,
  acab: MetricBlockSchema,
  marmoreio: MetricBlockSchema,

  // Morfológicas (metric_block)
  eg: MetricBlockSchema,
  pg: MetricBlockSchema,
  mg: MetricBlockSchema,

  // Medidas Fenotípicas (NUMERIC simples)
  fenotipo_aol: z.number().nullable(),
  fenotipo_acab: z.number().nullable(),
  fenotipo_ipp: z.number().nullable(),
  fenotipo_stay: z.number().nullable(),

  // Informações de Descendentes (progeny_info)
  p120_info: ProgenyInfoSchema,
  p210_info: ProgenyInfoSchema,
  p365_info: ProgenyInfoSchema,
  p450_info: ProgenyInfoSchema,

  created_at: z.string().datetime().optional(),
  updated_at: z.string().datetime().optional(),
});

export type GeneticEvaluation = z.infer<typeof GeneticEvaluationSchema>;

export const GeneticEvaluationCreateSchema = GeneticEvaluationSchema.omit({
  id: true,
  created_at: true,
  updated_at: true,
}).partial({
  iabczg: true,
  deca_index: true,
  pn_ed: true,
  pd_ed: true,
  pa_ed: true,
  ps_ed: true,
  pm_em: true,
  ipp: true,
  stay: true,
  pe_365: true,
  psn: true,
  aol: true,
  acab: true,
  marmoreio: true,
  eg: true,
  pg: true,
  mg: true,
  fenotipo_aol: true,
  fenotipo_acab: true,
  fenotipo_ipp: true,
  fenotipo_stay: true,
  p120_info: true,
  p210_info: true,
  p365_info: true,
  p450_info: true,
});

export type GeneticEvaluationCreate = z.infer<typeof GeneticEvaluationCreateSchema>;

export const GeneticEvaluationUpdateSchema = GeneticEvaluationCreateSchema;
export type GeneticEvaluationUpdate = z.infer<typeof GeneticEvaluationUpdateSchema>;

// ============================================
// EVALUATION PROGENY HISTORY
// ============================================

export const EvaluationProgenyHistorySchema = z.object({
  id: z.string().uuid(),
  evaluation_id: z.string().uuid(),
  periodo: z.enum(['P120', 'P210', 'P365', 'P450']),
  filhos: z.number().nullable(),
  rebanhos: z.number().nullable(),
  netos: z.number().nullable(),
  neto_rebanhos: z.number().nullable(),
  created_at: z.string().datetime().optional(),
});

export type EvaluationProgenyHistory = z.infer<typeof EvaluationProgenyHistorySchema>;

// ============================================
// VIEW: Animals with Evaluations
// ============================================

export const AnimalWithEvaluationsSchema = z.object({
  id: z.string().uuid(),
  nome: z.string().nullable(),
  serie: z.string().nullable(),
  rgn: z.string(),
  sexo: AnimalSexEnum,
  nascimento: z.string().date().nullable(),
  genotipado: BooleanStatusEnum.nullable(),
  csg: BooleanStatusEnum.nullable(),
  genotipado_csg: BooleanStatusEnum.nullable(),
  sire_id: z.string().uuid().nullable(),
  dam_id: z.string().uuid().nullable(),
  sire_nome: z.string().nullable(),
  sire_rgn: z.string().nullable(),
  dam_nome: z.string().nullable(),
  dam_rgn: z.string().nullable(),
  total_evaluations: z.number(),
  ultima_safra: z.number().nullable(),
  ultimo_iabczg: z.number().nullable(),
});

export type AnimalWithEvaluations = z.infer<typeof AnimalWithEvaluationsSchema>;

// ============================================
// FILTERS / QUERY PARAMS
// ============================================

export const AnimalFilterSchema = z.object({
  search: z.string().optional(),
  sexo: AnimalSexEnum.optional(),
  rgn: z.string().optional(),
  limit: z.number().min(1).max(500).default(50),
  offset: z.number().min(0).default(0),
});

export type AnimalFilter = z.infer<typeof AnimalFilterSchema>;

export const EvaluationFilterSchema = z.object({
  animal_id: z.string().uuid().optional(),
  safra: z.number().optional(),
  fonte_origem: FonteOrigemEnum.optional(),
  limit: z.number().min(1).max(500).default(50),
  offset: z.number().min(0).default(0),
});

export type EvaluationFilter = z.infer<typeof EvaluationFilterSchema>;

// ============================================
// API RESPONSE TYPES
// ============================================

export const AnimalResponseSchema = z.object({
  data: Animal,
  message: z.string().optional(),
});

export const AnimalListResponseSchema = z.object({
  data: z.array(Animal),
  total: z.number(),
  limit: z.number(),
  offset: z.number(),
});

export const EvaluationResponseSchema = z.object({
  data: GeneticEvaluation,
  message: z.string().optional(),
});

export const EvaluationListResponseSchema = z.object({
  data: z.array(GeneticEvaluation),
  total: z.number(),
  limit: z.number(),
  offset: z.number(),
});

// ============================================
// UTILITY: Converter metric_block para display
// ============================================

export function formatMetricBlock(metric: MetricBlock | null): string {
  if (!metric) return '-';
  const parts: string[] = [];
  if (metric.dep !== null) parts.push(`DEP: ${metric.dep.toFixed(2)}`);
  if (metric.ac !== null) parts.push(`AC: ${metric.ac}%`);
  if (metric.deca !== null) parts.push(`DECA: ${metric.deca}`);
  if (metric.p_percent !== null) parts.push(`P%: ${metric.p_percent}%`);
  return parts.join(' | ') || '-';
}

export function formatProgenyInfo(info: ProgenyInfo | null): string {
  if (!info || (info.filhos === null && info.rebanhos === null)) return '-';
  const parts: string[] = [];
  if (info.filhos !== null) parts.push(`${info.filhos} filhos`);
  if (info.rebanhos !== null) parts.push(`${info.rebanhos} rebanhos`);
  return parts.join(' | ');
}