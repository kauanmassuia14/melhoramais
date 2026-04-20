"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

interface AuthGuardProps {
  children: React.ReactNode;
}

export function AuthGuard({ children }: AuthGuardProps) {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const [hasChecked, setHasChecked] = useState(false);

  useEffect(() => {
    if (!isLoading) {
      const storedToken = localStorage.getItem("access_token");
      const storedUser = localStorage.getItem("user");
      
      if (!storedToken || !storedUser) {
        router.push("/login");
      } else {
        setHasChecked(true);
      }
    }
  }, [isLoading, router]);

  if (isLoading || !hasChecked) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-deep-dark">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-cyan-glow/30 border-t-cyan-glow rounded-full animate-spin" />
          <p className="text-text-muted text-sm">Carregando...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
