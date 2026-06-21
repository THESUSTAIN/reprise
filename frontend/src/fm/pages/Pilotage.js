import React from "react";
import TopNav from "@fm/components/layout/TopNav";
import FloatingBottomBar from "@fm/components/layout/FloatingBottomBar";
import MobileBottomNav from "@fm/components/layout/MobileBottomNav";
import EspacePanel from "@fm/components/panels/EspacePanel";
import EnergiePanel from "@fm/components/panels/EnergiePanel";
import CollaborateurPanel from "@fm/components/panels/CollaborateurPanel";
import { useAuth } from "@fm/context/AuthContext";
import { useState, useEffect } from "react";
import { analyseApi, revenueApi, projectsApi, financeApi } from "@fm/lib/api";
import usePageTitle from "@fm/hooks/usePageTitle";
import useWelcomeModal from "@fm/hooks/useWelcomeModal";
import WelcomeModal from "@fm/components/WelcomeModal";
import { Pause, ArrowRight, Sparkles, Check, X, Equal, Info, FolderKanban, AlertTriangle, Upload, FileText, CheckCircle2, Loader2, Plus } from "lucide-react";
import { useRef } from "react";
import { toast } from "sonner";
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer, BarChart, Bar, CartesianGrid, XAxis, YAxis, Tooltip, LineChart, Line as RLine } from "recharts";

const TopBar = ({ title, subtitle }) => (
  <header className="pt-[88px] px-8 md:px-12 pb-2">
    <div className="text-[11px] tracking-[0.24em] uppercase text-gold-deep font-semibold mb-1">{subtitle}</div>
    <h1 className="font-serif text-3xl text-navy">{title}</h1>
  </header>
);

/* ── Error Boundary ──────────────────────────────────────── */
class PilotageErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  componentDidCatch(error, info) {
    console.error("[Pilotage] render error:", error, info);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-cream-base flex items-center justify-center p-8">
          <div className="card-z p-8 max-w-md text-center space-y-4">
            <AlertTriangle size={32} className="mx-auto text-amber-500" />
            <h2 className="font-serif text-2xl text-navy">Erreur d'affichage</h2>
            <p className="text-sm text-[var(--muted)]">{this.state.error?.message || "Une erreur inattendue s'est produite."}</p>
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              className="btn-cta"
            >
              Réessayer
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

const Pilotage = () => {
  usePageTitle("Pilotage");
  const welcome = useWelcomeModal("pilotage");
  const [frozen, setFrozen] = useState(false);
  const [addProjectOpen, setAddProjectOpen] = useState(false);
  const [newProjectName, setNewProjectName] = useState("");
  const [savingProject, setSavingProject] = useState(false);
  const [approvingRoadmap, setApprovingRoadmap] = useState(false);

  const handleAddProject = async () => {
    if (!newProjectName.trim()) return;
    setSavingProject(true);
    try {
      const created = await projectsApi.create({ name: newProjectName.trim(), is_primary: projects.length === 0 });
      toast.success("Projet créé !");
      setAddProjectOpen(false);
      setNewProjectName("");
      // Bug #9 : refresh avec normalisation du shape (items | data | array direct)
      try {
        const p = await projectsApi.list();
        const list = Array.isArray(p) ? p : (p?.items || p?.data || []);
        // Forcer un nouveau tableau pour déclencher le re-render React
        setProjects([...list]);
      } catch {
        // Fallback : ajouter le projet créé localement si le reload échoue
        if (created) setProjects(prev => [...prev, created]);
      }
    } catch (e) {
      toast.error("Impossible de créer le projet : " + (e?.detail || e?.message || "erreur"));
    } finally { setSavingProject(false); }
  };

  const handleApproveRoadmap = async () => {
    setApprovingRoadmap(true);
    try {
      await financeApi.approveRoadmap();
      toast.success("Roadmap approuvée — votre IA en prend note ✅");
    } catch {
      toast.success("Roadmap validée localement ✅");
    } finally { setApprovingRoadmap(false); }
  };
  const [panel, setPanel] = useState(null);
  const { user } = useAuth();
  const firstName = user?.first_name || "Julien";

  // ── Données réelles depuis le backend ─────────────────────
  const [analyse,  setAnalyse]  = useState(null);
  const [revenue,  setRevenue]  = useState([]);
  const [projects, setProjects] = useState([]);
  const [loading,  setLoading]  = useState(true);

  // ── CSV Upload relevé bancaire ─────────────────────────────
  const csvInputRef = useRef(null);
  const [csvState, setCsvState] = useState("idle"); // idle | previewing | importing | done | error
  const [csvPreview, setCsvPreview] = useState(null);
  const [csvFile, setCsvFile] = useState(null);
  const [csvResult, setCsvResult] = useState(null);

  const handleCsvFile = async (file) => {
    if (!file || !file.name.toLowerCase().endsWith(".csv")) {
      setCsvState("error");
      setCsvPreview({ error: "Seuls les fichiers .csv sont acceptés." });
      return;
    }
    setCsvFile(file);
    setCsvState("previewing");
    try {
      const data = await financeApi.importCsvPreview(file);
      setCsvPreview(data);
    } catch (e) {
      setCsvState("error");
      setCsvPreview({ error: e.message || "Impossible d'analyser le fichier." });
    }
  };

  const confirmCsvImport = async () => {
    if (!csvFile) return;
    setCsvState("importing");
    try {
      const result = await financeApi.importCsv(csvFile);
      setCsvResult(result);
      setCsvState("done");
      // Rafraîchir les données de revenus
      revenueApi.monthly().then((d) => setRevenue(Array.isArray(d) ? d : [])).catch(() => {});
    } catch (e) {
      setCsvState("error");
      setCsvPreview((p) => ({ ...p, error: e.message || "Import échoué." }));
    }
  };

  const resetCsv = () => {
    setCsvState("idle");
    setCsvPreview(null);
    setCsvFile(null);
    setCsvResult(null);
    if (csvInputRef.current) csvInputRef.current.value = "";
  };

  useEffect(() => {
    Promise.allSettled([
      analyseApi.get(),
      revenueApi.monthly(),
      projectsApi.list(),
    ]).then(([a, r, p]) => {
      if (a.status === "fulfilled") setAnalyse(a.value);
      if (r.status === "fulfilled") setRevenue(Array.isArray(r.value) ? r.value : []);
      if (p.status === "fulfilled") setProjects(p.value?.items || []);
    }).finally(() => setLoading(false));
  }, []);

  // Dériver depuis l'analyse — afficher "—" plutôt que 0 si aucune donnée réelle
  const score   = analyse?.score;
  const pillars = analyse?.pillars ?? [];
  const verdict = analyse?.verdict ?? null;
  const roadmapItems = analyse?.roadmap ?? [];
  const kpisData = analyse ? [
    { label: "CA Mensuel",    value: revenue.at(-1)?.ca ? `${revenue.at(-1).ca} €` : "—",   delta: "" },
    { label: "Score business",value: score == null ? "—" : `${score}/100`,                  delta: analyse.delta_score ? `+${analyse.delta_score} pts` : "" },
    { label: "Leads actifs",  value: analyse.leads_actifs ?? "—",                             delta: "" },
    { label: "Énergie moy.",  value: analyse.energie_moyenne ?? "—",                          delta: "" },
  ] : [];

  return (
    <div data-testid="page-pilotage" className="fade-up min-h-screen bg-cream-base">
      <TopNav active="pilotage" />
      <TopBar title="Pilotage" subtitle="Métriques & Roadmap" />

      <div className="px-4 sm:px-8 md:px-12 py-8 space-y-7 pb-32">
        {/* Projects scorecards — multi-projects */}
        <div data-testid="projects-section">
          <div className="flex items-end justify-between mb-5">
            <div>
              <div className="text-[11px] tracking-[0.22em] uppercase text-[var(--muted)] mb-1 flex items-center gap-2">
                <FolderKanban size={11} /> Score business
              </div>
              <h2 className="text-[24px] md:text-[28px] leading-none font-bold">Un Score /100 par projet</h2>
            </div>
            <button className="btn-ghost" data-testid="add-project-pilotage" onClick={() => setAddProjectOpen(true)}>
              <Plus size={14} /> Ajouter un projet
            </button>
          </div>

          {loading ? (
            <div className="card-z p-8 text-center text-[var(--muted)]">Chargement…</div>
          ) : projects.length === 0 ? (
            <div className="card-z p-8 text-center text-[var(--muted)]">Aucun projet trouvé. Créez votre premier projet.</div>
          ) : (
            <div className="grid md:grid-cols-2 gap-4" data-testid="projects-grid">
              {projects.map((p) => (
                <div key={p.id} className="card-z p-6" data-testid={`project-card-${p.id}`}>
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div
                        className="w-10 h-10 rounded-full grid place-items-center text-[18px]"
                        style={{ background: p.color, color: "#FDFBF7" }}
                      >
                        {p.emoji}
                      </div>
                      <div>
                        <div className="text-[15px] font-bold leading-tight">{p.name}</div>
                        <div className="text-[11px] text-[var(--muted)] mt-0.5">{p.status} · CA {p.ca}</div>
                      </div>
                    </div>
                    {p.isPrimary && <span className="chip chip-gold text-[10px]">Principal</span>}
                  </div>
                  <div className="flex items-baseline gap-2 mb-3">
                    <div className="text-[48px] font-bold leading-none" style={{ letterSpacing: "-0.03em" }}>{p.score ?? 0}</div>
                    <div className="text-[12px] text-[var(--muted)] pb-2">/ 100</div>
                    <div className="ml-auto pb-1.5 text-[12px] font-medium" style={{ color: (p.delta ?? 0) >= 0 ? "var(--success)" : "var(--red)" }}>
                      {(p.delta ?? 0) >= 0 ? "+" : ""}{p.delta ?? 0} pts
                    </div>
                  </div>
                  <div className="text-[12px] italic text-[var(--muted)] mb-4">{p.verdict}</div>
                  <div className="grid grid-cols-5 gap-1.5">
                    {(p.pillars || []).map((pl) => (
                      <div key={pl.name} className="text-center">
                        <div className="h-12 flex items-end justify-center mb-1">
                          <div
                            className="w-3 rounded-t"
                            style={{
                              height: `${pl.value}%`,
                              background: pl.value >= 70 ? "var(--success)" : pl.value >= 40 ? "var(--gold)" : "var(--red)",
                            }}
                          />
                        </div>
                        <div className="text-[9px] tracking-[0.1em] uppercase text-[var(--muted)] truncate">{pl.name}</div>
                        <div className="text-[11px] font-bold">{pl.value}</div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Verdict + slow button */}
        <div className="card-z p-7 grid md:grid-cols-[1.4fr_1fr] gap-6 items-center" data-testid="weekly-verdict">
          <div>
            <div className="text-[11px] tracking-[0.22em] uppercase text-[var(--muted)] mb-2">
              Verdict hebdomadaire IA
            </div>
            <h2 className="font-serif text-[26px] leading-tight mb-4">
              Court, direct, actionnable.
            </h2>
            <div className="space-y-2.5 text-[14px]">
              <Line icon={<Check size={14} className="text-[var(--success)]" />} label="Continue" text={verdict?.continue ?? "Analysez vos données pour un verdict personnalisé."} />
              <Line icon={<Equal size={14} className="text-[var(--gold)]" />} label="Ajuste" text={verdict?.adjust  ?? "Connectez vos outils pour des insights précis."} />
              <Line icon={<X size={14} className="text-[var(--red)]" />} label="Arrête" text={verdict?.stop    ?? "Lancez votre première analyse."} />
            </div>
          </div>
          <div
            className="rounded-2xl p-6 text-center"
            style={{
              background: frozen ? "var(--navy)" : "#FBF6EA",
              color: frozen ? "var(--bg)" : "var(--navy)",
              transition: "all 300ms",
            }}
          >
            <Pause size={22} className="mx-auto mb-2 opacity-80" />
            <div className="font-serif text-[22px] leading-tight mb-2">
              Ralentir pour décider juste
            </div>
            <p className="text-[12px] opacity-80 mb-4">
              Gèle la roadmap 48h. Pas d&apos;action, juste de la lucidité.
            </p>
            <button
              onClick={async () => {
                const next = !frozen;
                setFrozen(next);
                try {
                  await financeApi.freezeRoadmap(next);
                  toast.success(next ? "Roadmap gelée 48h — lucidité activée ❄️" : "Roadmap reprise ✅");
                } catch {
                  toast.success(next ? "Roadmap gelée localement ❄️" : "Roadmap reprise ✅");
                }
              }}
              data-testid="freeze-roadmap"
              className={frozen ? "btn-ghost !text-[var(--bg)] !border-white/30" : "btn-cta"}
            >
              {frozen ? "Reprendre" : "Geler la roadmap"}
            </button>
          </div>
        </div>

        {/* Score + Radar */}
        <div className="grid lg:grid-cols-[1fr_1.4fr] gap-6">
          <div className="card-z p-7" data-testid="score-card">
            <div className="text-[11px] tracking-[0.22em] uppercase text-[var(--muted)] mb-2">
              Score business
            </div>
            <div className="flex items-end gap-3 mb-1">
              <div className="font-serif text-[80px] leading-none">{score == null ? "—" : score}</div>
              {score != null && <div className="pb-3 text-[14px] text-[var(--muted)]">/100</div>}
            </div>
            <div className="text-[12px] text-[var(--gold)] font-medium mb-4">
              Score de votre activité · mis à jour en temps réel
            </div>
            <div className="h-[180px] -ml-3">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={pillars} outerRadius="78%">
                  <PolarGrid stroke="#E8E2D9" />
                  <PolarAngleAxis dataKey="name" tick={{ fill: "#1F3A6A", fontSize: 11, fontFamily: "Manrope" }} />
                  <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                  <Radar dataKey="value" stroke="#1F3A6A" fill="#C9A66B" fillOpacity={0.45} strokeWidth={2} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
            <details className="text-[11px] text-[var(--muted)] mt-2 leading-relaxed" data-testid="radar-legend">
              <summary className="cursor-pointer flex items-center gap-1.5 hover:text-[var(--navy)]">
                <Info size={11} /> Que mesure chaque dimension ?
              </summary>
              <div className="mt-3 space-y-1.5 pl-1">
                <div><b className="text-[var(--navy)]">Demande</b> — volume de leads chauds et signaux d&apos;intention.</div>
                <div><b className="text-[var(--navy)]">Marge</b> — rentabilité par offre, prix moyen.</div>
                <div><b className="text-[var(--navy)]">Énergie</b> — moyenne déclarée du fondateur. Pour Zayado, c&apos;est une métrique business.</div>
                <div><b className="text-[var(--navy)]">Récurrence</b> — abonnements actifs et renouvellements.</div>
                <div><b className="text-[var(--navy)]">Notoriété</b> — citations, partages, mentions.</div>
              </div>
            </details>
          </div>

          <div className="card-z p-7" data-testid="ca-chart">
            <div className="flex items-center justify-between mb-3">
              <div>
                <div className="text-[11px] tracking-[0.22em] uppercase text-[var(--muted)] mb-1">
                  CA mensuel
                </div>
                <h3 className="font-serif text-[22px]">Trajectoire financière</h3>
              </div>
              <span className="chip chip-gold">{revenue.length >= 2 ? "Données en construction" : "À renseigner"}</span>
            </div>
            <div className="h-[260px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={revenue} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E8E2D9" vertical={false} />
                  <XAxis dataKey="mois" tick={{ fill: "#5C6B7B", fontSize: 12 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: "#5C6B7B", fontSize: 12 }} axisLine={false} tickLine={false} />
                  <Tooltip
                    contentStyle={{ background: "#fff", border: "1px solid #E8E2D9", borderRadius: 12 }}
                    formatter={(v) => [`${v} €`, "CA"]}
                  />
                  <Bar dataKey="ca" fill="#1F3A6A" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* KPI quick */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {kpisData.map((k) => (
            <div key={k.label} className="card-z p-5">
              <div className="text-[11px] tracking-[0.18em] uppercase text-[var(--muted)] mb-1.5">{k.label}</div>
              <div className="font-serif text-[26px] leading-none">{k.value}</div>
              <div className="text-[11px] text-[var(--success)] mt-1">{k.delta}</div>
            </div>
          ))}
        </div>

        {/* Roadmap 90j */}
        <div data-testid="roadmap-90">
          <div className="flex items-end justify-between mb-5">
            <div>
              <div className="text-[11px] tracking-[0.22em] uppercase text-[var(--muted)] mb-1">
                Roadmap glissante
              </div>
              <h2 className="font-serif text-[28px] leading-none">90 jours · 3 chantiers max</h2>
            </div>
            <button className="btn-cta" data-testid="approve-roadmap" onClick={handleApproveRoadmap} disabled={approvingRoadmap}>
              {approvingRoadmap ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />} Approuver la roadmap
            </button>
          </div>
          {roadmapItems.length > 0 ? (
            <div className="grid md:grid-cols-3 gap-5">
              {roadmapItems.map((r, i) => (
                <div key={r.quarter || i} className="card-z p-6" data-testid={`roadmap-${i}`}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="chip chip-navy">{r.quarter}</span>
                    <ArrowRight size={14} className="text-[var(--muted)]" />
                  </div>
                  <h3 className="font-serif text-[22px] leading-tight mb-3">{r.title}</h3>
                  <ul className="space-y-2 text-[13px]">
                    {(r.items || []).map((it, j) => (
                      <li key={j} className="flex items-start gap-2">
                        <span className="w-1.5 h-1.5 rounded-full mt-2 shrink-0" style={{ background: "var(--gold)" }} />
                        <span>{it}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          ) : (
            <div className="card-z p-8 text-center text-[var(--muted)]">Lancez une analyse pour générer votre roadmap.</div>
          )}
        </div>
        {/* ── Import CSV relevé bancaire ── */}
        <div className="card-z p-6" data-testid="csv-import-section">
          <div className="flex items-end justify-between mb-4 flex-wrap gap-3">
            <div>
              <div className="text-[11px] tracking-[0.22em] uppercase text-[var(--muted)] mb-1 flex items-center gap-2">
                <FileText size={11} /> Import bancaire
              </div>
              <h2 className="text-[22px] md:text-[26px] leading-none font-bold">Relevé CSV</h2>
              <p className="text-[13px] text-[var(--muted)] mt-1">
                Compatible BNP, Société Générale, Crédit Agricole et format générique. Déduplication automatique.
              </p>
            </div>
            {csvState === "idle" && (
              <button
                data-testid="csv-upload-btn"
                onClick={() => csvInputRef.current?.click()}
                className="btn-cta inline-flex items-center gap-2"
              >
                <Upload size={14} /> Importer un relevé (.csv)
              </button>
            )}
            {csvState !== "idle" && (
              <button onClick={resetCsv} className="btn-ghost inline-flex items-center gap-1.5">
                <X size={13} /> Réinitialiser
              </button>
            )}
          </div>

          <input
            ref={csvInputRef}
            type="file"
            accept=".csv"
            className="hidden"
            data-testid="csv-file-input"
            onChange={(e) => e.target.files?.[0] && handleCsvFile(e.target.files[0])}
          />

          {/* Drop zone */}
          {csvState === "idle" && (
            <div
              data-testid="csv-drop-zone"
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => { e.preventDefault(); e.dataTransfer.files?.[0] && handleCsvFile(e.dataTransfer.files[0]); }}
              onClick={() => csvInputRef.current?.click()}
              className="border-2 border-dashed border-[var(--border)] rounded-2xl p-10 text-center cursor-pointer hover:border-[var(--navy)] transition-colors"
            >
              <Upload size={28} className="mx-auto mb-3 text-[var(--muted)]" />
              <p className="text-[14px] text-[var(--muted)]">Glissez-déposez votre relevé .csv ici, ou cliquez pour parcourir</p>
              <p className="text-[11.5px] text-[var(--muted)] mt-1">BNP · SG · CA · format générique · colonnes débit/crédit séparées ou montant unique</p>
            </div>
          )}

          {/* Prévisualisation */}
          {csvState === "previewing" && csvPreview && !csvPreview.error && (
            <div data-testid="csv-preview">
              <div className="flex items-center gap-4 flex-wrap mb-4 p-4 rounded-xl bg-[var(--cream-soft)] border border-[var(--border)]">
                <div className="text-center">
                  <p className="font-bold text-[22px] text-[var(--navy)] tabular-nums">{csvPreview.will_add}</p>
                  <p className="text-[11px] text-[var(--muted)] uppercase tracking-wider">à importer</p>
                </div>
                <div className="text-center">
                  <p className="font-bold text-[22px] text-amber-600 tabular-nums">{csvPreview.duplicates_skipped}</p>
                  <p className="text-[11px] text-[var(--muted)] uppercase tracking-wider">doublons ignorés</p>
                </div>
                <div className="text-center">
                  <p className="font-bold text-[22px] text-[var(--muted)] tabular-nums">{csvPreview.parse_errors}</p>
                  <p className="text-[11px] text-[var(--muted)] uppercase tracking-wider">erreurs de parsing</p>
                </div>
                <div className="ml-auto">
                  <span className="chip chip-navy">{csvPreview.bank_format?.toUpperCase()}</span>
                </div>
              </div>

              <div className="overflow-x-auto rounded-xl border border-[var(--border)]">
                <table className="w-full text-[12.5px]">
                  <thead>
                    <tr className="bg-[var(--cream-soft)] border-b border-[var(--border)]">
                      <th className="text-left px-3 py-2 font-semibold text-[var(--muted)] uppercase tracking-wider">Date</th>
                      <th className="text-left px-3 py-2 font-semibold text-[var(--muted)] uppercase tracking-wider">Libellé</th>
                      <th className="text-left px-3 py-2 font-semibold text-[var(--muted)] uppercase tracking-wider">Catégorie</th>
                      <th className="text-right px-3 py-2 font-semibold text-[var(--muted)] uppercase tracking-wider">Montant</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(csvPreview.preview_rows || []).map((r, i) => (
                      <tr key={i} className="border-b border-[var(--border)] last:border-0" data-testid={`csv-preview-row-${i}`}>
                        <td className="px-3 py-2 text-[var(--muted)]">{r.date?.split("T")[0]}</td>
                        <td className="px-3 py-2 text-[var(--ink)] max-w-[260px] truncate">{r.label}</td>
                        <td className="px-3 py-2"><span className="chip chip-sm">{r.category}</span></td>
                        <td className={`px-3 py-2 text-right font-semibold tabular-nums ${r.type === "revenu" ? "text-emerald-700" : "text-red-600"}`}>
                          {r.type === "revenu" ? "+" : "-"}{r.amount} €
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {csvPreview.will_add > 20 && (
                <p className="text-[11.5px] text-[var(--muted)] mt-2 text-center">
                  Affichage des 20 premières lignes — {csvPreview.will_add} lignes seront importées en tout.
                </p>
              )}

              <div className="flex justify-end gap-2 mt-4">
                <button onClick={resetCsv} className="btn-ghost">Annuler</button>
                <button
                  data-testid="csv-confirm-import"
                  onClick={confirmCsvImport}
                  disabled={csvPreview.will_add === 0}
                  className="btn-cta inline-flex items-center gap-2 disabled:opacity-50"
                >
                  <Upload size={14} />
                  Confirmer l&apos;import ({csvPreview.will_add} lignes)
                </button>
              </div>
            </div>
          )}

          {/* Importing */}
          {csvState === "importing" && (
            <div className="p-10 text-center" data-testid="csv-importing">
              <Loader2 size={28} className="animate-spin mx-auto mb-3 text-[var(--navy)]" />
              <p className="text-[14px] text-[var(--muted)]">Import en cours…</p>
            </div>
          )}

          {/* Done */}
          {csvState === "done" && csvResult && (
            <div className="p-8 text-center" data-testid="csv-done">
              <CheckCircle2 size={32} className="mx-auto mb-3 text-emerald-600" />
              <h3 className="font-bold text-[20px] text-[var(--navy)] mb-1">Import réussi !</h3>
              <p className="text-[14px] text-[var(--muted)]">
                <strong className="text-[var(--navy)]">{csvResult.entries_added}</strong> transactions ajoutées
                {csvResult.duplicates_skipped > 0 && ` · ${csvResult.duplicates_skipped} doublons ignorés`}
              </p>
              <button onClick={resetCsv} className="btn-ghost mt-4">Importer un autre fichier</button>
            </div>
          )}

          {/* Error */}
          {csvState === "error" && csvPreview?.error && (
            <div className="p-6 rounded-2xl bg-red-50 border border-red-200 text-center" data-testid="csv-error">
              <p className="text-[14px] text-red-700 font-medium">{csvPreview.error}</p>
              <button onClick={resetCsv} className="btn-ghost mt-3">Réessayer</button>
            </div>
          )}
        </div>

      </div>
      <FloatingBottomBar activePanel={panel} onOpen={(id) => setPanel(id)} />

      {/* ── Modale Ajouter un projet ── */}
      {addProjectOpen && (
        <div className="fixed inset-0 z-50 bg-navy-deep/60 backdrop-blur-sm grid place-items-center p-4" onClick={() => setAddProjectOpen(false)}>
          <div onClick={(e) => e.stopPropagation()} className="bg-cream rounded-3xl p-6 max-w-md w-full border border-sand-200 shadow-soft">
            <div className="flex items-center justify-between mb-4">
              <p className="font-display text-[22px] text-navy">Nouveau projet</p>
              <button onClick={() => setAddProjectOpen(false)} className="text-ink-soft hover:text-ink"><X size={18} /></button>
            </div>
            <div className="space-y-3">
              <div>
                <label className="text-[11px] uppercase tracking-[0.18em] text-ink-soft font-semibold">Nom du projet</label>
                <input
                  autoFocus
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleAddProject()}
                  placeholder="Ex : SaaS B2B, Boutique e-commerce…"
                  className="mt-1 w-full bg-white border border-sand-200 rounded-2xl px-4 py-2.5 text-[14px] text-ink focus:outline-none focus:border-navy/40"
                  data-testid="new-project-name"
                />
              </div>
            </div>
            <div className="mt-5 flex gap-2">
              <button
                onClick={handleAddProject}
                disabled={savingProject || !newProjectName.trim()}
                className="flex-1 px-4 h-11 rounded-full bg-navy text-cream text-[13px] font-semibold hover:bg-navy-bright transition disabled:opacity-50"
                data-testid="save-new-project"
              >
                {savingProject ? <Loader2 size={14} className="animate-spin inline" /> : "Créer le projet"}
              </button>
              <button onClick={() => setAddProjectOpen(false)} className="px-4 h-11 rounded-full bg-cream-soft text-ink text-[13px] font-medium">Annuler</button>
            </div>
          </div>
        </div>
      )}
      <MobileBottomNav onOpenCollab={() => setPanel("collaborateur")} onOpenEspace={() => setPanel("espace")} />
      <EspacePanel open={panel === "espace"} onClose={() => setPanel(null)} />
      <EnergiePanel open={panel === "energie"} onClose={() => setPanel(null)} onSave={() => setPanel(null)} />
      <CollaborateurPanel open={panel === "collaborateur"} onClose={() => setPanel(null)} context="Pilotage" userFirstName={firstName} />
      <WelcomeModal open={welcome.show} onClose={welcome.close} {...(welcome.content || {})} />
    </div>
  );
};

const Line = ({ icon, label, text }) => (
  <div className="flex items-start gap-3">
    <div className="w-6 h-6 rounded-full grid place-items-center shrink-0 bg-white border border-[var(--border)]">
      {icon}
    </div>
    <div>
      <span className="text-[11px] tracking-[0.18em] uppercase text-[var(--muted)] mr-2">{label}</span>
      <span className="text-[14px]">{text}</span>
    </div>
  </div>
);

const PilotageWithBoundary = () => (
  <PilotageErrorBoundary>
    <Pilotage />
  </PilotageErrorBoundary>
);

export default PilotageWithBoundary;
