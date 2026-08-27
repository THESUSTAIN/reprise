import { useEffect, useState } from "react";
import { Compass, ArrowRight, Zap, ListChecks, Sparkles, Target, Lightbulb } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { getVision, getHumeur, getTaches } from "../lib/api";
import useIsMobile from "../hooks/useIsMobile";

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

  const dernierHumeur = humeur[0];
  const capaciteValue = dernierHumeur ? dernierHumeur.energie : null;
  const tachesOuvertes = taches.filter((t) => t.statut !== "Terminé");
  const prioritePrincipale = tachesOuvertes
    .slice()
    .sort((a, b) => (a.priorite === "Haute" ? -1 : 1) - (b.priorite === "Haute" ? -1 : 1))[0];

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
        <div className="glass p-4">
          <p className="text-xs text-white/50">Priorité principale</p>
          <p className="font-head text-lg font-semibold text-white mt-1 truncate">{prioritePrincipale ? prioritePrincipale.titre : "À définir"}</p>
          <p className="text-[11px] text-white/40 mt-0.5">{tachesOuvertes.length} tâche(s) ouverte(s)</p>
        </div>
        <div className="glass p-4">
          <p className="text-xs text-white/50">Capacité disponible</p>
          <p className="font-head text-lg font-semibold text-white mt-1">{capaciteValue != null ? `${capaciteValue}/100` : "—"}</p>
          <p className="text-[11px] text-white/40 mt-0.5">{capaciteValue == null ? "Check-in facultatif" : capaciteValue >= 70 ? "Marge disponible" : "À surveiller"}</p>
        </div>
        <div className="glass p-4">
          <p className="text-xs text-white/50">Ma Vision</p>
          <p className="font-head text-lg font-semibold text-white mt-1 truncate">{vision?.value ? "Défini" : "À définir"}</p>
          <p className="text-[11px] text-white/40 mt-0.5">{vision?.value ? "Relié à vos priorités" : "Reliez une action à votre Vision"}</p>
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
