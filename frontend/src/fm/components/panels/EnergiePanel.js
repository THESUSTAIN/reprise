import React, { useState } from "react";
import SidePanel from "./SidePanel";
import { PANEL } from "@fm/constants/testIds";
import { energyApi } from "@fm/lib/api";

const FORMS = [
  { id: 1, emoji: "😞", label: "Fatigué" },
  { id: 2, emoji: "😐", label: "Mitigé" },
  { id: 3, emoji: "🙂", label: "Bien" },
  { id: 4, emoji: "😄", label: "Très bien" },
  { id: 5, emoji: "🤩", label: "En feu" },
];

export default function EnergiePanel({ open, onClose, onSave }) {
  const [forme, setForme] = useState(4);
  const [stress, setStress] = useState(3);
  const [focus, setFocus] = useState(7);

  return (
    <SidePanel
      open={open}
      onClose={onClose}
      title="Check-in du jour"
      subtitle="Une minute pour faire le point."
      width={420}
      testId={PANEL.energie}
      closeTestId={PANEL.energieClose}
    >
      <div className="p-7 space-y-7">
        <div>
          <p className="uppercase-eyebrow mb-3">😀 Forme</p>
          <div className="flex items-center justify-between gap-1.5">
            {FORMS.map((f) => {
              const active = forme === f.id;
              return (
                <button
                  key={f.id}
                  data-testid={`energie-forme-${f.id}`}
                  onClick={() => setForme(f.id)}
                  className={`flex flex-col items-center gap-1.5 p-2 rounded-2xl flex-1 transition-all ${
                    active
                      ? "bg-navy text-white"
                      : "bg-white hover:bg-sand-100"
                  }`}
                >
                  <span className="text-xl">{f.emoji}</span>
                  <span className="text-[10.5px] font-medium">{f.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        <RangeBlock
          eyebrow="😐 Stress"
          value={stress}
          onChange={setStress}
          testId="energie-stress-range"
          leftLabel="Calme"
          rightLabel="Tendu"
        />

        <RangeBlock
          eyebrow="🎯 Focus"
          value={focus}
          onChange={setFocus}
          testId="energie-focus-range"
          leftLabel="Dispersé"
          rightLabel="Aligné"
        />

        <button
          data-testid={PANEL.energieSave}
          onClick={async () => {
            try { await energyApi.save({ forme, stress, focus }); } catch {}
            onSave?.({ forme, stress, focus });
            onClose?.();
          }}
          className="w-full h-12 rounded-full bg-navy text-white text-sm font-semibold hover:bg-navy-hover transition-colors"
        >
          Enregistrer
        </button>
      </div>
    </SidePanel>
  );
}

function RangeBlock({ eyebrow, value, onChange, testId, leftLabel, rightLabel }) {
  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <p className="uppercase-eyebrow">{eyebrow}</p>
        <span className="text-[12.5px] font-semibold text-slate-800 tabular-nums">
          {value}/10
        </span>
      </div>
      <input
        type="range"
        min={0}
        max={10}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="slider-zen w-full"
        data-testid={testId}
      />
      <div className="flex justify-between text-[11px] text-slate-500 mt-1.5">
        <span>{leftLabel}</span>
        <span>{rightLabel}</span>
      </div>
    </div>
  );
}
