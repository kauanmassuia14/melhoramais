'use client';

import Link from 'next/link';
import { BeakerIcon, UserPlusIcon, EnvelopeIcon, LockClosedIcon, UserIcon } from '@heroicons/react/24/outline';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

export default function RegisterPage() {
  return (
    <main className="min-h-screen flex bg-slate-950 overflow-hidden">
      {/* Left Side: Immersive Visuals */}
      <section className="hidden lg:flex lg:w-1/2 relative flex-col justify-between p-12 mesh-bg overflow-hidden">
        {/* Decorative Blur */}
        <div className="absolute top-[-10%] right-[-10%] w-[60%] h-[60%] bg-blue-600/20 rounded-full blur-[120px] animate-pulse" />
        <div className="absolute bottom-[-10%] left-[-10%] w-[60%] h-[60%] bg-emerald-600/10 rounded-full blur-[120px] animate-pulse" />

        {/* Brand */}
        <div className="relative z-10 flex items-center gap-3">
          <div className="w-12 h-12 bg-white/10 backdrop-blur-xl rounded-2xl flex items-center justify-center border border-white/20 shadow-2xl">
            <BeakerIcon className="w-7 h-7 text-white" />
          </div>
          <span className="text-3xl font-bold text-white tracking-tighter">Melhora+</span>
        </div>

        {/* Tagline */}
        <div className="relative z-10 space-y-6">
          <h1 className="text-6xl font-bold text-white leading-[1.1] tracking-tight">
            Crie sua conta <br />
            <span className="gradient-text italic font-serif">Acelere seu sucesso.</span>
          </h1>
          <p className="text-xl text-slate-300/80 max-w-md leading-relaxed">
            Faça parte da plataforma que está transformando a gestão de dados genéticos no Brasil e no mundo.
          </p>
        </div>

        {/* Footer info */}
        <div className="relative z-10">
          <p className="text-slate-400 font-medium">Junte-se à comunidade Melhora+ hoje.</p>
        </div>
      </section>

      {/* Right Side: Clean Form */}
      <section className="w-full lg:w-1/2 flex items-center justify-center p-8 bg-slate-950 border-l border-slate-900 shadow-[-20px_0px_60px_rgba(0,0,0,0.5)]">
        <div className="w-full max-w-sm space-y-10">
          <div className="space-y-4">
            <h2 className="text-4xl font-bold text-white tracking-tight">Comece sua jornada</h2>
            <p className="text-slate-400">Preencha os dados abaixo para criar seu perfil.</p>
          </div>

          <form className="space-y-5" onSubmit={(e) => e.preventDefault()}>
            <Input 
              label="Nome Completo" 
              placeholder="Ex: João da Silva" 
              type="text"
              icon={<UserIcon className="w-5 h-5" />}
            />
            <Input 
              label="E-mail Profissional" 
              placeholder="nome@empresa.com" 
              type="email"
              icon={<EnvelopeIcon className="w-5 h-5" />}
            />
            <div className="grid grid-cols-1 gap-5">
              <Input 
                label="Senha Forte" 
                placeholder="••••••••" 
                type="password"
                icon={<LockClosedIcon className="w-5 h-5" />}
              />
              <Input 
                label="Confirmar Senha" 
                placeholder="••••••••" 
                type="password"
                icon={<LockClosedIcon className="w-5 h-5" />}
              />
            </div>

            <Button className="w-full group mt-4">
              Criar Conta Gratuita
              <UserPlusIcon className="w-5 h-5 ml-2 group-hover:scale-110 transition-transform" />
            </Button>
          </form>

          <div className="pt-8 border-t border-slate-900 text-center">
            <p className="text-slate-500">
              Já possui uma conta?{' '}
              <Link href="/login" className="text-blue-400 hover:text-blue-300 font-bold transition-all">
                Fazer Login
              </Link>
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}
