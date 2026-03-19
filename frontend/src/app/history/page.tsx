'use client';

import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Card } from '@/components/ui/Card';
import { 
  CheckCircleIcon, 
  ExclamationCircleIcon, 
  ArrowDownTrayIcon,
  TagIcon
} from '@heroicons/react/24/outline';

const MOCK_HISTORY = [
  { id: 1, date: '19/03/2026', platform: 'ANCP', file: 'fazenda_sol_norte.xlsx', status: 'success', animals: 1240 },
  { id: 2, date: '18/03/2026', platform: 'PMGZ', file: 'lote_venda_touros.xlsx', status: 'success', animals: 850 },
  { id: 3, date: '17/03/2026', platform: 'Geneplus', file: 'reproducao_matrizes.pag', status: 'error', animals: 0 },
  { id: 4, date: '15/03/2026', platform: 'ANCP', file: 'desmama_lote_a.xlsx', status: 'success', animals: 2100 },
];

export default function HistoryPage() {
  return (
    <DashboardLayout>
      <div className="space-y-8 animate-in fade-in duration-700">
        <section className="space-y-2">
          <h1 className="text-4xl font-bold text-white tracking-tight">Histórico de Tratamentos</h1>
          <p className="text-slate-400 text-lg">Gerencie e faça download de todos os seus processamentos anteriores.</p>
        </section>

        <Card variant="bento" className="overflow-hidden p-0">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-900/50">
                <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-widest">Data</th>
                <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-widest">Plataforma</th>
                <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-widest">Arquivo Origem</th>
                <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-widest text-center">Animais</th>
                <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-widest">Status</th>
                <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-widest text-right">Ação</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {MOCK_HISTORY.map((item) => (
                <tr key={item.id} className="hover:bg-blue-500/5 transition-colors group">
                  <td className="px-6 py-5 text-sm text-slate-300 font-medium">{item.date}</td>
                  <td className="px-6 py-5">
                    <span className="flex items-center gap-2 text-sm text-white font-bold">
                      <TagIcon className="w-4 h-4 text-blue-400" />
                      {item.platform}
                    </span>
                  </td>
                  <td className="px-6 py-5 text-sm text-slate-400 font-mono italic">{item.file}</td>
                  <td className="px-6 py-5 text-sm text-slate-300 text-center font-bold">
                    {item.animals > 0 ? item.animals.toLocaleString() : '-'}
                  </td>
                  <td className="px-6 py-5">
                    {item.status === 'success' ? (
                      <span className="inline-flex items-center gap-1.5 py-1 px-3 rounded-full bg-emerald-500/10 text-emerald-400 text-xs font-bold border border-emerald-500/20">
                        <CheckCircleIcon className="w-4 h-4" />
                        Sucesso
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 py-1 px-3 rounded-full bg-red-500/10 text-red-500 text-xs font-bold border border-red-500/20">
                        <ExclamationCircleIcon className="w-4 h-4" />
                        Erro
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-5 text-right">
                    <button 
                      className={`p-2 rounded-lg transition-all ${
                        item.status === 'success' 
                        ? 'text-blue-400 hover:bg-blue-500 hover:text-white' 
                        : 'text-slate-600 cursor-not-allowed'
                      }`}
                      disabled={item.status !== 'success'}
                    >
                      <ArrowDownTrayIcon className="w-5 h-5" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </div>
    </DashboardLayout>
  );
}
