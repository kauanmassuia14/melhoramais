'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Card } from '@/components/ui/Card';
import { api, type GeneticsFarm as Farm } from '@/lib/api';
import {
  CheckCircleIcon,
  XCircleIcon,
  ChartBarSquareIcon,
  ArrowPathIcon,
  FunnelIcon,
  InformationCircleIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  DocumentArrowDownIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Types
interface Platform {
  code: string;
  name: string;
  description: string;
  characteristics_count: number;
}

interface Characteristic {
  code: string;
  name: string;
  column: string;
  description: string;
}

interface GroupData {
  name: string;
  description: string;
  average: number;
  count: number;
  farm_count?: number;
  farms?: Array<{
    id: number;
    name: string;
    average: number;
    animal_count: number;
  }>;
  std_dev?: number;
}

interface BenchmarkGroup {
  platform: string;
  characteristic: string;
  characteristic_description: string;
  groups: GroupData[];
  total_animals: number;
  total_farms: number;
}

interface AuctionAnimal {
  id: number;
  rgn: string;
  nome: string;
  sexo: string;
  raca: string;
  farm_id: number;
  farm_name: string;
  value: number;
  percentile: number;
  top_percent: string;
  characteristics: Record<string, number>;
}

// Interface Farm local removida pois estamos usando a do lib/api agora

function BenchmarkingContent() {
  const searchParams = useSearchParams();
  const initialFarmId = searchParams.get('farm_id') || '';
  
  // State
  const [platforms, setPlatforms] = useState<Platform[]>([]);
  const [selectedPlatform, setSelectedPlatform] = useState<string>('');
  const [characteristics, setCharacteristics] = useState<Characteristic[]>([]);
  const [selectedCharacteristics, setSelectedCharacteristics] = useState<Set<string>>(new Set());
  const [benchmarkData, setBenchmarkData] = useState<BenchmarkGroup | null>(null);
  const [auctionData, setAuctionData] = useState<AuctionAnimal[]>([]);
  const [farms, setFarms] = useState<Farm[]>([]);
  
  // Filters
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [sexo, setSexo] = useState<string>('');
  const [farmId, setFarmId] = useState<string>(initialFarmId);
  
  // UI state
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'checklist' | 'groups' | 'chart' | 'auction'>('checklist');
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set(['Top 5 Clientes']));
  const [characteristicsExpanded, setCharacteristicsExpanded] = useState(true);
  const [selectedCharInfo, setSelectedCharInfo] = useState<string | null>(null);

  // Download benchmark report
  const handleDownloadReport = async () => {
    if (!selectedPlatform || selectedCharacteristics.size === 0) return;
    setDownloading(true);
    try {
      const char = Array.from(selectedCharacteristics)[0];
      const blob = await api.downloadBenchmarkReport(selectedPlatform, char, farmId || undefined);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `relatorio_benchmark_${selectedPlatform}_${char}_${new Date().toISOString().slice(0, 10)}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      setError(err.message || 'Erro ao gerar relatório');
    } finally {
      setDownloading(false);
    }
  };

  // Load platforms on mount
  useEffect(() => {
    const loadPlatforms = async () => {
      try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_BASE}/benchmark/platforms`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });
        const data = await response.json();
        if (Array.isArray(data)) {
          setPlatforms(data);
          if (data.length > 0) {
            setSelectedPlatform(data[0].code);
          }
        } else {
          setPlatforms([]);
        }
      } catch (err) {
        setError('Falha ao carregar plataformas');
        setPlatforms([]);
      }
    };
    loadPlatforms();
  }, []);

  // Load farms on mount
  useEffect(() => {
    const loadFarms = async () => {
      try {
        const farmsData = await api.getGeneticsFarms();
        setFarms(Array.isArray(farmsData) ? farmsData : []);
      } catch (err) {
        console.error('Falha ao carregar fazendas', err);
        setFarms([]);
      }
    };
    loadFarms();
  }, []);

  // Load characteristics when platform changes
  useEffect(() => {
    if (!selectedPlatform) return;
    
    const loadCharacteristics = async () => {
      try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_BASE}/benchmark/characteristics/${selectedPlatform}`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });
        const data = await response.json();
        setCharacteristics(Array.isArray(data.characteristics) ? data.characteristics : []);
        setSelectedCharacteristics(new Set());
      } catch (err) {
        setError('Falha ao carregar características');
        setCharacteristics([]);
      }
    };
    loadCharacteristics();
  }, [selectedPlatform]);

  // Load benchmark data when filters change
  useEffect(() => {
    if (!selectedPlatform || selectedCharacteristics.size === 0) return;
    
    const loadBenchmarkData = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const char = Array.from(selectedCharacteristics)[0];
        const params = new URLSearchParams({
          platform_code: selectedPlatform,
          characteristic: char,
        });
        
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);
        if (sexo) params.append('sexo', sexo);
        if (farmId) params.append('farm_id', farmId);
        
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_BASE}/benchmark/groups?${params}`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });
        const data = await response.json();
        setBenchmarkData(data);
      } catch (err) {
        setError('Failed to load benchmark data');
      } finally {
        setLoading(false);
      }
    };
    
    loadBenchmarkData();
  }, [selectedPlatform, selectedCharacteristics, startDate, endDate, sexo, farmId]);

  // Load auction data
  const loadAuctionData = async () => {
    if (!selectedPlatform || selectedCharacteristics.size === 0) return;
    
    setLoading(true);
    try {
      const char = Array.from(selectedCharacteristics)[0];
      const params = new URLSearchParams({
        platform_code: selectedPlatform,
        characteristic: char,
        limit: '50',
      });
      
      if (farmId) params.append('farm_id', farmId);
      
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE}/benchmark/auction?${params}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      const data = await response.json();
      setAuctionData(data.animals || []);
    } catch (err) {
      setError('Failed to load auction data');
    } finally {
      setLoading(false);
    }
  };

  // Toggle characteristic selection
  const toggleCharacteristic = (code: string) => {
    const newSelected = new Set(selectedCharacteristics);
    if (newSelected.has(code)) {
      newSelected.delete(code);
    } else {
      newSelected.add(code);
    }
    setSelectedCharacteristics(newSelected);
  };

  // Select all characteristics
  const selectAllCharacteristics = () => {
    setSelectedCharacteristics(new Set(characteristics.map(c => c.code)));
  };

  // Clear all characteristics
  const clearAllCharacteristics = () => {
    setSelectedCharacteristics(new Set());
  };

  // Toggle group expansion
  const toggleGroupExpansion = (groupName: string) => {
    const newExpanded = new Set(expandedGroups);
    if (newExpanded.has(groupName)) {
      newExpanded.delete(groupName);
    } else {
      newExpanded.add(groupName);
    }
    setExpandedGroups(newExpanded);
  };

  // Get chart data
  const getChartData = () => {
    if (!benchmarkData) return [];
    
    return (benchmarkData.groups || []).map(group => ({
      name: group.name,
      average: group.average,
      count: group.count,
    }));
  };

  return (
    <DashboardLayout>
      <div className="space-y-8 animate-in fade-in duration-700">
        {/* Header */}
        <section className="flex items-center justify-between">
          <div className="space-y-2">
            <h1 className="text-4xl font-bold text-white tracking-tight">
              Benchmarking Genético
            </h1>
            <p className="text-slate-400 text-lg">
              Compare o desempenho genético do seu rebanho com referências do mercado.
            </p>
          </div>
          {benchmarkData && (
            <button
              onClick={handleDownloadReport}
              disabled={downloading}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-glow/10 border border-emerald-glow/30 text-emerald-glow-400 text-sm font-semibold hover:bg-emerald-glow/20 transition-all disabled:opacity-50 shadow-lg shadow-emerald-glow/10"
            >
              <DocumentArrowDownIcon className={`w-5 h-5 ${downloading ? 'animate-spin' : ''}`} />
              {downloading ? 'Gerando PDF...' : 'Exportar PDF'}
            </button>
          )}
        </section>

        {/* Error Banner */}
        {error && (
          <div className="flex items-center justify-between p-4 rounded-xl bg-rose-neon/[0.08] border border-rose-neon/20">
            <div className="flex items-center gap-3">
              <ExclamationTriangleIcon className="w-5 h-5 text-rose-neon-400" />
              <span className="text-sm text-rose-neon-400">{error}</span>
            </div>
            <button
              onClick={() => setError(null)}
              className="px-3 py-1 rounded-lg text-xs text-rose-neon-400 hover:bg-rose-neon/10"
            >
              ✕
            </button>
          </div>
        )}

        {/* Platform Selection */}
        <Card variant="bento" className="p-6">
          <h2 className="text-xl font-bold text-white mb-4">
            Selecione a Plataforma de Melhoramento
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {platforms.map(platform => (
              <button
                key={platform.code}
                onClick={() => setSelectedPlatform(platform.code)}
                className={`p-4 rounded-xl border-2 transition-all ${
                  selectedPlatform === platform.code
                    ? 'border-blue-500 bg-blue-500/10'
                    : 'border-slate-700 bg-slate-800/50 hover:border-slate-600'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-slate-700 flex items-center justify-center">
                    <ChartBarSquareIcon className="w-5 h-5 text-blue-400" />
                  </div>
                  <div className="text-left">
                    <h3 className="font-bold text-white">{platform.name}</h3>
                    <p className="text-sm text-slate-400">{platform.description}</p>
                    <p className="text-xs text-slate-500 mt-1">
                      {platform.characteristics_count} características
                    </p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </Card>

        {/* Filters */}
        <Card variant="bento" className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <FunnelIcon className="w-5 h-5" />
              Filtros
            </h2>
            <button
              onClick={() => {
                setStartDate('');
                setEndDate('');
                setSexo('');
                setFarmId('');
              }}
              className="text-sm text-blue-400 hover:text-blue-300"
            >
              Limpar filtros
            </button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">
                Data Início
              </label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">
                Data Fim
              </label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">
                Sexo
              </label>
              <select
                value={sexo}
                onChange={(e) => setSexo(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Todos</option>
                <option value="M">Machos</option>
                <option value="F">Fêmeas</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">
                Fazenda
              </label>
              <select
                value={farmId}
                onChange={(e) => setFarmId(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Todas as Fazendas</option>
                {farms.map(farm => (
                  <option key={farm.id} value={String(farm.id)}>
                    {farm.nome}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </Card>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Panel - Checklists */}
          <div className="lg:col-span-1 space-y-6">
            <Card variant="bento" className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-white">
                  Características Genéticas
                </h2>
                <div className="flex gap-2">
                  <button
                    onClick={selectAllCharacteristics}
                    className="text-xs text-blue-400 hover:text-blue-300"
                  >
                    Selecionar todas
                  </button>
                  <button
                    onClick={clearAllCharacteristics}
                    className="text-xs text-slate-400 hover:text-slate-300"
                  >
                    Limpar
                  </button>
                </div>
              </div>
              
              <p className="text-sm text-slate-400 mb-4">
                Selecione as características que deseja analisar. Clique no ícone <InformationCircleIcon className="w-4 h-4 inline" /> para detalhes.
              </p>
              
              <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2">
                {characteristics.map(characteristic => (
                  <div
                    key={characteristic.code}
                    className={`p-3 rounded-lg border transition-all ${
                      selectedCharacteristics.has(characteristic.code)
                        ? 'border-blue-500 bg-blue-500/10'
                        : 'border-slate-700 bg-slate-800/50'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => toggleCharacteristic(characteristic.code)}
                          className="mt-1"
                        >
                          {selectedCharacteristics.has(characteristic.code) ? (
                            <CheckCircleIcon className="w-5 h-5 text-blue-400" />
                          ) : (
                            <XCircleIcon className="w-5 h-5 text-slate-500" />
                          )}
                        </button>
                        <div>
                          <h3 className="font-medium text-white">
                            {characteristic.code.toUpperCase()} - {characteristic.name}
                          </h3>
                          <p className="text-xs text-slate-400 mt-1">
                            {characteristic.description}
                          </p>
                          <p className="text-[10px] text-cyan-400/70 mt-1 font-mono">
                            Coluna: {characteristic.column}
                          </p>
                        </div>
                      </div>
                      <div className="flex flex-col items-center gap-1">
                        <InformationCircleIcon className="w-4 h-4 text-slate-500 cursor-help" />
                        {selectedCharacteristics.has(characteristic.code) && (
                          <CheckCircleIcon className="w-4 h-4 text-blue-400" />
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="mt-4 pt-4 border-t border-slate-700">
                <p className="text-sm text-slate-400">
                  <strong>{selectedCharacteristics.size}</strong> de{' '}
                  <strong>{characteristics.length}</strong> características selecionadas
                </p>
              </div>
            </Card>
          </div>
          
          {/* Right Panel - Results */}
          <div className="lg:col-span-2 space-y-6">
            {/* Tabs */}
            <div className="flex gap-2">
              {[
                { id: 'groups', label: 'Grupos' },
                { id: 'chart', label: 'Gráfico' },
                { id: 'auction', label: 'Leilão' },
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    activeTab === tab.id
                      ? 'bg-blue-500 text-white'
                      : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
            
            {/* Loading/Error */}
            {loading && (
              <div className="flex items-center justify-center p-12">
                <ArrowPathIcon className="w-8 h-8 text-blue-400 animate-spin" />
                <span className="ml-2 text-slate-400">Carregando dados...</span>
              </div>
            )}
            
            {error && (
              <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20">
                <p className="text-red-400">{error}</p>
              </div>
            )}
            
            {/* Groups Tab */}
            {!loading && !error && activeTab === 'groups' && benchmarkData && (
              <div className="space-y-4">
                <Card variant="bento" className="p-6">
                  <div className="flex items-center justify-between mb-6">
                    <div>
                      <h2 className="text-xl font-bold text-white">
                        Comparação de Grupos
                      </h2>
                      <p className="text-sm text-slate-400">
                        {benchmarkData.characteristic} - {benchmarkData.characteristic_description}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-slate-400">
                        Total: {benchmarkData.total_animals} animais
                      </p>
                      <p className="text-sm text-slate-400">
                        {benchmarkData.total_farms} fazendas
                      </p>
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    {(benchmarkData.groups || []).map(group => (
                      <div
                        key={group.name}
                        className="border border-slate-700 rounded-xl overflow-hidden"
                      >
                        <button
                          onClick={() => toggleGroupExpansion(group.name)}
                          className="w-full p-4 flex items-center justify-between bg-slate-800/50 hover:bg-slate-800 transition-colors"
                        >
                          <div className="flex items-center gap-3">
                            <div className="w-12 h-12 rounded-lg bg-slate-700 flex items-center justify-center">
                              <ChartBarSquareIcon className="w-6 h-6 text-blue-400" />
                            </div>
                            <div className="text-left">
                              <h3 className="font-bold text-white">{group.name}</h3>
                              <p className="text-sm text-slate-400">{group.description}</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-4">
                            <div className="text-right">
                              <p className="text-2xl font-bold text-white">
                                {group.average.toFixed(3)}
                              </p>
                              <p className="text-sm text-slate-400">
                                {group.count} animais
                              </p>
                            </div>
                            {expandedGroups.has(group.name) ? (
                              <ChevronUpIcon className="w-5 h-5 text-slate-400" />
                            ) : (
                              <ChevronDownIcon className="w-5 h-5 text-slate-400" />
                            )}
                          </div>
                        </button>
                        
                        {expandedGroups.has(group.name) && (
                          <div className="p-4 bg-slate-800/30 border-t border-slate-700">
                            {group.farms ? (
                              <div className="space-y-3">
                                <h4 className="text-sm font-medium text-slate-300">
                                  Fazendas no grupo:
                                </h4>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                  {group.farms.map(farm => (
                                    <div
                                      key={farm.id}
                                      className="p-3 rounded-lg bg-slate-800/50 border border-slate-700"
                                    >
                                      <div className="flex items-center justify-between">
                                        <div>
                                          <p className="font-medium text-white">
                                            {farm.name}
                                          </p>
                                          <p className="text-sm text-slate-400">
                                            {farm.animal_count} animais
                                          </p>
                                        </div>
                                        <div className="text-right">
                                          <p className="text-xl font-bold text-blue-400">
                                            {farm.average.toFixed(3)}
                                          </p>
                                        </div>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            ) : (
                              <div className="grid grid-cols-2 gap-4">
                                {group.std_dev !== undefined && (
                                  <div>
                                    <p className="text-sm text-slate-400">Desvio Padrão</p>
                                    <p className="text-xl font-bold text-white">
                                      ±{group.std_dev.toFixed(3)}
                                    </p>
                                  </div>
                                )}
                                {group.farm_count !== undefined && (
                                  <div>
                                    <p className="text-sm text-slate-400">Fazendas</p>
                                    <p className="text-xl font-bold text-white">
                                      {group.farm_count}
                                    </p>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </Card>
              </div>
            )}
            
            {/* Chart Tab */}
            {!loading && !error && activeTab === 'chart' && benchmarkData && (
              <Card variant="bento" className="p-6">
                <h2 className="text-xl font-bold text-white mb-6">
                  Gráfico Comparativo
                </h2>
                
                <div className="h-96">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={getChartData()}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                      <XAxis dataKey="name" stroke="#9CA3AF" />
                      <YAxis stroke="#9CA3AF" />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#1F2937',
                          border: '1px solid #374151',
                          borderRadius: '0.5rem',
                        }}
                      />
                      <Legend />
                      <Bar
                        dataKey="average"
                        fill="#3B82F6"
                        name="Média"
                        radius={[4, 4, 0, 0]}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                
                <div className="mt-6 grid grid-cols-3 gap-4">
                  {(benchmarkData.groups || []).map(group => (
                    <div
                      key={group.name}
                      className="p-4 rounded-lg bg-slate-800/50 border border-slate-700"
                    >
                      <h4 className="text-sm font-medium text-slate-300 mb-2">
                        {group.name}
                      </h4>
                      <p className="text-2xl font-bold text-white">
                        {group.average.toFixed(3)}
                      </p>
                      <p className="text-sm text-slate-400">
                        {group.count} animais
                      </p>
                    </div>
                  ))}
                </div>
              </Card>
            )}
            
            {/* Auction Tab */}
            {!loading && !error && activeTab === 'auction' && (
              <Card variant="bento" className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h2 className="text-xl font-bold text-white">
                      Animais para Leilão
                    </h2>
                    <p className="text-sm text-slate-400">
                      Top performers baseados na característica selecionada
                    </p>
                  </div>
                  <button
                    onClick={loadAuctionData}
                    className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm font-medium transition-colors"
                  >
                    Atualizar Lista
                  </button>
                </div>
                
                {auctionData.length === 0 ? (
                  <div className="text-center py-12">
                    <p className="text-slate-400 mb-4">
                      Clique em "Atualizar Lista" para carregar os animais para leilão.
                    </p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-slate-700">
                          <th className="text-left py-3 px-4 text-sm font-medium text-slate-300">
                            RGN
                          </th>
                          <th className="text-left py-3 px-4 text-sm font-medium text-slate-300">
                            Nome
                          </th>
                          <th className="text-left py-3 px-4 text-sm font-medium text-slate-300">
                            Sexo
                          </th>
                          <th className="text-left py-3 px-4 text-sm font-medium text-slate-300">
                            Raça
                          </th>
                          <th className="text-left py-3 px-4 text-sm font-medium text-slate-300">
                            Fazenda
                          </th>
                          <th className="text-right py-3 px-4 text-sm font-medium text-slate-300">
                            Valor
                          </th>
                          <th className="text-right py-3 px-4 text-sm font-medium text-slate-300">
                            Percentil
                          </th>
                          <th className="text-right py-3 px-4 text-sm font-medium text-slate-300">
                            TOP %
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {auctionData.map(animal => (
                          <tr
                            key={animal.id}
                            className="border-b border-slate-800 hover:bg-slate-800/30"
                          >
                            <td className="py-3 px-4 text-white font-medium">
                              {animal.rgn}
                            </td>
                            <td className="py-3 px-4 text-slate-300">
                              {animal.nome}
                            </td>
                            <td className="py-3 px-4">
                              <span
                                className={`px-2 py-1 rounded text-xs font-medium ${
                                  animal.sexo === 'M'
                                    ? 'bg-blue-500/20 text-blue-400'
                                    : 'bg-pink-500/20 text-pink-400'
                                }`}
                              >
                                {animal.sexo === 'M' ? 'Macho' : 'Fêmea'}
                              </span>
                            </td>
                            <td className="py-3 px-4 text-slate-300">
                              {animal.raca || '-'}
                            </td>
                            <td className="py-3 px-4 text-slate-300">
                              {animal.farm_name}
                            </td>
                            <td className="py-3 px-4 text-right text-white font-bold">
                              {animal.value.toFixed(3)}
                            </td>
                            <td className="py-3 px-4 text-right text-slate-300">
                              {animal.percentile.toFixed(1)}%
                            </td>
                            <td className="py-3 px-4 text-right">
                              <span
                                className={`px-2 py-1 rounded text-xs font-bold ${
                                  animal.percentile > 90
                                    ? 'bg-green-500/20 text-green-400'
                                    : animal.percentile > 75
                                    ? 'bg-blue-500/20 text-blue-400'
                                    : animal.percentile > 50
                                    ? 'bg-yellow-500/20 text-yellow-400'
                                    : 'bg-slate-500/20 text-slate-400'
                                }`}
                              >
                                {animal.top_percent}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
                
                {auctionData.length > 0 && (
                  <div className="mt-6 p-4 rounded-lg bg-slate-800/50 border border-slate-700">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-slate-400">
                          Total de animais selecionados
                        </p>
                        <p className="text-2xl font-bold text-white">
                          {auctionData.length}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-slate-400">
                          Média do grupo
                        </p>
                        <p className="text-2xl font-bold text-blue-400">
                          {(
                            auctionData.reduce((sum, a) => sum + a.value, 0) /
                            auctionData.length
                          ).toFixed(3)}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </Card>
            )}
            
            {/* No Data */}
            {!loading && !error && !benchmarkData && (
              <Card variant="bento" className="p-12">
                <div className="text-center">
                  <ChartBarSquareIcon className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                  <h3 className="text-xl font-bold text-white mb-2">
                    Selecione as características
                  </h3>
                  <p className="text-slate-400 max-w-md mx-auto">
                    Escolha pelo menos uma característica genética no painel à esquerda para
                    começar a análise de benchmarking.
                  </p>
                </div>
              </Card>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

export default function BenchmarkingPage() {
  return (
    <Suspense fallback={<div className="p-8 text-slate-400">Carregando benchmarking...</div>}>
      <BenchmarkingContent />
    </Suspense>
  );
}