import React from "react";

// Circular gauge using pure SVG. value 0-100.
export function Gauge({ value = 0, size = 150, stroke = 12, label, sublabel, color = "#D4AF37" }) {
  const radius = (size - stroke) / 2;
  const circ = 2 * Math.PI * radius;
  const clamped = Math.max(0, Math.min(100, value));
  const offset = circ - (clamped / 100) * circ;
  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          className="text-slate-300/40 dark:text-slate-700/60"
          strokeWidth={stroke}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 0.9s cubic-bezier(0.22,1,0.36,1)" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-serif text-2xl font-semibold" style={{ color }}>
          {label ?? `${clamped}%`}
        </span>
        {sublabel && <span className="text-xs text-muted-foreground mt-0.5">{sublabel}</span>}
      </div>
    </div>
  );
}

export default Gauge;
