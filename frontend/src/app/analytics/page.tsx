'use client';

import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Card } from '@/components/ui/Card';
import { 
  ChartBarSquareIcon, 
  CubeTransparentIcon, 
  ArrowTrendingUpIcon,
  UsersIcon,
  BeakerIcon
} from '@heroicons/react/24/outline';

export default function AnalyticsPage() {
  return (
    <DashboardLayout>
      <div className="space-y-8 animate-in fade-in duration-700">
        <section className="space-y-2">
          <h1 className="text-4xl font-bold text-white tracking-tight">Análises Genéticas</h1>
          <p className="text-slate-400 text-lg">Insights avançados sobre o seu rebanho e performance de dados.</p>
        </section>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard 
            title="Total Processado" 
            value="42.850" 
            trend="+12%" 
            icon={<CubeTransparentIcon className="w-6 h-6" />} 
            color="blue"
          />
          <StatCard 
            title="Média Padronização" 
            value="98.4%" 
            trend="+2%" 
            icon={<ArrowTrendingUpIcon className="w-6 h-6" />} 
            color="emerald"
          />
          <StatCard 
            title="Sistemas Ativos" 
            value="3" 
            trend="Estável" 
            icon={<BeakerIcon className="w-6 h-6" />} 
            color="purple"
          />
          <StatCard 
            title="Relatórios / Mês" 
            value="148" 
            trend="+5%" 
            icon={<ChartBarSquareIcon className="w-6 h-6" />} 
            color="amber"
          />
        </div>

        {/* Big Analytics Cards */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <Card variant="bento" className="lg:col-span-8 h-96 flex flex-col justify-between">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-xl font-bold text-white">Crescimento de Volume</h3>
                <p className="text-slate-500 text-sm">Animais processados nos últimos 6 meses</p>
              </div>
              <select className="bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-400 px-3 py-1 outline-none focus:border-blue-500">
                <option>Últimos 6 meses</option>
                <option>Este ano</option>
              </select>
            </div>
            
            {/* Mock Chart Visualization */}
            <div className="flex-1 flex items-end gap-2 pt-8">
              {[40, 60, 45, 90, 75, 100].map((h, i) => (
                <div key={i} className="flex-1 bg-slate-800/50 rounded-t-xl group relative cursor-pointer overflow-hidden">
                  <div 
                    className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-blue-600 to-blue-400 transition-all duration-1000 ease-out group-hover:from-blue-500 group-hover:to-blue-300"
                    style={{ height: `${h}%` }}
                  ></div>
                </div>
              ))}
            </div>
          </Card>

          <Card variant="bento" className="lg:col-span-4 space-y-6">
            <h3 className="text-xl font-bold text-white">Distribuição por Plataforma</h3>
            <div className="space-y-4">
              <DistributionRow label="ANCP" percentage={55} color="bg-blue-500" />
              <DistributionRow label="PMGZ" percentage={30} color="bg-emerald-500" />
              <DistributionRow label="Geneplus" percentage={15} color="bg-amber-500" />
            </div>
            <div className="pt-6 border-t border-slate-800">
              <p className="text-xs text-slate-500 leading-relaxed italic">
                A plataforma ANCP representa a maior fatia de dados unificados no sistema Melhora+.
              </p>
            </div>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}

function StatCard({ title, value, trend, icon, color }: any) {
  const colors: any = {
    blue: 'bg-blue-600/10 text-blue-400 border-blue-500/20',
    emerald: 'bg-emerald-600/10 text-emerald-400 border-emerald-500/20',
    purple: 'bg-purple-600/10 text-purple-400 border-purple-500/20',
    amber: 'bg-amber-600/10 text-amber-400 border-amber-500/20',
  };

  return (
    <Card variant="bento" className="p-6">
      <div className="flex justify-between items-start mb-4">
        <div className={`w-12 h-12 rounded-2xl flex items-center justify-center border ${colors[color]}`}>
          {icon}
        </div>
        <span className={`text-xs font-bold px-2 py-1 rounded-md ${trend.includes('+') ? 'bg-emerald-500/10 text-emerald-400' : 'bg-slate-800 text-slate-400'}`}>
          {trend}
        </span>
      </div>
      <div className="space-y-1">
        <p className="text-slate-500 text-sm font-medium uppercase tracking-widest">{title}</p>
        <p className="text-3xl font-bold text-white tracking-tight">{value}</p>
      </div>
    </Card>
  );
}

function DistributionRow({ label, percentage, color }: any) {
  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center text-sm">
        <span className="text-slate-300 font-medium">{label}</span>
        <span className="text-white font-bold">{percentage}%</span>
      </div>
      <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${percentage}%` }}></div>
      </div>
    </div>
  );
}
