'use client';

import { CheckCircleIcon } from '@heroicons/react/24/outline';
import { Card } from '@/components/ui/Card';

interface Platform {
  id: string;
  name: string;
  description: string;
  icon: string;
}

interface PlatformPickerProps {
  platforms: Platform[];
  selectedId: string;
  onSelect: (id: string) => void;
}

export const PlatformPicker = ({ platforms, selectedId, onSelect }: PlatformPickerProps) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {platforms.map((p) => {
        const isSelected = selectedId === p.id;
        return (
          <button
            key={p.id}
            onClick={() => onSelect(p.id)}
            className="group relative text-left outline-none"
          >
            <Card 
              variant="bento" 
              className={`h-full p-8 transition-all duration-500 overflow-hidden ${
                isSelected 
                ? 'border-blue-500/50 bg-blue-500/5 shadow-lg shadow-blue-500/10' 
                : 'border-slate-800 bg-slate-900/40 hover:border-slate-700'
              }`}
            >
              <div className={`absolute top-0 right-0 p-4 transition-all duration-500 ${isSelected ? 'opacity-100' : 'opacity-0'}`}>
                <CheckCircleIcon className="w-6 h-6 text-blue-400" />
              </div>
              
              <div className="text-4xl mb-6 grayscale group-hover:grayscale-0 transition-all duration-500 scale-100 group-hover:scale-110">
                {p.icon}
              </div>
              
              <div className="space-y-2">
                <h3 className="font-bold text-xl text-white group-hover:text-blue-400 transition-colors">
                  {p.name}
                </h3>
                <p className="text-sm text-slate-400 leading-relaxed group-hover:text-slate-300 transition-colors">
                  {p.description}
                </p>
              </div>
            </Card>
          </button>
        );
      })}
    </div>
  );
};
