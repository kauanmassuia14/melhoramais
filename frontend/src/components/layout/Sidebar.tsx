'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  HomeIcon, 
  ClockIcon, 
  ChartBarIcon, 
  Cog6ToothIcon, 
  ArrowRightOnRectangleIcon,
  BeakerIcon 
} from '@heroicons/react/24/outline';

const MENU_ITEMS = [
  { id: 'dashboard', label: 'Dashboard', icon: HomeIcon, href: '/' },
  { id: 'history', label: 'Histórico', icon: ClockIcon, href: '/history' },
  { id: 'analytics', label: 'Análises', icon: ChartBarIcon, href: '/analytics' },
  { id: 'settings', label: 'Configurações', icon: Cog6ToothIcon, href: '/settings' },
];

export const Sidebar = () => {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-900/20 backdrop-blur-md hidden lg:flex flex-col p-6 space-y-8 sticky top-0 h-screen">
      <div className="flex items-center gap-3 px-2">
        <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center shadow-lg shadow-blue-600/20">
          <BeakerIcon className="w-5 h-5 text-white" />
        </div>
        <span className="text-xl font-bold gradient-text tracking-tight">Melhora+</span>
      </div>

      <nav className="flex-1 space-y-2">
        {MENU_ITEMS.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link 
              key={item.id}
              href={item.href} 
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-300 ${
                isActive 
                ? 'bg-blue-600/10 text-blue-400 border border-blue-500/20' 
                : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
              }`}
            >
              <item.icon className="w-5 h-5" />
              <span className="font-medium text-sm">{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="pt-6 border-t border-slate-800 space-y-4">
        <Link 
          href="/login" 
          className="flex items-center gap-3 px-3 py-2 text-slate-400 hover:text-white transition-colors group"
        >
          <ArrowRightOnRectangleIcon className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          <span className="font-medium text-sm">Sair</span>
        </Link>
      </div>
    </aside>
  );
};
