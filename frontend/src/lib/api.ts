const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface DashboardStats {
  total_animals: number;
  total_farms: number;
  animals_by_source: Record<string, number>;
  animals_by_sex: Record<string, number>;
  recent_uploads: number;
  avg_p210: number | null;
  avg_p365: number | null;
  avg_p450: number | null;
}

export interface ProcessingLog {
  id: number;
  id_farm: number;
  source_system: string;
  filename: string | null;
  total_rows: number;
  rows_inserted: number;
  rows_updated: number;
  rows_failed: number;
  status: string;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface Animal {
  id_animal: number;
  id_farm: number;
  rgn_animal: string;
  nome_animal: string | null;
  raca: string | null;
  sexo: string | null;
  data_nascimento: string | null;
  p210_peso_desmama: number | null;
  p365_peso_ano: number | null;
  p450_peso_sobreano: number | null;
  fonte_origem: string | null;
}

export interface ColumnMapping {
  id: number;
  source_system: string;
  source_column: string;
  target_column: string;
  data_type: string;
  is_required: boolean;
}

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(err.detail || `API error: ${res.status}`);
  }
  return res.json();
}

export const api = {
  // Stats
  getStats: (farmId?: number) =>
    fetchApi<DashboardStats>(`/stats${farmId ? `?farm_id=${farmId}` : ''}`),

  // Logs
  getLogs: (farmId?: number, source?: string, limit = 50) => {
    const params = new URLSearchParams();
    if (farmId) params.set('farm_id', String(farmId));
    if (source) params.set('source_system', source);
    params.set('limit', String(limit));
    return fetchApi<ProcessingLog[]>(`/logs?${params.toString()}`);
  },

  // Animals
  getAnimals: (opts?: { farmId?: number; source?: string; limit?: number; offset?: number }) => {
    const params = new URLSearchParams();
    if (opts?.farmId) params.set('farm_id', String(opts.farmId));
    if (opts?.source) params.set('source', opts.source);
    params.set('limit', String(opts?.limit || 50));
    params.set('offset', String(opts?.offset || 0));
    return fetchApi<Animal[]>(`/animals?${params.toString()}`);
  },

  // Mappings
  getMappings: (sourceSystem?: string) =>
    fetchApi<ColumnMapping[]>(`/mappings${sourceSystem ? `?source_system=${sourceSystem}` : ''}`),

  // Upload
  uploadFile: async (file: File, sourceSystem: string, farmId = 1) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('source_system', sourceSystem);
    formData.append('farm_id', String(farmId));

    const res = await fetch(`${API_BASE}/process-genetic-data`, {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(err.detail);
    }

    return res.blob();
  },
};
