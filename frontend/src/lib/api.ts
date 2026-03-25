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
  mae_rgn: string | null;
  pai_rgn: string | null;
  p210_peso_desmama: number | null;
  p365_peso_ano: number | null;
  p450_peso_sobreano: number | null;
  pe_perimetro_escrotal: number | null;
  a_area_olho_lombo: number | null;
  eg_espessura_gordura: number | null;
  im_idade_primeiro_parto: number | null;
  fonte_origem: string | null;
  data_processamento: string | null;
}

export interface ColumnMapping {
  id: number;
  source_system: string;
  source_column: string;
  target_column: string;
  data_type: string;
  is_required: boolean;
}

export interface Farm {
  id_farm: number;
  nome_farm: string;
  cnpj: string | null;
  responsavel: string | null;
  email: string | null;
  created_at: string | null;
}

function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('access_token');
}

function getRefreshToken(): string | null {
  if (typeof undefined === 'undefined') return null;
  return localStorage.getItem('refresh_token');
}

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = localStorage.getItem('refresh_token');
  if (!refreshToken) return null;

  try {
    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!res.ok) return null;

    const data = await res.json();
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    localStorage.setItem('user', JSON.stringify(data.user));
    return data.access_token;
  } catch {
    return null;
  }
}

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getAccessToken();

  const makeRequest = async (accessToken: string | null): Promise<Response> => {
    return fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      },
    });
  };

  let res = await makeRequest(token);

  // If 401, try to refresh token and retry once
  if (res.status === 401) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      res = await makeRequest(newToken);
    } else {
      // Refresh failed, redirect to login
      if (typeof window !== 'undefined') {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }
      throw new Error('Session expired');
    }
  }

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
  getAnimals: (opts?: {
    farmId?: number;
    source?: string;
    raca?: string;
    sexo?: string;
    search?: string;
    limit?: number;
    offset?: number;
  }) => {
    const params = new URLSearchParams();
    if (opts?.farmId) params.set('farm_id', String(opts.farmId));
    if (opts?.source) params.set('source', opts.source);
    if (opts?.raca) params.set('raca', opts.raca);
    if (opts?.sexo) params.set('sexo', opts.sexo);
    if (opts?.search) params.set('search', opts.search);
    params.set('limit', String(opts?.limit || 50));
    params.set('offset', String(opts?.offset || 0));
    return fetchApi<Animal[]>(`/animals?${params.toString()}`);
  },

  getAnimal: (id: number) => fetchApi<Animal>(`/animals/${id}`),

  // Farms
  getFarms: () => fetchApi<Farm[]>('/farms'),
  getFarm: (id: number) => fetchApi<Farm>(`/farms/${id}`),
  createFarm: (data: { nome_farm: string; cnpj?: string; responsavel?: string; email?: string }) =>
    fetchApi<Farm>('/farms', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Mappings
  getMappings: (sourceSystem?: string) =>
    fetchApi<ColumnMapping[]>(`/mappings${sourceSystem ? `?source_system=${sourceSystem}` : ''}`),
  createMapping: (data: { source_system: string; source_column: string; target_column: string; data_type?: string; is_required?: boolean }) =>
    fetchApi<ColumnMapping>('/mappings', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  deleteMapping: (id: number) =>
    fetchApi<void>(`/mappings/${id}`, { method: 'DELETE' }),

  // Upload
  uploadFile: async (file: File, sourceSystem: string, farmId?: number): Promise<Blob> => {
    const token = getAccessToken();
    const formData = new FormData();
    formData.append('file', file);
    formData.append('source_system', sourceSystem);
    if (farmId) formData.append('farm_id', String(farmId));

    const doUpload = async (accessToken: string | null): Promise<Response> => {
      return fetch(`${API_BASE}/process-genetic-data`, {
        method: 'POST',
        headers: {
          ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        },
        body: formData,
      });
    };

    let res = await doUpload(token);

    if (res.status === 401) {
      const newToken = await refreshAccessToken();
      if (newToken) {
        res = await doUpload(newToken);
      }
    }

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(err.detail);
    }

    return res.blob();
  },

  // Auth helpers
  changePassword: (senha_atual: string, senha_nova: string) =>
    fetchApi<{ message: string }>('/auth/change-password', {
      method: 'POST',
      body: JSON.stringify({ senha_atual, senha_nova }),
    }),

  getMe: () =>
    fetchApi<{
      id: number; nome: string; email: string;
      id_farm: number | null; role: string; ativo: boolean;
    }>('/auth/me'),
};
