import { useEffect, useState } from "react";
import { ArrowRight, Feather, Wind, Play, Square } from "lucide-react";
import { toast } from "sonner";
import { getHumeur, createHumeur, authMe } from "../lib/api";

// Mon Refuge — l'espace où l'on souffle. Aucune performance attendue ici :
// un check-in d'énergie (vraies données wellness), une respiration guidée,
// une pensée du jour, et le Mode Foi qui ajoute un verset.
// Tout ce qui s'affiche est réel : les check-ins viennent de l'API et le
// choix Foi est conservé localement (lu aussi par la page Aujourd'hui).

const CLE_FOI = "mx_foi";

const openCopilot = (ask) =>
  window.dispatchEvent(new CustomEvent("cours:open-copilot", { detail: ask ? { ask } : {} }));

const HUMEURS = ["Épuisé", "Fatigué", "Bien", "Motivé", "En feu"];

const PENSEES = [
  "« Tu n'as pas besoin de voir tout l'escalier. Juste la première marche. »",
  "« Aujourd'hui, tenir compte autant que construire. Tu n'as pas à tout porter. »",
  "« La journée s'adapte à ta batterie, pas l'inverse. »",
  "« Une marche suffit. Elle compte déjà. »",
];

const VERSETS = [
  { ref: "Psaume 46:2", texte: "« Dieu est pour nous un refuge et un appui, un secours qui ne manque jamais dans la détresse. »" },
  { ref: "Matthieu 11:28", texte: "« Venez à moi, vous tous qui êtes fatigués et chargés, et je vous donnerai du repos. »" },
  { ref: "Psaume 37:5", texte: "« Remets ton sort à l'Éternel, confie-toi en lui, et il agira. »" },
  { ref: "Philippiens 4:6", texte: "« Ne vous inquiétez de rien ; mais en toute chose faites connaître vos besoins à Dieu. »" },
];

const PHASES = [
  { label: "Inspirez", duree: 4, echelle: 1.35 },
  { label: "Retenez", duree: 4, echelle: 1.35 },
  { label: "Expirez", duree: 6, echelle: 1 },
];

const duJour = (liste) => liste[new Date().getDate() % liste.length];

export default function MonRefuge() {
  const [humeur, setHumeur] = useState([]);
  const [prenom, setPrenom] = useState("");
  const [foi, setFoi] = useState(() => {
    try { return localStorage.getItem(CLE_FOI) === "1"; } catch { return false; }
  });
  const [energie, setEnergie] = useState(60);
  const [humeurChoisie, setHumeurChoisie] = useState("Bien");
  const [note, setNote] = useState("");
  const [envoi, setEnvoi] = useState(false);
  const [respire, setRespire] = useState(false);
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    Promise.all([getHumeur().catch(() => []), authMe().catch(() => null)]).then(([h, u]) => {
      setHumeur(Array.isArray(h) ? h : []);
      if (u) {
        setPrenom(u.first_name || u.name || "");
        if ((u.settings || {}).ambiance === "foi") setFoi(true);
      }
    });
  }, []);

  useEffect(() => {
    try { localStorage.setItem(CLE_FOI, foi ? "1" : "0"); } catch { /* noop */ }
  }, [foi]);

  useEffect(() => {
    if (!respire) return undefined;
    const t = setTimeout(() => setPhase((p) => (p + 1) % PHASES.length), PHASES[phase].duree * 1000);
    return () => clearTimeout(t);
  }, [respire, phase]);

  const envoyerCheckin = async () => {
    if (envoi) return;
    setEnvoi(true);
    try {
      await createHumeur({ energie, humeur: humeurChoisie, note: note.trim() || undefined });
      const h = await getHumeur().catch(() => []);
      setHumeur(Array.isArray(h) ? h : []);
      setNote("");
      toast.success("Check-in enregistré. Merci d'avoir pris ce moment.");
    } catch {
      toast.error("Le check-in n'a pas pu être enregistré. Réessayez.");
    } finally {
      setEnvoi(false);
    }
  };

  const dernier = humeur[0];
  const phaseActive = PHASES[phase];
  const pensee = duJour(PENSEES);
  const verset = duJour(VERSETS);

  return (
    <div className="space-y-4" data-testid="page-refuge">
      {/* En-tête */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="eyebrow-chip">Mon Refuge · Souffle &amp; ancrage</p>
          <h1 className="font-head text-2xl sm:text-3xl font-semibold text-white mt-1">
            {prenom ? `${prenom}, ici` : "Ici"}, <em className="gold-text">on souffle.</em>
          </h1>
          <p className="text-white/55 text-sm mt-1">
            {dernier
              ? `Dernier check-in : ${dernier.energie != null ? `${dernier.energie}%` : "—"} · ${dernier.humeur || "humeur non précisée"}`
              : "Aucun check-in pour l'instant — le premier prend dix secondes."}
          </p>
        </div>
        <button onClick={() => openCopilot("J'ai besoin de souffler. Parle-moi calmement.")} data-testid="refuge-copilote-btn"
          className="inline-flex items-center gap-1.5 rounded-xl border border-white/15 bg-white/5 px-4 py-2.5 text-sm font-semibold text-white/85 hover:bg-white/10 transition-colors">
          <Feather size={15} className="text-[#DEC2A3]" /> Parler au Copilote
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
        {/* Check-in d'énergie */}
        <section className="glass p-6 md:col-span-3" data-testid="refuge-checkin">
          <p className="eyebrow-chip mb-2">Check-in du moment</p>
          <h2 className="font-head text-lg font-semibold text-white">Comment est ta batterie, là, maintenant ?</h2>

          <label htmlFor="refuge-energie" className="mt-4 flex items-center justify-between text-[12.5px] text-white/65">
            <span>Énergie</span>
            <span className="font-head font-semibold text-[#E8D5BC]" data-testid="refuge-energie-valeur">{energie}%</span>
          </label>
          <input id="refuge-energie" type="range" min="0" max="100" step="5" value={energie}
            onChange={(e) => setEnergie(Number(e.target.value))}
            className="mt-2 w-full accent-[#DEC2A3]" data-testid="refuge-energie-slider" />

          <p className="mt-4 text-[12.5px] text-white/65">Humeur</p>
          <div className="mt-2 flex flex-wrap gap-2" data-testid="refuge-humeur-choix">
            {HUMEURS.map((h) => (
              <button key={h} onClick={() => setHumeurChoisie(h)} data-testid={`refuge-humeur-${h.toLowerCase().replace(/\s/g, "-")}`}
                className={`rounded-full px-3.5 py-1.5 text-xs font-semibold transition-colors ${humeurChoisie === h ? "gold-bg text-[#0A1128]" : "border border-white/15 bg-white/5 text-white/60 hover:text-white"}`}>
                {h}
              </button>
            ))}
          </div>

          <input value={note} onChange={(e) => setNote(e.target.value)}
            placeholder="Un mot sur ton état (facultatif)…"
            className="mt-4 w-full rounded-xl border border-white/15 bg-black/25 px-3.5 py-2.5 text-sm text-white placeholder:text-white/35 outline-none focus:border-[#DEC2A3]/60 transition-colors"
            data-testid="refuge-note-input" />

          <button onClick={envoyerCheckin} disabled={envoi} data-testid="refuge-checkin-submit"
            className="mt-4 inline-flex items-center gap-1.5 rounded-xl gold-bg px-5 py-2.5 text-sm font-bold text-[#0A1128] disabled:opacity-50">
            {envoi ? "Enregistrement…" : "Enregistrer mon check-in"} <ArrowRight size={14} />
          </button>
        </section>

        {/* Respiration guidée */}
        <section className="glass p-6 md:col-span-3 flex flex-col" data-testid="refuge-respiration">
          <p className="eyebrow-chip mb-2">Respiration 4 · 4 · 6</p>
          <h2 className="font-head text-lg font-semibold text-white">Trois cycles suffisent à descendre la pression.</h2>

          <div className="flex-1 grid place-items-center py-8">
            <div className="relative grid place-items-center">
              <div className="w-32 h-32 rounded-full border border-[#DEC2A3]/40 bg-[#DEC2A3]/[.08]"
                style={{
                  transform: `scale(${respire ? phaseActive.echelle : 1})`,
                  transition: `transform ${respire ? phaseActive.duree : 0.6}s ease-in-out`,
                }} />
              <div className="absolute inset-0 grid place-items-center text-center">
                <div>
                  <p className="font-head text-lg font-semibold text-white" data-testid="refuge-respiration-phase">
                    {respire ? phaseActive.label : "Prêt ?"}
                  </p>
                  <p className="text-[11px] text-white/50">{respire ? `${phaseActive.duree} secondes` : "4 s · 4 s · 6 s"}</p>
                </div>
              </div>
            </div>
          </div>

          <button onClick={() => { setRespire((r) => !r); setPhase(0); }} data-testid="refuge-respiration-toggle"
            className={`self-center inline-flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-bold transition-colors ${respire ? "border border-white/20 bg-white/5 text-white" : "gold-bg text-[#0A1128]"}`}>
            {respire ? <><Square size={14} /> Arrêter</> : <><Play size={14} /> Commencer</>}
          </button>
        </section>

        {/* Pensée du jour + Mode Foi */}
        <section className="glass p-6 md:col-span-3" data-testid="refuge-pensee">
          <div className="flex items-start justify-between gap-3">
            <p className="eyebrow-chip">Pensée du jour</p>
            <button onClick={() => setFoi((f) => !f)} data-testid="refuge-foi-toggle" aria-pressed={foi}
              className={`shrink-0 inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-[11px] font-semibold transition-colors ${foi ? "gold-bg border-transparent text-[#0A1128]" : "border-white/20 bg-white/5 text-white/60 hover:text-white"}`}>
              <Wind size={12} /> Mode Foi {foi ? "activé" : "désactivé"}
            </button>
          </div>
          <p className="font-head italic text-[17px] leading-relaxed text-[#F3E9DB] mt-3">{pensee}</p>
          {foi && (
            <div className="mt-4 border-l-2 border-[#DEC2A3] bg-[#DEC2A3]/[.06] rounded-r-xl px-3.5 py-2.5" data-testid="refuge-verset">
              <span className="block text-[9px] uppercase tracking-[.14em] text-[#DEC2A3] font-semibold mb-1">{verset.ref} · Mode Foi</span>
              <p className="text-[12.5px] text-white/70 leading-relaxed">{verset.texte}</p>
            </div>
          )}
          <p className="mt-4 text-[11px] text-white/40">Une pensée n'est pas une vérité. Elle passe, toi tu restes.</p>
        </section>

        {/* Derniers check-ins — données réelles */}
        <section className="glass p-6 md:col-span-3" data-testid="refuge-historique">
          <p className="eyebrow-chip mb-3">Tes derniers check-ins</p>
          {dernier ? (
            <ul className="divide-y divide-white/[.07] list-none p-0 m-0">
              {humeur.slice(0, 5).map((h, i) => (
                <li key={h.id || i} className="flex items-center gap-3 py-2.5 text-[13px]" data-testid={`refuge-checkin-ligne-${i}`}>
                  <span className="w-11 shrink-0 font-head font-semibold text-[#E8D5BC]">{h.energie != null ? `${h.energie}%` : "—"}</span>
                  <span className="text-white/80">{h.humeur || "—"}</span>
                  <span className="ml-auto text-[11px] text-white/40">
                    {h.date ? new Intl.DateTimeFormat("fr-FR", { day: "numeric", month: "short" }).format(new Date(h.date)) : ""}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <div>
              <p className="text-[13px] text-white/50 leading-relaxed">
                Ton historique apparaîtra ici. Il permet à la page Aujourd'hui d'adapter tes journées à ton énergie réelle.
              </p>
              <button onClick={() => document.querySelector('[data-testid="refuge-energie-slider"]')?.focus()}
                className="mt-3 inline-flex items-center gap-1.5 rounded-xl gold-bg px-4 py-2 text-sm font-semibold text-[#0A1128]"
                data-testid="refuge-premier-checkin">
                Faire mon premier check-in <ArrowRight size={13} />
              </button>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
