import { useEffect, useState } from "react";
import { WalletCards, TrendingUp, ArrowRight, Bot } from "lucide-react";
import { useNavigate } from "react-router-dom";
import Pilotage from "./Pilotage";
import Croissance from "./Croissance";
import { getProspects, getPilotageOverview } from "../lib/api";

// Regroupe Pilotage et Croissance sous une seule entree de menu "Contexte".
// Vue "resume" par defaut (reprend la structure de la maquette de design
// partagee : 2 cartes cote a cote, icone + tag + titre + etat vide honnete
// + CTA) mais avec de vraies donnees au lieu des placeholders fixes de la
// maquette. Les vues completes Pilotage/Croissance restent accessibles
// via les onglets, sans rien retirer de ce qui existait deja.
function ResumeContexte({ onOpenTab }) {
  const navigate = useNavigate();
  const [pilotage, setPilotage] = useState(null);
  const [prospects, setProspects] = useState(null);

  useEffect(() => {
    getPilotageOverview().then(setPilotage).catch(() => setPilotage({ entries: [], summary: {} }));
    getProspects().then((rows) => setProspects(Array.isArray(rows) ? rows : [])).catch(() => setProspects([]));
  }, []);

  const tresorerie = Number(pilotage?.summary?.tresorerie || 0);
  const aDesDonneesFinancieres = Boolean(pilotage?.entries?.length || tresorerie > 0);

  return (
    <>
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-[.14em] text-[#DEC2A3]">Contexte business</p>
        <h1 className="font-head text-2xl sm:text-3xl font-semibold text-white mt-1">Les données servent le Cap.</h1>
        <p className="text-white/55 text-sm mt-1 max-w-xl">Pilotage et Croissance éclairent les décisions, sans prendre la place de votre direction.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="glass p-6" data-testid="contexte-card-pilotage">
          <div className="flex items-center gap-2 mb-4">
            <span className="w-9 h-9 rounded-lg gold-bg flex items-center justify-center shrink-0"><WalletCards size={17} className="text-[#0A1128]" /></span>
            <span className="text-[11px] font-semibold uppercase tracking-wide text-[#DEC2A3]">Pilotage & trésorerie</span>
          </div>
          <h2 className="font-head text-lg font-semibold text-white">Relier votre trésorerie au Cap.</h2>
          <p className="text-[13px] text-white/55 mt-1.5 leading-relaxed">Comptes, revenus, factures et charges — la lecture est consolidée depuis les sources que vous autorisez.</p>
          {pilotage === null ? (
            <p className="text-sm text-white/40 mt-6">Chargement…</p>
          ) : aDesDonneesFinancieres ? (
            <div className="mt-6">
              <p className="text-2xl font-head font-semibold text-white">{tresorerie.toLocaleString("fr-FR")} €</p>
              <p className="text-[11px] text-white/40 mt-0.5">Trésorerie déclarée</p>
            </div>
          ) : (
            <div className="flex items-center gap-2 mt-6">
              <span className="w-6 h-0.5 bg-[#DEC2A3]" />
              <span className="text-sm text-white/45">aucune donnée importée</span>
            </div>
          )}
          <button onClick={() => onOpenTab("pilotage")} className="mt-5 inline-flex items-center gap-1.5 rounded-xl border border-white/15 px-4 py-2 text-sm font-semibold text-white/80 hover:bg-white/5 transition-colors">
            {aDesDonneesFinancieres ? "Ouvrir Pilotage" : "Configurer les sources"} <ArrowRight size={14} />
          </button>
        </div>

        <div className="glass p-6" data-testid="contexte-card-croissance">
          <div className="flex items-center gap-2 mb-4">
            <span className="w-9 h-9 rounded-lg bg-blue-400/15 flex items-center justify-center shrink-0"><TrendingUp size={17} className="text-blue-300" /></span>
            <span className="text-[11px] font-semibold uppercase tracking-wide text-blue-300">Croissance</span>
          </div>
          <h2 className="font-head text-lg font-semibold text-white">Rechercher les bons signaux.</h2>
          <p className="text-[13px] text-white/55 mt-1.5 leading-relaxed">Prospects, pipeline et prochaines actions — vue synthétique, le détail complet reste dans l'onglet Croissance.</p>
          {prospects === null ? (
            <p className="text-sm text-white/40 mt-6">Chargement…</p>
          ) : prospects.length > 0 ? (
            <div className="mt-6">
              <p className="text-2xl font-head font-semibold text-white">{prospects.length}</p>
              <p className="text-[11px] text-white/40 mt-0.5">prospect(s) dans le pipeline</p>
            </div>
          ) : (
            <div className="flex items-center gap-2 mt-6">
              <span className="w-6 h-0.5 bg-[#DEC2A3]" />
              <span className="text-sm text-white/45">aucun prospect connecté</span>
            </div>
          )}
          <button onClick={() => onOpenTab("croissance")} className="mt-5 inline-flex items-center gap-1.5 rounded-xl border border-white/15 px-4 py-2 text-sm font-semibold text-white/80 hover:bg-white/5 transition-colors">
            {prospects && prospects.length > 0 ? "Ouvrir Croissance" : "Définir une cible"} <ArrowRight size={14} />
          </button>
        </div>
      </div>
    </>
  );
}

const TABS = [
  { id: "resume", label: "Résumé", Icon: null },
  { id: "pilotage", label: "Pilotage & trésorerie", Icon: WalletCards },
  { id: "croissance", label: "Croissance", Icon: TrendingUp },
  { id: "agents", label: "Agents IA", Icon: Bot },
];

function AgentsContext() {
  return (
    <section className="glass p-6" data-testid="contexte-agents">
      <div className="flex items-start gap-3">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-white/15 bg-white/[.06] text-[#F1E2CC]"><Bot size={19} /></span>
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[.14em] text-[#DEC2A3]">Agents IA</p>
          <h1 className="font-head mt-1 text-2xl font-semibold text-white">Des agents au service du contexte, jamais à votre insu.</h1>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-white/60">Cet espace réunira les agents autorisés à préparer une analyse, surveiller une source ou mettre en forme un brouillon. Aucun agent n’est déclaré actif tant qu’il n’a pas été configuré et que son périmètre n’a pas été validé.</p>
        </div>
      </div>
      <div className="mt-6 grid grid-cols-1 gap-3 md:grid-cols-3">
        {[
          ["Sources", "Connecter des données ou des outils avec votre accord."],
          ["Périmètre", "Définir ce que l’agent peut préparer, sans envoi autonome."],
          ["Validation", "Vous relisez et décidez avant toute action externe."],
        ].map(([title, detail]) => <div key={title} className="rounded-xl border border-white/12 bg-white/[.04] p-4"><p className="text-sm font-semibold text-white">{title}</p><p className="mt-1 text-xs leading-relaxed text-white/55">{detail}</p></div>)}
      </div>
      <p className="mt-5 rounded-xl border border-dashed border-white/15 px-4 py-3 text-sm text-white/55">Aucun agent n’est encore configuré pour cet espace.</p>
      <button disabled title="La configuration d'agents IA n'est pas encore construite côté serveur." className="mt-3 rounded-xl border border-white/15 px-4 py-2.5 text-sm font-semibold text-white/40 cursor-not-allowed">Configurer un agent — Bientôt</button>
    </section>
  );
}

export default function Contexte() {
  const [tab, setTab] = useState("resume");
  return (
    <div className="space-y-6" data-testid="page-contexte">
      <nav className="flex gap-2">
        {TABS.map(({ id, label, Icon }) => (
          <button key={id} onClick={() => setTab(id)} data-testid={`contexte-tab-${id}`}
            className={`inline-flex items-center gap-1.5 rounded-full px-4 py-2 text-sm font-semibold transition-colors ${tab === id ? "gold-bg text-[#0A1128]" : "bg-white/5 border border-white/15 text-white/70"}`}>
            {Icon && <Icon size={14} />} {label}
          </button>
        ))}
      </nav>

      {tab === "resume" && <ResumeContexte onOpenTab={setTab} />}
      {tab === "pilotage" && <Pilotage embedded />}
      {tab === "croissance" && <Croissance embedded />}
      {tab === "agents" && <AgentsContext />}
    </div>
  );
}
