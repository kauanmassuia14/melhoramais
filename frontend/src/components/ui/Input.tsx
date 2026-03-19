import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: React.ReactNode;
}

export const Input = ({ label, error, icon, className = '', ...props }: InputProps) => {
  return (
    <div className="space-y-2 w-full group">
      {label && (
        <label className="text-sm font-medium text-slate-400 ml-1 transition-colors group-focus-within:text-blue-400">
          {label}
        </label>
      )}
      <div className="relative flex items-center">
        {icon && (
          <div className="absolute left-4 text-slate-500 group-focus-within:text-blue-500 transition-colors">
            {icon}
          </div>
        )}
        <input
          className={`input-premium ${icon ? 'pl-12' : ''} ${error ? 'border-red-500 focus:ring-red-500/50' : ''} ${className}`}
          {...props}
        />
      </div>
      {error && <p className="text-xs text-red-500 ml-1 font-medium">{error}</p>}
    </div>
  );
};
