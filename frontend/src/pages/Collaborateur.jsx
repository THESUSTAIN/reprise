import { useState } from "react";
import { Users, ArrowRight, Map } from "lucide-react";
import { toast } from "sonner";
import { sendCopilotWorkRequest } from "../lib/api";

// Page "Collaborateur" — reprise de la maquette de design, branchee sur le
// vrai endpoint deja existant POST /api/growth/work-request (enregistre la
// demande + notifie l'equipe par email, best-effort). Rien de fabrique :
// si l'envoi echoue, l'utilisateur le voit.
const NIVEAUX = [
  { value: "avec", label: "Faire avec moi" },
  { value: "analyser", label: "Analyser avec moi" },
  { value: "preparer", label: "Préparer pour moi" },
  { value: "executer", label: "Exécuter après validation" },
];

export default function Collaborateur() {
  const [message, setMessage] = useState("");
  const [niveau, setNiveau] = useState("avec");
  const [contact, setContact] = useState("");
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);

  const submit = async () => {
    if (!message.trim()) return;
    setSending(true);
    try {
      const res = await sendCopilotWorkRequest({ message: `[${NIVEAUX.find((n) => n.value === niveau)?.label}] ${message.trim()}`, contact, channel: "collaborateur" });
      if (res?.ok === false) throw new Error(res.error || "Échec");
      setSent(true);
      toast.success("Demande envoyée à l'équipe.");
    } catch {
      toast.error("Échec de l'envoi — réessaie dans un instant.");
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="page-collaborateur">
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-[.14em] text-[#DEC2A3]">Collaborateur Zayado</p>
        <h1 className="font-head text-2xl sm:text-3xl font-semibold text-white mt-1">Ne portez pas tout seul.</h1>
        <p className="text-white/55 text-sm mt-1 max-w-xl">Demandez à une personne de clarifier, construire, analyser ou préparer avec vous.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[1.4fr_1fr] gap-4">
        <div className="glass p-6">
          <div className="flex items-center gap-2 mb-4">
            <span className="w-9 h-9 rounded-lg gold-bg flex items-center justify-center shrink-0"><Users size={17} className="text-[#0A1128]" /></span>
            <span className="text-[11px] font-semibold uppercase tracking-wide text-[#DEC2A3]">Demande structurée</span>
          </div>
          <h2 className="font-head text-lg font-semibold text-white mb-4">De quoi avez-vous besoin ?</h2>

          <label className="block text-xs text-white/60 mb-1.5">Votre besoin</label>
          <textarea value={message} onChange={(e) => setMessage(e.target.value)} rows={4}
            placeholder="Ex. analyser mon offre, préparer une prospection ou clarifier une priorité…"
            className="w-full rounded-xl border border-white/15 bg-white/5 px-3.5 py-2.5 text-sm text-white placeholder:text-white/35 focus:outline-none focus:border-[#DEC2A3]/50" />

          <label className="block text-xs text-white/60 mb-1.5 mt-4">Niveau d'aide</label>
          <select value={niveau} onChange={(e) => setNiveau(e.target.value)}
            className="w-full rounded-xl border border-white/15 bg-white/5 px-3.5 py-2.5 text-sm text-white/85">
            {NIVEAUX.map((n) => <option key={n.value} value={n.value}>{n.label}</option>)}
          </select>

          <label className="block text-xs text-white/60 mb-1.5 mt-4">Email de contact (optionnel)</label>
          <input value={contact} onChange={(e) => setContact(e.target.value)} placeholder="vous@exemple.fr"
            className="w-full rounded-xl border border-white/15 bg-white/5 px-3.5 py-2.5 text-sm text-white placeholder:text-white/35 focus:outline-none focus:border-[#DEC2A3]/50" />

          <button onClick={submit} disabled={sending || !message.trim()} data-testid="collaborateur-submit"
            className="mt-5 inline-flex items-center gap-1.5 rounded-xl gold-bg px-5 py-2.5 text-sm font-semibold text-[#0A1128] disabled:opacity-50">
            {sent ? "Demande enregistrée" : sending ? "Envoi…" : "Valider ma demande"} <ArrowRight size={15} />
          </button>
        </div>

        <div className="glass p-6">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-[#DEC2A3] mb-3">Transparence</p>
          <h2 className="font-head text-lg font-semibold text-white mb-2">Vous gardez la validation finale.</h2>
          <p className="text-[13px] text-white/55 leading-relaxed">
            Le Collaborateur ne reçoit que les éléments que vous choisissez de partager. Le délai, le périmètre et le statut sont visibles avant l'exécution.
          </p>
          <div className="mt-5 space-y-2.5 text-sm text-white/70">
            <div className="flex items-center gap-2"><span className={`w-1.5 h-1.5 rounded-full ${sent ? "bg-emerald-400" : "bg-white/25"}`} /> Demande envoyée</div>
            <div className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-white/25" /> Collaborateur assigné</div>
            <div className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-white/25" /> À valider</div>
          </div>
        </div>
      </div>

      <section className="glass p-6" data-testid="collaborateur-roadmap">
        <div className="flex items-start gap-3">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-white/15 bg-white/[.06] text-[#F1E2CC]"><Map size={19} /></span>
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[.14em] text-[#DEC2A3]">Roadmap d’accompagnement</p>
            <h2 className="font-head mt-1 text-xl font-semibold text-white">Votre demande devient une feuille de route à valider.</h2>
            <p className="mt-2 max-w-2xl text-sm leading-relaxed text-white/60">La Roadmap ne vit plus comme un module isolé. Elle commence ici : clarification du besoin, proposition de périmètre, puis validation de votre part avant toute exécution.</p>
          </div>
        </div>
        <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-3">
          {["Clarifier votre objectif", "Cadrer le périmètre et le délai", "Valider avant l’exécution"].map((label, index) => <div key={label} className="flex items-center gap-3 rounded-xl border border-white/12 bg-white/[.04] p-3"><span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#DEC2A3]/15 text-xs font-bold text-[#F1E2CC]">{index + 1}</span><span className="text-sm text-white/75">{label}</span></div>)}
        </div>
      </section>
    </div>
  );
}
