import React from "react";
import { X, MessageCircle, Loader2 } from "lucide-react";

function Field({ label, children }) {
  return (
    <label className="block">
      <span className="text-[11.5px] uppercase tracking-wider text-ink-soft font-semibold block mb-1.5">{label}</span>
      {children}
    </label>
  );
}

export default function WaComposer({ waLead, setWaLead, onSend, sending, isPremium }) {
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-navy/40 backdrop-blur-sm fade-in p-4" onClick={() => setWaLead(null)}>
      <div className="card-cream p-6 w-full max-w-md rise" onClick={(e) => e.stopPropagation()} data-testid="wa-composer">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-display text-[22px] text-navy flex items-center gap-2">
            <MessageCircle size={18} className="text-emerald-600" /> WhatsApp à {waLead.lead.name}
          </h3>
          <button onClick={() => setWaLead(null)} className="w-8 h-8 grid place-items-center rounded-full hover:bg-sand-200"><X size={16} /></button>
        </div>
        {!isPremium && (
          <div className="mb-4 p-3 rounded-xl bg-cream-soft border border-sand-300" data-testid="wa-free-banner">
            <p className="text-[12px] text-ink leading-relaxed">
              <strong className="text-navy">Mode Free</strong> · le bouton ouvre WhatsApp dans un nouvel onglet avec votre message pré-rempli. Vous validez et envoyez manuellement.
            </p>
          </div>
        )}
        <Field label="Numéro (format E.164, ex : +33612345678)">
          <input data-testid="wa-phone-input" autoFocus value={waLead.phone}
            onChange={(e) => setWaLead({ ...waLead, phone: e.target.value })}
            placeholder="+33..."
            className="w-full h-10 px-3 rounded-xl bg-white border border-sand-300 text-[14px] focus:outline-none focus:border-navy/50" />
        </Field>
        <Field label="Message">
          <textarea data-testid="wa-message-input" rows={5} value={waLead.message}
            onChange={(e) => setWaLead({ ...waLead, message: e.target.value })}
            className="w-full px-3 py-2.5 rounded-xl bg-white border border-sand-300 text-[14px] focus:outline-none focus:border-navy/50 resize-none" />
        </Field>
        <div className="flex justify-end gap-2 mt-4">
          <button onClick={() => setWaLead(null)} className="px-4 h-10 rounded-full bg-cream-soft text-ink hover:bg-sand-200 text-[13px] font-medium">Annuler</button>
          <button data-testid="wa-send-btn" onClick={onSend} disabled={sending}
            className="inline-flex items-center gap-2 px-5 h-10 rounded-full bg-emerald-600 text-white text-[13px] font-semibold hover:bg-emerald-700 transition-colors disabled:opacity-50">
            {sending ? <Loader2 size={14} className="animate-spin" /> : <MessageCircle size={14} />}
            {isPremium ? "Envoyer (auto)" : "Ouvrir WhatsApp"}
          </button>
        </div>
      </div>
    </div>
  );
}
