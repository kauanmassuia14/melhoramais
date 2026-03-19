import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "Melhora+ | Unificador de Dados Genéticos",
  description: "Transforme relatórios brutos em insights padronizados com inteligência e precisão.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="pt-BR"
      className={`${inter.variable} h-full antialiased dark`}
    >
      <body className="min-h-full bg-slate-950 font-sans selection:bg-blue-500/30">
        {children}
      </body>
    </html>
  );
}
