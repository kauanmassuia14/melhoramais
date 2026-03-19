'use client';

import { 
  BellIcon, 
  UserCircleIcon, 
  MagnifyingGlassIcon 
} from '@heroicons/react/24/outline';

export const Header = () => {
  return (
    <header className="h-16 border-b border-slate-800 flex items-center justify-between px-8 bg-slate-950/80 backdrop-blur-sm sticky top-0 z-10 w-full">
      {/* Search bar */}
      <div className="flex items-center bg-slate-900/50 border border-slate-800 rounded-lg px-3 py-1.5 w-96 group focus-within:border-blue-500/50 transition-all">
        <MagnifyingGlassIcon className="w-4 h-4 text-slate-500 group-focus-within:text-blue-400" />
        <input 
          type="text" 
          placeholder="Buscar relatórios..." 
          className="bg-transparent border-none outline-none text-sm px-2 w-full placeholder:text-slate-600 text-slate-200" 
        />
      </div>

      {/* Profile & Notifications */}
      <div className="flex items-center gap-4">
        <button className="p-2 text-slate-400 hover:text-white transition-colors relative">
          <BellIcon className="w-6 h-6" />
          <span className="absolute top-2 right-2 w-2 h-2 bg-blue-500 rounded-full border border-slate-950"></span>
        </button>
        
        <div className="h-8 w-[1px] bg-slate-800 mx-2"></div>
        
        <div className="flex items-center gap-3">
          <div className="text-right hidden sm:block">
            <p className="text-sm font-medium text-white">Genética Ltda.</p>
            <p className="text-xs text-slate-500">Administrador</p>
          </div>
          <UserCircleIcon className="w-8 h-8 text-slate-400" />
        </div>
      </div>
    </header>
  );
};
