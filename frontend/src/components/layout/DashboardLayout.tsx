import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { AuthGuard } from "@/components/ui/auth-guard";

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export const DashboardLayout = ({ children }: DashboardLayoutProps) => {
  return (
    <AuthGuard>
      <div className="flex min-h-screen bg-deep-dark text-text-primary">
        <Sidebar />
        <div className="flex-1 flex flex-col min-w-0">
          <Header />
          <main className="flex-1 p-8 overflow-y-auto">
            <div className="max-w-7xl mx-auto w-full">{children}</div>
          </main>
          <footer className="py-6 text-center text-text-muted text-xs border-t border-white/[0.04]">
            <span className="font-mono">
              &copy; 2026 Melhora+ Biotecnologia & Genética
            </span>
            {" · "}
            <span className="text-cyan-glow/50">GENOME_ENGINE v2.0</span>
          </footer>
        </div>
      </div>
    </AuthGuard>
  );
};
