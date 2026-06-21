import React from "react";
import { Wallet, Handshake, TrendingUp, Calendar, HeartPulse } from "lucide-react";
import { DASH } from "@fm/constants/testIds";

const DEFAULT_ITEMS = [
  { icon: Wallet, label: "Finances", value: 0 },
  { icon: Handshake, label: "Commercial", value: 0 },
  { icon: TrendingUp, label: "Croissance", value: 0 },
  { icon: Calendar, label: "Organisation", value: 0 },
  { icon: HeartPulse, label: "Bien-être", value: 0 },
];

const ICONS = {
  "Finances":    Wallet,
  "Commercial":  Handshake,
  "Croissance":  TrendingUp,
  "Organisation": Calendar,
  "Bien-être":    HeartPulse,
};

function dynamicLabel(score) {
  if (score == null) return "Démarrez votre suivi pour voir votre dynamique.";
  if (score >= 80) return "Très bonne dynamique.";
  if (score >= 60) return "Dynamique solide à consolider.";
  if (score >= 40) return "Quelques signaux à surveiller.";
  if (score >= 20) return "Démarrage — il y a du travail.";
  return "Pas encore de données — renseignez vos premiers indicateurs.";
}

export default function SanteGlobale({ data }) {
  const items = (data?.items?.length ? data.items : DEFAULT_ITEMS).map((it) => ({
    ...it,
    icon: ICONS[it.label] || Wallet,
  }));
  const score = data?.score ?? 0;
  const radius = 50;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div
      data-testid={DASH.santeCard}
      className="card-cream p-6 md:p-7 rise flex flex-col"
      style={{ animationDelay: "180ms" }}
    >
      <p className="uppercase-eyebrow mb-6 !text-navy">Santé globale</p>
      <div className="flex items-center gap-6">
        <div className="relative w-[128px] h-[128px] shrink-0">
          <svg width="128" height="128" viewBox="0 0 128 128" className="-rotate-90">
            <circle cx="64" cy="64" r={radius} stroke="#EFE8D7" strokeWidth="10" fill="none" />
            <defs>
              <linearGradient id="gauge" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0" stopColor="#0B1B3A" />
                <stop offset="1" stopColor="#D6B27A" />
              </linearGradient>
            </defs>
            <circle
              cx="64"
              cy="64"
              r={radius}
              stroke="url(#gauge)"
              strokeWidth="10"
              fill="none"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              className="transition-[stroke-dashoffset] duration-700"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="font-display text-[32px] text-navy leading-none">{score}</span>
            <span className="text-[10px] tracking-wider text-ink-soft mt-1.5">/ 100</span>
          </div>
        </div>

        <div className="flex-1 space-y-2.5">
          {items.map((it, i) => {
            const Icon = it.icon;
            return (
              <div key={i} className="flex items-center gap-2.5">
                <Icon size={13} strokeWidth={1.8} className="text-ink-soft shrink-0" />
                <span className="text-[12.5px] text-ink-soft w-[88px]">{it.label}</span>
                <div className="flex-1 h-1.5 bg-sand-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-navy rounded-full transition-all duration-700"
                    style={{ width: `${it.value}%` }}
                  />
                </div>
                <span className="text-[11.5px] font-semibold text-navy w-12 text-right tabular-nums">
                  {it.value}/100
                </span>
              </div>
            );
          })}
        </div>
      </div>
      <p className="mt-auto pt-6 text-[12.5px] text-ink-soft italic font-serif-italic">
        {dynamicLabel(score)}
      </p>
    </div>
  );
}
