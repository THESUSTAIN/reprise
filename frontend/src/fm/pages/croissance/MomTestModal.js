import React from "react";
import { useEscapeClose } from "@fm/hooks/useEscapeClose";

export default function MomTestModal({ data, onClose }) {
  useEscapeClose(true, onClose);
  return (
    <div className="fixed inset-0 z-50 bg-navy/40 backdrop-blur-sm grid place-items-center p-4" data-testid="mom-test-modal" onClick={onClose}>
      <div className="bg-white rounded-2xl max-w-2xl w-full shadow-float max-h-[88vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="px-6 py-4 border-b border-sand-200 flex items-center justify-between bg-cream-soft sticky top-0">
          <div>
            <p className="text-[11px] tracking-[0.22em] uppercase text-gold-deep font-semibold">Guide d&apos;interview</p>
            <h3 className="font-display text-2xl text-navy">Mom Test · {data.questions?.length || 0} questions</h3>
          </div>
          <button onClick={onClose} className="w-9 h-9 rounded-full hover:bg-sand-200 grid place-items-center text-ink">✕</button>
        </div>
        <div className="p-6 space-y-5">
          {data.intro && (
            <div className="rounded-xl bg-cream-soft p-4 border border-sand-200">
              <p className="text-[11px] uppercase tracking-[0.18em] text-ink-soft font-semibold mb-1">Amorce</p>
              <p className="text-[14px] text-ink italic">« {data.intro} »</p>
            </div>
          )}
          <ol className="space-y-3">
            {(data.questions || []).map((q, i) => (
              <li key={i} className="rounded-xl border border-sand-200 p-4" data-testid={`mom-test-q-${i}`}>
                <div className="flex items-start gap-3">
                  <span className="font-display text-2xl text-gold-deep leading-none">{i + 1}</span>
                  <div className="flex-1">
                    <p className="text-[14px] text-navy font-medium">{q.q}</p>
                    {q.why && <p className="text-[12px] text-ink-soft mt-1 italic">→ {q.why}</p>}
                  </div>
                </div>
              </li>
            ))}
          </ol>
          {data.pitfalls?.length > 0 && (
            <div className="rounded-xl bg-red-50 border border-red-200 p-4">
              <p className="text-[11px] uppercase tracking-[0.18em] text-red-700 font-semibold mb-2">Pièges à éviter</p>
              <ul className="space-y-1.5">
                {data.pitfalls.map((p, i) => (
                  <li key={i} className="text-[13px] text-red-800 flex gap-2"><span>•</span><span>{p}</span></li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
