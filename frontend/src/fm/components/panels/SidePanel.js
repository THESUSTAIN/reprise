import React, { useEffect } from "react";
import { X } from "lucide-react";

export default function SidePanel({
  open,
  onClose,
  title,
  subtitle,
  width = 420,
  testId,
  closeTestId,
  children,
  variant = "light",
}) {
  // Lock scroll
  useEffect(() => {
    if (open) {
      const prev = document.body.style.overflow;
      document.body.style.overflow = "hidden";
      return () => {
        document.body.style.overflow = prev;
      };
    }
  }, [open]);

  // Escape to close
  useEffect(() => {
    if (!open) return;
    const onKey = (e) => e.key === "Escape" && onClose?.();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  const isDark = variant === "dark";

  return (
    <div className="fixed inset-0 z-50">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-navy/30 backdrop-blur-[2px] fade-in"
        onClick={onClose}
        data-testid={`${testId}-backdrop`}
      />
      <aside
        data-testid={testId}
        style={{ width: `min(${width}px, 92vw)` }}
        className={`absolute top-0 right-0 h-full slide-in-right shadow-float rounded-l-[32px] flex flex-col overflow-hidden ${
          isDark ? "bg-navy text-white" : "bg-[#FCFBF9] text-slate-900"
        }`}
      >
        <div
          className={`flex items-start justify-between gap-4 px-7 pt-7 pb-4 border-b ${
            isDark ? "border-white/10" : "border-sand-200"
          }`}
        >
          <div>
            <h3
              className={`font-serif text-2xl leading-tight ${
                isDark ? "text-white" : "text-navy"
              }`}
            >
              {title}
            </h3>
            {subtitle && (
              <p
                className={`mt-1 text-[13px] ${
                  isDark ? "text-white/60" : "text-slate-500"
                }`}
              >
                {subtitle}
              </p>
            )}
          </div>
          <button
            data-testid={closeTestId}
            onClick={onClose}
            aria-label="Fermer"
            className={`w-9 h-9 rounded-full grid place-items-center transition-colors ${
              isDark
                ? "bg-white/10 hover:bg-white/15 text-white"
                : "bg-sand-100 hover:bg-sand-200 text-slate-700"
            }`}
          >
            <X size={16} strokeWidth={2} />
          </button>
        </div>
        <div className="flex-1 min-h-0 flex flex-col overflow-hidden">{children}</div>
      </aside>
    </div>
  );
}
