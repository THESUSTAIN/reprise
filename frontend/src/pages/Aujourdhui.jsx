import { useEffect, useState } from "react";
import { Compass, ArrowRight, Zap, ListChecks, Sparkles, Target, Lightbulb, X } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { getVision, getHumeur, getTaches } from "../lib/api";
import useIsMobile from "../hooks/useIsMobile";

const CLE_GUIDE_MASQUE = "zay_guide_premiers_pas_masque";

// Accueil quotidien Cap Vivant.
//
// Structure visuelle reprise de la maquette de design partagee
// (cap-vivant-3002-mouvement-original.zip : carte "hero" + anneau de
// capacite + trajectoire Vision -> Decision -> Action + cartes
// decision/reflexion) - mais entierement rebranchee sur les vraies
// donnees de ce projet plutot que les "-" en dur de la maquette. Aucun
// appel a /auth/*, /settings/profile etc. (routes qui n'existent pas ici)
// n'a ete repris.
//
// Honnetete assumee : il n'existe dans ce projet AUCUN moteur de decision
// cote serveur (verifie a plusieurs reprises) - la carte "Decision a
// clarifier" reste donc un etat vide honnete, jamais une decision
// fabriquee.
export default function Aujourdhui() {
  const navigate = useNavigate();
  const isMobile = useIsMobile();
  const [vision, setVision] = useState(null);
  const [humeur, setHumeur] = useState([]);
  const [taches, setTaches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [guideMasque, setGuideMasque] = useState(() => {
    try { return localStorage.getItem(CLE_GUIDE_MASQUE) === "1"; } catch { return false; }
  });
  // Le guide « Premiers pas » s'affiche désormais en fenêtre modale plutôt
  // qu'en bloc inséré dans la page : l'ancien bloc arrivait après la carte
  // hero et les métriques à 0, donc souvent hors champ au premier
  // chargement — l'utilisateur voyait les zéros avant l'explication. La
  // modale capte l'attention immédiatement, dans l'ordre.
  // `modalOuverte` ne persiste pas : fermer la modale (X, Échap, clic hors
  // cadre) ne fait que la refermer pour la session — un rappel discret
  // permet de la rouvrir. Seul « Ne plus afficher » persiste dans
  // localStorage et masque le guide définitivement.
  const [modalOuverte, setModalOuverte] = useState(true);

  useEffect(() => {
    Promise.all([
      getVision().catch(() => null),
      getHumeur().catch(() => []),
      getTaches().catch(() => []),
    ]).then(([v, h, t]) => {
      setVision(v);
      setHumeur(Array.isArray(h) ? h : []);
      setTaches(Array.isArray(t) ? t : []);
    }).finally(() => setLoading(false));
  }, []);

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

  // Les trois gestes qui alimentent réellement le cockpit. « fait » est lu
  // dans les vraies données : la coche ne se déclenche jamais par elle-même.
  const etapesDemarrage = [
    {
      titre: "Définir votre Cap",
      detail: "En une phrase, ce vers quoi vous allez. C'est ce qui permet à l'appli de trier vos priorités au lieu d'empiler une liste.",
      cta: "Ouvrir ma Vision",
      fait: Boolean(vision?.value),
      action: () => navigate("/vision"),
    },
    {
      titre: "Noter une première action",
      detail: "Une seule tâche concrète suffit. Elle apparaîtra ensuite ici, dans « Priorité du jour ».",
      cta: "Ouvrir Mon Mouvement",
      fait: taches.length > 0,
      action: () => navigate("/taches"),
    },
    {
      titre: "Faire un check-in d'énergie",
      detail: "Dix secondes. C'est ce qui alimente l'anneau de capacité et adapte le nombre de tâches proposées chaque jour.",
      cta: "Ouvrir Mindset & capacité",
      fait: humeur.length > 0,
      action: () => navigate("/mindset"),
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

  // Sur mobile, on remonte l'action concrète (Priorité du jour) tout en haut,
  // avant la carte hero décorative : sur un petit écran, l'utilisateur veut
  // d'abord "quoi faire maintenant", pas la trajectoire Vision->Décision->Action.
  const prioriteBlock = (
    <div className="glass p-5" data-testid="aujourdhui-priorite">
      <p className="font-head font-semibold flex items-center gap-2 mb-3"><ListChecks size={14} className="text-[#DEC2A3]" /> Priorité du jour</p>
      {loading ? (
        <p className="text-sm text-white/40">Chargement…</p>
      ) : prioritePrincipale ? (
        <>
          <p className="text-base font-semibold text-white">{prioritePrincipale.titre}</p>
          {tachesOuvertes.length > 1 && (
            <p className="text-xs text-white/40 mt-1">+ {tachesOuvertes.length - 1} autre(s) tâche(s) ouverte(s), secondaires pour l'instant.</p>
          )}
          <button onClick={() => navigate("/mouvement")} data-testid="aujourdhui-goto-mouvement"
            className="mt-3 inline-flex items-center gap-1 text-xs text-[#DEC2A3] hover:text-[#FFD700] transition-colors">
            Ouvrir Mon Mouvement <ArrowRight size={13} />
          </button>
        </>
      ) : (
        <>
          <p className="text-sm text-white/40">Aucune tâche ouverte pour l'instant.</p>
          <button onClick={() => navigate("/taches")} data-testid="aujourdhui-goto-taches" className="mt-3 inline-flex items-center gap-1 text-xs text-[#DEC2A3] hover:text-[#FFD700] transition-colors">
            Ouvrir la liste des tâches <ArrowRight size={13} />
          </button>
        </>
      )}
    </div>
  );

  return (
    <div className="space-y-6" data-testid="page-aujourdhui">
      {/* En-tête pattern "eyebrow / titre / description", repris de la maquette */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[.14em] text-[#DEC2A3]">Aujourd'hui aligné</p>
          <h1 className="font-head text-2xl sm:text-3xl font-semibold text-white mt-1">Ce qui compte maintenant.</h1>
          <p className="text-white/55 text-sm mt-1 max-w-xl">Votre Vision devient une décision concrète, sans perdre de vue votre capacité.</p>
        </div>
        <button onClick={() => window.dispatchEvent(new CustomEvent("cours:open-copilot"))}
          className="inline-flex items-center gap-1.5 rounded-xl border border-white/15 bg-white/5 px-4 py-2.5 text-sm font-semibold text-white/85 hover:bg-white/10 transition-colors">
          <Sparkles size={15} className="text-[#DEC2A3]" /> Ouvrir le Copilote
        </button>
      </div>

      {/* Rappel discret : affiché uniquement quand la modale a été refermée
          pour la session (X / Échap / clic hors cadre) sans que le guide
          soit fini ni définitivement masqué. Sans lui, fermer la modale par
          réflexe ferait perdre l'accès aux trois gestes de démarrage. */}
      {afficherRappelGuide && (
        <button onClick={() => setModalOuverte(true)} data-testid="premiers-pas-rappel"
          className="w-full flex items-center justify-between gap-3 rounded-xl border border-[#DEC2A3]/25 bg-[#DEC2A3]/[.06] px-4 py-3 text-left hover:bg-[#DEC2A3]/[.1] transition-colors">
          <span className="flex items-center gap-2 text-sm text-white/80">
            <Sparkles size={15} className="text-[#DEC2A3] shrink-0" />
            La configuration de votre cockpit n'est pas terminée.
          </span>
          <span className="shrink-0 inline-flex items-center gap-1 text-xs font-semibold text-[#DEC2A3]">
            Reprendre <ArrowRight size={12} />
          </span>
        </button>
      )}

      {/* Guide de démarrage, en fenêtre modale.
          Un compte neuf affichait un cockpit rempli de « 0 », « — » et
          « À définir » : rien n'expliquait dans quel ordre remplir ces cases,
          ni pourquoi. Cette modale s'ouvre automatiquement avant que
          l'utilisateur ne voie les zéros, énonce les trois gestes fondateurs,
          indique lesquels sont déjà faits, et disparaît dès qu'ils le sont
          tous. Fermer la modale (X, Échap, clic hors cadre) ne fait que la
          reporter — voir le rappel ci-dessus ; seul « Ne plus afficher »
          la masque définitivement. */}
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
                <p className="text-[11px] font-semibold uppercase tracking-[.14em] text-[#DEC2A3]">Premiers pas</p>
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
              <button onClick={() => setModalOuverte(false)}
                className="text-xs text-white/45 hover:text-white/70 transition-colors">
                Plus tard
              </button>
              <button onClick={masquerGuide} data-testid="premiers-pas-ne-plus-afficher"
                className="text-xs text-white/45 hover:text-white/70 transition-colors underline underline-offset-2">
                Ne plus afficher
              </button>
            </div>
          </section>
        </div>
      )}

      {/* Sur mobile : l'action du jour remonte immédiatement sous l'en-tête. */}
      {isMobile && prioriteBlock}

      {/* Carte hero : statut + trajectoire + anneau de capacité réel */}
      <div className="glass p-6 grid grid-cols-1 lg:grid-cols-[1fr_auto] gap-6 items-center" data-testid="aujourdhui-hero">
        <div>
          <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-400/15 border border-emerald-400/25 px-3 py-1 text-[11px] font-semibold text-emerald-300">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" /> {vision?.value ? "Vision active" : "Vision à définir"}
          </span>
          <h2 className="font-head text-xl font-semibold text-white mt-3">
            {prioritePrincipale ? `Faire avancer « ${prioritePrincipale.titre} ».` : "Faire avancer une action qui mérite votre énergie."}
          </h2>
          <p className="text-white/55 text-sm mt-1 max-w-lg">La Vision vous aide à choisir une action réaliste plutôt qu'à remplir une liste.</p>
          <div className="flex items-center gap-2 mt-4 text-xs text-white/60">
            <span className="px-2.5 py-1 rounded-full bg-white/5 border border-white/10">Vision</span>
            <ArrowRight size={13} className="text-white/30" />
            <span className="px-2.5 py-1 rounded-full bg-white/5 border border-white/10">Décision</span>
            <ArrowRight size={13} className="text-white/30" />
            <span className="px-2.5 py-1 rounded-full gold-bg text-[#0A1128] font-semibold">Action</span>
          </div>
        </div>

        {/* Anneau de capacité — vraie donnée (dernier check-in Humeur), même
            pattern visuel que les gauges de Mindset & capacité. */}
        <div className="flex flex-col items-center gap-2 shrink-0">
          <div className="relative w-24 h-24">
            <svg className="w-24 h-24 -rotate-90">
              <circle cx="48" cy="48" r="40" stroke="rgba(255,255,255,0.1)" strokeWidth="8" fill="none" />
              {capaciteValue != null && (
                <circle cx="48" cy="48" r="40" stroke="#DEC2A3" strokeWidth="8" fill="none"
                  strokeDasharray={2 * Math.PI * 40}
                  strokeDashoffset={2 * Math.PI * 40 * (1 - capaciteValue / 100)}
                  strokeLinecap="round" />
              )}
            </svg>
            <div className="absolute inset-0 flex items-center justify-center font-head font-semibold text-lg text-white">
              {capaciteValue != null ? capaciteValue : "—"}
            </div>
          </div>
          <span className="text-xs text-white/50">capacité</span>
          {capaciteValue == null && (
            <button onClick={() => navigate("/mindset")} className="text-[11px] text-[#DEC2A3] hover:text-[#FFD700] inline-flex items-center gap-1">
              Faire un check-in <ArrowRight size={11} />
            </button>
          )}
        </div>
      </div>

      {/* Métriques du jour — vraies données */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4" data-testid="aujourdhui-metrics">
        {/* Chaque métrique sans donnée dit ce qui la remplira, au lieu
            d'afficher un « 0 » ou un tiret muet pris pour une panne. */}
        <div className="glass p-4">
          <p className="text-xs text-white/50">Priorité principale</p>
          <p className="font-head text-lg font-semibold text-white mt-1 truncate">
            {loading ? "…" : prioritePrincipale ? prioritePrincipale.titre : "Aucune action notée"}
          </p>
          <p className="text-[11px] text-white/40 mt-0.5">
            {loading ? "Chargement…" : tachesOuvertes.length ? `${tachesOuvertes.length} tâche(s) ouverte(s)` : "Notez une action pour la voir ici"}
          </p>
        </div>
        <div className="glass p-4">
          <p className="text-xs text-white/50">Capacité disponible</p>
          <p className="font-head text-lg font-semibold text-white mt-1">
            {loading ? "…" : capaciteValue != null ? `${capaciteValue}/100` : "Pas encore mesurée"}
          </p>
          <p className="text-[11px] text-white/40 mt-0.5">
            {loading ? "Chargement…" : capaciteValue == null ? "Un check-in de 10 s la calcule" : capaciteValue >= 70 ? "Marge disponible" : "À surveiller"}
          </p>
        </div>
        <div className="glass p-4">
          <p className="text-xs text-white/50">Ma Vision</p>
          <p className="font-head text-lg font-semibold text-white mt-1 truncate">
            {loading ? "…" : vision?.value ? "Définie" : "Pas encore définie"}
          </p>
          <p className="text-[11px] text-white/40 mt-0.5">
            {loading ? "Chargement…" : vision?.value ? "Reliée à vos priorités" : "Écrivez votre Cap en une phrase"}
          </p>
        </div>
      </div>

      {/* Décision à clarifier + Impact sur la Vision — état honnête, pas de décision fabriquée */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="glass p-5" data-testid="aujourdhui-decisions">
          <div className="flex items-center gap-2 mb-2">
            <span className="w-8 h-8 rounded-lg gold-bg flex items-center justify-center shrink-0"><Target size={16} className="text-[#0A1128]" /></span>
            <span className="text-[11px] font-semibold uppercase tracking-wide text-[#DEC2A3]">Décision à clarifier</span>
          </div>
          <h3 className="font-head font-semibold text-white">Quelle action mérite d'être choisie maintenant ?</h3>
          <p className="text-[13px] text-white/55 mt-1.5 leading-relaxed">
            Cette fonctionnalité arrive bientôt — le Copilote pourra analyser votre contexte réel pour préparer une proposition, sans jamais rien engager sans votre validation.
          </p>
          <button onClick={() => window.dispatchEvent(new CustomEvent("cours:open-copilot"))}
            className="mt-3 inline-flex items-center gap-1.5 rounded-xl gold-bg px-4 py-2 text-sm font-semibold text-[#0A1128]">
            Clarifier avec le Copilote <ArrowRight size={14} />
          </button>
        </div>

        <div className="glass p-5" data-testid="aujourdhui-cap-link">
          <div className="flex items-center gap-2 mb-2">
            <span className="w-8 h-8 rounded-lg bg-blue-400/15 flex items-center justify-center shrink-0"><Lightbulb size={16} className="text-blue-300" /></span>
            <span className="text-[11px] font-semibold uppercase tracking-wide text-blue-300">Impact sur la Vision</span>
          </div>
          <h3 className="font-head font-semibold text-white">Le travail avance mieux quand le pourquoi reste visible.</h3>
          {vision?.value ? (
            <p className="text-[13px] text-white/55 mt-1.5 leading-relaxed line-clamp-3">{vision.value}</p>
          ) : (
            <p className="text-[13px] text-white/55 mt-1.5 leading-relaxed">Commencez par structurer votre Vision ; les décisions pourront ensuite être reliées à un résultat attendu.</p>
          )}
          <button onClick={() => navigate("/vision")} className="mt-3 inline-flex items-center gap-1 text-sm text-[#DEC2A3] hover:text-[#FFD700] transition-colors">
            Construire ma Vision <ArrowRight size={14} />
          </button>
        </div>
      </div>

      {/* Sur PC, la priorité du jour reste à sa place d'origine, en bas.
          Sur mobile, elle est déjà remontée en haut (voir isMobile && prioriteBlock). */}
      {!isMobile && prioriteBlock}
    </div>
  );
}
