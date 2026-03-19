import { Sidebar } from './Sidebar';
import { Header } from './Header';

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export const DashboardLayout = ({ children }: DashboardLayoutProps) => {
  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-200 selection:bg-blue-500/30">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 bg-slate-950/50 overflow-y-auto">
        <Header />
        <main className="flex-1 p-8 overflow-y-auto">
          <div className="max-w-7xl mx-auto w-full">
            {children}
          </div>
        </main>
        
        <footer className="mt-auto py-8 text-center text-slate-600 text-sm border-t border-slate-900">
          &copy; 2026 Melhora+ Biotecnologia & Genética. Todos os direitos reservados.
        </footer>
      </div>
    </div>
  );
};
