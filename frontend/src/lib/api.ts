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
  anc_mg?: number | null;
  anc_te?: number | null;
  anc_m?: number | null;
  anc_p?: number | null;
  anc_dp?: number | null;
  anc_sp?: number | null;
  anc_e?: number | null;
  anc_sao?: number | null;
  anc_leg?: number | null;
  anc_sh?: number | null;
  anc_pp30?: number | null;
  gen_iqg?: number | null;
  gen_pmm?: number | null;
  gen_p?: number | null;
  gen_dp?: number | null;
  gen_sp?: number | null;
  gen_e?: number | null;
  gen_sao?: number | null;
  gen_leg?: number | null;
  gen_sh?: number | null;
  gen_pp30?: number | null;
  pmg_iabc?: number | null;
  pmg_zpmm?: number | null;
  pmg_p?: number | null;
  pmg_dp?: number | null;
  pmg_sp?: number | null;
  pmg_e?: number | null;
  pmg_sao?: number | null;
  pmg_leg?: number | null;
  pmg_sh?: number | null;
  pmg_pp30?: number | null;
  pmg_deca?: number | null;
  pmg_p_percent?: number | null;
  pmg_f_percent?: number | null;
  pmg_pn_dep?: number | null;
  pmg_pn_ac?: number | null;
  pmg_pa_dep?: number | null;
  pmg_pa_ac?: number | null;
  pmg_ps_dep?: number | null;
  pmg_ps_ac?: number | null;
  pmg_pm_dep?: number | null;
  pmg_pm_ac?: number | null;
  pmg_stay_dep?: number | null;
  pmg_stay_ac?: number | null;
  pmg_ipp_dep?: number | null;
  pmg_pe365_dep?: number | null;
  pmg_aol_dep?: number | null;
  pmg_acab_dep?: number | null;
  pmg_mar_dep?: number | null;
  pmg_eg_dep?: number | null;
  pmg_p_dep?: number | null;
  pmg_m_dep?: number | null;
  pmg_psn_dep?: number | null;
  genotipado?: boolean | null;
  csg?: boolean | null;
}

export interface ColumnMapping {
  id: number;
  source_system: string;
  source_column: string;
  target_column: string;
  data_type: string;
  is_required: boolean;
}

export interface Notification {
  id: number;
  id_user: number;
  title: string;
  message: string;
  type: string;
  is_read: boolean;
  link: string | null;
  created_at: string | null;
}

export interface Farm {
  id_farm: string;
  nome_farm: string;
  cnpj: string | null;
  responsavel: string | null;
  email: string | null;
  created_at: string | null;
}

export interface GeneticsFarm {
  id: string;
  nome: string;
  dono_fazenda: string | null;
  cnpj?: string | null;
  created_at: string | null;
}

export interface Upload {
  upload_id: string;
  nome: string;
  id_farm: string;
  fonte_origem: string;
  arquivo_nome_original: string | null;
  arquivo_hash: string | null;
  total_registros: number;
  rows_inserted: number;
  rows_updated: number;
  status: string;
  error_message: string | null;
  usuario_id: number | null;
  data_upload: string | null;
  completed_at: string | null;
}

export interface UploadWithAnimals {
  upload: Upload;
  farm_nome: string;
  animais_preview: Animal[];
  total_animais: number;
}

export interface UploadCreate {
  nome: string;
  id_farm: string;
  fonte_origem: string;
  arquivo_nome_original?: string;
  arquivo_hash?: string;
}

export interface UploadDetail {
  log: ProcessingLog;
  animals_preview: Animal[];
  total_count: number;
}

export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public isNetworkError: boolean = false
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('access_token');
}

function getRefreshToken(): string | null {
  if (typeof window === 'undefined') return null;
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

async function fetchApi<T>(path: string, options?: RequestInit, _retries = 1): Promise<T> {
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

  if (res.status === 401) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      res = await makeRequest(newToken);
    } else {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }
      throw new ApiError('Sessão expirada. Faça login novamente.', 401);
    }
  }

  if (!res.ok) {
    let errMsg = `Erro ${res.status}`;
    try {
      const err = await res.json();
      errMsg = err.detail || errMsg;
    } catch {
      errMsg = res.statusText || errMsg;
    }
    throw new ApiError(errMsg, res.status);
  }

  if (res.status === 204) {
    return {} as T;
  }

  return res.json();
}

export const api = {
  getStats: (farmId?: number) =>
    fetchApi<DashboardStats>(`/stats${farmId ? `?farm_id=${farmId}` : ''}`),

  getStatsV2: (farmId?: string) =>
    fetchApi<DashboardStats>(`/v2/animals/stats${farmId ? `?farm_id=${farmId}` : ''}`),

  getLogs: (farmId?: number, source?: string, limit = 50) => {
    const params = new URLSearchParams();
    if (farmId) params.set('farm_id', String(farmId));
    if (source) params.set('source_system', source);
    params.set('limit', String(limit));
    return fetchApi<ProcessingLog[]>(`/logs?${params.toString()}`);
  },

  deleteLog: (logId: number) =>
    fetchApi<void>(`/logs/${logId}`, { method: 'DELETE' }),

  deleteLogs: (logIds: number[]) =>
    fetchApi<void>(`/logs`, { method: 'DELETE', body: JSON.stringify(logIds) }),

  getUploadDetail: (logId: number) =>
    fetchApi<UploadDetail>(`/reports/upload/${logId}`),

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

  getFarms: () => fetchApi<Farm[]>('/farms'),
  getFarm: (id: string) => fetchApi<Farm>(`/farms/${id}`),
  updateFarm: (id: string, data: { nome_farm?: string; cnpj?: string; responsavel?: string; email?: string }) =>
    fetchApi<Farm>(`/farms/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  deleteFarm: (id: string) =>
    fetchApi<{ message: string }>(`/farms/${id}`, { method: 'DELETE' }),
  createFarm: (data: { nome_farm: string; cnpj?: string; responsavel?: string; email?: string }) =>
    fetchApi<Farm>('/farms', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Genetics Farms (UUID-based)
  getGeneticsFarms: () => fetchApi<GeneticsFarm[]>('/genetics/farms'),
  getGeneticsFarm: (id: string) => fetchApi<GeneticsFarm>(`/genetics/farms/${id}`),
  updateGeneticsFarm: (id: string, data: { nome?: string; dono_fazenda?: string }) =>
    fetchApi<GeneticsFarm>(`/genetics/farms/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  deleteGeneticsFarm: (id: string) =>
    fetchApi<{ message: string }>(`/genetics/farms/${id}`, { method: 'DELETE' }),
  createGeneticsFarm: (data: { nome: string; dono_fazenda?: string }) =>
    fetchApi<GeneticsFarm>('/genetics/farms', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getMappings: (sourceSystem?: string) =>
    fetchApi<ColumnMapping[]>(`/mappings${sourceSystem ? `?source_system=${sourceSystem}` : ''}`),
  createMapping: (data: { source_system: string; source_column: string; target_column: string; data_type?: string; is_required?: boolean }) =>
    fetchApi<ColumnMapping>('/mappings', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  deleteMapping: (id: number) =>
    fetchApi<void>(`/mappings/${id}`, { method: 'DELETE' }),
  updateMapping: (id: number, data: { source_system?: string; source_column?: string; target_column?: string; data_type?: string; is_required?: boolean }) =>
    fetchApi<ColumnMapping>(`/mappings/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

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
      let errMsg = 'Upload falhou';
      try {
        const err = await res.json();
        errMsg = err.detail || errMsg;
      } catch { }
      throw new ApiError(errMsg, res.status);
    }

    return res.blob();
  },

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

  downloadDashboardReport: async (opts?: { farmId?: number; includeAnimals?: boolean; includeLogs?: boolean }): Promise<Blob> => {
    const token = getAccessToken();
    const params = new URLSearchParams();
    if (opts?.farmId) params.set('farm_id', String(opts.farmId));
    if (opts?.includeAnimals) params.set('include_animals', 'true');
    if (opts?.includeLogs) params.set('include_logs', 'true');

    const doDownload = async (accessToken: string | null): Promise<Response> => {
      return fetch(`${API_BASE}/report/dashboard?${params.toString()}`, {
        headers: {
          ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        },
      });
    };

    let res = await doDownload(token);

    if (res.status === 401) {
      const newToken = await refreshAccessToken();
      if (newToken) {
        res = await doDownload(newToken);
      } else {
        if (typeof window !== 'undefined') {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('user');
          window.location.href = '/login';
        }
        throw new ApiError('Sessão expirada', 401);
      }
    }

    if (!res.ok) {
      throw new ApiError('Download do relatório falhou', res.status);
    }

    return res.blob();
  },

  downloadUploadReport: async (logId: number): Promise<Blob> => {
    const token = getAccessToken();
    const doDownload = async (accessToken: string | null): Promise<Response> => {
      return fetch(`${API_BASE}/reports/upload/${logId}/pdf`, {
        headers: {
          ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        },
      });
    };

    let res = await doDownload(token);

    if (res.status === 401) {
      const newToken = await refreshAccessToken();
      if (newToken) {
        res = await doDownload(newToken);
      } else {
        if (typeof window !== 'undefined') {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('user');
          window.location.href = '/login';
        }
        throw new ApiError('Sessão expirada', 401);
      }
    }

    if (!res.ok) {
      throw new ApiError('Download do relatório falhou', res.status);
    }

    return res.blob();
  },

  downloadAnimalReport: async (animalId: number): Promise<Blob> => {
    const token = getAccessToken();
    const doDownload = async (accessToken: string | null): Promise<Response> => {
      return fetch(`${API_BASE}/reports/animal/${animalId}/pdf`, {
        headers: {
          ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        },
      });
    };

    let res = await doDownload(token);

    if (res.status === 401) {
      const newToken = await refreshAccessToken();
      if (newToken) {
        res = await doDownload(newToken);
      } else {
        throw new ApiError('Sessão expirada', 401);
      }
    }

    if (!res.ok) {
      throw new ApiError('Download do relatório falhou', res.status);
    }

    return res.blob();
  },

  downloadBenchmarkReport: async (platformCode: string, characteristic: string, farmId?: string): Promise<Blob> => {
    const token = getAccessToken();
    const params = new URLSearchParams({ platform_code: platformCode, characteristic });
    if (farmId) params.set('farm_id', String(farmId));

    const doDownload = async (accessToken: string | null): Promise<Response> => {
      return fetch(`${API_BASE}/reports/benchmark/pdf?${params.toString()}`, {
        headers: {
          ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        },
      });
    };

    let res = await doDownload(token);

    if (res.status === 401) {
      const newToken = await refreshAccessToken();
      if (newToken) {
        res = await doDownload(newToken);
      } else {
        throw new ApiError('Sessão expirada', 401);
      }
    }

    if (!res.ok) {
      throw new ApiError('Download do relatório falhou', res.status);
    }

    return res.blob();
  },

  getNotifications: (unreadOnly = false) =>
    fetchApi<Notification[]>(`/notifications${unreadOnly ? '?unread_only=true' : ''}`),
  
  createNotification: (data: { title: string; message: string; type?: string; link?: string }) =>
    fetchApi<Notification>('/notifications', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  getUnreadCount: () =>
    fetchApi<{ count: number }>('/notifications/unread-count'),
  
  markAsRead: (id: number) =>
    fetchApi<Notification>(`/notifications/${id}`, {
      method: 'PUT',
      body: JSON.stringify({ is_read: true }),
    }),
  
  markAllAsRead: () =>
    fetchApi<{ message: string }>('/notifications/read-all', { method: 'PUT' }),

  // Uploads API
  getUploads: (opts?: { farmId?: string; fonteOrigem?: string; status?: string; limit?: number; offset?: number }) => {
    const params = new URLSearchParams();
    if (opts?.farmId) params.set('farm_id', String(opts.farmId));
    if (opts?.fonteOrigem) params.set('fonte_origem', opts.fonteOrigem);
    if (opts?.status) params.set('status', opts.status);
    params.set('limit', String(opts?.limit || 50));
    params.set('offset', String(opts?.offset || 0));
    return fetchApi<Upload[]>(`/uploads?${params.toString()}`);
  },

  getUpload: (uploadId: string) =>
    fetchApi<UploadWithAnimals>(`/uploads/${uploadId}`),

  createUpload: (data: UploadCreate) =>
    fetchApi<Upload>('/uploads', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  deleteUpload: (uploadId: string) =>
    fetchApi<void>(`/uploads/${uploadId}`, { method: 'DELETE' }),

  // Genetics V2 API
  getAnimalsV2: (opts?: {
    farmId?: string;
    fonteOrigem?: string;
    sexo?: string;
    search?: string;
    limit?: number;
    offset?: number;
  }) => {
    const params = new URLSearchParams();
    if (opts?.farmId) params.set('farm_id', opts.farmId);
    if (opts?.sexo) params.set('sexo', opts.sexo);
    if (opts?.search) params.set('search', opts.search);
    params.set('limit', String(opts?.limit || 50));
    params.set('offset', String(opts?.offset || 0));
    if (opts?.fonteOrigem) params.set('fonte_origem', opts.fonteOrigem);
    if (opts?.farmId) params.set('farm_id', opts.farmId);
    return fetchApi<{
      total: number;
      limit: number;
      offset: number;
      data: any[];
    }>(`/v2/animals?${params.toString()}`);
  },

  getAnimalV2: (animalId: string) =>
    fetchApi<any>(`/v2/animals/${animalId}`),

  getAnimalsStatsByFarm: () =>
    fetchApi<{ farm_id: string; farm_name: string; total_animals: number }[]>('/v2/animals/stats/by-farm'),

  getAnimalsRanking: (opts?: { farmId?: string; metric?: string; limit?: number }) => {
    const params = new URLSearchParams();
    if (opts?.farmId) params.set('farm_id', opts.farmId);
    if (opts?.metric) params.set('metric', opts.metric);
    params.set('limit', String(opts?.limit || 20));
    return fetchApi<any[]>(`/v2/animals/stats/ranking?${params.toString()}`);
  },

  deleteAnimalsV2: (animalIds: string[]) =>
    fetchApi<void>(`/v2/animals/bulk`, {
      method: 'DELETE',
      body: JSON.stringify(animalIds),
    }),

  uploadFileWithUpload: async (file: File, sourceSystem: string, farmId: string, uploadId: string): Promise<Blob> => {
    const token = getAccessToken();
    const formData = new FormData();
    formData.append('file', file);
    formData.append('source_system', sourceSystem);
    formData.append('farm_id', String(farmId));
    formData.append('upload_id', uploadId);

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
      let errMsg = 'Upload falhou';
      try {
        const err = await res.json();
        errMsg = err.detail || errMsg;
      } catch { }
      throw new ApiError(errMsg, res.status);
    }

    return res.blob();
  },
};
