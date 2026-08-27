import { useEffect, useState } from "react";
import {
  Wallet, TrendingUp, PieChart, LineChart as LineIcon, Plus, Trash2,
  ArrowUpRight, ArrowDownRight, Building2, Download, AlertTriangle, Calculator, Gauge, Loader2,
  Landmark, Plug, ShieldCheck,
} from "lucide-react";
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from "recharts";
import { toast } from "sonner";
import {
  getKpis, getFactures, createFacture, deleteFacture,
  getDepenses, createDepense, deleteDepense, euro,
  getTresorerieHistory, getDecision, simulatePilotage, getHealthScore, exportCsvUrl, getOdooConfig,
} from "../lib/api";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter,
} from "../components/ui/dialog";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "../components/ui/select";

const STATUT_COLORS = {
  "Payée": "text-emerald-400 bg-emerald-400/10 border-emerald-400/30",
  "En retard": "text-rose-400 bg-rose-400/10 border-rose-400/30",
  "En attente": "text-amber-400 bg-amber-400/10 border-amber-400/30",
  "À envoyer": "text-sky-400 bg-sky-400/10 border-sky-400/30",
};

function KpiCard({ icon: Icon, label, value, delta, positive }) {
  return (
    <div className="glass glass-hover p-5 fade-in" data-testid={`kpi-${label}`}>
      <div className="flex items-start justify-between">
        <span className="text-[13px] text-white/60">{label}</span>
        <div className="w-9 h-9 rounded-xl bg-[#DEC2A3]/15 border border-[#DEC2A3]/25 flex items-center justify-center">
          <Icon size={17} className="text-[#DEC2A3]" strokeWidth={1.5} />
        </div>
      </div>
      <div className="mt-3 font-head text-2xl font-semibold tracking-tight">{value}</div>
      {delta && (
        <div className={`mt-1.5 flex items-center gap-1 text-xs ${positive ? "text-emerald-400" : "text-rose-400"}`}>
          {positive ? <ArrowUpRight size={13} /> : <ArrowDownRight size={13} />} {delta}
        </div>
      )}
    </div>
  );
}

function DecisionBanner({ decision }) {
  if (!decision) return null;
  return (
    <div className={`glass p-4 flex items-start gap-3 border-l-4 ${decision.severity === "high" ? "border-l-rose-400" : "border-l-amber-400"}`} data-testid="decision-banner">
      <AlertTriangle size={18} className={decision.severity === "high" ? "text-rose-400" : "text-amber-400"} />
      <div>
        <div className="text-sm font-semibold text-white">{decision.title}</div>
        <p className="text-[12.5px] text-white/60 mt-0.5">{decision.detail}</p>
      </div>
    </div>
  );
}

function FinancialSourceCard({ icon: Icon, title, detail, status, tone = "muted" }) {
  const tones = {
    muted: "border-white/15 bg-white/[0.05] text-white/60",
    connected: "border-emerald-300/30 bg-emerald-300/10 text-emerald-200",
  };
  return (
    <div className="rounded-2xl border border-white/15 bg-white/[0.045] p-4" data-testid={`pilotage-source-${title.toLowerCase()}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-[#F1E2CC]/25 bg-[#F1E2CC]/10 text-[#F1E2CC]"><Icon size={18} /></div>
        <span className={`inline-flex rounded-full border px-2 py-1 text-[10px] font-bold ${tones[tone]}`}>{status}</span>
      </div>
      <p className="mt-4 font-head text-sm font-semibold text-white">{title}</p>
      <p className="mt-1 text-xs leading-5 text-white/52">{detail}</p>
    </div>
  );
}

function FinancialSources() {
  const [odooConnected, setOdooConnected] = useState(false);

  useEffect(() => {
    getOdooConfig().then((config) => setOdooConnected(Boolean(config?.connected))).catch(() => setOdooConnected(false));
  }, []);

  const openIntegrations = () => window.dispatchEvent(new CustomEvent("cours:open-settings", { detail: { section: "integrations" } }));

  return (
    <section className="glass overflow-hidden p-5 sm:p-6" data-testid="pilotage-financial-sources">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="max-w-2xl">
          <p className="text-[11px] font-bold uppercase tracking-[.17em] text-[#F1E2CC]">Sources financières</p>
          <h2 className="mt-1 font-head text-xl font-semibold text-white">Une lecture consolidée, sans remplacer vos outils.</h2>
          <p className="mt-2 text-sm leading-6 text-white/58">MyExtension AI rassemble uniquement les comptes, factures, dépenses et encaissements que vous autorisez. Aucune écriture comptable, aucun paiement et aucune donnée inventée.</p>
        </div>
        <button onClick={openIntegrations} className="inline-flex items-center gap-2 rounded-xl border border-[#F1E2CC]/45 bg-[#F1E2CC]/10 px-4 py-2.5 text-sm font-semibold text-[#F4D990] transition hover:bg-[#F1E2CC]/18" data-testid="pilotage-open-integrations"><Plug size={15} /> Configurer les sources</button>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-3">
        <FinancialSourceCard icon={Building2} title="Odoo" detail="Factures, dépenses et statuts autorisés. Odoo reste votre système de gestion." status={odooConnected ? "Connecté" : "À connecter"} tone={odooConnected ? "connected" : "muted"} />
        <FinancialSourceCard icon={Wallet} title="Pennylane" detail="Factures, dépenses et vision comptable, après autorisation explicite." status="À connecter" />
        <FinancialSourceCard icon={Landmark} title="Qonto" detail="Comptes, soldes et transactions bancaires, en lecture seule." status="À connecter" />
      </div>

      <div className="mt-5 flex flex-wrap items-start gap-3 rounded-xl border border-white/12 bg-white/[0.035] p-3 text-xs leading-5 text-white/58">
        <ShieldCheck size={17} className="mt-0.5 shrink-0 text-[#F1E2CC]" />
        <p className="m-0"><strong className="font-semibold text-white/82">Votre outil source reste la vérité.</strong> Chaque connexion devra indiquer son périmètre, sa dernière synchronisation et pouvoir être révoquée. Les capacités de paiement restent hors du périmètre initial.</p>
      </div>
    </section>
  );
}

function SimulateurTresorerie() {
  const [scenarios, setScenarios] = useState([
    { id: "prudent", name: "Prudent", nbContrats: 1, montant: 1000, depenses: 0 },
    { id: "central", name: "Central", nbContrats: 3, montant: 1500, depenses: 500 },
    { id: "ambitieux", name: "Ambitieux", nbContrats: 6, montant: 2000, depenses: 1200 },
  ]);
  const [results, setResults] = useState({});
  const [loading, setLoading] = useState(false);

  const updateScenario = (id, field, value) => setScenarios((current) => current.map((scenario) => scenario.id === id ? { ...scenario, [field]: value } : scenario));

  const run = async () => {
    setLoading(true);
    try {
      const entries = await Promise.all(scenarios.map(async (scenario) => {
        const result = await simulatePilotage({ nb_contrats: Number(scenario.nbContrats) || 0, montant_moyen: Number(scenario.montant) || 0, depenses_supplementaires: Number(scenario.depenses) || 0 });
        return [scenario.id, result];
      }));
      setResults(Object.fromEntries(entries));
    } catch {
      toast.error("Impossible de comparer les scénarios pour le moment");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass p-5" data-testid="simulateur-tresorerie">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div><h3 className="font-head flex items-center gap-2 font-semibold"><Calculator size={16} className="text-[#DEC2A3]" /> Comparateur de scénarios</h3><p className="mt-1 text-[12px] text-white/50">Comparez trois hypothèses avant de décider, sans présenter une projection comme une certitude.</p></div>
        <span className="rounded-full border border-white/15 bg-white/[0.04] px-2.5 py-1 text-[10px] text-white/45">Simulation indicative</span>
      </div>
      <div className="mb-1.5 grid grid-cols-3 gap-2 px-3 text-[10px] font-semibold uppercase tracking-wide text-white/40">
        <span>Contrats</span><span>€ moyen / contrat</span><span>Dépenses supplémentaires</span>
      </div>
      <div className="space-y-3">
        {scenarios.map((scenario) => (
          <div key={scenario.id} className="rounded-2xl border border-white/10 bg-white/[0.035] p-3" data-testid={`simulation-scenario-${scenario.id}`}>
            <div className="mb-2 flex items-center justify-between"><strong className="text-sm text-white">{scenario.name}</strong><span className="text-[10px] uppercase tracking-wide text-white/40">Hypothèse</span></div>
            <div className="grid grid-cols-3 gap-2">
              <input type="number" value={scenario.nbContrats} onChange={(e) => updateScenario(scenario.id, "nbContrats", e.target.value)} aria-label={`${scenario.name} contrats`} placeholder="Contrats" className="rounded-lg border border-white/15 bg-white/5 px-2.5 py-2 text-sm text-white" />
              <input type="number" value={scenario.montant} onChange={(e) => updateScenario(scenario.id, "montant", e.target.value)} aria-label={`${scenario.name} montant`} placeholder="€ moyen" className="rounded-lg border border-white/15 bg-white/5 px-2.5 py-2 text-sm text-white" />
              <input type="number" value={scenario.depenses} onChange={(e) => updateScenario(scenario.id, "depenses", e.target.value)} aria-label={`${scenario.name} dépenses`} placeholder="Dépenses +" className="rounded-lg border border-white/15 bg-white/5 px-2.5 py-2 text-sm text-white" />
            </div>
            {results[scenario.id] && <div className="mt-3 grid grid-cols-2 gap-3 text-center" data-testid={`simulation-result-${scenario.id}`}><div><div className="text-[11px] text-white/50">Trésorerie projetée</div><div className="font-head text-lg font-semibold text-emerald-400">{euro(results[scenario.id].projected_tresorerie)}</div></div><div><div className="text-[11px] text-white/50">Marge projetée</div><div className="font-head text-lg font-semibold">{results[scenario.id].projected_marge}%</div></div></div>}
          </div>
        ))}
      </div>
      <button onClick={run} disabled={loading} data-testid="sim-run-btn" className="gold-bg mt-4 flex w-full items-center justify-center gap-2 rounded-full py-2 text-sm font-semibold text-[#0A1128] disabled:opacity-60">{loading ? <Loader2 size={14} className="animate-spin" /> : <Calculator size={14} />} Comparer les scénarios</button>
    </div>
  );
}

function ScoreSante({ score }) {
  if (!score) return null;
  const color = score.score >= 70 ? "#34d399" : score.score >= 40 ? "#fbbf24" : "#f87171";
  return (
    <div className="glass p-5 flex flex-col items-center text-center" data-testid="score-sante">
      <h3 className="font-head font-semibold flex items-center gap-2 mb-3"><Gauge size={16} className="text-[#DEC2A3]" /> Score de santé financière</h3>
      <div className="relative w-24 h-24 my-1">
        <svg className="w-24 h-24 -rotate-90">
          <circle cx="48" cy="48" r="40" stroke="rgba(255,255,255,0.1)" strokeWidth="8" fill="none" />
          <circle cx="48" cy="48" r="40" stroke={color} strokeWidth="8" fill="none"
            strokeDasharray={2 * Math.PI * 40} strokeDashoffset={2 * Math.PI * 40 * (1 - score.score / 100)} strokeLinecap="round" />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center font-head text-2xl font-semibold">{score.score}</div>
      </div>
      <p className="text-[11px] text-white/50 mt-2">Marge {score.marge_score} · Trésorerie {score.tresorerie_score} · Retards {score.retard_score}</p>
    </div>
  );
}

function AddFactureDialog({ onAdded }) {
  const [open, setOpen] = useState(false);
  const [f, setF] = useState({ client: "", reference: "", montant: "", statut: "À envoyer", echeance: "" });
  const submit = async () => {
    if (!f.client || !f.montant) return toast.error("Client et montant requis");
    await createFacture({ ...f, montant: parseFloat(f.montant) });
    toast.success("Facture ajoutée");
    setOpen(false);
    setF({ client: "", reference: "", montant: "", statut: "À envoyer", echeance: "" });
    onAdded();
  };
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <button data-testid="add-facture-btn" className="flex items-center gap-1 text-xs text-[#DEC2A3] hover:text-[#FFD700] transition-colors">
          <Plus size={14} /> Ajouter
        </button>
      </DialogTrigger>
      <DialogContent className="bg-[#0A1128] border-white/15 text-white">
        <DialogHeader><DialogTitle className="font-head">Nouvelle facture</DialogTitle></DialogHeader>
        <div className="space-y-3">
          <div><Label className="text-white/70">Client</Label>
            <Input data-testid="facture-client" value={f.client} onChange={(e) => setF({ ...f, client: e.target.value })} className="bg-white/5 border-white/15 mt-1" /></div>
          <div className="grid grid-cols-2 gap-3">
            <div><Label className="text-white/70">Référence</Label>
              <Input value={f.reference} onChange={(e) => setF({ ...f, reference: e.target.value })} className="bg-white/5 border-white/15 mt-1" /></div>
            <div><Label className="text-white/70">Montant (€)</Label>
              <Input data-testid="facture-montant" type="number" value={f.montant} onChange={(e) => setF({ ...f, montant: e.target.value })} className="bg-white/5 border-white/15 mt-1" /></div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div><Label className="text-white/70">Statut</Label>
              <Select value={f.statut} onValueChange={(v) => setF({ ...f, statut: v })}>
                <SelectTrigger className="bg-white/5 border-white/15 mt-1" data-testid="facture-statut"><SelectValue /></SelectTrigger>
                <SelectContent className="bg-[#0A1128] border-white/15 text-white">
                  {["À envoyer", "En attente", "En retard", "Payée"].map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}
                </SelectContent>
              </Select></div>
            <div><Label className="text-white/70">Échéance</Label>
              <Input type="date" value={f.echeance} onChange={(e) => setF({ ...f, echeance: e.target.value })} className="bg-white/5 border-white/15 mt-1" /></div>
          </div>
        </div>
        <DialogFooter>
          <button data-testid="facture-submit" onClick={submit} className="gold-bg text-[#0A1128] font-semibold rounded-full px-5 py-2 text-sm">Enregistrer</button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function AddDepenseDialog({ onAdded }) {
  const [open, setOpen] = useState(false);
  const [d, setD] = useState({ libelle: "", categorie: "SaaS", montant: "", date: "" });
  const submit = async () => {
    if (!d.libelle || !d.montant) return toast.error("Libellé et montant requis");
    await createDepense({ ...d, montant: parseFloat(d.montant) });
    toast.success("Dépense ajoutée");
    setOpen(false);
    setD({ libelle: "", categorie: "SaaS", montant: "", date: "" });
    onAdded();
  };
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <button data-testid="add-depense-btn" className="flex items-center gap-1 text-xs text-[#DEC2A3] hover:text-[#FFD700] transition-colors">
          <Plus size={14} /> Ajouter
        </button>
      </DialogTrigger>
      <DialogContent className="bg-[#0A1128] border-white/15 text-white">
        <DialogHeader><DialogTitle className="font-head">Nouvelle dépense</DialogTitle></DialogHeader>
        <div className="space-y-3">
          <div><Label className="text-white/70">Libellé</Label>
            <Input data-testid="depense-libelle" value={d.libelle} onChange={(e) => setD({ ...d, libelle: e.target.value })} className="bg-white/5 border-white/15 mt-1" /></div>
          <div className="grid grid-cols-2 gap-3">
            <div><Label className="text-white/70">Catégorie</Label>
              <Select value={d.categorie} onValueChange={(v) => setD({ ...d, categorie: v })}>
                <SelectTrigger className="bg-white/5 border-white/15 mt-1"><SelectValue /></SelectTrigger>
                <SelectContent className="bg-[#0A1128] border-white/15 text-white">
                  {["SaaS", "Marketing", "Outils", "Sous-traitance", "Autre"].map((c) => <SelectItem key={c} value={c}>{c}</SelectItem>)}
                </SelectContent>
              </Select></div>
            <div><Label className="text-white/70">Montant (€)</Label>
              <Input data-testid="depense-montant" type="number" value={d.montant} onChange={(e) => setD({ ...d, montant: e.target.value })} className="bg-white/5 border-white/15 mt-1" /></div>
          </div>
        </div>
        <DialogFooter>
          <button data-testid="depense-submit" onClick={submit} className="gold-bg text-[#0A1128] font-semibold rounded-full px-5 py-2 text-sm">Enregistrer</button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default function Pilotage() {
  const [kpis, setKpis] = useState(null);
  const [factures, setFactures] = useState([]);
  const [depenses, setDepenses] = useState([]);
  const [history, setHistory] = useState([]);
  const [decision, setDecision] = useState(null);
  const [score, setScore] = useState(null);

  const load = async () => {
    try {
      const [nextKpis, nextFactures, nextDepenses, nextHistory, nextDecision, nextScore] = await Promise.all([
        getKpis().catch(() => null),
        getFactures().catch(() => []),
        getDepenses().catch(() => []),
        getTresorerieHistory().catch(() => []),
        getDecision().catch(() => null),
        getHealthScore().catch(() => null),
      ]);
      setKpis(nextKpis);
      setFactures(Array.isArray(nextFactures) ? nextFactures : []);
      setDepenses(Array.isArray(nextDepenses) ? nextDepenses : []);
      setHistory(Array.isArray(nextHistory) ? nextHistory : []);
      setDecision(nextDecision);
      setScore(nextScore);
    } catch {
      setKpis(null); setFactures([]); setDepenses([]); setHistory([]); setDecision(null); setScore(null);
    }
  };
  useEffect(() => { load(); }, []);

  const trend = history.map((h) => ({ jour: h.date.slice(5), valeur: h.tresorerie }));

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-head text-3xl sm:text-4xl font-semibold"><span className="gold-text">Pilotage & trésorerie</span></h1>
          <p className="text-white/55 text-sm mt-1">Lire vos indicateurs, arbitrer avec le Cap et rester maître de vos outils financiers.</p>
        </div>
        <a href={exportCsvUrl()} download className="glass glass-hover px-4 py-2 text-sm flex items-center gap-2" data-testid="export-btn">
          <Download size={15} /> Exporter
        </a>
      </div>

      <FinancialSources />

      <DecisionBanner decision={decision} />

      {/* KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <KpiCard icon={Building2} label="Trésorerie disponible" value={kpis ? euro(kpis.tresorerie) : "—"} />
        <KpiCard icon={TrendingUp} label="Chiffre d'affaires" value={kpis ? euro(kpis.chiffre_affaires) : "—"} />
        <KpiCard icon={PieChart} label="Marge nette" value={kpis ? `${kpis.marge_nette}%` : "—"} />
        <KpiCard icon={LineIcon} label="Résultat net" value={kpis ? euro(kpis.resultat_net) : "—"} />
      </div>

      {/* Chart + Analyse */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="glass p-5 xl:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-head font-semibold">Évolution de la trésorerie</h3>
            <span className="text-xs text-white/50">Historique réel</span>
          </div>
          {trend.length < 2 ? (
            <p className="text-sm text-white/40 py-16 text-center">
              Pas encore assez d'historique — un point est enregistré chaque jour. Revenez dans quelques jours pour voir la courbe se dessiner.
            </p>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={trend} margin={{ left: -10, right: 10, top: 10 }}>
                <defs>
                  <linearGradient id="gold" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#F1E2CC" stopOpacity={0.55} />
                    <stop offset="100%" stopColor="#DEC2A3" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="jour" stroke="rgba(255,255,255,0.4)" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke="rgba(255,255,255,0.4)" fontSize={11} tickLine={false} axisLine={false} tickFormatter={(v) => `${Math.round(v / 1000)}k`} />
                <Tooltip
                  contentStyle={{ background: "#0B1F3A", border: "1px solid rgba(222, 194, 163,0.4)", borderRadius: 12, color: "#fff" }}
                  formatter={(v) => [euro(v), "Trésorerie"]}
                />
                <Area type="monotone" dataKey="valeur" stroke="#F1E2CC" strokeWidth={3} fill="url(#gold)" dot={{ r: 3, fill: "#F1E2CC" }} activeDot={{ r: 5 }} isAnimationActive={false} />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>

        <ScoreSante score={score} />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <SimulateurTresorerie />
        <div className="glass p-5">
          <h3 className="font-head font-semibold flex items-center gap-2 mb-3">
            <span className="text-[#DEC2A3]">✦</span> Analyse de contexte
          </h3>
          <p className="text-sm text-white/70 leading-relaxed">
            {!kpis ? "Aucune source financière connectée pour l'instant — rien à analyser." : (
              <>
                Votre trésorerie est {kpis.tresorerie > 0 ? "saine" : "à surveiller"}.
                {kpis.en_retard > 0 && ` ${euro(kpis.en_retard)} de factures sont en retard.`}
              </>
            )}
          </p>
          <div className="mt-4 space-y-2">
            {[
              kpis && kpis.en_retard > 0 && `Relancer ${euro(kpis.en_retard)} de factures en retard`,
              kpis && kpis.marge_nette < 20 && `Marge nette à ${kpis.marge_nette}% — revoir les charges récurrentes`,
              kpis && kpis.total_depenses > 0 && `${euro(kpis.total_depenses)} de dépenses ce mois — vérifier les abonnements inutilisés`,
            ].filter(Boolean).map((t) => (
              <div key={t} className="flex items-start gap-2 text-[13px] text-white/70">
                <span className="text-[#DEC2A3] mt-0.5">✓</span> {t}
              </div>
            ))}
            {kpis && !kpis.en_retard && kpis.marge_nette >= 20 && (
              <p className="text-[13px] text-white/45">Rien à signaler — vos indicateurs sont sains.</p>
            )}
          </div>
        </div>
      </div>

      {/* Factures + Dépenses */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="glass p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-head font-semibold">Factures à suivre</h3>
            <AddFactureDialog onAdded={load} />
          </div>
          <div className="space-y-2" data-testid="factures-list">
            {factures.map((f) => (
              <div key={f.id} className="flex items-center justify-between rounded-xl bg-white/5 border border-white/10 px-3.5 py-2.5 group">
                <div className="min-w-0">
                  <div className="text-sm font-medium truncate">{f.client}</div>
                  <div className="text-[11px] text-white/45">#{f.reference || "—"}</div>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`text-[10px] px-2 py-0.5 rounded-full border ${STATUT_COLORS[f.statut] || ""}`}>{f.statut}</span>
                  <span className="text-sm font-semibold">{euro(f.montant)}</span>
                  <button onClick={async () => { await deleteFacture(f.id); load(); }} data-testid={`delete-facture-${f.id}`} className="text-white/30 hover:text-rose-400 transition-colors">
                    <Trash2 size={15} />
                  </button>
                </div>
              </div>
            ))}
            {factures.length === 0 && <p className="text-sm text-white/40 py-4 text-center">Aucune facture.</p>}
          </div>
        </div>

        <div className="glass p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-head font-semibold">Dépenses récentes</h3>
            <AddDepenseDialog onAdded={load} />
          </div>
          <div className="space-y-2" data-testid="depenses-list">
            {depenses.map((d) => (
              <div key={d.id} className="flex items-center justify-between rounded-xl bg-white/5 border border-white/10 px-3.5 py-2.5">
                <div className="min-w-0">
                  <div className="text-sm font-medium truncate">{d.libelle}</div>
                  <div className="text-[11px] text-white/45">{d.categorie}</div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm font-semibold text-rose-300">-{euro(d.montant)}</span>
                  <button onClick={async () => { await deleteDepense(d.id); load(); }} data-testid={`delete-depense-${d.id}`} className="text-white/30 hover:text-rose-400 transition-colors">
                    <Trash2 size={15} />
                  </button>
                </div>
              </div>
            ))}
            {depenses.length === 0 && <p className="text-sm text-white/40 py-4 text-center">Aucune dépense.</p>}
          </div>
        </div>
      </div>
    </div>
  );
}
