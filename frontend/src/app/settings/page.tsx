'use client';

import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { 
  UserIcon, 
  ShieldCheckIcon, 
  BellAlertIcon,
  KeyIcon,
  AdjustmentsHorizontalIcon
} from '@heroicons/react/24/outline';

export default function SettingsPage() {
  return (
    <DashboardLayout>
      <div className="space-y-8 animate-in fade-in duration-700">
        <section className="space-y-2">
          <h1 className="text-4xl font-bold text-white tracking-tight">Configurações</h1>
          <p className="text-slate-400 text-lg">Personalize sua experiência e gerencie os parâmetros do sistema.</p>
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar Settings Nav */}
          <aside className="lg:col-span-1 space-y-2">
            <SettingsNavItem icon={<UserIcon className="w-5 h-5" />} label="Perfil do Usuário" active />
            <SettingsNavItem icon={<ShieldCheckIcon className="w-5 h-5" />} label="Segurança & Acesso" />
            <SettingsNavItem icon={<AdjustmentsHorizontalIcon className="w-5 h-5" />} label="Mapeamentos" />
            <SettingsNavItem icon={<BellAlertIcon className="w-5 h-5" />} label="Notificações" />
            <SettingsNavItem icon={<KeyIcon className="w-5 h-5" />} label="Chaves de API" />
          </aside>

          {/* Settings Content */}
          <div className="lg:col-span-3 space-y-8">
            <Card variant="bento" className="space-y-8">
              <div className="border-b border-slate-800 pb-6">
                <h2 className="text-2xl font-bold text-white">Informações do Perfil</h2>
                <p className="text-sm text-slate-500">Atualize sua foto e dados pessoais.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Input label="Nome" defaultValue="Administrador" />
                <Input label="E-mail" defaultValue="admin@geneticasolutions.com" disabled />
                <Input label="Organização" defaultValue="Genética Solutions Ltda." />
                <Input label="Cargo" defaultValue="Diretor Técnico" />
              </div>

              <div className="pt-4 flex gap-4">
                <Button variant="primary">Salvar Alterações</Button>
                <Button variant="secondary">Cancelar</Button>
              </div>
            </Card>

            <Card variant="bento" className="space-y-8 border-red-500/20 bg-red-500/5">
              <div className="border-b border-red-500/10 pb-6">
                <h2 className="text-2xl font-bold text-white">Zona de Risco</h2>
                <p className="text-sm text-slate-500">Ações irreversíveis sobre sua conta e dados.</p>
              </div>

              <div className="flex flex-col md:flex-row items-center justify-between gap-6 p-6 bg-slate-900/50 rounded-2xl border border-slate-800">
                <div className="space-y-1">
                  <p className="font-bold text-white">Deletar Conta</p>
                  <p className="text-xs text-slate-500">Isso apagará permanentemente todos os seus logs e configurações.</p>
                </div>
                <Button variant="danger" size="sm">Deletar Permanentemente</Button>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

function SettingsNavItem({ icon, label, active = false }: any) {
  return (
    <button className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${active ? 'bg-blue-600/10 text-blue-400 border border-blue-500/20 font-bold' : 'text-slate-500 hover:text-white hover:bg-slate-900/50 uppercase tracking-widest text-[10px]'}`}>
      {icon}
      <span>{label}</span>
    </button>
  );
}
