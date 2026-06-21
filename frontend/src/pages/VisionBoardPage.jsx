import React, { useEffect, useMemo, useRef, useState } from "react";
import axios from "axios";
import "./VisionBoardPage.css";
import {
  LayoutDashboard, Radar, Eye, LineChart, GraduationCap, BookOpen,
  Sparkles, Share2, Download, MoreHorizontal, CheckCircle2, Pencil,
  Target, Send, BarChart3, Book, ChevronRight, Plus, RefreshCw,
  Briefcase, TrendingUp, HeartPulse, Users, Compass, Globe,
  ShieldCheck, Star, Feather, Crown, Zap, Lightbulb, Lock, ExternalLink,
  Sun, Moon,
} from "lucide-react";
import { useTheme } from "../contexts/ThemeContext";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const NAV = [
  { icon: LayoutDashboard, label: "Dashboard", href: "/" },
  { icon: Radar, label: "Expansion Agent", href: "/expansion" },
  { icon: Eye, label: "Vision Board", href: "/vision-board", active: true },
  { icon: LineChart, label: "Pilotage", href: "/pilotage" },
  { icon: GraduationCap, label: "Academy", href: "/copilote" },
  { icon: BookOpen, label: "Ressources", href: "/workspace" },
];

const SUBTABS = [
  { id: "canvas", label: "Vision Canvas", icon: Pencil },
  { id: "pillars", label: "Strategic Pillars", icon: Crown },
  { id: "values", label: "Core Values", icon: Star },
  { id: "roadmap", label: "Roadmap", icon: BarChart3 },
  { id: "book", label: "Vision Book", icon: Book },
];

const PILLAR_ICONS = { briefcase: Briefcase, "trending-up": TrendingUp, "heart-pulse": HeartPulse, users: Users, compass: Compass, globe: Globe };
const VALUE_ICONS = [ShieldCheck, Feather, Zap, Crown, Star, Compass];

const fmtEur = (n) => (n ? `${Number(n).toLocaleString("fr-FR")} €` : "—");

// Visuels magazine (fond par défaut tant que le compte Canva équipe n'est pas connecté)
const IMG = {
  ocean: "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1100&q=80",
  villa: "https://images.unsplash.com/photo-1706808849780-7a04fbac83ef?auto=format&fit=crop&w=900&q=80",
  summit: "https://images.unsplash.com/photo-1458724715045-81841536951e?auto=format&fit=crop&w=1100&q=80",
  workspace: "https://images.unsplash.com/photo-1587522384446-64daf3e2689a?auto=format&fit=crop&w=900&q=80",
};

export default function VisionBoardPage() {
  const { theme, toggleTheme } = useTheme();
  const [tab, setTab] = useState("canvas");
  const [aiTab, setAiTab] = useState("analyse");
  const [board, setBoard] = useState(null);
  const [info, setInfo] = useState(null);
  const [copilot, setCopilot] = useState(null);
  const [analyse, setAnalyse] = useState(null);
  const [canva, setCanva] = useState({ connected: false });
  const [book, setBook] = useState(null);
  const [bookLoading, setBookLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const toastTimer = useRef(null);

  const notify = (msg, kind = "ok") => {
    setToast({ msg, kind });
    clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToast(null), 3500);
  };

  useEffect(() => {
    (async () => {
      try {
        const [b, i, c, a, cv, bk] = await Promise.all([
          axios.get(`${API}/vision/board`),
          axios.get(`${API}/vision/info`),
          axios.get(`${API}/vision/copilot-data`),
          axios.post(`${API}/vision/analyse`),
          axios.get(`${API}/canva/status`),
          axios.get(`${API}/vision/visionbook`),
        ]);
        setBoard(b.data); setInfo(i.data); setCopilot(c.data);
        setAnalyse(a.data); setCanva(cv.data);
        if (bk.data && bk.data.flipbook_url) setBook(bk.data);
      } catch (e) { /* noop */ }
    })();
    const params = new URLSearchParams(window.location.search);
    if (params.get("canva") === "connected") notify("Canva connecté avec succès ✦", "ok");
    if (params.get("canva") === "error") notify("Connexion Canva échouée — vérifie la Redirect URL dans le portail Canva", "err");
  }, []);

  const images = useMemo(
    () => (board?.cards || []).filter((c) => c.type === "image" && c.content?.src).map((c) => c.content.src),
    [board]
  );
  const quote = useMemo(
    () => (board?.cards || []).find((c) => c.type === "quote")?.content?.text,
    [board]
  );

  const openCanva = async () => {
    try {
      const { data } = await axios.get(`${API}/canva/auth/start`);
      window.location.href = data.authorization_url;
    } catch { notify("Impossible de démarrer Canva", "err"); }
  };

  const generateBook = async () => {
    setBookLoading(true); setTab("book");
    try {
      const { data } = await axios.post(`${API}/vision/visionbook/generate`);
      setBook(data); notify("Vision Book généré ✦", "ok");
    } catch (e) {
      notify(e?.response?.data?.detail || "Génération du Vision Book échouée", "err");
    } finally { setBookLoading(false); }
  };

  const scores = analyse?.scores || {};
  const obj = info?.objectifs || {};
  const phase = obj.phase || {};

  return (
    <div className="vb-root" data-testid="vision-board-page">
      {/* ---------- TOP NAV ---------- */}
      <div className="vb-topnav">
        <div className="vb-brand">
          <div className="vb-logo-mark">M</div>
          <div>
            <b>MyExtension<span className="vb-ai">AI</span></b>
            <small>v2.0</small>
          </div>
        </div>
        <nav className="vb-mainnav">
          {NAV.map((n) => (
            <a key={n.label} href={n.href} className={n.active ? "active" : ""}
               data-testid={`nav-${n.label.toLowerCase().replace(/\s+/g, "-")}`}>
              <n.icon size={16} /> {n.label}
            </a>
          ))}
        </nav>
        <div className="vb-user">
          <button
            onClick={toggleTheme}
            data-testid="vb-theme-toggle"
            title={theme === "dark" ? "Mode clair" : "Mode sombre"}
            style={{
              display: "grid", placeItems: "center", width: 38, height: 38,
              borderRadius: 10, border: "1px solid var(--line)", background: "var(--glass)",
              color: "var(--ink)", cursor: "pointer",
            }}
          >
            {theme === "dark" ? <Sun size={16} style={{ color: "#D6A85F" }} /> : <Moon size={16} />}
          </button>
          <div style={{ textAlign: "right" }}>
            <div className="vb-uname">Alexandre</div>
            <div className="vb-urole">Entrepreneur</div>
          </div>
          <div className="vb-avatar" style={{ display: "grid", placeItems: "center",
            background: "linear-gradient(135deg,#163D57,#0B1F3A)", color: "#D6A85F", fontWeight: 700 }}>AL</div>
        </div>
      </div>

      {/* ---------- SUB HEADER ---------- */}
      <div className="vb-subhead">
        <div className="vb-title">
          <h1 className="vb-serif">Vision Board</h1>
          <p>{board?.title || "Ma feuille de route vers ma vision"}</p>
        </div>
        <div className="vb-tabs">
          {SUBTABS.map((t) => (
            <button key={t.id} className={`vb-tab ${tab === t.id ? "active" : ""}`}
              onClick={() => setTab(t.id)} data-testid={`subtab-${t.id}`}>
              <t.icon size={15} /> {t.label}
            </button>
          ))}
        </div>
        <div className="vb-actions">
          <span className="vb-saved"><CheckCircle2 size={15} /> Enregistré auto.</span>
          <button className="vb-btn" data-testid="share-btn"><Share2 size={15} /> Partager</button>
          <button className="vb-btn vb-btn-gold" data-testid="export-btn"><Download size={15} /> Exporter</button>
          <button className="vb-btn vb-btn-ghost" data-testid="more-btn"><MoreHorizontal size={16} /></button>
        </div>
      </div>

      {/* ---------- BODY ---------- */}
      <div className="vb-body">
        <div>
          {tab === "canvas" && (
            <CanvasView {...{ info, obj, phase, analyse, images, quote, canva, openCanva, copilot, notify }} />
          )}
          {tab === "pillars" && <PillarsView info={info} />}
          {tab === "values" && <ValuesView info={info} />}
          {tab === "roadmap" && <RoadmapView board={board} obj={obj} />}
          {tab === "book" && (
            <BookView book={book} loading={bookLoading} onGenerate={generateBook} />
          )}
        </div>

        {/* RIGHT AI PANEL */}
        <aside className="vb-ai-panel" data-testid="ai-panel">
          <div className="vb-ai-head">
            <Sparkles size={18} className="sp" style={{ color: "#D6A85F" }} />
            <b>Assistant Vision <span className="sp">AI</span></b>
          </div>
          <div className="vb-ai-tabs">
            {["analyse", "idees", "actions"].map((t) => (
              <button key={t} className={aiTab === t ? "active" : ""} onClick={() => setAiTab(t)}
                data-testid={`ai-tab-${t}`}>
                {t === "analyse" ? "Analyse" : t === "idees" ? "Idées" : "Actions"}
              </button>
            ))}
          </div>
          <div className="vb-ai-content">
            {aiTab === "analyse" && (
              <>
                {[["Clarté", scores.clarte], ["Alignement", scores.alignement],
                  ["Ambition", scores.ambition], ["Faisabilité", scores.faisabilite],
                  ["Équilibre", scores.equilibre]].map(([lbl, v]) => (
                  <div className="vb-score-row" key={lbl} data-testid={`score-${lbl.toLowerCase()}`}>
                    <div className="lbl"><span>{lbl}</span><b>{v ?? "—"}%</b></div>
                    <div className="vb-score-bar"><i style={{ width: `${v || 0}%` }} /></div>
                  </div>
                ))}
                <div className="vb-global">
                  <div className="vb-ring" style={{ "--p": scores.global || 0 }}>
                    <span>{scores.global || "—"}</span>
                  </div>
                  <div>
                    <div style={{ fontSize: 13, color: "var(--muted)" }}>Score global</div>
                    <div style={{ fontFamily: "Satoshi", fontSize: 22, color: "var(--cream)", fontWeight: 700 }}>
                      {scores.global || "—"} / 100
                    </div>
                  </div>
                </div>
                <div style={{ fontSize: 12.5, color: "var(--muted)", marginBottom: 4 }}>Points forts</div>
                <ul className="vb-strong">
                  {(analyse?.swot?.forces || []).slice(0, 3).map((f) => (
                    <li key={f}><CheckCircle2 size={15} /> {f}</li>
                  ))}
                </ul>
                <button className="vb-btn vb-btn-gold" style={{ width: "100%", justifyContent: "center", marginTop: 16 }}
                  onClick={async () => { const { data } = await axios.post(`${API}/vision/analyse`); setAnalyse(data); notify("Analyse mise à jour"); }}
                  data-testid="analyse-board-btn">
                  <Sparkles size={15} /> Analyser mon board
                </button>
              </>
            )}
            {aiTab === "idees" && (
              <>
                {(analyse?.opportunites_business || []).map((o, i) => (
                  <div className="vb-idea" key={i}><Lightbulb size={16} /> <span>{o}</span></div>
                ))}
              </>
            )}
            {aiTab === "actions" && (
              <>
                {(analyse?.conseils || []).map((c, i) => (
                  <div className="vb-idea" key={i}><ChevronRight size={16} /> <span>{c}</span></div>
                ))}
              </>
            )}
          </div>
        </aside>
      </div>

      {/* ---------- BOTTOM ACTION BAR ---------- */}
      <div className="vb-actionbar" data-testid="action-bar">
        <button className="vb-action" onClick={() => notify("Mission créée depuis la vision")} data-testid="action-mission">
          <span className="ico"><Target size={18} /></span>
          <span><b>Créer une mission</b><small>Transformer en action</small></span>
          <ChevronRight size={16} className="arrow" />
        </button>
        <button className="vb-action" onClick={() => notify("Envoyé à l'Expansion Agent")} data-testid="action-expansion">
          <span className="ico"><Send size={18} /></span>
          <span><b>Envoyer à Expansion Agent</b><small>Obtenir un plan d'action</small></span>
          <ChevronRight size={16} className="arrow" />
        </button>
        <button className="vb-action" onClick={() => notify("KPI ajoutés au Dashboard")} data-testid="action-dashboard">
          <span className="ico"><BarChart3 size={18} /></span>
          <span><b>Ajouter au Dashboard</b><small>Suivre mes KPI</small></span>
          <ChevronRight size={16} className="arrow" />
        </button>
        <button className="vb-action" onClick={generateBook} data-testid="action-visionbook">
          <span className="ico"><Book size={18} /></span>
          <span><b>Générer le Vision Book</b><small>Votre vision en livre</small></span>
          <ChevronRight size={16} className="arrow" />
        </button>
      </div>

      {toast && (
        <div className={`vb-toast ${toast.kind}`} data-testid="vb-toast">
          {toast.kind === "ok" ? <CheckCircle2 size={16} color="#34d399" /> : <Zap size={16} color="#f87171" />}
          {toast.msg}
        </div>
      )}
    </div>
  );
}

/* ====================== VIEWS ====================== */

function CanvasView({ info, obj, phase, analyse, images, quote, canva, openCanva, copilot }) {
  const swot = analyse?.swot || {};
  const [showJson, setShowJson] = useState(false);
  // 3 états adaptatifs — pilotés UNIQUEMENT par completion_score (jamais par la faisabilité IA)
  const completion = copilot?.completion_score ?? 0;
  const etat = completion < 30 ? 1 : completion < 70 ? 2 : 3;
  const etatLabel = etat === 1 ? "Premier accès" : etat === 2 ? "En cours" : "Canvas actif";

  return (
    <>
      <div className="vb-canvas-wrap">
        <div className="vb-canvas-bar">
          <span className="vb-canva-pill"><Eye size={13} /> Fond Canva · {info?.objectifs ? "Feuille de Route" : "Vision"} · Zayado</span>
          <span className="vb-canva-pill" data-testid="canvas-state-pill"
            title="État adaptatif basé sur le taux de remplissage des blocs métier (completion_score)">
            <Zap size={13} /> État {etat} · {etatLabel} · {completion}%
          </span>
          <button className="vb-btn vb-btn-ghost" style={{ marginLeft: "auto", padding: "6px 12px" }}
            onClick={openCanva} data-testid="open-canva-btn">
            {canva?.connected ? <><ExternalLink size={14} /> Modifier dans Canva</> : <><ExternalLink size={14} /> Ouvrir dans Canva</>}
          </button>
        </div>

        {etat === 1 ? (
          <div className="vb-canvas-onboard" data-testid="canvas-state-empty">
            <Sparkles size={40} style={{ color: "#D6A85F" }} />
            <h2 className="vb-serif">Construis ta vision avant de la vivre</h2>
            <p>Choisis un modèle pour démarrer ton Vision Board. Le Co-pilote remplira les premiers blocs métier avec toi.</p>
            <div className="vb-onboard-actions">
              <button className="vb-btn vb-btn-gold" onClick={openCanva} data-testid="onboard-open-canva">
                <ExternalLink size={15} /> Ouvrir dans Canva
              </button>
              <button className="vb-btn"><Plus size={15} /> Partir d'un modèle</button>
            </div>
          </div>
        ) : (
          <>
            {etat === 2 && (
              <div className="vb-canvas-nudge" data-testid="canvas-state-nudge">
                <Lightbulb size={16} />
                <span>Ta vision prend forme ({completion}%). Ajoute tes objectifs et tes valeurs pour atteindre le canvas actif.</span>
              </div>
            )}
            <div className="vb-canvas" data-testid="vision-canvas">
              {/* Vision — éditorial plein cadre */}
              <div className="vb-photo vb-w2 vb-h2" data-testid="block-vision">
                <img src={IMG.ocean} alt="vision" />
                <div className="scrim" />
                <span className="corner">Ma vision</span>
                <div className="cap">
                  <div className="k">Vision · 1 an</div>
                  <h3>{info?.vision_1an || "Devenir un entrepreneur libre qui impacte des milliers de personnes."}</h3>
                </div>
              </div>

              {/* Villa lifestyle */}
              <div className="vb-photo vb-h2" data-testid="block-image-0">
                <img src={IMG.villa} alt="maison de rêve" />
                <div className="scrim" />
                <div className="cap"><div className="k">Lifestyle</div><h3>Ma maison de rêve</h3></div>
              </div>

              {/* Objectif CA */}
              <div className="vb-card vb-h2" data-testid="block-objectif-ca">
                <div className="vb-card-tag"><TrendingUp size={12} /> Objectif CA</div>
                <div className="vb-kpi-val">{fmtEur(obj.ca_cible)}</div>
                <div className="vb-kpi-sub">Cible annuelle récurrente</div>
                <div className="vb-prog"><i style={{ width: "58%" }} /></div>
              </div>

              {/* Pull quote */}
              <div className="vb-card vb-w2" data-testid="block-quote">
                <div className="vb-quote">« {quote || "Discipline aujourd'hui, liberté demain."} »
                  <span className="by">— Zayado</span></div>
              </div>

              {/* Marge op */}
              <div className="vb-card" data-testid="block-marge">
                <div className="vb-card-tag"><BarChart3 size={12} /> Marge op.</div>
                <div className="vb-kpi-val">{obj.marge_op_pct ?? "—"}%</div>
              </div>

              {/* Ikigai */}
              <div className="vb-card" data-testid="block-ikigai">
                <div className="vb-card-tag"><Compass size={12} /> Ikigai</div>
                <div className="vb-kpi-val">{obj.ikigai_score ?? "—"}<span style={{ fontSize: 14, color: "var(--muted)" }}>/100</span></div>
              </div>

              {/* Summit éditorial */}
              <div className="vb-photo vb-w2 vb-h2" data-testid="block-image-1">
                <img src={IMG.summit} alt="sommet" />
                <div className="scrim" />
                <span className="corner">Focus</span>
                <div className="cap"><div className="k">État d'esprit</div>
                  <h3>Rêver grand. Travailler dur. Impacter le monde.</h3></div>
              </div>

              {/* Phase actuelle */}
              <div className="vb-card vb-h2" data-testid="block-phase">
                <div className="vb-card-tag"><Zap size={12} /> Phase actuelle</div>
                <div style={{ fontFamily: "Satoshi", fontSize: 19, color: "var(--cream)" }}>{phase.label || "Lancement"}</div>
                <div className="vb-kpi-sub">Mois {phase.mois || 4} / {phase.total || 12}</div>
                <div className="vb-prog"><i style={{ width: `${((phase.mois || 4) / (phase.total || 12)) * 100}%` }} /></div>
              </div>

              {/* Workspace éditorial */}
              <div className="vb-photo vb-h2" data-testid="block-image-2">
                <img src={IMG.workspace} alt="workspace" />
                <div className="scrim" />
                <div className="cap"><div className="k">Discipline</div><h3>Mon espace de création</h3></div>
              </div>

              {/* SWOT — IA blocks */}
              {[["Forces", swot.forces], ["Faiblesses", swot.faiblesses],
                ["Opportunités", swot.opportunites], ["Menaces", swot.menaces]].map(([lbl, items]) => (
                <div className="vb-card ai vb-h2" key={lbl} data-testid={`block-swot-${lbl.toLowerCase()}`}>
                  <div className="vb-card-tag"><Sparkles size={12} /> {lbl} · IA</div>
                  <ul className="vb-swot-list">{(items || []).slice(0, 3).map((x) => <li key={x}>{x}</li>)}</ul>
                </div>
              ))}
            </div>
          </>
        )}

        <div className="vb-canvas-tools">
          <button className="vb-btn"><Plus size={15} /> Bloc</button>
          <button className="vb-btn vb-btn-mint"><Sparkles size={15} /> IA régénère SWOT</button>
          <button className="vb-btn" onClick={openCanva}><Pencil size={15} /> Modifier Canva</button>
          <button className="vb-btn"><Download size={15} /> Export PDF</button>
        </div>
      </div>

      {/* Co-pilot transparency — repliable, masqué par défaut (pro) */}
      <div className="vb-copilot" data-testid="copilot-json">
        <button className="vb-copilot-head vb-copilot-toggle" onClick={() => setShowJson((v) => !v)}
          data-testid="copilot-toggle">
          <Sparkles size={16} style={{ color: "#D6A85F" }} />
          <b>Transparence IA — ce que lit ton Co-pilote</b>
          <span className="vb-badge">{showJson ? "Masquer" : "Afficher"}</span>
          <ChevronRight size={16} className="vb-chev" style={{ transform: showJson ? "rotate(90deg)" : "none" }} />
        </button>
        {showJson && (
          <>
            <p className="note">L'IA ne lit <b>jamais</b> le fond Canva — uniquement le contenu métier structuré ci-dessous.</p>
            <pre>{JSON.stringify(copilot || {}, null, 2)}</pre>
          </>
        )}
      </div>
    </>
  );
}

function PillarsView({ info }) {
  const piliers = info?.piliers || [];
  return (
    <div className="vb-grid vb-pillars" data-testid="pillars-view">
      {piliers.map((p) => {
        const Ico = PILLAR_ICONS[p.icon] || Crown;
        return (
          <div className="vb-pillar" key={p.id} data-testid={`pillar-${p.id}`}>
            <div className="ico"><Ico size={22} /></div>
            <h3 className="vb-serif">{p.label}</h3>
            <p>{p.text}</p>
            <div className="pv">{p.progress}% atteint</div>
            <div className="vb-prog"><i style={{ width: `${p.progress}%` }} /></div>
          </div>
        );
      })}
    </div>
  );
}

function ValuesView({ info }) {
  const valeurs = info?.valeurs || [];
  return (
    <div className="vb-grid vb-values" data-testid="values-view">
      {valeurs.map((v, i) => {
        const Ico = VALUE_ICONS[i % VALUE_ICONS.length];
        return (
          <div className="vb-value" key={v} data-testid={`value-${i}`}>
            <div className="ico"><Ico size={20} /></div>
            <div>
              <b>{v}</b>
              <small>Valeur fondatrice · alignée à la vision</small>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function RoadmapView({ board, obj }) {
  const timeline = (board?.cards || []).find((c) => c.type === "timeline")?.content?.items || [];
  const fallback = [
    { id: "q1", label: "T1", items: ["Structurer l'offre", "Poser les fondations"] },
    { id: "q2", label: "T2", items: ["Atteindre 50K€ de CA"] },
    { id: "q3", label: "T3", items: ["Développer l'équipe", "Automatiser"] },
    { id: "q4", label: "T4", items: [`Viser ${fmtEur(obj.ca_cible)}`] },
  ];
  const steps = timeline.length ? timeline : fallback;
  return (
    <div data-testid="roadmap-view">
      <div className="vb-card" style={{ marginBottom: 18 }}>
        <div className="vb-card-tag"><BarChart3 size={12} /> Transformation Vision → Plan</div>
        <p style={{ color: "var(--cream)", fontSize: 15, margin: "6px 0 0" }}>
          {fmtEur(obj.ca_cible)} de CA → {obj.nb_clients?.toLocaleString("fr-FR")} clients → plan trimestriel → missions
        </p>
      </div>
      <div className="vb-road">
        {steps.map((s) => (
          <div className="vb-road-item" key={s.id} data-testid={`road-${s.id}`}>
            <div className="q">{s.label}</div>
            <h4 className="vb-serif">{(s.items && s.items[0]) || ""}</h4>
            <p>{(s.items || []).slice(1).join(" · ")}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function BookView({ book, loading, onGenerate }) {
  return (
    <div className="vb-book" data-testid="book-view">
      <div className="vb-book-side">
        <h3>Vision Book</h3>
        <p>Transforme ton Vision Board en livre interactif : Vision, Objectifs, Valeurs, KPI &amp; Roadmap réunis dans un flipbook partageable propulsé par Heyzine.</p>
        <div className="vb-fmt">
          <span className="on">Flipbook</span>
          <span className="on">PDF Premium</span>
          <span>Présentation</span>
        </div>
        <button className="vb-btn vb-btn-gold" style={{ width: "100%", justifyContent: "center" }}
          onClick={onGenerate} disabled={loading} data-testid="generate-book-btn">
          {loading ? <><span className="vb-spinner" /> Génération…</> : <><Book size={15} /> Générer le Vision Book</>}
        </button>
        {book?.flipbook_url && (
          <a className="vb-btn" style={{ width: "100%", justifyContent: "center", marginTop: 10 }}
            href={book.flipbook_url} target="_blank" rel="noreferrer" data-testid="open-flipbook-link">
            <ExternalLink size={15} /> Ouvrir en plein écran
          </a>
        )}
      </div>
      <div className="vb-flip">
        {loading ? (
          <div className="vb-flip-empty"><div className="vb-spinner" style={{ margin: "0 auto 14px" }} />
            Conversion du PDF en flipbook…</div>
        ) : book?.flipbook_url ? (
          <iframe src={book.flipbook_url} title="Vision Book" allowFullScreen data-testid="flipbook-iframe" />
        ) : (
          <div className="vb-flip-empty">
            <Book size={42} />
            <div>Aucun Vision Book généré pour l'instant.</div>
            <div style={{ fontSize: 12.5, marginTop: 6 }}>Clique sur « Générer le Vision Book » pour créer ton flipbook.</div>
          </div>
        )}
      </div>
    </div>
  );
}
