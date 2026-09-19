import { useEffect, useState } from "react";
import { ArrowRight, Sparkles, X, Plus, Heart } from "lucide-react";
import { useNavigate } from "react-router-dom";
import {
  ResponsiveContainer, LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid,
} from "recharts";
import { getVision, getHumeur, getTaches, createTache, updateTacheStatut, authMe } from "../lib/api";

const CLE_GUIDE_MASQUE = "zay_guide_premiers_pas_masque";
const CLE_AMBIANCE = "mx_ambiance";

const openCopilot = (ask) =>
  window.dispatchEvent(new CustomEvent("cours:open-copilot", { detail: ask ? { ask } : {} }));

// Aujourd'hui — refonte C+.
// La page VOIT (priorité, énergie, encouragement) ; le Copilote DÉCIDE et
// PRÉPARE. Toutes les données sont réelles (vision, check-ins, tâches) et un
// bloc vide dit honnêtement comment se remplir. Aucun lien ne pointe vers
// une page en cours de refonte (Mouvement, Mindset...) : le Copilote prend
// le relais en attendant.
export default function Aujourdhui() {
  const navigate = useNavigate();
  const [vision, setVision] = useState(null);
  const [humeur, setHumeur] = useState([]);
  const [taches, setTaches] = useState([]);
  const [prenom, setPrenom] = useState("");
  const [foi, setFoi] = useState(false);
  const [loading, setLoading] = useState(true);
  const [mode, setMode] = useState(() => {
    try { return localStorage.getItem(CLE_AMBIANCE) || "elan"; } catch { return "elan"; }
  });
  const [capture, setCapture] = useState("");
  const [captureBusy, setCaptureBusy] = useState(false);
  const [guideMasque, setGuideMasque] = useState(() => {
    try { return localStorage.getItem(CLE_GUIDE_MASQUE) === "1"; } catch { return false; }
  });
  const [modalOuverte, setModalOuverte] = useState(true);

  useEffect(() => {
    Promise.all([
      getVision().catch(() => null),
      getHumeur().catch(() => []),
      getTaches().catch(() => []),
      authMe().catch(() => null),
    ]).then(([v, h, t, u]) => {
      setVision(v);
      setHumeur(Array.isArray(h) ? h : []);
      setTaches(Array.isArray(t) ? t : []);
      if (u) {
        setPrenom(u.first_name || u.name || "");
        let foiLocal = false;
        try { foiLocal = localStorage.getItem("mx_foi") === "1"; } catch { /* noop */ }
        setFoi((u.settings || {}).ambiance === "foi" || foiLocal);
      }
    }).finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    try { localStorage.setItem(CLE_AMBIANCE, mode); } catch { /* noop */ }
  }, [mode]);

  const masquerGuide = () => {
    setGuideMasque(true);
    setModalOuverte(false);
    try { localStorage.setItem(CLE_GUIDE_MASQUE, "1"); } catch { /* noop */ }
  };

  const dernierHumeur = humeur[0];
  const capaciteValue = dernierHumeur ? dernierHumeur.energie : null;
  const tachesOuvertes = taches.filter((t) => t.statut !== "Terminé");
  const prioritePrincipale = tachesOuvertes
    .slice()
    .sort((a, b) => (a.priorite === "Haute" ? -1 : 1) - (b.priorite === "Haute" ? -1 : 1))[0];

  const capturer = async () => {
    const titre = capture.trim();
    if (!titre || captureBusy) return;
    setCaptureBusy(true);
    try {
      const t = await createTache({ titre, priorite: "Normale" });
      setTaches((prev) => [t, ...prev]);
      setCapture("");
    } catch { /* la capture reste dans le champ si l'envoi échoue */ }
    finally { setCaptureBusy(false); }
  };

  const basculerTache = async (t) => {
    const cible = t.statut === "Terminé" ? "A faire" : "Terminé";
    setTaches((prev) => prev.map((x) => (x.id === t.id ? { ...x, statut: cible } : x)));
    try { await updateTacheStatut(t.id, cible); }
    catch { setTaches((prev) => prev.map((x) => (x.id === t.id ? t : x))); }
  };

  const etapesDemarrage = [
    {
      titre: "Définir votre Cap",
      detail: "En une phrase, ce vers quoi vous allez. C'est ce qui permet à l'appli de trier vos priorités au lieu d'empiler une liste.",
      cta: "Ouvrir Ma Vision",
      fait: Boolean(vision?.why || vision?.value),
      action: () => navigate("/vision"),
    },
    {
      titre: "Noter une première action",
      detail: "Une seule tâche concrète suffit — capturez-la juste en dessous, dans « Priorité du jour ».",
      cta: "Noter une action",
      fait: taches.length > 0,
      action: () => {
        setModalOuverte(false);
        setTimeout(() => document.querySelector('[data-testid="capture-input"]')?.focus(), 300);
      },
    },
    {
      titre: "Faire un check-in d'énergie",
      detail: "Dix secondes, en parlant au Copilote. C'est ce qui alimente l'anneau de capacité.",
      cta: "Faire mon check-in",
      fait: humeur.length > 0,
      action: () => openCopilot("Je veux faire mon check-in d'énergie du jour."),
    },
  ];
  const compteNeuf = etapesDemarrage.some((etape) => !etape.fait);
  const afficherModalGuide = !loading && !guideMasque && compteNeuf && modalOuverte;
  const afficherRappelGuide = !loading && !guideMasque && compteNeuf && !modalOuverte;

  useEffect(() => {
    if (!afficherModalGuide) return;
    const onKeyDown = (e) => { if (e.key === "Escape") setModalOuverte(false); };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [afficherModalGuide]);

  const dateDuJour = new Intl.DateTimeFormat("fr-FR", { weekday: "long", day: "numeric", month: "long", year: "numeric" }).format(new Date());
  const refuge = mode === "refuge";

  // ── Séries réelles pour les graphiques (aucune donnée fabriquée) ──
  const energieSerie = humeur
    .filter((h) => h.date && h.energie != null)
    .slice()
    .sort((a, b) => new Date(a.date) - new Date(b.date))
    .slice(-30)
    .map((h) => ({
      jour: new Intl.DateTimeFormat("fr-FR", { day: "numeric", month: "short" }).format(new Date(h.date)),
      energie: h.energie,
    }));
  const jours7 = [...Array(7)].map((_, i) => {
    const d = new Date();
    d.setDate(d.getDate() - (6 - i));
    return d;
  });
  const actionsSerie = jours7.map((d) => {
    const duJour = taches.filter((t) => t.created_at && new Date(t.created_at).toDateString() === d.toDateString());
    return {
      jour: new Intl.DateTimeFormat("fr-FR", { weekday: "short" }).format(d),
      notées: duJour.length,
      terminées: duJour.filter((t) => t.statut === "Terminé").length,
    };
  });
  const aDesActions = taches.some((t) => t.created_at);

  const tooltipStyle = {
    background: "#0B1F3A", border: "1px solid rgba(222,194,163,.35)", borderRadius: 12,
    color: "#fff", fontSize: 12, boxShadow: "0 10px 24px rgba(0,0,0,.4)",
  };

  return (
    <div className="space-y-4" data-testid="page-aujourdhui">
      {/* En-tête + bascule Élan/Refuge */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="eyebrow-chip">{dateDuJour} · Mode {refuge ? "Refuge" : "Élan"}</p>
          <h1 className="font-head text-2xl sm:text-3xl font-semibold text-white mt-1">
            {refuge
              ? <>On ralentit. <em className="gold-text">Une marche suffit.</em></>
              : <>{prenom ? `Bonjour ${prenom}, ` : "Bonjour, "}<em className="gold-text">ce qui compte maintenant.</em></>}
          </h1>
          <p className="text-white/55 text-sm mt-1">
            {loading ? "Chargement…"
              : `${tachesOuvertes.length} action(s) ouverte(s) · capacité ${capaciteValue != null ? `${capaciteValue}%` : "à mesurer"}`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex rounded-full border border-white/15 bg-white/5 p-1" data-testid="mode-toggle">
            <button onClick={() => setMode("elan")} data-testid="mode-elan-btn"
              className={`rounded-full px-4 py-1.5 text-xs font-semibold transition-colors ${!refuge ? "gold-bg text-[#0A1128]" : "text-white/60 hover:text-white"}`}>
              ⚡ Élan
            </button>
            <button onClick={() => setMode("refuge")} data-testid="mode-refuge-btn"
              className={`rounded-full px-4 py-1.5 text-xs font-semibold transition-colors ${refuge ? "gold-bg text-[#0A1128]" : "text-white/60 hover:text-white"}`}>
              🕊 Refuge
            </button>
          </div>
          <button onClick={() => openCopilot()} data-testid="ouvrir-copilote-btn"
            className="inline-flex items-center gap-1.5 rounded-xl border border-white/15 bg-white/5 px-4 py-2.5 text-sm font-semibold text-white/85 hover:bg-white/10 transition-colors">
            <Sparkles size={15} className="text-[#DEC2A3]" /> Copilote
          </button>
        </div>
      </div>

      {afficherRappelGuide && (
        <button onClick={() => setModalOuverte(true)} data-testid="premiers-pas-rappel"
          className="w-full flex items-center justify-between gap-3 rounded-xl border border-[#DEC2A3]/25 bg-[#DEC2A3]/[.06] px-4 py-3 text-left hover:bg-[#DEC2A3]/[.1] transition-colors">
          <span className="flex items-center gap-2 text-sm text-white/80">
            <Sparkles size={15} className="text-[#DEC2A3] shrink-0" />
            La configuration de votre cockpit n'est pas terminée.
          </span>
          <span className="shrink-0 inline-flex items-center gap-1 text-xs font-semibold text-[#DEC2A3]">Reprendre <ArrowRight size={12} /></span>
        </button>
      )}

      {/* Guide de démarrage (modale) — inchangé dans son principe, les liens
          pointent uniquement vers des pages visibles ou le Copilote. */}
      {afficherModalGuide && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#050B1A]/70 backdrop-blur-sm"
          data-testid="aujourdhui-premiers-pas-modal-backdrop"
          onClick={() => setModalOuverte(false)}>
          <section role="dialog" aria-modal="true" aria-labelledby="premiers-pas-titre"
            className="glass w-full max-w-xl p-5 sm:p-6 border-[#DEC2A3]/30 max-h-[90vh] overflow-y-auto"
            data-testid="aujourdhui-premiers-pas"
            onClick={(e) => e.stopPropagation()}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="eyebrow-chip">Premiers pas</p>
                <h2 id="premiers-pas-titre" className="font-head text-lg font-semibold text-white mt-1">Trois gestes pour que le cockpit se remplisse.</h2>
                <p className="text-[13px] text-white/55 mt-1 leading-relaxed">
                  Les chiffres de cette page sont calculés à partir de vos données. Tant que vous n'avez rien saisi,
                  ils restent volontairement à zéro — ce n'est pas une panne. Voici par quoi commencer.
                </p>
              </div>
              <button onClick={() => setModalOuverte(false)} aria-label="Fermer, me le rappeler plus tard"
                className="shrink-0 rounded-lg p-1.5 text-white/35 hover:bg-white/10 hover:text-white/70 transition-colors"
                data-testid="premiers-pas-close">
                <X size={16} />
              </button>
            </div>
            <ol className="mt-5 grid grid-cols-1 sm:grid-cols-3 gap-3 list-none p-0 m-0">
              {etapesDemarrage.map((etape, index) => (
                <li key={etape.titre}
                  className={`rounded-xl border p-4 ${etape.fait ? "border-emerald-400/30 bg-emerald-400/[.07]" : "border-white/12 bg-white/[.04]"}`}
                  data-testid={`premiers-pas-etape-${index + 1}`}>
                  <div className="flex items-center gap-2">
                    <span className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[11px] font-bold ${etape.fait ? "bg-emerald-400/25 text-emerald-200" : "gold-bg text-[#0A1128]"}`}>
                      {etape.fait ? "✓" : index + 1}
                    </span>
                    <p className="m-0 text-sm font-semibold text-white">{etape.titre}</p>
                  </div>
                  <p className="m-0 mt-2 text-[12.5px] leading-relaxed text-white/55">{etape.detail}</p>
                  {!etape.fait && (
                    <button onClick={etape.action}
                      className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-[#DEC2A3] hover:text-[#FFD700] transition-colors">
                      {etape.cta} <ArrowRight size={12} />
                    </button>
                  )}
                </li>
              ))}
            </ol>
            <div className="mt-5 flex items-center justify-between gap-3 border-t border-white/10 pt-4">
              <button onClick={() => setModalOuverte(false)} className="text-xs text-white/45 hover:text-white/70 transition-colors">Plus tard</button>
              <button onClick={masquerGuide} data-testid="premiers-pas-ne-plus-afficher"
                className="text-xs text-white/45 hover:text-white/70 transition-colors underline underline-offset-2">Ne plus afficher</button>
            </div>
          </section>
        </div>
      )}

      {/* Grille C+ */}
      <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
        {/* Priorité du jour + capture */}
        <section className="glass p-6 md:col-span-4" data-testid="aujourdhui-priorite">
          <p className="eyebrow-chip mb-2">Priorité du jour</p>
          <h2 className="font-head text-xl font-semibold text-white">Ta journée, réduite à l'essentiel</h2>
          <p className="text-[12px] text-white/50 mt-1 mb-4">Le reste attend dans la réserve — rien ne se perd.</p>

          <div className="rounded-xl border border-[#DEC2A3]/40 bg-[#DEC2A3]/[.08] px-4 py-3.5 mb-4">
            {loading ? (
              <p className="text-sm text-white/40">Chargement…</p>
            ) : prioritePrincipale ? (
              <>
                <p className="font-head text-[15px] font-semibold text-white">{prioritePrincipale.titre}</p>
                <p className="text-[11.5px] text-white/50 mt-1">
                  {vision?.why ? `Reliée à ta vision : « ${String(vision.why).slice(0, 80)}${String(vision.why).length > 80 ? "…" : ""} »` : "Relie ton Cap dans Ma Vision pour donner du poids à cette action."}
                </p>
              </>
            ) : (
              <>
                <p className="font-head text-[15px] font-semibold text-white">Aucune action notée pour l'instant.</p>
                <p className="text-[11.5px] text-white/50 mt-1">Capture ta première action juste en dessous — une seule suffit.</p>
              </>
            )}
          </div>

          <div className="flex gap-2 mb-2">
            <input
              value={capture}
              onChange={(e) => setCapture(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && capturer()}
              placeholder="Une idée qui fuse, une action à ne pas oublier…"
              data-testid="capture-input"
              className="flex-1 rounded-xl border border-white/15 bg-black/25 px-3.5 py-2.5 text-sm text-white placeholder:text-white/35 outline-none focus:border-[#DEC2A3]/60 transition-colors"
            />
            <button onClick={capturer} disabled={captureBusy || !capture.trim()} data-testid="capture-submit"
              className="rounded-xl gold-bg px-4 text-sm font-bold text-[#0A1128] disabled:opacity-50 inline-flex items-center gap-1">
              <Plus size={15} /> Ajouter
            </button>
          </div>

          <div>
            {taches.slice(0, 4).map((t) => (
              <div key={t.id} className="flex items-center gap-2.5 py-2.5 border-b border-white/[.07] last:border-0 text-[13px]" data-testid={`tache-ligne-${t.id}`}>
                <button onClick={() => basculerTache(t)} aria-label={t.statut === "Terminé" ? "Rouvrir" : "Terminer"}
                  data-testid={`tache-check-${t.id}`}
                  className={`w-[18px] h-[18px] rounded-md border shrink-0 grid place-items-center text-[10px] transition-colors ${t.statut === "Terminé" ? "gold-bg border-transparent text-[#0A1128]" : "border-white/30 text-transparent hover:border-[#DEC2A3]"}`}>
                  ✓
                </button>
                <span className={t.statut === "Terminé" ? "line-through text-white/40" : "text-white/85"}>{t.titre}</span>
                <span className="ml-auto text-[9px] uppercase tracking-wide px-2 py-0.5 rounded-full border border-[#DEC2A3]/30 bg-[#DEC2A3]/[.1] text-[#E8D5BC] font-semibold shrink-0">
                  {t.priorite || "Normale"}
                </span>
              </div>
            ))}
            {!loading && taches.length === 0 && (
              <p className="text-[12.5px] text-white/40 py-2">Ta liste apparaîtra ici, alimentée par tes captures.</p>
            )}
          </div>
        </section>

        {/* Énergie & burn-out */}
        <section className="glass p-6 md:col-span-2" data-testid="aujourdhui-energie">
          <p className="eyebrow-chip mb-3">Énergie & burn-out</p>
          <div className="flex items-center gap-4">
            <div className="relative w-20 h-20 shrink-0">
              <svg className="w-20 h-20 -rotate-90">
                <circle cx="40" cy="40" r="33" stroke="rgba(255,255,255,0.1)" strokeWidth="7" fill="none" />
                {capaciteValue != null && (
                  <circle cx="40" cy="40" r="33" stroke="#DEC2A3" strokeWidth="7" fill="none"
                    strokeDasharray={2 * Math.PI * 33}
                    strokeDashoffset={2 * Math.PI * 33 * (1 - capaciteValue / 100)}
                    strokeLinecap="round" />
                )}
              </svg>
              <div className="absolute inset-0 flex items-center justify-center font-head font-semibold text-base text-white">
                {capaciteValue != null ? `${capaciteValue}%` : "—"}
              </div>
            </div>
            <div>
              <p className="text-[13px] font-semibold text-white">
                {capaciteValue == null ? "Pas encore mesurée" : capaciteValue >= 70 ? "Bonne marge" : capaciteValue >= 45 ? "Niveau correct" : "Niveau bas"}
              </p>
              <p className="text-[11.5px] text-white/50 mt-0.5">
                {capaciteValue == null ? "Un check-in de 10 s suffit." : capaciteValue >= 45 ? "Ta batterie du moment." : "Ménage-toi aujourd'hui."}
              </p>
            </div>
          </div>
          {capaciteValue == null ? (
            <button onClick={() => openCopilot("Je veux faire mon check-in d'énergie du jour.")}
              className="mt-4 inline-flex items-center gap-1.5 rounded-xl gold-bg px-4 py-2 text-sm font-semibold text-[#0A1128]"
              data-testid="checkin-copilot-btn">
              Faire un check-in <ArrowRight size={13} />
            </button>
          ) : capaciteValue < 45 ? (
            <div className="mt-4 rounded-xl border border-rose-300/30 bg-rose-400/10 px-3.5 py-2.5 text-[11.5px] text-rose-200" data-testid="energie-alerte">
              ⚠ Risque de surchauffe — allège la journée, une marche suffit.
            </div>
          ) : (
            <div className="mt-4 rounded-xl border border-white/10 bg-white/[.04] px-3.5 py-2.5 text-[11.5px] text-white/55">
              Capacité avant ambition : la journée s'adapte à ta batterie.
            </div>
          )}
        </section>

        {/* Encouragement (+ verset si Mode Foi) */}
        <section className={`glass p-6 md:col-span-2 ${refuge ? "border-[#DEC2A3]/50" : ""}`} data-testid="aujourdhui-encouragement">
          <p className="eyebrow-chip mb-3">Encouragement</p>
          <p className="font-head italic text-[16px] leading-relaxed text-[#F3E9DB]">
            {refuge
              ? "« Aujourd'hui, tenir compte autant que construire. Tu n'as pas à tout porter. »"
              : "« Tu n'as pas besoin de voir tout l'escalier. Juste la première marche. »"}
          </p>
          {foi && (
            <div className="mt-3 border-l-2 border-[#DEC2A3] bg-[#DEC2A3]/[.06] rounded-r-xl px-3.5 py-2.5 text-[11px] text-white/65" data-testid="verset-du-jour">
              <span className="block text-[9px] uppercase tracking-[.14em] text-[#DEC2A3] font-semibold font-sans not-italic mb-1">Psaume 37:5 · Mode Foi</span>
              « Remets ton sort à l'Éternel, confie-toi en lui, et il agira. »
            </div>
          )}
          <p className="mt-3 text-[11px] text-white/40 flex items-center gap-1.5"><Heart size={11} className="text-[#DEC2A3]" /> Une pensée n'est pas une vérité.</p>
        </section>

        {/* Raccourcis */}
        <button onClick={() => navigate("/vision")} data-testid="raccourci-vision"
          className="glass glass-hover p-4 md:col-span-2 flex items-center gap-3 text-left">
          <span className="w-9 h-9 rounded-xl border border-[#DEC2A3]/30 bg-[#DEC2A3]/[.12] grid place-items-center shrink-0">🔭</span>
          <span><b className="block text-[13px] text-white">Ma Vision</b><small className="text-[11px] text-white/50">{vision?.why ? "Cap défini — relire ma raison d'être" : "Définir ma raison d'être"}</small></span>
        </button>
        <button onClick={() => openCopilot("J'ai une décision à clarifier. Pose-moi les bonnes questions.")} data-testid="raccourci-decision"
          className="glass glass-hover p-4 md:col-span-2 flex items-center gap-3 text-left">
          <span className="w-9 h-9 rounded-xl border border-[#DEC2A3]/30 bg-[#DEC2A3]/[.12] grid place-items-center shrink-0">⚖️</span>
          <span><b className="block text-[13px] text-white">Une décision à clarifier ?</b><small className="text-[11px] text-white/50">Le Copilote la cadre avec toi</small></span>
        </button>
        <button onClick={() => openCopilot("J'ai une idée qui fuse. Note-la et aide-moi à la trier.")} data-testid="raccourci-idee"
          className="glass glass-hover p-4 md:col-span-2 flex items-center gap-3 text-left">
          <span className="w-9 h-9 rounded-xl border border-[#DEC2A3]/30 bg-[#DEC2A3]/[.12] grid place-items-center shrink-0">💡</span>
          <span><b className="block text-[13px] text-white">Une idée qui fuse ?</b><small className="text-[11px] text-white/50">Confie-la au Copilote</small></span>
        </button>
      </div>

      {/* Graphiques — courbes & barres calculées uniquement sur tes vraies données */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4" data-testid="aujourdhui-graphiques">
        <section className="glass p-6" data-testid="graphique-energie">
          <p className="eyebrow-chip mb-1">Ton énergie</p>
          <h3 className="font-head text-base font-semibold text-white mb-4">30 derniers jours</h3>
          {energieSerie.length >= 2 ? (
            <ResponsiveContainer width="100%" height={190}>
              <LineChart data={energieSerie} margin={{ top: 6, right: 10, bottom: 0, left: -22 }}>
                <CartesianGrid stroke="rgba(255,255,255,.07)" vertical={false} />
                <XAxis dataKey="jour" tick={{ fill: "rgba(255,255,255,.45)", fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis domain={[0, 100]} tick={{ fill: "rgba(255,255,255,.45)", fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={tooltipStyle} labelStyle={{ color: "#DEC2A3" }} formatter={(v) => [`${v}%`, "Énergie"]} />
                <Line type="monotone" dataKey="energie" stroke="#DEC2A3" strokeWidth={2.5} dot={{ r: 3, fill: "#DEC2A3", strokeWidth: 0 }} activeDot={{ r: 5 }} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="py-6">
              <p className="text-[13px] text-white/50 leading-relaxed">
                La courbe apparaîtra après tes deux premiers check-ins d'énergie — dix secondes chacun, depuis Mon Refuge ou le Copilote.
              </p>
              <button onClick={() => navigate("/refuge")} data-testid="graphique-energie-cta"
                className="mt-3 inline-flex items-center gap-1.5 rounded-xl gold-bg px-4 py-2 text-sm font-semibold text-[#0A1128]">
                Faire un check-in <ArrowRight size={13} />
              </button>
            </div>
          )}
        </section>

        <section className="glass p-6" data-testid="graphique-actions">
          <p className="eyebrow-chip mb-1">Ton rythme d'actions</p>
          <h3 className="font-head text-base font-semibold text-white mb-4">7 derniers jours</h3>
          {aDesActions ? (
            <ResponsiveContainer width="100%" height={190}>
              <BarChart data={actionsSerie} margin={{ top: 6, right: 10, bottom: 0, left: -28 }} barGap={3}>
                <CartesianGrid stroke="rgba(255,255,255,.07)" vertical={false} />
                <XAxis dataKey="jour" tick={{ fill: "rgba(255,255,255,.45)", fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis allowDecimals={false} tick={{ fill: "rgba(255,255,255,.45)", fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={tooltipStyle} labelStyle={{ color: "#DEC2A3" }} cursor={{ fill: "rgba(255,255,255,.05)" }} />
                <Bar dataKey="notées" fill="#6483B4" radius={[5, 5, 0, 0]} maxBarSize={22} />
                <Bar dataKey="terminées" fill="#DEC2A3" radius={[5, 5, 0, 0]} maxBarSize={22} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="py-6">
              <p className="text-[13px] text-white/50 leading-relaxed">
                L'histogramme se remplira dès ta première action capturée dans « Priorité du jour », juste au-dessus.
              </p>
              <button onClick={() => document.querySelector('[data-testid="capture-input"]')?.focus()} data-testid="graphique-actions-cta"
                className="mt-3 inline-flex items-center gap-1.5 rounded-xl gold-bg px-4 py-2 text-sm font-semibold text-[#0A1128]">
                Noter une action <ArrowRight size={13} />
              </button>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
