"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDownIcon } from "@heroicons/react/24/outline";

interface SelectOption {
  value: string | number;
  label: string;
}

interface SelectProps {
  value: string | number | "";
  onChange: (value: string | number) => void;
  options: SelectOption[];
  placeholder?: string;
  label?: string;
  className?: string;
}

export function Select({
  value,
  onChange,
  options,
  placeholder = "Selecione...",
  label,
  className = "",
}: SelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const selectedOption = options.find((opt) => opt.value === value);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className={className}>
      {label && (
        <label className="block text-sm text-text-secondary mb-2">{label}</label>
      )}
      <div ref={ref} className="relative">
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-left flex items-center justify-between hover:bg-white/10 hover:border-white/20 transition-all focus:outline-none focus:border-emerald-glow/50 focus:ring-2 focus:ring-emerald-glow/10"
        >
          <span className={selectedOption ? "text-white" : "text-text-muted"}>
            {selectedOption?.label || placeholder}
          </span>
          <ChevronDownIcon
            className={`w-5 h-5 text-text-muted transition-transform ${
              isOpen ? "rotate-180" : ""
            }`}
          />
        </button>

        <AnimatePresence>
          {isOpen && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.15 }}
              className="absolute top-full left-0 right-0 mt-2 bg-surface-1 border border-white/10 rounded-xl overflow-hidden z-50 shadow-xl"
            >
              <div className="max-h-60 overflow-y-auto py-1">
                {options.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => {
                      onChange(option.value);
                      setIsOpen(false);
                    }}
                    className={`w-full px-4 py-2.5 text-left hover:bg-white/5 transition-colors flex items-center ${
                      option.value === value
                        ? "text-emerald-glow-400 bg-emerald-glow/[0.08]"
                        : "text-text-primary"
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

interface NativeSelectProps {
  value: string | number | "";
  onChange: (value: string | number) => void;
  options: SelectOption[];
  placeholder?: string;
  label?: string;
  className?: string;
}

export function NativeSelect({
  value,
  onChange,
  options,
  placeholder = "Selecione...",
  label,
  className = "",
}: NativeSelectProps) {
  return (
    <div className={className}>
      {label && (
        <label className="block text-sm text-text-secondary mb-2">{label}</label>
      )}
      <select
        value={value}
        onChange={(e) => onChange(e.target.value ? Number(e.target.value) : "")}
        className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-emerald-glow/50 focus:ring-2 focus:ring-emerald-glow/10 transition-all appearance-none cursor-pointer"
      >
        <option value="">{placeholder}</option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}