import { useEffect, useState } from "react";
import {
  Zap, Flame, Plus, Trash2, Check, RefreshCw, Wind, Heart, AlertTriangle,
  ShieldCheck, MessageCircle, TrendingUp, CalendarDays, Loader2,
} from "lucide-react";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
  ScatterChart, Scatter, ZAxis,
} from "recharts";
import { toast } from "sonner";
import {
  getRituels, createRituel, toggleRituel, deleteRituel,
  getHumeur, createHumeur, getWellnessCorrelations, getYearPixels, getVision, getTaches, euro,
} from "../lib/api";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter,
} from "../components/ui/dialog";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "../components/ui/select";

const AFFIRMATIONS = [
  "Je transforme ma vision en actions concrètes, un pas à la fois.",
  "Mon énergie est ma ressource la plus précieuse. Je la protège.",
  "Je ne cherche pas la perfection, je cherche la constance.",
  "Chaque petit progrès me rapproche de la personne que je deviens.",
  "L'abandon n'est pas une option : je m'ajuste, je continue.",
];

const HUMEURS = ["Épuisé", "Fatigué", "Bien", "Motivé", "En feu"];


function Gauge({ value, color, label, sub }) {
  return (
    <div className="glass glass-hover p-5 flex items-center gap-4 fade-in" data-testid={`gauge-${label}`}>
      <div className="relative w-20 h-20 shrink-0">
        <svg className="w-20 h-20 -rotate-90">
          <circle cx="40" cy="40" r="34" stroke="rgba(255,255,255,0.1)" strokeWidth="7" fill="none" />
          <circle cx="40" cy="40" r="34" stroke={color} strokeWidth="7" fill="none"
            strokeDasharray={2 * Math.PI * 34}
            strokeDashoffset={2 * Math.PI * 34 * (1 - value / 100)}
            strokeLinecap="round" />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center font-head font-semibold text-lg">{value}</div>
      </div>
      <div>
        <div className="text-sm text-white/60">{label}</div>
        <div className="font-head font-semibold text-lg">{sub}</div>
      </div>
    </div>
  );
}

function CheckinDialog({ onSaved }) {
  const [open, setOpen] = useState(false);
  const [energie, setEnergie] = useState(70);
  const [humeur, setHumeur] = useState("Bien");
  const [note, setNote] = useState("");
  const submit = async () => {
    await createHumeur({ energie: parseInt(energie), humeur, note });
    toast.success("Check-in enregistré");
    setOpen(false);
    setNote("");
    onSaved();
  };
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <button data-testid="checkin-btn" className="gold-bg text-[#0A1128] font-semibold rounded-full px-4 py-2 text-sm flex items-center gap-1.5">
          <Plus size={15} /> Check-in du jour
        </button>
      </DialogTrigger>
      <DialogContent className="bg-[#0A1128] border-white/15 text-white">
        <DialogHeader><DialogTitle className="font-head">Comment te sens-tu ?</DialogTitle></DialogHeader>
        <div className="space-y-5 py-2">
          <div>
            <Label className="text-white/70">Énergie : <span className="text-[#DEC2A3] font-semibold">{energie}/100</span></Label>
            <input data-testid="checkin-energie" type="range" min="0" max="100" value={energie} onChange={(e) => setEnergie(e.target.value)} className="w-full mt-3 accent-[#DEC2A3]" />
          </div>
          <div><Label className="text-white/70">Humeur</Label>
            <Select value={humeur} onValueChange={setHumeur}>
              <SelectTrigger className="bg-white/5 border-white/15 mt-1" data-testid="checkin-humeur"><SelectValue /></SelectTrigger>
              <SelectContent className="bg-[#0A1128] border-white/15 text-white">
                {HUMEURS.map((h) => <SelectItem key={h} value={h}>{h}</SelectItem>)}
              </SelectContent>
            </Select></div>
          <div><Label className="text-white/70">Note (optionnel)</Label>
            <Input value={note} onChange={(e) => setNote(e.target.value)} className="bg-white/5 border-white/15 mt-1" placeholder="Une pensée du jour…" /></div>
        </div>
        <DialogFooter>
          <button data-testid="checkin-submit" onClick={submit} className="gold-bg text-[#0A1128] font-semibold rounded-full px-5 py-2 text-sm">Enregistrer</button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

/* Corrélations énergie/performance — relie réellement Bien-être et Pilotage,
 * les deux domaines vivaient en silo jusqu'ici. */
function WellnessCorrelations() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getWellnessCorrelations().then(setData).catch(() => setData({ points: [], has_data: false })).finally(() => setLoading(false));
  }, []);

  return (
    <div className="glass p-5" data-testid="wellness-correlations">
      <h3 className="font-head font-semibold flex items-center gap-2 mb-1"><TrendingUp size={17} className="text-[#DEC2A3]" /> Corrélation énergie / performance</h3>
      <p className="text-[12px] text-white/50 mb-4">Votre énergie du jour comparée à votre chiffre d'affaires du même jour.</p>
      {loading ? (
        <div className="flex justify-center py-10"><Loader2 size={20} className="animate-spin text-white/40" /></div>
      ) : !data?.has_data ? (
        <p className="text-sm text-white/45 py-8 text-center">
          Pas encore assez de jours avec un check-in énergie ET des données financières le même jour. Continuez vos check-ins quotidiens.
        </p>
      ) : (
        <>
          <ResponsiveContainer width="100%" height={220}>
            <ScatterChart margin={{ left: -10, right: 10, top: 10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
              <XAxis type="number" dataKey="energie" name="Énergie" domain={[0, 100]} stroke="rgba(255,255,255,0.4)" fontSize={11} tickLine={false} axisLine={false} label={{ value: "Énergie", position: "insideBottom", offset: -2, fill: "rgba(255,255,255,0.4)", fontSize: 11 }} />
              <YAxis type="number" dataKey="chiffre_affaires" name="CA" stroke="rgba(255,255,255,0.4)" fontSize={11} tickLine={false} axisLine={false} tickFormatter={(v) => `${Math.round(v / 1000)}k`} />
              <ZAxis range={[60, 60]} />
              <Tooltip cursor={{ strokeDasharray: "3 3" }} contentStyle={{ background: "#0B1F3A", border: "1px solid rgba(222, 194, 163,0.4)", borderRadius: 12, color: "#fff" }}
                formatter={(v, name) => [name === "chiffre_affaires" ? euro(v) : v, name === "chiffre_affaires" ? "CA" : "Énergie"]} />
              <Scatter data={data.points} fill="#DEC2A3" />
            </ScatterChart>
          </ResponsiveContainer>
          {data.insight && <p className="mt-3 text-[12.5px] text-white/70 leading-relaxed">{data.insight}</p>}
        </>
      )}
    </div>
  );
}

/* Year in Pixels — un pixel par jour, coloré selon l'énergie déclarée.
 * Uniquement les jours avec un vrai check-in ; le reste reste vide. */
function YearInPixels() {
  const [days, setDays] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getYearPixels().then((r) => setDays(r.days || [])).catch(() => setDays([])).finally(() => setLoading(false));
  }, []);

  const byDate = Object.fromEntries(days.map((d) => [d.date, d.energie]));
  const colorFor = (e) => (e == null ? "rgba(255,255,255,0.05)" : e >= 65 ? "#34d399" : e >= 45 ? "#DEC2A3" : "#f87171");

  const year = new Date().getFullYear();
  const start = new Date(year, 0, 1);
  const cells = [];
  for (let d = new Date(start); d.getFullYear() === year; d.setDate(d.getDate() + 1)) {
    const iso = d.toISOString().slice(0, 10);
    cells.push({ date: iso, energie: byDate[iso] });
  }

  return (
    <div className="glass p-5" data-testid="year-in-pixels">
      <h3 className="font-head font-semibold flex items-center gap-2 mb-1"><CalendarDays size={17} className="text-[#DEC2A3]" /> Year in Pixels — {year}</h3>
      <p className="text-[12px] text-white/50 mb-4">Un pixel par jour de check-in — vert = bonne énergie, or = moyenne, rouge = basse.</p>
      {loading ? (
        <div className="flex justify-center py-10"><Loader2 size={20} className="animate-spin text-white/40" /></div>
      ) : (
        <div className="grid gap-[3px]" style={{ gridTemplateColumns: "repeat(53, minmax(0, 1fr))" }}>
          {cells.map((c) => (
            <div key={c.date} title={`${c.date}${c.energie != null ? ` — ${c.energie}/100` : " — pas de check-in"}`}
              className="aspect-square rounded-[2px]" style={{ background: colorFor(c.energie) }} />
          ))}
        </div>
      )}
    </div>
  );
}

export default function BienEtre() {
  const [rituels, setRituels] = useState([]);
  const [humeurs, setHumeurs] = useState([]);
  const [newRituel, setNewRituel] = useState("");
  const [affIdx, setAffIdx] = useState(0);
  const [vision, setVision] = useState(null);
  const [taches, setTaches] = useState([]);

  const load = async () => {
    try {
      const [nextRituels, nextHumeurs, nextVision, nextTaches] = await Promise.all([
        getRituels().catch(() => []),
        getHumeur().catch(() => []),
        getVision().catch(() => null),
        getTaches().catch(() => []),
      ]);
      setRituels(Array.isArray(nextRituels) ? nextRituels : []);
      setHumeurs(Array.isArray(nextHumeurs) ? nextHumeurs : []);
      setVision(nextVision);
      setTaches(Array.isArray(nextTaches) ? nextTaches : []);
    } catch {
      setRituels([]); setHumeurs([]); setVision(null); setTaches([]);
    }
  };
  useEffect(() => { load(); }, []);

  const latest = humeurs[0];
  const energie = latest ? latest.energie : 0;
  const doneCount = rituels.filter((r) => r.done).length;
  const focusPct = rituels.length ? Math.round((doneCount / rituels.length) * 100) : 0;
  const bestStreak = rituels.reduce((m, r) => Math.max(m, r.streak || 0), 0);
  const energyTimeline = [...humeurs].slice(0, 30).reverse().map((entry) => ({
    date: entry.date ? new Date(`${entry.date}T12:00:00`).toLocaleDateString("fr-FR", { day: "2-digit", month: "short" }) : "—",
    energie: entry.energie,
    humeur: entry.humeur,
  }));
  const recentEnergy = humeurs.slice(0, 7);
  const averageEnergy = recentEnergy.length ? Math.round(recentEnergy.reduce((sum, entry) => sum + Number(entry.energie || 0), 0) / recentEnergy.length) : 0;
  const lowDays = recentEnergy.filter((entry) => Number(entry.energie || 0) < 45).length;
  const burnoutRisk = !recentEnergy.length ? "À évaluer" : lowDays >= 3 || averageEnergy < 40 ? "Élevé" : lowDays >= 1 || averageEnergy < 60 ? "Modéré" : "Faible";
  const verdict = burnoutRisk === "Élevé"
    ? "Ton énergie reste basse depuis plusieurs check-ins. Réduis la charge non essentielle et protège une vraie phase de récupération."
    : burnoutRisk === "Modéré"
      ? "Ton énergie mérite une attention cette semaine. Planifie une action de récupération avant que la fatigue ne s’installe."
      : burnoutRisk === "Faible"
        ? "Ton niveau d’énergie est stable. Préserve tes rituels et concentre ton effort sur une priorité à fort impact."
        : "Enregistre quelques check-ins pour recevoir un verdict fondé sur ta timeline réelle.";
  const openCopilot = () => window.dispatchEvent(new CustomEvent("cours:open-copilot", { detail: { ask: `Voici mon état : énergie ${energie}/100, risque de surcharge ${burnoutRisk}. Donne-moi un plan concret pour aujourd’hui.` } }));

  // Action recommandée (#) — dérivée du vrai risque + des vraies tâches ouvertes,
  // jamais un texte générique déconnecté des données. Pas de nouvelle recommandation
  // "inventée" : on choisit parmi 5 actions concrètes et réversibles, avec une
  // cible réelle (le nom d'une vraie tâche) quand il y en a une à désigner.
  const tachesOuvertes = taches.filter((t) => t.statut !== "Terminé");
  const tachesTriees = [...tachesOuvertes].sort((a, b) => (a.priorite === "Haute" ? -1 : 1) - (b.priorite === "Haute" ? -1 : 1));
  const actionRecommandee = (() => {
    if (!recentEnergy.length) return { verbe: "Se concentrer", detail: "Commence par un check-in pour que la recommandation s'appuie sur ta vraie énergie." };
    if (burnoutRisk === "Élevé") {
      const cible = tachesTriees[tachesTriees.length - 1];
      return { verbe: "Récupérer", detail: cible ? `Reporte « ${cible.titre} » et prends une vraie pause avant de reprendre.` : "Prends une vraie pause avant de reprendre — aucune tâche urgente en attente." };
    }
    if (burnoutRisk === "Modéré") {
      const cible = tachesTriees[tachesTriees.length - 1];
      return { verbe: "Déléguer ou reporter", detail: cible ? `« ${cible.titre} » peut attendre demain — garde ton énergie pour l'essentiel.` : "Allège ta charge si possible aujourd'hui." };
    }
    const cible = tachesTriees[0];
    return { verbe: "Se concentrer", detail: cible ? `Ton énergie permet d'avancer sur « ${cible.titre} » en priorité.` : "Aucune tâche ouverte — bon moment pour avancer sur ta Vision." };
  })();

  // Plan de journée (#) — vraies tâches de Mon Mouvement, juste réordonnées/plafonnées
  // selon la capacité réelle du jour. Rien d'inventé : si aucune tâche, état vide honnête.
  const planCapacite = burnoutRisk === "Élevé" ? 1 : burnoutRisk === "Modéré" ? 3 : 5;
  const planDuJour = tachesTriees.slice(0, planCapacite);

  const addRituel = async () => {
    if (!newRituel.trim()) return;
    await createRituel({ nom: newRituel });
    setNewRituel("");
    load();
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-head text-3xl sm:text-4xl font-semibold flex items-center gap-2">
            <Zap className="text-[#DEC2A3]" size={30} /> <span className="gold-text">Mindset & capacité</span>
          </h1>
          <p className="text-white/55 text-sm mt-1">Pilotez votre énergie et votre mindset pour performer durablement.</p>
        </div>
        <CheckinDialog onSaved={load} />
      </div>

      {/* Gauges */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Gauge value={energie} color="#34d399" label="Énergie actuelle" sub={latest ? latest.humeur : "—"} />
        <Gauge value={focusPct} color="#DEC2A3" label="Rituels du jour" sub={`${doneCount}/${rituels.length}`} />
        <Gauge value={Math.min(100, bestStreak * 10)} color="#f472b6" label="Meilleure série" sub={`${bestStreak} jours`} />
      </div>

      <div className={`rounded-2xl border p-4 sm:p-5 ${burnoutRisk === "Élevé" ? "border-rose-400/35 bg-rose-400/10" : burnoutRisk === "Modéré" ? "border-amber-400/35 bg-amber-400/10" : "border-emerald-400/25 bg-emerald-400/10"}`} data-testid="wellness-verdict">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div className="flex gap-3"><span className={`mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${burnoutRisk === "Élevé" ? "bg-rose-400/15 text-rose-300" : burnoutRisk === "Modéré" ? "bg-amber-400/15 text-amber-300" : "bg-emerald-400/15 text-emerald-300"}`}>{burnoutRisk === "Élevé" ? <AlertTriangle size={18} /> : <ShieldCheck size={18} />}</span><div><div className="font-head text-[15px] font-semibold">{burnoutRisk === "À évaluer" ? "Verdict du jour · pas encore de données" : `Verdict du jour · risque de surcharge : ${burnoutRisk}`}</div><p className="m-0 mt-0.5 text-[13px] leading-relaxed text-white/65">{verdict}</p></div></div><button onClick={openCopilot} className="inline-flex shrink-0 items-center justify-center gap-1.5 rounded-xl border border-[#DEC2A3]/40 bg-[#DEC2A3]/15 px-3 py-2 text-xs font-semibold text-[#F0DCA5] hover:bg-[#DEC2A3]/25"><MessageCircle size={14} /> Parler au copilote</button></div>
      </div>

      {/* Action recommandée + Plan de journée + Lien avec Vision — dérivés de vraies données */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="glass p-5" data-testid="action-recommandee">
          <h3 className="font-head font-semibold mb-2">Action recommandée</h3>
          <p className="text-[#DEC2A3] text-sm font-semibold mb-1">{actionRecommandee.verbe}</p>
          <p className="text-[13px] text-white/65 leading-relaxed">{actionRecommandee.detail}</p>
        </div>

        <div className="glass p-5" data-testid="plan-de-journee">
          <h3 className="font-head font-semibold mb-3">Plan de journée</h3>
          {planDuJour.length ? (
            <ul className="space-y-2">
              {planDuJour.map((t) => (
                <li key={t.id} className="flex items-center gap-2 text-sm text-white/80">
                  <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${t.priorite === "Haute" ? "bg-rose-400" : "bg-white/30"}`} />
                  {t.titre}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-white/40">Aucune tâche ouverte dans Mon Mouvement.</p>
          )}
          {tachesOuvertes.length > planDuJour.length && (
            <p className="text-[11px] text-white/40 mt-3">+ {tachesOuvertes.length - planDuJour.length} autre(s) tâche(s) — volontairement pas affichée(s) aujourd'hui vu ta capacité.</p>
          )}
        </div>

        <div className="glass p-5" data-testid="lien-vision">
          <h3 className="font-head font-semibold mb-2">Lien avec votre Vision</h3>
          {vision?.value ? (
            <>
              <p className="text-[13px] text-white/70 leading-relaxed line-clamp-3">{vision.value}</p>
              <p className="text-[12px] text-white/45 mt-3">
                {burnoutRisk === "Élevé" ? "Ton énergie actuelle ne permet pas d'avancer sereinement sur ce Cap — récupère d'abord." : "Ton énergie du jour soutient la progression vers ce Cap."}
              </p>
            </>
          ) : (
            <p className="text-sm text-white/40">Aucun Cap défini pour l'instant.</p>
          )}
        </div>
      </div>

      {/* Timeline + Affirmation */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="glass p-5 xl:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-head font-semibold">Timeline d’énergie</h3>
            <span className="text-xs text-white/50">30 derniers check-ins</span>
          </div>
          {energyTimeline.length ? <ResponsiveContainer width="100%" height={240}>
            <LineChart data={energyTimeline} margin={{ left: -10, right: 10, top: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
              <XAxis dataKey="date" stroke="rgba(255,255,255,0.4)" fontSize={11} tickLine={false} axisLine={false} minTickGap={28} />
              <YAxis stroke="rgba(255,255,255,0.4)" fontSize={11} tickLine={false} axisLine={false} domain={[0, 100]} />
              <Tooltip contentStyle={{ background: "#0A1128", border: "1px solid rgba(52,211,153,0.4)", borderRadius: 12, color: "#fff" }} formatter={(v) => [`${v}/100`, "Énergie"]} labelFormatter={(label) => label} />
              <Line type="monotone" dataKey="energie" stroke="#34d399" strokeWidth={2.5} dot={{ r: 3, fill: "#34d399" }} activeDot={{ r: 5 }} />
            </LineChart>
          </ResponsiveContainer> : <div className="flex h-[240px] items-center justify-center text-center text-sm text-white/45">Enregistre tes premiers check-ins pour démarrer une timeline réelle.</div>}
        </div>

        <div className="glass p-6 flex flex-col fade-in relative overflow-hidden">
          <div className="absolute inset-0 opacity-20" style={{ backgroundImage: "url(https://images.unsplash.com/photo-1777492480070-5316d7562a2d?crop=entropy&cs=srgb&fm=jpg&q=85&w=800)", backgroundSize: "cover", backgroundPosition: "center" }} />
          <div className="relative flex flex-col h-full">
            <div className="flex items-center gap-2 text-[#DEC2A3] text-xs font-semibold uppercase tracking-wider">
              <Heart size={14} /> Affirmation du jour
            </div>
            <p className="font-vision italic text-2xl leading-snug text-white/90 my-auto py-6">
              « {AFFIRMATIONS[affIdx]} »
            </p>
            <button
              data-testid="new-affirmation"
              onClick={() => setAffIdx((i) => (i + 1) % AFFIRMATIONS.length)}
              className="self-start flex items-center gap-1.5 text-sm text-[#DEC2A3] hover:text-[#FFD700] transition-colors"
            >
              <RefreshCw size={14} /> Nouvelle affirmation
            </button>
          </div>
        </div>
      </div>

      {/* Rituels + anti-abandon */}
      <div id="missions" className="grid grid-cols-1 lg:grid-cols-3 gap-4 scroll-mt-6">
        <div className="glass p-5 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-head font-semibold flex items-center gap-2"><Wind size={17} className="text-[#DEC2A3]" /> Mes rituels</h3>
          </div>
          <div className="space-y-2" data-testid="rituels-list">
            {rituels.map((r) => (
              <div key={r.id} className="flex items-center gap-3 rounded-xl bg-white/5 border border-white/10 px-3.5 py-2.5">
                <button
                  onClick={async () => { await toggleRituel(r.id); load(); }}
                  data-testid={`toggle-rituel-${r.id}`}
                  className={`w-6 h-6 rounded-lg flex items-center justify-center transition-colors ${r.done ? "gold-bg" : "border border-white/25"}`}
                >
                  {r.done && <Check size={15} className="text-[#0A1128]" />}
                </button>
                <div className="flex-1 min-w-0">
                  <div className={`text-sm font-medium ${r.done ? "line-through text-white/40" : ""}`}>{r.nom}</div>
                  {r.detail && <div className="text-[11px] text-white/40">{r.detail}</div>}
                </div>
                <span className="flex items-center gap-1 text-xs text-amber-400"><Flame size={13} /> {r.streak}</span>
                <button onClick={async () => { await deleteRituel(r.id); load(); }} data-testid={`delete-rituel-${r.id}`} className="text-white/30 hover:text-rose-400 transition-colors"><Trash2 size={15} /></button>
              </div>
            ))}
            {rituels.length === 0 && <p className="text-sm text-white/40 py-4 text-center">Aucun rituel. Ajoutez-en un ci-dessous.</p>}
          </div>
          <div className="flex items-center gap-2 mt-4 bg-white/5 border border-white/15 rounded-full pl-4 pr-1.5 py-1.5">
            <input
              data-testid="new-rituel-input"
              value={newRituel}
              onChange={(e) => setNewRituel(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && addRituel()}
              placeholder="Nouveau rituel (ex: méditation 5 min)…"
              className="flex-1 bg-transparent text-sm text-white placeholder:text-white/40 focus:outline-none"
            />
            <button onClick={addRituel} data-testid="add-rituel-btn" className="w-8 h-8 rounded-full gold-bg flex items-center justify-center"><Plus size={16} className="text-[#0A1128]" /></button>
          </div>
        </div>

        <div className="glass p-5">
          <h3 className="font-head font-semibold mb-3">Anti-abandon</h3>
          <p className="text-[13px] text-white/60 leading-relaxed mb-4">
            La plupart des solopreneurs abandonnent, non par manque de vision, mais par manque de constance. Tiens ta série.
          </p>
          <div className="rounded-2xl bg-gradient-to-br from-[#DEC2A3]/20 to-transparent border border-[#DEC2A3]/30 p-5 text-center">
            <Flame size={28} className="text-[#DEC2A3] mx-auto" />
            <div className="font-head text-4xl font-bold mt-2">{bestStreak}</div>
            <div className="text-xs text-white/60 mt-1">jours de constance</div>
          </div>
          <p className="text-[12px] text-white/50 mt-4 text-center">Coche un rituel aujourd'hui pour ne pas casser ta série.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <WellnessCorrelations />
        <YearInPixels />
      </div>
    </div>
  );
}
