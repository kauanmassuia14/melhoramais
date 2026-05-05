"use client";

import { motion, AnimatePresence } from "framer-motion";
import { ExclamationTriangleIcon, CheckCircleIcon, XMarkIcon } from "@heroicons/react/24/outline";
import { useState, useEffect, ReactNode } from "react";

type ConfirmType = "danger" | "warning" | "success";

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  type?: ConfirmType;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({
  open,
  title,
  message,
  confirmText = "Confirmar",
  cancelText = "Cancelar",
  type = "danger",
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === "Escape") onCancel();
    };
    if (open) {
      document.addEventListener("keydown", handleEsc);
      document.body.style.overflow = "hidden";
    }
    return () => {
      document.removeEventListener("keydown", handleEsc);
      document.body.style.overflow = "";
    };
  }, [open, onCancel]);

  const getStyles = () => {
    switch (type) {
      case "danger":
        return {
          icon: "text-red-400",
          bg: "bg-red-500/10",
          border: "border-red-500/30",
          button: "bg-red-500 hover:bg-red-600",
        };
      case "warning":
        return {
          icon: "text-yellow-400",
          bg: "bg-yellow-500/10",
          border: "border-yellow-500/30",
          button: "bg-yellow-500 hover:bg-yellow-600",
        };
      case "success":
        return {
          icon: "text-emerald-400",
          bg: "bg-emerald-500/10",
          border: "border-emerald-500/30",
          button: "bg-emerald-500 hover:bg-emerald-600",
        };
    }
  };

  const styles = getStyles();

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onCancel}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-md z-50"
          >
            <div className={`mx-4 rounded-2xl border ${styles.border} ${styles.bg} backdrop-blur-xl shadow-2xl`}>
              <div className="p-6">
                <div className="flex items-start gap-4">
                  <div className={`p-3 rounded-xl ${styles.bg} ${styles.icon}`}>
                    <ExclamationTriangleIcon className="w-6 h-6" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-white">{title}</h3>
                    <p className="mt-2 text-sm text-slate-400 leading-relaxed">{message}</p>
                  </div>
                  <button
                    onClick={onCancel}
                    className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
                  >
                    <XMarkIcon className="w-5 h-5" />
                  </button>
                </div>
                <div className="mt-6 flex gap-3">
                  <button
                    onClick={onCancel}
                    className="flex-1 px-4 py-2.5 rounded-xl border border-white/10 text-slate-300 font-medium hover:bg-white/5 transition-colors"
                  >
                    {cancelText}
                  </button>
                  <button
                    onClick={onConfirm}
                    className={`flex-1 px-4 py-2.5 rounded-xl ${styles.button} text-white font-medium transition-colors`}
                  >
                    {confirmText}
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

interface ConfirmState {
  open: boolean;
  title: string;
  message: string;
  type?: ConfirmType;
  onConfirm?: () => void;
}

const confirmDefault: ConfirmState = {
  open: false,
  title: "",
  message: "",
};

let confirmResolve: ((confirmed: boolean) => void) | null = null;

export function useConfirm() {
  const [state, setState] = useState<ConfirmState>(confirmDefault);

  const confirm = (options: {
    title: string;
    message: string;
    type?: ConfirmType;
  }): Promise<boolean> => {
    return new Promise((resolve) => {
      confirmResolve = resolve;
      setState({
        open: true,
        title: options.title,
        message: options.message,
        type: options.type || "danger",
      });
    });
  };

  const handleConfirm = () => {
    setState(confirmDefault);
    if (confirmResolve) {
      confirmResolve(true);
      confirmResolve = null;
    }
  };

  const handleCancel = () => {
    setState(confirmDefault);
    if (confirmResolve) {
      confirmResolve(false);
      confirmResolve = null;
    }
  };

  return { confirm, dialog: state.open ? (
    <ConfirmDialog
      open={state.open}
      title={state.title}
      message={state.message}
      type={state.type}
      onConfirm={handleConfirm}
      onCancel={handleCancel}
    />
  ) : null };
}