import { useEffect, useState } from "react";
import {
  Feather, Heart, Building2, Coins, Plus, Trash2, Pencil, Save, Sparkles, Target, FileText, Loader2, ArrowRight,
} from "lucide-react";
import { toast } from "sonner";
import {
  getObjectifs, createObjectif, updateObjectif, deleteObjectif, objectifToAction,
  getVision, setVision, getSwot, generateSwot, getVisionDocument, generateVisionDocument,
  getCopilotBrief,
} from "../lib/api";
import { KeyInsights } from "../components/CockpitSections";
import AlignmentCelebration from "../components/AlignmentCelebration";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter,
} from "../components/ui/dialog";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "../components/ui/select";

const CAT = {
  "Liberté": { icon: Feather, color: "#38bdf8" },
  "Impact": { icon: Heart, color: "#f472b6" },
  "Entreprise": { icon: Building2, color: "#DEC2A3" },
  "Finance": { icon: Coins, color: "#34d399" },
};

const MINDSET = [
  { t: "Vision > Motivation", d: "La motivation fluctue. Reviens chaque matin à ton pourquoi pour tenir sur la durée." },
  { t: "1 % chaque jour", d: "Les petits pas répétés battent les grands élans ponctuels. Vise la constance, pas la perfection." },
  { t: "Célèbre les victoires", d: "Note une victoire par jour. Le cerveau abandonne moins quand il voit le progrès." },
];

function ObjectifDialog({ onSaved, existing }) {
  const [open, setOpen] = useState(false);
  const [o, setO] = useState(existing || { titre: "", categorie: "Liberté", description: "", valeur_actuelle: 0, valeur_cible: 100, unite: "" });
  const submit = async () => {
    if (!o.titre) return toast.error("Titre requis");
    const payload = { ...o, valeur_actuelle: parseFloat(o.valeur_actuelle) || 0, valeur_cible: parseFloat(o.valeur_cible) || 1 };
    if (existing) await updateObjectif(existing.id, payload);
    else await createObjectif(payload);
    toast.success(existing ? "Objectif mis à jour" : "Objectif ajouté");
    setOpen(false);
    onSaved();
  };
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {existing ? (
          <button data-testid={`edit-objectif-${existing.id}`} className="text-white/40 hover:text-[#DEC2A3] transition-colors"><Pencil size={14} /></button>
        ) : (
          <button data-testid="add-objectif-btn" className="glass glass-hover flex flex-col items-center justify-center gap-2 p-6 text-white/60 hover:text-white min-h-[160px]">
            <Plus size={22} /> <span className="text-sm">Ajouter un objectif</span>
          </button>
        )}
      </DialogTrigger>
      <DialogContent className="bg-[#0A1128] border-white/15 text-white">
        <DialogHeader><DialogTitle className="font-head">{existing ? "Modifier" : "Nouvel"} objectif</DialogTitle></DialogHeader>
        <div className="space-y-3">
          <div><Label className="text-white/70">Titre</Label>
            <Input data-testid="objectif-titre" value={o.titre} onChange={(e) => setO({ ...o, titre: e.target.value })} className="bg-white/5 border-white/15 mt-1" /></div>
          <div><Label className="text-white/70">Catégorie</Label>
            <Select value={o.categorie} onValueChange={(v) => setO({ ...o, categorie: v })}>
              <SelectTrigger className="bg-white/5 border-white/15 mt-1"><SelectValue /></SelectTrigger>
              <SelectContent className="bg-[#0A1128] border-white/15 text-white">
                {Object.keys(CAT).map((c) => <SelectItem key={c} value={c}>{c}</SelectItem>)}
              </SelectContent>
            </Select></div>
          <div><Label className="text-white/70">Description</Label>
            <Textarea value={o.description} onChange={(e) => setO({ ...o, description: e.target.value })} className="bg-white/5 border-white/15 mt-1" /></div>
          <div className="grid grid-cols-3 gap-3">
            <div><Label className="text-white/70">Actuel</Label>
              <Input data-testid="objectif-actuel" type="number" value={o.valeur_actuelle} onChange={(e) => setO({ ...o, valeur_actuelle: e.target.value })} className="bg-white/5 border-white/15 mt-1" /></div>
            <div><Label className="text-white/70">Cible</Label>
              <Input data-testid="objectif-cible" type="number" value={o.valeur_cible} onChange={(e) => setO({ ...o, valeur_cible: e.target.value })} className="bg-white/5 border-white/15 mt-1" /></div>
            <div><Label className="text-white/70">Unité</Label>
              <Input value={o.unite} onChange={(e) => setO({ ...o, unite: e.target.value })} className="bg-white/5 border-white/15 mt-1" /></div>
          </div>
        </div>
        <DialogFooter>
          <button data-testid="objectif-submit" onClick={submit} className="gold-bg text-[#0A1128] font-semibold rounded-full px-5 py-2 text-sm">Enregistrer</button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default function Vision({ onChanged }) {
  const [objectifs, setObjectifs] = useState([]);
  const [vision, setVisionText] = useState("");
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState("");
  const [swot, setSwot] = useState(null);
  const [swotLoading, setSwotLoading] = useState(false);
  const [document, setDocument] = useState(null);
  const [docLoading, setDocLoading] = useState(false);
  const [brief, setBrief] = useState(null);

  const load = async () => {
    setObjectifs(await getObjectifs());
    const v = await getVision();
    setVisionText(v.value);
    setDraft(v.value);
    const s = await getSwot().catch(() => ({ swot: null }));
    setSwot(s.swot);
    const d = await getVisionDocument().catch(() => ({ content: null }));
    setDocument(d.content);
    getCopilotBrief().then(setBrief).catch(() => {});
    onChanged && onChanged(); // resynchronise les onglets Canvas/Piliers/Analyse (VisionBoard.jsx)
  };
  // `load` orchestre volontairement le chargement initial ; il ne doit pas être recréé comme dépendance d’un hook.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { load(); }, []);

  const runGenerateSwot = async () => {
    setSwotLoading(true);
    try {
      const r = await generateSwot();
      setSwot(r.swot);
      toast.success("Analyse SWOT générée à partir de vos vraies données ✦");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Analyse indisponible pour le moment.");
    } finally {
      setSwotLoading(false);
    }
  };

  const runGenerateDocument = async () => {
    setDocLoading(true);
    try {
      const r = await generateVisionDocument();
      setDocument(r.content);
      toast.success("Plan 30 jours généré ✦");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Génération indisponible pour le moment.");
    } finally {
      setDocLoading(false);
    }
  };

  const saveVision = async () => {
    await setVision(draft);
    setVisionText(draft);
    setEditing(false);
    toast.success("Vision mise à jour");
  };

  const globalScore = objectifs.length
    ? Math.round(objectifs.reduce((s, o) => s + Math.min(100, (o.valeur_actuelle / (o.valeur_cible || 1)) * 100), 0) / objectifs.length)
    : 0;

  return (
    <div className="space-y-6">
      {/* Hero */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="glass p-8 lg:col-span-2 relative overflow-hidden fade-in">
          <div
            className="absolute inset-0 opacity-25"
            style={{ backgroundImage: "url(https://images.unsplash.com/photo-1658070781328-0c173542795f?crop=entropy&cs=srgb&fm=jpg&q=85&w=1200)", backgroundSize: "cover", backgroundPosition: "center" }}
          />
          <div className="relative">
            <div className="font-vision italic text-4xl sm:text-5xl gold-text mb-4">Ma vision</div>
            {editing ? (
              <div className="space-y-3">
                <Textarea data-testid="vision-textarea" value={draft} onChange={(e) => setDraft(e.target.value)} className="bg-white/10 border-white/20 text-white text-lg min-h-[120px]" />
                <div className="flex gap-2">
                  <button data-testid="vision-save" onClick={saveVision} className="gold-bg text-[#0A1128] font-semibold rounded-full px-4 py-1.5 text-sm flex items-center gap-1.5"><Save size={14} /> Enregistrer</button>
                  <button onClick={() => { setEditing(false); setDraft(vision); }} className="text-white/60 text-sm px-3">Annuler</button>
                </div>
              </div>
            ) : (
              <>
                <p className="font-vision text-2xl sm:text-3xl leading-snug text-white/90 max-w-xl">{vision}</p>
                <button data-testid="vision-edit" onClick={() => setEditing(true)} className="mt-4 flex items-center gap-1.5 text-sm text-[#DEC2A3] hover:text-[#FFD700] transition-colors">
                  <Pencil size={14} /> Modifier ma vision
                </button>
              </>
            )}
          </div>
        </div>

        <div className="glass p-6 flex flex-col items-center justify-center text-center fade-in">
          <span className="text-xs text-white/50 uppercase tracking-wider">Équilibre de vie</span>
          <div className="relative my-4 w-32 h-32">
            <svg className="w-32 h-32 -rotate-90">
              <circle cx="64" cy="64" r="56" stroke="rgba(255,255,255,0.1)" strokeWidth="10" fill="none" />
              <circle cx="64" cy="64" r="56" stroke="#DEC2A3" strokeWidth="10" fill="none"
                strokeDasharray={2 * Math.PI * 56}
                strokeDashoffset={2 * Math.PI * 56 * (1 - globalScore / 100)}
                strokeLinecap="round" />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="font-head text-3xl font-semibold">{globalScore}%</span>
            </div>
          </div>
          <p className="text-sm text-white/60">Score global d'alignement</p>
          <span className="mt-2 text-xs text-emerald-400 bg-emerald-400/10 px-3 py-1 rounded-full">
            {globalScore >= 60 ? "Bonne dynamique" : "À renforcer"}
          </span>
        </div>
      </div>

      {/* Pillars */}
      <div>
        <h3 className="font-head font-semibold mb-3 flex items-center gap-2"><Target size={18} className="text-[#DEC2A3]" /> Mes piliers</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4" data-testid="objectifs-grid">
          {objectifs.map((o) => {
            const meta = CAT[o.categorie] || CAT["Entreprise"];
            const Icon = meta.icon;
            const pct = Math.min(100, Math.round((o.valeur_actuelle / (o.valeur_cible || 1)) * 100));
            return (
              <div key={o.id} className="glass glass-hover p-5 fade-in" data-testid={`objectif-${o.id}`}>
                <div className="flex items-start justify-between">
                  <div className="w-9 h-9 rounded-xl flex items-center justify-center" style={{ background: `${meta.color}22`, border: `1px solid ${meta.color}44` }}>
                    <Icon size={17} style={{ color: meta.color }} strokeWidth={1.5} />
                  </div>
                  <div className="flex items-center gap-2">
                    <button onClick={async () => { await objectifToAction(o.id); toast.success("Action créée dans vos rituels ✦"); }}
                      data-testid={`objectif-to-action-${o.id}`} title="Transformer en action"
                      className="text-white/40 hover:text-[#DEC2A3] transition-colors"><ArrowRight size={14} /></button>
                    <ObjectifDialog existing={o} onSaved={load} />
                    <button onClick={async () => { await deleteObjectif(o.id); load(); }} data-testid={`delete-objectif-${o.id}`} className="text-white/40 hover:text-rose-400 transition-colors"><Trash2 size={14} /></button>
                  </div>
                </div>
                <div className="mt-3 text-[11px] uppercase tracking-wider" style={{ color: meta.color }}>{o.categorie}</div>
                <div className="font-head font-semibold mt-0.5">{o.titre}</div>
                <div className="text-xs text-white/50 mt-1">{o.valeur_actuelle} / {o.valeur_cible} {o.unite}</div>
                <div className="mt-3 h-1.5 rounded-full bg-white/10 overflow-hidden">
                  <div className="h-full rounded-full transition-all duration-500" style={{ width: `${pct}%`, background: meta.color }} />
                </div>
              </div>
            );
          })}
          <ObjectifDialog onSaved={load} />
        </div>
      </div>

      {/* SWOT réel (IA, vos données) + Vision Document + Mindset */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="glass p-5 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-head font-semibold flex items-center gap-2"><Sparkles size={17} className="text-[#DEC2A3]" /> Analyse IA — SWOT</h3>
            <button onClick={runGenerateSwot} disabled={swotLoading} data-testid="swot-generate-btn"
              className="text-xs font-semibold text-[#DEC2A3] hover:text-[#FFD700] flex items-center gap-1.5 disabled:opacity-50">
              {swotLoading ? <Loader2 size={13} className="animate-spin" /> : <Sparkles size={13} />}
              {swot ? "Régénérer" : "Générer l'analyse"}
            </button>
          </div>
          {!swot ? (
            <p className="text-sm text-white/45 py-6 text-center">
              Pas encore d'analyse — générez un SWOT basé sur votre vision et vos objectifs réels (pas un modèle générique).
            </p>
          ) : (
            <div className="grid grid-cols-2 gap-4">
              {Object.entries(swot).map(([k, items]) => (
                <div key={k}>
                  <div className="text-xs font-semibold text-[#DEC2A3] mb-2">{k}</div>
                  <ul className="space-y-1">
                    {(items || []).map((i) => <li key={i} className="text-[13px] text-white/65">• {i}</li>)}
                  </ul>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="glass p-5">
          <h3 className="font-head font-semibold mb-3">Mindset du fondateur</h3>
          <div className="space-y-3">
            {MINDSET.map((m) => (
              <div key={m.t} className="rounded-xl bg-white/5 border border-white/10 p-3.5">
                <div className="text-sm font-medium text-[#DEC2A3]">{m.t}</div>
                <p className="text-[12px] text-white/60 mt-1 leading-relaxed">{m.d}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Vision Document — plan 30 jours généré par le copilote */}
      <div className="glass p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-head font-semibold flex items-center gap-2"><FileText size={17} className="text-[#DEC2A3]" /> Vision Document — plan 30 jours</h3>
          <button onClick={runGenerateDocument} disabled={docLoading} data-testid="vision-doc-generate-btn"
            className="text-xs font-semibold text-[#DEC2A3] hover:text-[#FFD700] flex items-center gap-1.5 disabled:opacity-50">
            {docLoading ? <Loader2 size={13} className="animate-spin" /> : <Sparkles size={13} />}
            {document ? "Régénérer" : "Générer mon plan"}
          </button>
        </div>
        {!document ? (
          <p className="text-sm text-white/45 py-6 text-center">
            Demandez au copilote de préparer un plan d'action concret sur 30 jours, basé sur votre vision et vos objectifs.
          </p>
        ) : (
          <div className="text-[13px] text-white/75 leading-relaxed whitespace-pre-wrap" data-testid="vision-doc-content">{document}</div>
        )}
      </div>

      {/* ── Fusion cockpit : Ressources & Inspiration (données réelles) ── */}
      <KeyInsights data={brief} />
      <AlignmentCelebration score={brief?.vision?.alignment_percent} />
    </div>
  );
}
