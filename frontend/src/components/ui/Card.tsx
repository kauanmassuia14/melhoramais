import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  variant?: 'bento' | 'glass' | 'simple';
  hoverable?: boolean;
}

export const Card = ({ children, className = '', variant = 'bento', hoverable = true }: CardProps) => {
  const variants = {
    bento: 'bento-card',
    glass: 'glass-card',
    simple: 'bg-slate-900/40 border border-slate-800/60 rounded-2xl p-6',
  };

  const hoverEffect = hoverable ? 'transition-all duration-500 hover:translate-y-[-4px] hover:shadow-2xl hover:shadow-blue-500/10' : '';

  return (
    <div className={`${variants[variant]} ${hoverEffect} ${className}`}>
      {children}
    </div>
  );
};
