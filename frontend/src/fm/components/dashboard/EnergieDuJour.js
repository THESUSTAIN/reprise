import React, { useState, useEffect } from "react";
import { DASH } from "@fm/constants/testIds";
import { energyApi } from "@fm/lib/api";

const MOODS = [
  { id: 1, label: "Très bas", emoji: "😞" },
  { id: 2, label: "Bas", emoji: "😐" },
  { id: 3, label: "Bien", emoji: "🙂" },
  { id: 4, label: "Très bien", emoji: "😄" },
  { id: 5, label: "Excellent", emoji: "🤩" },
];

export default function EnergieDuJour() {
  const [mood, setMood] = useState(5);
  const [stress, setStress] = useState(3);
  const [focus, setFocus] = useState(7);
  const [saved, setSaved] = useState(false);

  // Load the latest check-in
  useEffect(() => {
    energyApi.latest().then((d) => {
      if (d?.forme) {
        setMood(d.forme);
        setStress(d.stress);
        setFocus(d.focus);
        setSaved(true);
      }
    }).catch(() => {});
  }, []);

  const save = async () => {
    try {
      await energyApi.save({ forme: mood, stress, focus });
      setSaved(true);
      setTimeout(() => setSaved(false), 2400);
    } catch {}
  };

  return (
    <div
      className="card-cream p-6 md:p-7 rise flex flex-col"
      style={{ animationDelay: "240ms" }}
    >
      <p className="uppercase-eyebrow mb-6 !text-navy">Énergie du jour</p>
      <p className="text-[13.5px] text-ink-soft mb-4">Comment vous sentez-vous ?</p>

      <div
        className="flex items-center justify-between gap-1.5 mb-6"
        data-testid={DASH.energieMood}
      >
        {MOODS.map((m) => {
          const active = mood === m.id;
          return (
            <button
              key={m.id}
              data-testid={`mood-${m.id}`}
              onClick={() => setMood(m.id)}
              aria-label={m.label}
              className={`w-11 h-11 rounded-full text-lg grid place-items-center transition-all ${
                active
                  ? "bg-navy text-cream scale-110 shadow-soft"
                  : "bg-cream-soft hover:bg-sand-200 grayscale hover:grayscale-0"
              }`}
            >
              <span className={active ? "" : "opacity-70"}>{m.emoji}</span>
            </button>
          );
        })}
      </div>

      <Slider label="Stress" value={stress} max={10} onChange={setStress} testId="energie-stress" />
      <Slider label="Focus" value={focus} max={10} onChange={setFocus} testId="energie-focus" />

      <button
        data-testid={DASH.energieSave}
        onClick={save}
        className="mt-auto w-full h-12 rounded-full bg-navy text-cream text-sm font-semibold hover:bg-navy-bright transition-colors"
      >
        {saved ? "✓ Enregistré" : "Enregistrer"}
      </button>
    </div>
  );
}

function Slider({ label, value, max, onChange, testId }) {
  return (
    <div className="mb-4">
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-[13px] text-ink-soft">{label}</span>
        <span className="text-[12.5px] font-semibold text-navy tabular-nums">
          {value}/{max}
        </span>
      </div>
      <input
        type="range"
        min={0}
        max={max}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="slider-zen w-full"
        data-testid={testId}
      />
    </div>
  );
}
