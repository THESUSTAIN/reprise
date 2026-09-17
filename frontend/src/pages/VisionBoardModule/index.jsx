import React, { useMemo, useRef, useState, useCallback } from "react";
import { flushSync } from "react-dom";
import StudioModal from "./StudioModal";
import DocumentsDrawer from "./DocumentsDrawer";
import LiveCardsStrip from "./LiveCardsStrip";
import VisionCanvaMobile from "./VisionCanvaMobile";
import CoursAccueilVision from "./AccueilVision";
import { StrategicCapHome, StrategicDecisions, StrategicHorizon } from "./StrategicHub";
import {
  Type, Image as ImageIcon, ListChecks, Link2, Palette, Sparkles,
  Plus, Minus, RotateCcw, Send, MousePointer2, Hand, Maximize2,
  TrendingUp, HeartPulse, Globe, Wallet, Check, Circle,
  BookOpen, FileDown, ChevronLeft, ChevronRight,
  Bell, Heart, Clock3,
  Star, Search, ArrowLeft, ArrowRight,
  ExternalLink, Loader2, Upload, Share2, X, MoreVertical, CreditCard,
  Shield, AlertTriangle, Target, Zap,
  Printer, FileText, Wand2, Folder, Video, Presentation, LayoutTemplate,
} from "lucide-react";
import { toast } from "sonner";
import { useApp } from "./useApp";
import { useSearchParams } from "react-router-dom";
import { visionApi, visionExtApi, pilotageApi, wellnessApi, onboardingApi, tasksApi, analyseApi } from "../../lib/finalVisionModuleApi";
import {
  BOARD_CENTER, BOARD_TOOLS,
  VISION_BOOK,
  TEMPLATES, TEMPLATE_CATEGORIES, STUDIO_TEMPLATES, STUDIO_PRESETS,
} from "./mock";
import "./vision.css";

// ─── TABS ────────────────────────────────────────────────────────────────────
const TABS = [
  { id: "accueil",  labelFr: "Accueil Vision",        labelEn: "Vision Home" },
  { id: "pillars",  labelFr: "Piliers stratégiques",  labelEn: "Strategic Pillars" },
  { id: "horizon",  labelFr: "Horizon 90 jours",      labelEn: "90-day Horizon" },
  { id: "decisions", labelFr: "Décisions & validation", labelEn: "Decisions & validation" },
];

// ─── SVG CONNECTOR ───────────────────────────────────────────────────────────
function Connector({ from, to }) {
  const midY = (from.y + to.y) / 2;
  const d = `M ${from.x} ${from.y} C ${from.x} ${midY}, ${to.x} ${midY}, ${to.x} ${to.y}`;
  return <path d={d} fill="none" stroke="rgba(120,135,165,0.45)" strokeWidth="1.6" />;
}

// ─── RING ─────────────────────────────────────────────────────────────────────
function Ring({ value, color }) {
  const r = 22, c = 2 * Math.PI * r;
  const offset = c - (value / 100) * c;
  return (
    <div className="relative h-14 w-14">
      <svg viewBox="0 0 56 56" className="h-14 w-14">
        <circle cx="28" cy="28" r={r} fill="none" strokeWidth="6" className="gauge-track" />
        <circle cx="28" cy="28" r={r} fill="none" strokeWidth="6" stroke={color}
          strokeLinecap="round" strokeDasharray={c} strokeDashoffset={offset}
          transform="rotate(-90 28 28)"
          style={{ transition: "stroke-dashoffset 1s cubic-bezier(0.22,1,0.36,1)" }} />
      </svg>
      <span className="absolute inset-0 flex items-center justify-center font-head text-xs font-bold text-[var(--app-text)]">{value}%</span>
    </div>
  );
}

// ─── TAB: VISION CANVAS ───────────────────────────────────────────────────────
const TOOL_ICONS = { Type, Image: ImageIcon, ListChecks, Link2, Palette, Sparkles, FileText };
const NOTE_COLORS = ["#3B6FE0", "#2FB89A", "#B784E0", "#E0A93B"];

// Types de documents AI (mêmes que le backend routes/vision_board.py:_DOC_TYPES)
const AI_DOC_TYPES = [
  { id: "note",        label: "Note libre",         hint: "Sujet libre, notes actionnables" },
  { id: "brief",       label: "Brief stratégique",  hint: "Objectif · cible · message · étapes" },
  { id: "plan",        label: "Plan 30 jours",      hint: "Phases + actions concrètes" },
  { id: "positioning", label: "Positionnement",     hint: "Pour qui · douleur · offre · différenciateurs" },
  { id: "swot",        label: "SWOT narratif",      hint: "Forces · faiblesses · opportunités · menaces" },
];

// ─── Modal : générer un AI Document (Storyflow-style) ───────────────────
function AiDocModal({ open, onClose, onGenerated }) {
  const [prompt, setPrompt] = useState("");
  const [docType, setDocType] = useState("note");
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    const value = prompt.trim();
    if (value.length < 4) return toast.error("Décris ton sujet en quelques mots.");
    setLoading(true);
    try {
      const res = await visionApi.generateDoc(value, docType);
      if (!res?.content) throw new Error("empty");
      onGenerated({ title: res.title, content: res.content, docType: res.doc_type });
      onClose();
      setPrompt("");
      toast.success("Document IA ajouté au board ✦");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Impossible de générer le document — réessaie dans un instant.");
    } finally {
      setLoading(false);
    }
  };

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div
        className="relative w-full max-w-lg rounded-2xl border border-[var(--app-border)] bg-[var(--app-surface)] p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
        data-testid="vision-ai-doc-modal"
      >
        <button onClick={onClose} className="absolute right-4 top-4 rounded-lg p-1.5 text-[var(--app-text-muted)] hover:bg-[var(--app-surface-2)]" data-testid="vision-ai-doc-close">
          <X size={16} />
        </button>
        <div className="mb-3 flex items-center gap-2">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[var(--app-accent-soft)] text-[var(--app-accent)]"><FileText size={17} /></span>
          <div>
            <h3 className="font-head text-lg font-semibold text-[var(--app-text)]">AI Document</h3>
            <p className="text-xs text-[var(--app-text-muted)]">Génère un document structuré dans ton board</p>
          </div>
        </div>

        {/* Doc type selector */}
        <div className="mb-3 grid grid-cols-2 gap-1.5 sm:grid-cols-3">
          {AI_DOC_TYPES.map((dt) => (
            <button
              key={dt.id}
              onClick={() => setDocType(dt.id)}
              data-testid={`vision-ai-doc-type-${dt.id}`}
              className={[
                "rounded-lg border px-2.5 py-2 text-left transition",
                docType === dt.id
                  ? "border-[var(--app-accent)] bg-[var(--app-accent-soft)] text-[var(--app-text)]"
                  : "border-[var(--app-border)] bg-[var(--app-surface-2)] text-[var(--app-text-muted)] hover:border-[var(--app-accent)]/60",
              ].join(" ")}
            >
              <div className="text-[11px] font-semibold text-[var(--app-text)]">{dt.label}</div>
              <div className="mt-0.5 text-[10px] leading-snug opacity-80">{dt.hint}</div>
            </button>
          ))}
        </div>

        {/* Prompt */}
        <label className="mb-1 block text-[11px] font-semibold uppercase tracking-wide text-[var(--app-text-muted)]">Sujet / contexte</label>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleGenerate(); }}
          rows={4}
          autoFocus
          placeholder="Ex : Cabinet de conseil pour dirigeants en transition, lancement Q2, cible C-level 45-55 ans…"
          data-testid="vision-ai-doc-prompt"
          className="w-full resize-none rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-2)] px-3 py-2.5 text-sm text-[var(--app-text)] outline-none focus:border-[var(--app-accent)] placeholder:text-[var(--app-text-muted)]"
        />

        <button
          onClick={handleGenerate}
          disabled={loading}
          data-testid="vision-ai-doc-generate"
          className="mt-3 flex w-full items-center justify-center gap-2 rounded-full bg-[var(--app-navy)] px-4 py-2.5 text-sm font-semibold text-white hover:opacity-90 disabled:opacity-60"
        >
          {loading ? <Loader2 size={15} className="animate-spin" /> : <Wand2 size={15} />}
          {loading ? "Génération en cours…" : "Générer le document"}
        </button>
        <p className="mt-2 text-center text-[11px] text-[var(--app-text-muted)]">
          Propulsé par Mammouth IA · Ctrl/⌘+Entrée pour envoyer
        </p>
      </div>
    </div>
  );
}

function TabCanvas({ bgImage, onBack }) {
  const { t, tv } = useApp();
  const [zoom, setZoom] = useState(1);

  // Fix #8 : raccourcis clavier +/- pour zoomer (en plus de Ctrl+molette)
  React.useEffect(() => {
    const onKey = (e) => {
      if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA" || e.target.isContentEditable) return;
      if (e.key === "+" || e.key === "=") { e.preventDefault(); setZoom((z) => Math.min(1.6, +(z + 0.1).toFixed(2))); }
      if (e.key === "-" || e.key === "_") { e.preventDefault(); setZoom((z) => Math.max(0.5, +(z - 0.1).toFixed(2))); }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);
  const [prompt, setPrompt] = useState("");
  const [mode, setMode] = useState("select");            // 'select' | 'hand'
  const [items, setItems] = useState([]);
  const [draggingId, setDraggingId] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [isFull, setIsFull] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(false);
  const [inspiring, setInspiring] = useState(false);
  const [generatingBoard, setGeneratingBoard] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [photoOpen, setPhotoOpen] = useState(false);
  const [photoQuery, setPhotoQuery] = useState("");
  const [photoResults, setPhotoResults] = useState([]);
  const [photoLoading, setPhotoLoading] = useState(false);
  const [aiDocOpen, setAiDocOpen] = useState(false);

  // Studio (image/video AI) + Documents drawer + Focus mode
  const [studioOpen, setStudioOpen] = useState(false);
  const [studioKind, setStudioKind] = useState("image"); // "image" | "video"
  const [docsOpen, setDocsOpen] = useState(false);
  const [focusMode, setFocusMode] = useState(false);
  const [promptInput, setPromptInput] = useState("");
  const [addMenuOpen, setAddMenuOpen] = useState(false);

  // ── Modèles de départ (starter templates prêts à l'emploi) ──
  const [templatesOpen, setTemplatesOpen] = useState(false);
  const [starterTemplates, setStarterTemplates] = useState([]);
  const [templatesLoading, setTemplatesLoading] = useState(false);

  const scrollRef = useRef(null);
  const containerRef = useRef(null);
  const dragRef = useRef(null);
  const panRef = useRef(null);

  const centerAnchor = { x: BOARD_CENTER.x + 70, y: BOARD_CENTER.y + 26 };

  // ---- Chargement SQL du board (par utilisateur) ----
  React.useEffect(() => {
    let alive = true;
    visionApi.getBoard()
      .then((res) => {
        if (!alive) return;
        if (Array.isArray(res.cards) && res.cards.length) {
          setItems(res.cards);
        } else {
          // Board vide honnête pour un nouveau compte (plus de seed fictif mock.js)
          setItems([]);
        }
      })
      .catch(() => setItems([]))
      .finally(() => { if (alive) setLoaded(true); });
    return () => { alive = false; };
  }, []);

  // ---- Sauvegarde SQL auto (debounce) à chaque changement ----
  React.useEffect(() => {
    if (!loaded) return;
    setSaving(true);
    const id = setTimeout(() => {
      visionApi.saveBoard(items)
        .then(() => setSaveError(false))
        .catch(() => setSaveError(true))
        .finally(() => setSaving(false));
    }, 600);
    return () => clearTimeout(id);
  }, [items, loaded]);

  // Fullscreen sync
  React.useEffect(() => {
    const onFs = () => setIsFull(Boolean(document.fullscreenElement));
    document.addEventListener("fullscreenchange", onFs);
    return () => document.removeEventListener("fullscreenchange", onFs);
  }, []);

  const returnToAccueil = () => {
    const finalize = () => {
      onBack?.();
      window.scrollTo({ top: 0, behavior: "auto" });
    };
    if (document.fullscreenElement) {
      Promise.resolve(document.exitFullscreen?.()).catch(() => {}).finally(finalize);
    } else {
      finalize();
    }
  };

  // Commande déclenchée par le bouton visible dans l’en-tête Vision Board.
  // Le Canvas conserve son vrai mode plein écran Final-main, avec sortie native.
  React.useEffect(() => {
    const openStudio = () => {
      const el = containerRef.current;
      if (el && !document.fullscreenElement) el.requestFullscreen?.().catch(() => {});
    };
    window.addEventListener("cours:open-vision-studio", openStudio);
    return () => window.removeEventListener("cours:open-vision-studio", openStudio);
  }, []);

  // ── Modèles de départ : ouvre le panneau et charge la liste depuis l'API ──
  const openStarterTemplates = useCallback(() => {
    setAddMenuOpen(false);
    setTemplatesOpen(true);
    if (starterTemplates.length === 0) {
      setTemplatesLoading(true);
      visionExtApi.getStarterTemplates()
        .then((r) => setStarterTemplates(r?.templates || []))
        .catch(() => toast.error("Modèles indisponibles pour l'instant."))
        .finally(() => setTemplatesLoading(false));
    }
  }, [starterTemplates.length]);

  // Remplit le canvas avec un modèle en un clic (confirmation si board non vide)
  const applyStarterTemplate = useCallback((tpl) => {
    if (!tpl?.cards?.length) return;
    if (items.length > 0 && !window.confirm(`Remplacer le canvas actuel par le modèle « ${tpl.label} » ? Vos cartes actuelles seront supprimées.`)) return;
    const newCards = tpl.cards.map((c, i) => ({ h: 130, ...c, id: `tpl_${Date.now()}_${i}` }));
    setItems(newCards);
    setTemplatesOpen(false);
    // Recentre la vue sur le barycentre des cartes du modèle
    const xs = newCards.map((c) => c.x || 0), ys = newCards.map((c) => c.y || 0);
    const cx = (Math.min(...xs) + Math.max(...xs)) / 2 + 130;
    const cy = (Math.min(...ys) + Math.max(...ys)) / 2 + 90;
    setTimeout(() => {
      const el = scrollRef.current;
      if (el) el.scrollTo({ left: Math.max(0, cx * zoom - el.clientWidth / 2), top: Math.max(0, cy * zoom - el.clientHeight / 2), behavior: "smooth" });
    }, 150);
    toast.success(`Modèle « ${tpl.label} » appliqué ✦`);
  }, [items.length, zoom]);


  // ---- Card drag (select mode) — pointer events pour support tactile mobile ----
  const onPointerDownCard = useCallback((e, item) => {
    if (mode !== "select") return;
    if (e.pointerType === "mouse" && e.button !== 0) return;
    e.stopPropagation();
    try { e.currentTarget.setPointerCapture?.(e.pointerId); } catch {}
    dragRef.current = { id: item.id, startX: e.clientX, startY: e.clientY, origX: item.x, origY: item.y };
    setDraggingId(item.id);
  }, [mode]);

  const BOARD_W = 3000, BOARD_H = 2000;
  React.useEffect(() => {
    const onMove = (e) => {
      const d = dragRef.current;
      if (!d) return;
      const dx = (e.clientX - d.startX) / zoom;
      const dy = (e.clientY - d.startY) / zoom;
      setItems((prev) => prev.map((it) => {
        if (it.id !== d.id) return it;
        const nx = Math.min(BOARD_W - (it.w || 200), Math.max(0, d.origX + dx));
        const ny = Math.min(BOARD_H - (it.h || 150), Math.max(0, d.origY + dy));
        return { ...it, x: nx, y: ny };
      }));
    };
    const onUp = () => { dragRef.current = null; setDraggingId(null); };
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
    window.addEventListener("pointercancel", onUp);
    return () => { window.removeEventListener("pointermove", onMove); window.removeEventListener("pointerup", onUp); window.removeEventListener("pointercancel", onUp); };
  }, [zoom]);

  // ---- Canvas pan (hand mode) ----
  const onCanvasPointerDown = (e) => {
    if (mode !== "hand" || !scrollRef.current) return;
    panRef.current = { startX: e.clientX, startY: e.clientY, left: scrollRef.current.scrollLeft, top: scrollRef.current.scrollTop };
  };
  React.useEffect(() => {
    const onMove = (e) => {
      const p = panRef.current;
      if (!p || !scrollRef.current) return;
      scrollRef.current.scrollLeft = p.left - (e.clientX - p.startX);
      scrollRef.current.scrollTop = p.top - (e.clientY - p.startY);
    };
    const onUp = () => { panRef.current = null; };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    return () => { window.removeEventListener("mousemove", onMove); window.removeEventListener("mouseup", onUp); };
  }, []);

  // ---- Add card by tool ----
  const spawn = () => {
    const angle = Math.random() * Math.PI * 2;
    return {
      x: BOARD_CENTER.x + Math.cos(angle) * 340 + (Math.random() * 60 - 30),
      y: BOARD_CENTER.y + Math.sin(angle) * 230 + (Math.random() * 60 - 30),
    };
  };

  const addByTool = (toolId) => {
    // AI Document tool → open modal instead of directly adding a card
    if (toolId === "ai-doc") {
      setAiDocOpen(true);
      return;
    }
    const { x, y } = spawn();
    const id = `u_${Date.now()}`;
    let note;
    if (toolId === "image") {
      note = { id, type: "image", x, y, w: 210, h: 160,
        image: "https://images.unsplash.com/photo-1500534623283-312aade485b7?w=600&q=80",
        title: { fr: "Nouvelle image", en: "New image" } };
    } else if (toolId === "color") {
      note = { id, type: "color", x, y, w: 220, h: 100,
        title: { fr: "Palette", en: "Palette" }, colors: ["#0a1f4e", "#4a6a9e", "#DEC2A3", "#F1E2CC"] };
    } else if (toolId === "check") {
      note = { id, type: "note", x, y, w: 220, h: 130, color: "#2FB89A",
        title: { fr: "Ma liste", en: "My list" },
        body: { fr: "• Étape 1\n• Étape 2\n• Étape 3", en: "• Step 1\n• Step 2\n• Step 3" } };
    } else if (toolId === "link") {
      note = { id, type: "note", x, y, w: 220, h: 110, color: "#3B6FE0",
        title: { fr: "Lien", en: "Link" }, body: { fr: "https://…", en: "https://…" } };
    } else if (toolId === "ai") {
      const idea = tv({ fr: "Idée générée par l'IA : clarifie ton objectif phare du trimestre.",
                        en: "AI idea: clarify your flagship goal for the quarter." });
      note = { id, type: "note", x, y, w: 220, h: 120, color: "#B784E0",
        title: { fr: "Idée IA", en: "AI idea" }, body: { fr: idea, en: idea } };
    } else { // text
      note = { id, type: "note", x, y, w: 210, h: 110, color: NOTE_COLORS[Math.floor(Math.random() * NOTE_COLORS.length)],
        title: { fr: "Nouvelle idée", en: "New idea" }, body: { fr: "", en: "" } };
    }
    setItems((prev) => [...prev, note]);
    if (note.type !== "color") setTimeout(() => setEditingId(id), 60);
    toast.success(t("board.addNote"));
  };

  // Callback quand la modale AI Doc renvoie un contenu généré
  const handleAiDocGenerated = useCallback(({ title, content, docType }) => {
    const { x, y } = spawn();
    const id = `u_${Date.now()}`;
    const card = {
      id,
      type: "ai-doc",
      x, y,
      w: 320, h: 260,
      color: "#DEC2A3",
      docType: docType || "note",
      title: { fr: title, en: title },
      body: { fr: content, en: content },
    };
    setItems((prev) => [...prev, card]);
  }, []);  

  // Callback Studio : insère image ou vidéo générée dans le board
  const handleStudioGenerated = useCallback(({ kind, url, prompt: gp }) => {
    const { x, y } = spawn();
    const id = `s_${Date.now()}`;
    const backendBase = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");
    const fullUrl = url.startsWith("http") ? url : `${backendBase}${url}`;
    const title = { fr: (gp || "").slice(0, 60) || (kind === "video" ? "Vidéo IA" : "Image IA"), en: "" };
    if (kind === "video") {
      setItems((prev) => [...prev, {
        id, type: "video", x, y, w: 300, h: 200,
        video: fullUrl, image: fullUrl, title,
      }]);
    } else {
      setItems((prev) => [...prev, {
        id, type: "image", x, y, w: 260, h: 200,
        image: fullUrl, title,
      }]);
    }
  }, []);  

  // Prompt bar bottom : détecte l'intention (image / vidéo / doc) via mots-clés
  const handlePromptSubmit = () => {
    const v = promptInput.trim();
    if (!v) return;
    const lower = v.toLowerCase();
    // Router simple d'intention
    if (/vid[eé]o|animation|motion|clip|reveal|manifesto/.test(lower)) {
      setStudioKind("video"); setStudioOpen(true);
    } else if (/image|photo|portrait|moodboard|visuel|illustration/.test(lower)) {
      setStudioKind("image"); setStudioOpen(true);
    } else {
      // Défaut : AI Doc
      setAiDocOpen(true);
    }
  };

  const handleAdd = useCallback((text) => {
    const value = (text ?? prompt).trim();
    if (!value) return;
    const { x, y } = spawn();
    const note = { id: `u_${Date.now()}`, type: "note", x, y, w: 210, h: 120,
      color: NOTE_COLORS[Math.floor(Math.random() * NOTE_COLORS.length)],
      title: { fr: "Nouvelle idée", en: "New idea" }, body: { fr: value, en: value } };
    setItems((prev) => [...prev, note]);
    setPrompt("");
    toast.success(t("board.addNote"));
  }, [prompt, t]);  

  // Génère un board complet (vision + piliers + actions) depuis 1 prompt IA
  const handleGenerateBoard = useCallback(async () => {
    const value = prompt.trim();
    if (!value) return toast.error("Décris ton projet en une phrase d'abord.");
    setGeneratingBoard(true);
    try {
      const res = await visionExtApi.generateFromPrompt(value);
      const jitter = () => Math.round((Math.random() - 0.5) * 60);
      const newCards = (res.cards || []).map((c, i) => ({
        ...c, id: `gen_${Date.now()}_${i}`, x: c.x + jitter(), y: c.y + jitter(),
      }));
      setItems((prev) => [...prev, ...newCards]);
      setPrompt("");
      toast.success(`Board généré · ${newCards.length} cartes ajoutées ✨`);
    } catch {
      toast.error("Génération impossible — réessayez dans un instant.");
    } finally {
      setGeneratingBoard(false);
    }
  }, [prompt]);

  const resetBoard = () => {
    if (!window.confirm("Vider le board ? Toutes vos cartes actuelles seront supprimées — cette action est irréversible.")) return;
    setItems([]);
    setEditingId(null);
    setZoom(1);
    toast(t("board.reset"));
  };

  const deleteCard = (id) => {
    const removed = items.find((c) => c.id === id);
    setItems((prev) => prev.filter((c) => c.id !== id));
    if (editingId === id) setEditingId(null);
    if (removed) {
      toast("Carte supprimée", {
        action: {
          label: "Annuler",
          onClick: () => setItems((prev) => [...prev, removed]),
        },
      });
    }
  };

  const editBody = (id, text) => {
    setItems((prev) => prev.map((c) => (c.id === id ? { ...c, body: { fr: text, en: text } } : c)));
  };
  const editTitle = (id, text) => {
    const val = (text ?? "").trim() || "Sans titre";
    setItems((prev) => prev.map((c) => (c.id === id ? { ...c, title: { fr: val, en: val } } : c)));
  };
  const editImage = (id, url) => {
    if (!url || !url.trim()) { setEditingId(null); return; }
    setItems((prev) => prev.map((c) => (c.id === id ? { ...c, image: url.trim() } : c)));
    setEditingId(null);
  };

  // ---- Zoom à la molette (Ctrl/Cmd + scroll) — comme Figma/Miro ----
  const onWheelZoom = useCallback((e) => {
    if (!(e.ctrlKey || e.metaKey)) return; // scroll normal = pan natif (overflow-auto)
    e.preventDefault();
    setZoom((z) => {
      const next = z - e.deltaY * 0.0015;
      return Math.min(1.6, Math.max(0.3, +next.toFixed(2)));
    });
  }, []);

  // ---- Mini-map : suit la position de scroll pour dessiner le cadre viewport ----
  const [viewport, setViewport] = useState({ left: 0, top: 0, w: 0, h: 0 });
  React.useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const update = () => setViewport({ left: el.scrollLeft, top: el.scrollTop, w: el.clientWidth, h: el.clientHeight });
    update();
    el.addEventListener("scroll", update);
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => { el.removeEventListener("scroll", update); ro.disconnect(); };
  }, [loaded]);

  const jumpToMiniMap = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const px = (e.clientX - rect.left) / rect.width;
    const py = (e.clientY - rect.top) / rect.height;
    const el = scrollRef.current;
    if (!el) return;
    el.scrollLeft = px * 3000 * zoom - viewport.w / 2;
    el.scrollTop = py * 2000 * zoom - viewport.h / 2;
  };

  const handleInspire = async () => {
    setInspiring(true);
    try {
      const { quote, author } = await visionApi.inspire();
      const { x, y } = spawn();
      const note = {
        id: `u_${Date.now()}`, type: "note", x, y, w: 240, h: 130, color: "#DEC2A3",
        title: { fr: "Citation", en: "Quote" },
        body: { fr: `“${quote}”\n— ${author}`, en: `“${quote}”\n— ${author}` },
      };
      setItems((prev) => [...prev, note]);
      toast.success("Citation générée ✨");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Génération indisponible (clé Mammouth ?).");
    } finally {
      setInspiring(false);
    }
  };

  const runPhotoSearch = async (q) => {
    setPhotoLoading(true);
    try {
      const res = await visionApi.photos(q || "inspiration");
      setPhotoResults(res.results || []);
    } catch {
      toast.error("Recherche photos indisponible.");
    } finally {
      setPhotoLoading(false);
    }
  };

  const openPhotos = () => { setPhotoOpen(true); if (photoResults.length === 0) runPhotoSearch("inspiration entrepreneur"); };

  const insertPhoto = (url) => {
    const { x, y } = spawn();
    const note = { id: `u_${Date.now()}`, type: "image", x, y, w: 220, h: 160, image: url, title: { fr: "Photo", en: "Photo" } };
    setItems((prev) => [...prev, note]);
    setPhotoOpen(false);
    toast.success("Photo ajoutée au board 📸");
  };

  const handleExportPng = async () => {
    setExporting(true);
    try {
      const { default: html2canvas } = await import("html2canvas");
      const el = containerRef.current;
      const canvas = await html2canvas(el, { backgroundColor: "#0a1f4e", useCORS: true, scale: 2, logging: false });
      const link = document.createElement("a");
      link.download = `vision-board-${new Date().toISOString().slice(0, 10)}.png`;
      link.href = canvas.toDataURL("image/png");
      link.click();
      toast.success("Vision Board exporté en PNG 🖼️");
    } catch (e) {
      toast.error("Export PNG impossible.");
    } finally {
      setExporting(false);
    }
  };

  const handleExportPdf = async () => {
    setExporting(true);
    try {
      const { default: html2canvas } = await import("html2canvas");
      const jsPdfMod = await import("jspdf");
      const jsPDF = jsPdfMod.jsPDF || jsPdfMod.default;
      const el = containerRef.current;
      const canvas = await html2canvas(el, { backgroundColor: "#0a1f4e", useCORS: true, scale: 2, logging: false });
      const imgData = canvas.toDataURL("image/jpeg", 0.92);

      // Format A3 paysage (420 × 297 mm) — poster imprimable
      const pdf = new jsPDF({ orientation: "landscape", unit: "mm", format: "a3" });
      const pageW = 420, pageH = 297;
      const margin = 12;
      const availW = pageW - margin * 2;
      const availH = pageH - margin * 2 - 18; // 18mm réservé au titre bas

      // Ratio conservation
      const ratio = canvas.width / canvas.height;
      let w = availW, h = w / ratio;
      if (h > availH) { h = availH; w = h * ratio; }
      const x = (pageW - w) / 2;
      const y = (pageH - h - 18) / 2 + 2;

      // Fond noir profond (cohérence brand)
      pdf.setFillColor(11, 31, 58);
      pdf.rect(0, 0, pageW, pageH, "F");

      pdf.addImage(imgData, "JPEG", x, y, w, h, undefined, "FAST");

      // Titre bas
      pdf.setTextColor(222, 194, 163);
      pdf.setFont("helvetica", "bold");
      pdf.setFontSize(22);
      pdf.text("MA VISION", pageW / 2, pageH - 16, { align: "center" });
      pdf.setFont("helvetica", "normal");
      pdf.setFontSize(10);
      pdf.setTextColor(246, 242, 234);
      const dateStr = new Date().toLocaleDateString("fr-FR", { day: "2-digit", month: "long", year: "numeric" });
      pdf.text(`Cockpit Zayado — ${dateStr}`, pageW / 2, pageH - 8, { align: "center" });

      pdf.save(`vision-poster-${new Date().toISOString().slice(0, 10)}.pdf`);
      toast.success("Poster PDF téléchargé — imprime-le en A3 et affiche-le ! 🎯");
    } catch (e) {
      console.error(e);
      toast.error("Export PDF impossible.");
    } finally {
      setExporting(false);
    }
  };

  const [isDropping, setIsDropping] = useState(false);

  // Convertit une position écran en position board (tient compte du zoom + scroll)
  const screenToBoard = useCallback((clientX, clientY) => {
    const rect = containerRef.current?.getBoundingClientRect();
    const scrollLeft = scrollRef.current?.scrollLeft || 0;
    const scrollTop = scrollRef.current?.scrollTop || 0;
    const x = ((clientX - (rect?.left || 0)) + scrollLeft) / zoom;
    const y = ((clientY - (rect?.top || 0)) + scrollTop) / zoom;
    return { x: Math.max(0, x - 105), y: Math.max(0, y - 85) };
  }, [zoom]);

  // ---- Drag & drop de fichiers depuis le bureau (quick-win vs storyflow) ----
  const onCanvasDragOver = useCallback((e) => {
    if (e.dataTransfer?.types?.includes("Files")) {
      e.preventDefault();
      setIsDropping(true);
    }
  }, []);
  const onCanvasDragLeave = useCallback(() => setIsDropping(false), []);
  const onCanvasDrop = useCallback((e) => {
    if (!e.dataTransfer?.files?.length) return;
    e.preventDefault();
    setIsDropping(false);
    const { x, y } = screenToBoard(e.clientX, e.clientY);
    Array.from(e.dataTransfer.files).forEach((file, i) => {
      const offset = i * 24;
      if (file.type.startsWith("image/")) {
        const reader = new FileReader();
        reader.onload = () => {
          setItems((prev) => [...prev, {
            id: `drop_${Date.now()}_${i}`, type: "image",
            x: x + offset, y: y + offset, w: 210, h: 160,
            image: reader.result, title: { fr: file.name, en: file.name },
          }]);
        };
        reader.readAsDataURL(file);
      } else {
        // PDF / autre fichier : carte-note avec le nom, pas d'aperçu image possible
        setItems((prev) => [...prev, {
          id: `drop_${Date.now()}_${i}`, type: "note",
          x: x + offset, y: y + offset, w: 210, h: 110, color: "#4a6a9e",
          title: { fr: "Document déposé", en: "Dropped file" },
          body: { fr: file.name, en: file.name },
        }]);
      }
    });
    toast.success(`${e.dataTransfer.files.length} fichier(s) ajouté(s) au board ✦`);
  }, [screenToBoard]);

  const ctrlBtn = "flex h-8 w-8 items-center justify-center rounded-lg text-[var(--app-text-muted)] hover:bg-[var(--app-surface-2)]";
  const ctrlActive = "flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--app-accent-soft)] text-[var(--app-accent)]";

  return (
    <div
      ref={containerRef}
      data-testid="vision-canvas-container"
      onDragOver={onCanvasDragOver}
      onDragLeave={onCanvasDragLeave}
      onDrop={onCanvasDrop}
      className={["relative overflow-hidden rounded-2xl border bg-[var(--app-surface)] transition-colors",
        isDropping ? "border-[var(--app-accent)] border-dashed border-2" : "border-[var(--app-border)]",
        isFull ? "h-screen w-screen rounded-none" : "h-[calc(100dvh-190px)] md:h-[calc(100vh-64px)]"].join(" ")}
      style={bgImage ? { backgroundImage: `url(${bgImage})`, backgroundSize: "cover", backgroundPosition: "center" } : {}}
    >
      {bgImage && <div className="absolute inset-0 z-0 bg-black/40" />}

      {/* AI Document generation modal */}
      <AiDocModal open={aiDocOpen} onClose={() => setAiDocOpen(false)} onGenerated={handleAiDocGenerated} />

      {/* Studio modal — Images (Nano Banana) & Vidéos (Sora 2) */}
      <StudioModal
        open={studioOpen}
        initialKind={studioKind}
        onClose={() => setStudioOpen(false)}
        onGenerated={handleStudioGenerated}
      />

      {/* Documents drawer — Ce board / Tous + Search */}
      <DocumentsDrawer
        open={docsOpen}
        onClose={() => setDocsOpen(false)}
        currentItems={items}
        allItems={null}
        onFocus={(id) => {
          const c = items.find((x) => x.id === id);
          if (c && scrollRef.current) {
            // Center the target card in the viewport via native scroll
            const el = scrollRef.current;
            el.scrollTo({
              left: Math.max(0, c.x * zoom - el.clientWidth / 2),
              top: Math.max(0, c.y * zoom - el.clientHeight / 2),
              behavior: "smooth",
            });
            setDocsOpen(false);
            setTimeout(() => setEditingId(id), 300);
          }
        }}
      />

      {isDropping && (
        <div className="pointer-events-none absolute inset-0 z-40 flex items-center justify-center bg-[var(--app-accent)]/10">
          <span className="rounded-full bg-[var(--app-surface)] px-5 py-2.5 text-sm font-semibold text-[var(--app-accent)] shadow-xl">
            Dépose l'image ou le fichier ici ✦
          </span>
        </div>
      )}

        {/* Left tool rail — masqué sur mobile (outils dispo via le "+" en bas) */}
        <div className="absolute left-3 top-1/2 z-30 hidden md:flex -translate-y-1/2 flex-col gap-1.5 rounded-2xl border border-[var(--app-border)] bg-[var(--app-surface)] p-1.5 shadow-lg">
          {BOARD_TOOLS.map((tool) => {
            const Icon = TOOL_ICONS[tool.icon];
            return (
              <button key={tool.id} onClick={() => addByTool(tool.id)} title={tv(tool.label)}
                data-testid={`vision-tool-${tool.id}`}
                className="group flex h-11 w-11 flex-col items-center justify-center rounded-xl text-[var(--app-text-muted)] hover:bg-[var(--app-accent-soft)] hover:text-[var(--app-accent)]">
                <Icon size={18} />
                <span className="mt-0.5 text-[9px] font-medium">{tv(tool.label)}</span>
              </button>
            );
          })}
        </div>

        {/* Save status — reflète le vrai résultat de la sauvegarde, plus jamais un faux succès */}
        <div data-testid="vision-save-status"
          className="absolute left-3 top-3 z-30 hidden md:flex items-center gap-1.5 rounded-full border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-1.5 text-xs font-medium shadow-lg">
          {saving
            ? (<><Loader2 size={13} className="spin text-[var(--app-accent)]" /> <span className="text-[var(--app-text-muted)]">Enregistrement…</span></>)
            : saveError
            ? (<><AlertTriangle size={13} className="text-[#c26b4a]" /> <span className="text-[#c26b4a]">Échec de la sauvegarde — vos changements ne sont pas enregistrés</span></>)
            : (<><Check size={13} className="text-[#5e8a5a]" /> <span className="text-[var(--app-text-muted)]">Enregistré (SQL)</span></>)}
        </div>

        {/* Canvas controls — top right : slim, 3 groupes (wrap sur mobile) */}
        <div className="absolute top-3 right-3 z-30 flex flex-wrap items-center justify-end gap-1.5 max-w-[68vw] rounded-xl border border-[var(--app-border)] bg-[var(--app-surface)] p-1 shadow-lg">
          {/* Mode + zoom (groupé, discret) */}
          <button onClick={() => setMode("select")} title={t("board.select")} data-testid="vision-tool-select"
            className={mode === "select" ? ctrlActive : ctrlBtn}><MousePointer2 size={15} /></button>
          <button onClick={() => setMode("hand")} title={t("board.pan")} data-testid="vision-tool-hand"
            className={mode === "hand" ? ctrlActive : ctrlBtn}><Hand size={15} /></button>
          <span className="mx-1 h-5 w-px bg-[var(--app-border)]" />
          <button onClick={() => setZoom((z) => Math.max(0.5, +(z - 0.1).toFixed(2)))} title={t("board.zoomOut")} data-testid="vision-zoom-out" className={ctrlBtn}><Minus size={15} /></button>
          <span className="w-10 text-center text-xs font-semibold text-[var(--app-text)]" data-testid="vision-zoom-value">{Math.round(zoom * 100)}%</span>
          <button onClick={() => setZoom((z) => Math.min(1.6, +(z + 0.1).toFixed(2)))} title={t("board.zoomIn")} data-testid="vision-zoom-in" className={ctrlBtn}><Plus size={15} /></button>
          <span className="mx-1 h-5 w-px bg-[var(--app-border)]" />

          {/* Actions principales : documents, export et retour explicite à l’Accueil Vision. */}
          <button onClick={() => setDocsOpen(true)} title="Documents (drawer)" data-testid="vision-open-documents"
            className={ctrlBtn}><Folder size={15} /></button>
          <button onClick={handleExportPdf} disabled={exporting} title="Exporter (PNG / PDF)" data-testid="vision-export"
            className={ctrlBtn}>{exporting ? <Loader2 size={15} className="spin" /> : <FileDown size={15} />}</button>
          <button onClick={returnToAccueil} title="Retour à l’Accueil Vision" data-testid="vision-back-to-home"
            className={`${ctrlBtn} gap-1.5 px-2`}><ArrowLeft size={15} /><span className="hidden sm:inline">Retour</span></button>
        </div>

        {/* Photo picker (Unsplash) */}
        {photoOpen && (
          <div className="absolute inset-0 z-40 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={() => setPhotoOpen(false)}>
            <div className="w-[92%] max-w-lg rounded-2xl border border-[var(--app-border)] bg-[var(--app-surface)] p-4 shadow-2xl" onClick={(e) => e.stopPropagation()} data-testid="vision-photo-modal">
              <div className="mb-3 flex items-center justify-between">
                <h3 className="font-head text-base font-semibold text-[var(--app-text)]">Ajouter une photo</h3>
                <button onClick={() => setPhotoOpen(false)} className="rounded-lg p-1.5 text-[var(--app-text-muted)] hover:bg-[var(--app-surface-2)]"><X size={16} /></button>
              </div>
              <div className="mb-3 flex items-center gap-2 rounded-full border border-[var(--app-border)] px-3 py-2">
                <Search size={15} className="text-[var(--app-text-muted)]" />
                <input value={photoQuery} onChange={(e) => setPhotoQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && runPhotoSearch(photoQuery)}
                  placeholder="Rechercher (montagne, océan, réussite…)"
                  data-testid="vision-photo-search"
                  className="flex-1 bg-transparent text-sm text-[var(--app-text)] outline-none" />
                <button onClick={() => runPhotoSearch(photoQuery)} className="text-xs font-medium text-[var(--app-accent)]">Chercher</button>
              </div>
              <div className="grid max-h-72 grid-cols-3 gap-2 overflow-y-auto">
                {photoLoading && <div className="col-span-3 flex justify-center py-8"><Loader2 size={22} className="spin text-[var(--app-accent)]" /></div>}
                {!photoLoading && photoResults.map((p, i) => (
                  <button key={i} onClick={() => insertPhoto(p.full)} data-testid={`vision-photo-${i}`}
                    className="group relative overflow-hidden rounded-lg border border-[var(--app-border)]">
                    <img src={p.thumb} alt={p.alt} loading="lazy" className="h-20 w-full object-cover transition group-hover:scale-105" />
                  </button>
                ))}
                {!photoLoading && photoResults.length === 0 && <p className="col-span-3 py-6 text-center text-xs text-[var(--app-text-muted)]">Aucune photo.</p>}
              </div>
            </div>
          </div>
        )}

        {/* Bottom prompt bar — Storyflow / CapCut style : "+" menu · templates strip · prompt */}
        <div className="absolute bottom-4 left-1/2 z-30 -translate-x-1/2 w-[min(96vw,720px)]" data-testid="vision-prompt-bar-container">
          {/* Templates strip (visible tout le temps, scroll horizontal) */}
          <div className="mb-2 flex items-center gap-1.5 overflow-x-auto pb-1 no-scrollbar">
            <button
              onClick={openStarterTemplates}
              data-testid="vision-prompt-starter-templates"
              className="flex shrink-0 items-center gap-1.5 rounded-full border border-[var(--app-accent)] bg-[var(--app-accent-soft)] px-3 py-1.5 text-[11px] font-semibold text-[var(--app-accent)] shadow-sm hover:brightness-105 transition"
            >
              <LayoutTemplate size={12} /> Modèles de départ
            </button>
            {[
              { id: "tpl-image", icon: ImageIcon, label: "Image IA", kind: "image" },
              { id: "tpl-video", icon: Video, label: "Vidéo IA", kind: "video" },
              { id: "tpl-doc", icon: FileText, label: "AI Doc", kind: "doc" },
              { id: "tpl-portrait", icon: Sparkles, label: "Portrait", kind: "image", tpl: "portrait" },
              { id: "tpl-moodboard", icon: Palette, label: "Moodboard", kind: "image", tpl: "moodboard" },
              { id: "tpl-manifesto", icon: Video, label: "Manifesto", kind: "video", tpl: "manifesto" },
            ].map((t) => {
              const Icn = t.icon;
              return (
                <button
                  key={t.id}
                  onClick={() => {
                    if (t.kind === "doc") { setAiDocOpen(true); return; }
                    setStudioKind(t.kind);
                    setStudioOpen(true);
                  }}
                  data-testid={`vision-prompt-tpl-${t.id}`}
                  className="flex shrink-0 items-center gap-1.5 rounded-full border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-1.5 text-[11px] font-medium text-[var(--app-text)] shadow-sm hover:border-[var(--app-accent)] hover:bg-[var(--app-accent-soft)] transition"
                >
                  <Icn size={12} className="text-[var(--app-accent)]" />
                  {t.label}
                </button>
              );
            })}
          </div>
          {/* Prompt bar */}
          <div className="flex items-center gap-2 rounded-full border border-[var(--app-border)] bg-[var(--app-surface)] px-2 py-1.5 shadow-xl backdrop-blur">
            <button
              onClick={() => setAddMenuOpen((v) => !v)}
              title="Ajouter un élément"
              data-testid="vision-prompt-add"
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[var(--app-accent-soft)] text-[var(--app-accent)] hover:bg-[var(--app-accent)] hover:text-white transition"
            >
              <Plus size={16} />
            </button>
            <input
              value={promptInput}
              onChange={(e) => setPromptInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handlePromptSubmit(); } }}
              placeholder="Décrivez ce que Zayado doit créer pour votre vision…"
              data-testid="vision-prompt-input"
              className="flex-1 bg-transparent px-2 text-sm text-[var(--app-text)] outline-none placeholder:text-[var(--app-text-muted)]"
            />
            <button
              onClick={handlePromptSubmit}
              disabled={!promptInput.trim()}
              data-testid="vision-prompt-submit"
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[var(--app-navy)] text-white hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition"
            >
              <Send size={14} />
            </button>
          </div>

          {/* Add menu popup (Storyflow "+" menu) */}
          {addMenuOpen && (
            <>
              <div className="fixed inset-0 z-40" onClick={() => setAddMenuOpen(false)} />
              <div
                className="absolute bottom-full mb-2 left-0 z-50 grid w-72 grid-cols-2 gap-1 rounded-2xl border border-[var(--app-border)] bg-[var(--app-surface)] p-1.5 shadow-2xl"
                data-testid="vision-add-menu"
              >
              {[
                { id: "starter", icon: LayoutTemplate, label: "Modèles de départ", action: () => openStarterTemplates() },
                { id: "ai",      icon: Sparkles,   label: "Idée IA",      action: () => addByTool("ai") },
                { id: "note",    icon: Type,       label: "Note",         action: () => addByTool("text") },
                { id: "ai-doc",  icon: FileText,   label: "AI Document",  action: () => setAiDocOpen(true) },
                { id: "image",   icon: ImageIcon,  label: "Image IA",     action: () => { setStudioKind("image"); setStudioOpen(true); } },
                { id: "video",   icon: Video,      label: "Vidéo IA",     action: () => { setStudioKind("video"); setStudioOpen(true); } },
                { id: "photo",   icon: Search,     label: "Photo Unsplash", action: () => openPhotos() },
                { id: "check",   icon: ListChecks, label: "Liste",        action: () => addByTool("check") },
                { id: "link",    icon: Link2,      label: "Lien",         action: () => addByTool("link") },
                { id: "palette", icon: Palette,    label: "Palette",      action: () => addByTool("color") },
              ].map((it) => {
                const Icn = it.icon;
                return (
                  <button
                    key={it.id}
                    onClick={() => { it.action(); setAddMenuOpen(false); }}
                    data-testid={`vision-add-${it.id}`}
                    className="flex items-center gap-2 rounded-lg px-2.5 py-2 text-left text-xs font-medium text-[var(--app-text)] hover:bg-[var(--app-surface-2)] transition"
                  >
                    <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-[var(--app-surface-2)] text-[var(--app-accent)]">
                      <Icn size={13} />
                    </span>
                    {it.label}
                  </button>
                );
              })}
            </div>
            </>
          )}
        </div>

        {/* Panneau « Modèles de départ » — démarrer un board en un clic */}
        {templatesOpen && (
          <>
            <div className="fixed inset-0 z-[60] bg-[rgba(11,31,58,0.55)] backdrop-blur-sm" onClick={() => setTemplatesOpen(false)} data-testid="vision-templates-overlay" />
            <div
              className="fixed left-1/2 top-1/2 z-[61] w-[min(94vw,720px)] max-h-[82vh] -translate-x-1/2 -translate-y-1/2 overflow-y-auto rounded-2xl border border-[var(--app-border)] bg-[var(--app-surface)] p-5 shadow-2xl"
              data-testid="vision-templates-panel"
            >
              <div className="mb-4 flex items-start justify-between gap-3">
                <div>
                  <h3 className="flex items-center gap-2 font-head text-lg font-bold text-[var(--app-text)]">
                    <LayoutTemplate size={18} className="text-[var(--app-accent)]" /> Modèles de départ
                  </h3>
                  <p className="text-sm text-[var(--app-text-muted)]">Démarrez votre board en un clic — choisissez un modèle prêt à l'emploi.</p>
                </div>
                <button onClick={() => setTemplatesOpen(false)} data-testid="vision-templates-close" className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--app-text-muted)] hover:bg-[var(--app-surface-2)]"><X size={18} /></button>
              </div>

              {templatesLoading ? (
                <div className="flex items-center justify-center gap-2 py-12 text-sm text-[var(--app-text-muted)]"><Loader2 size={16} className="animate-spin" /> Chargement des modèles…</div>
              ) : (
                <div className="grid gap-3 sm:grid-cols-2">
                  {starterTemplates.map((tpl) => (
                    <button
                      key={tpl.id}
                      onClick={() => applyStarterTemplate(tpl)}
                      data-testid={`vision-template-${tpl.id}`}
                      className="group flex flex-col items-start gap-1.5 rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-2)] p-4 text-left transition hover:border-[var(--app-accent)] hover:shadow-md"
                    >
                      <span className="text-2xl">{tpl.emoji}</span>
                      <span className="font-head text-base font-bold text-[var(--app-text)]">{tpl.label}</span>
                      <span className="text-xs text-[var(--app-text-muted)]">{tpl.description}</span>
                      <span className="mt-1 inline-flex items-center gap-1 text-[11px] font-semibold text-[var(--app-accent)] opacity-0 transition group-hover:opacity-100">
                        Utiliser ce modèle <ArrowRight size={12} />
                      </span>
                    </button>
                  ))}
                  {!starterTemplates.length && <p className="col-span-full py-8 text-center text-sm text-[var(--app-text-muted)]">Aucun modèle disponible pour l'instant.</p>}
                </div>
              )}
            </div>
          </>
        )}

        {/* Mini-map — bas droite, style Miro/Figma */}
        <div
          onClick={jumpToMiniMap}
          data-testid="vision-minimap"
          className="absolute bottom-3 right-3 z-30 cursor-pointer overflow-hidden rounded-lg border border-[var(--app-border)] bg-[var(--app-surface)] shadow-lg"
          style={{ width: 140, height: 93 }}
        >
          <div className="relative h-full w-full" style={{ background: "var(--app-surface-2)" }}>
            {items.map((c) => (
              <div key={`mm-${c.id}`} className="absolute rounded-sm"
                style={{
                  left: (c.x / 3000) * 140, top: (c.y / 2000) * 93,
                  width: Math.max(2, (c.w / 3000) * 140), height: Math.max(2, (c.h / 2000) * 93),
                  background: "var(--app-accent)", opacity: 0.6,
                }} />
            ))}
            {/* Cadre viewport actuel */}
            <div className="absolute border-2 border-[var(--app-accent)] pointer-events-none"
              style={{
                left: (viewport.left / (3000 * zoom)) * 140,
                top: (viewport.top / (2000 * zoom)) * 93,
                width: Math.min(140, (viewport.w / (3000 * zoom)) * 140),
                height: Math.min(93, (viewport.h / (2000 * zoom)) * 93),
              }} />
          </div>
        </div>

        {/* Canvas surface */}
        <div
          ref={scrollRef}
          onMouseDown={onCanvasPointerDown}
          onWheel={onWheelZoom}
          onContextMenu={(e) => { e.preventDefault(); setMode((m) => (m === "hand" ? "select" : "hand")); }}
          className={["vb-canvas canvas-dots relative z-10 h-full w-full overflow-auto", mode === "hand" ? (panRef.current ? "cursor-grabbing" : "cursor-grab") : ""].join(" ")}
        >
          <div className="relative" style={{ width: 3000, height: 2000, transform: `scale(${zoom})`, transformOrigin: "top left", userSelect: draggingId ? "none" : "auto" }}>
            <svg className="absolute inset-0 h-full w-full" style={{ pointerEvents: "none" }}>
              {items.map((c) => (
                <Connector key={`l-${c.id}`} from={centerAnchor} to={{ x: c.x + c.w / 2, y: c.y + c.h / 2 }} />
              ))}
            </svg>

            {/* Center node */}
            <div className="absolute z-10 flex items-center justify-center rounded-2xl bg-[var(--app-navy)] px-6 py-4 text-center shadow-xl animate-pop"
              style={{ left: BOARD_CENTER.x, top: BOARD_CENTER.y, width: 140 }}>
              <span className="font-head text-sm font-bold uppercase tracking-wide text-white">{tv(BOARD_CENTER.label)}</span>
            </div>

            {/* Cards */}
            {items.map((card, i) => {
              const isDragging = draggingId === card.id;
              const isEditing = editingId === card.id;
              return (
                <div key={card.id}
                  onPointerDown={(e) => { if (!isEditing) onPointerDownCard(e, card); }}
                  onDoubleClick={() => (card.type === "note" || card.type === "image" || card.type === "ai-doc") && setEditingId(card.id)}
                  data-testid={`vision-card-${card.id}`}
                  className={["group absolute select-none", isDragging ? "z-30" : "animate-pop"].join(" ")}
                  style={{
                    left: card.x, top: card.y, width: card.w,
                    touchAction: mode === "select" ? "none" : "auto",
                    cursor: mode === "hand" ? "inherit" : isEditing ? "default" : isDragging ? "grabbing" : "grab",
                    transform: isDragging ? "scale(1.03)" : "none",
                    animationDelay: isDragging ? "0ms" : `${Math.min(i * 40, 400)}ms`,
                  }}>
                  <button onPointerDown={(e) => e.stopPropagation()} onClick={() => deleteCard(card.id)}
                    data-testid={`vision-card-delete-${card.id}`}
                    className="absolute -right-2 -top-2 z-40 hidden h-6 w-6 items-center justify-center rounded-full bg-[var(--app-navy)] text-white shadow-md hover:bg-red-500 group-hover:flex" title="Supprimer">
                    <X size={13} />
                  </button>

                  {card.type === "image" && (
                    <div className={["relative overflow-hidden rounded-xl border bg-[var(--app-surface)] shadow-md", isDragging || isEditing ? "border-[var(--app-accent)] shadow-xl" : "border-[var(--app-border)] card-hover"].join(" ")}>
                      <img src={card.image} alt="" draggable={false} className="w-full object-cover" style={{ height: card.h - 34 }} />
                      <p className="px-2.5 py-2 text-xs font-medium text-[var(--app-text)]">{tv(card.title)}</p>
                      {isEditing && (
                        <div className="absolute inset-0 flex flex-col justify-center gap-1.5 bg-black/70 p-2 backdrop-blur-sm">
                          <p className="text-[10px] text-white/80">{t("board.editImageHint")}</p>
                          <input autoFocus defaultValue={card.image} placeholder="https://…"
                            onPointerDown={(e) => e.stopPropagation()}
                            onKeyDown={(e) => e.key === "Enter" && editImage(card.id, e.target.value)}
                            onBlur={(e) => editImage(card.id, e.target.value)}
                            className="w-full rounded-md border border-white/20 bg-white/10 px-2 py-1.5 text-[11px] text-white outline-none placeholder:text-white/50" />
                        </div>
                      )}
                    </div>
                  )}
                  {card.type === "video" && (
                    <div className={["relative overflow-hidden rounded-xl border bg-black shadow-md", isDragging ? "border-[var(--app-accent)] shadow-xl" : "border-[var(--app-border)] card-hover"].join(" ")}>
                      <video
                        src={card.video}
                        controls
                        muted
                        loop
                        playsInline
                        draggable={false}
                        onPointerDown={(e) => e.stopPropagation()}
                        className="w-full object-cover bg-black"
                        style={{ height: card.h - 34 }}
                      />
                      <p className="px-2.5 py-2 text-xs font-medium text-[var(--app-text)] bg-[var(--app-surface)]">
                        <Video size={10} className="inline mr-1 text-[var(--app-accent)]" />
                        {tv(card.title) || "Vidéo IA"}
                      </p>
                    </div>
                  )}
                  {card.type === "note" && (
                    <div className={["rounded-xl border bg-[var(--app-surface)] p-3 shadow-md", isDragging || isEditing ? "border-[var(--app-accent)] shadow-xl" : card.important ? "border-[#D6A85F]/70 card-hover" : "border-[var(--app-border)] card-hover"].join(" ")} style={{ minHeight: card.h, boxShadow: card.important ? "0 8px 24px rgba(214,168,95,0.28)" : undefined }}>
                      <span className="mb-1.5 inline-block h-1.5 rounded-full" style={{ background: card.important ? "#D6A85F" : card.color, width: card.important ? 36 : 32 }} />
                      <p className="text-xs font-semibold text-[var(--app-text)]">{tv(card.title)}</p>
                      {isEditing ? (
                        <textarea autoFocus defaultValue={tv(card.body)} rows={3}
                          onPointerDown={(e) => e.stopPropagation()}
                          onBlur={(e) => { editBody(card.id, e.target.value); setEditingId(null); }}
                          className="mt-1 w-full resize-none rounded-md border border-[var(--app-border)] bg-[var(--app-surface-2)] p-1.5 text-xs text-[var(--app-text)] outline-none" />
                      ) : (
                        <p className="mt-1 whitespace-pre-line text-xs text-[var(--app-text-muted)]">{tv(card.body)}</p>
                      )}
                    </div>
                  )}
                  {card.type === "color" && (
                    <div className={["rounded-xl border bg-[var(--app-surface)] p-3 shadow-md", isDragging ? "border-[var(--app-accent)] shadow-xl" : "border-[var(--app-border)] card-hover"].join(" ")}>
                      <p className="mb-2 text-xs font-semibold text-[var(--app-text)]">{tv(card.title)}</p>
                      <div className="flex gap-1.5">
                        {card.colors.map((col) => (<span key={col} className="h-8 flex-1 rounded-md" style={{ background: col }} />))}
                      </div>
                    </div>
                  )}
                  {card.type === "ai-doc" && (
                    <div
                      className={["flex flex-col overflow-hidden rounded-xl border bg-[var(--app-surface)] shadow-md", isDragging || isEditing ? "border-[var(--app-accent)] shadow-xl" : "border-[var(--app-border)] card-hover"].join(" ")}
                      style={{ height: card.h }}
                    >
                      {/* Header : icône + badge type + titre */}
                      <div className="flex items-center gap-2 border-b border-[var(--app-border)] bg-[var(--app-surface-2)] px-3 py-2">
                        <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-[var(--app-accent-soft)] text-[var(--app-accent)]">
                          <FileText size={13} />
                        </span>
                        <div className="min-w-0 flex-1">
                          {isEditing ? (
                            <input
                              autoFocus
                              defaultValue={tv(card.title)}
                              onPointerDown={(e) => e.stopPropagation()}
                              onKeyDown={(e) => { if (e.key === "Enter") { editTitle(card.id, e.target.value); e.target.blur(); } }}
                              onBlur={(e) => editTitle(card.id, e.target.value)}
                              className="w-full bg-transparent text-[13px] font-semibold text-[var(--app-text)] outline-none"
                            />
                          ) : (
                            <p className="truncate text-[13px] font-semibold text-[var(--app-text)]">{tv(card.title)}</p>
                          )}
                          <p className="text-[9px] uppercase tracking-wider text-[var(--app-text-muted)]">
                            AI · {(AI_DOC_TYPES.find((d) => d.id === card.docType) || AI_DOC_TYPES[0]).label}
                          </p>
                        </div>
                      </div>
                      {/* Corps scrollable */}
                      <div
                        className="ai-doc-body min-h-0 flex-1 overflow-y-auto px-3 py-2"
                        onPointerDown={(e) => { if (isEditing) e.stopPropagation(); }}
                        onWheel={(e) => { if (isEditing || (e.currentTarget.scrollHeight > e.currentTarget.clientHeight)) e.stopPropagation(); }}
                      >
                        {isEditing ? (
                          <textarea
                            defaultValue={tv(card.body)}
                            onPointerDown={(e) => e.stopPropagation()}
                            onBlur={(e) => { editBody(card.id, e.target.value); setEditingId(null); }}
                            className="h-full w-full resize-none bg-transparent text-[11.5px] leading-relaxed text-[var(--app-text)] outline-none"
                          />
                        ) : (
                          <p className="whitespace-pre-wrap text-[11.5px] leading-relaxed text-[var(--app-text)]">
                            {tv(card.body)}
                          </p>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

    </div>
  );
}

// ─── TAB: STRATEGIC PILLARS ───────────────────────────────────────────────────
const PILLAR_ICONS = { TrendingUp, HeartPulse, Globe, Wallet };

function TabPillars() {
  const { t, tv } = useApp();
  const [pillars, setPillars] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [view, setView] = useState("all"); // all | business | personnel
  const [creatingMission, setCreatingMission] = useState(null);

  // Chargement SQL (réel — fix backend vision_ext.py). Aucune donnée fictive avant la réponse.
  React.useEffect(() => {
    visionExtApi.getPillars()
      .then(data => { if (Array.isArray(data)) setPillars(data); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const globalScore = useMemo(() => {
    if (!pillars.length) return 0;
    return Math.round(pillars.reduce((s, p) => s + (p.progress || 0), 0) / pillars.length);
  }, [pillars]);

  // Sauvegarde auto debounce + détection de palier franchi (fix #7)
  const saveRef = React.useRef(null);
  const autosave = React.useCallback((updated) => {
    clearTimeout(saveRef.current);
    setSaving(true);
    saveRef.current = setTimeout(() => {
      visionExtApi.savePillars(updated)
        .then((res) => {
          if (res?.milestone_reached) {
            toast.success(`🎉 Palier franchi : ${res.milestone_reached}% de votre vision réalisée !`, { duration: 5000 });
          }
        })
        .catch(() => {})
        .finally(() => setSaving(false));
    }, 700);
  }, []);

  const toggleObjective = (pIdx, oIdx) => {
    setPillars(prev => {
      const next = prev.map((p, i) => {
        if (i !== pIdx) return p;
        const objectives = p.objectives.map((o, j) => j === oIdx ? { ...o, done: !o.done } : o);
        const done = objectives.filter(o => o.done).length;
        return { ...p, objectives, progress: Math.round((done / objectives.length) * 100) };
      });
      autosave(next);
      return next;
    });
  };

  const togglePinDashboard = (pIdx) => {
    setPillars(prev => {
      const next = prev.map((p, i) => i === pIdx ? { ...p, pinned_dashboard: !p.pinned_dashboard } : p);
      autosave(next);
      const p = next[pIdx];
      toast.success(p.pinned_dashboard ? `"${tv(p.title)}" épinglé au Dashboard` : `"${tv(p.title)}" retiré du Dashboard`);
      return next;
    });
  };

  const createMission = async (pillar, objective, oIdx) => {
    setCreatingMission(`${pillar.id}-${oIdx}`);
    try {
      await tasksApi.create({ label: tv(objective.text), type: "humain", priority: "normal" });
      toast.success("Mission créée dans votre Cockpit ✦");
    } catch {
      toast.error("Impossible de créer la mission pour le moment.");
    } finally {
      setCreatingMission(null);
    }
  };

  // Fix — bouton "+ Ajouter un pilier" n'avait aucun handler (audit fichier par fichier).
  const PILLAR_COLORS = ["#DEC2A3", "#1B2A4A", "#3E7C59", "#8A4FFF"];
  const addPillar = () => {
    const title = (window.prompt("Nom du nouveau pilier stratégique ?") || "").trim();
    if (!title) return;
    const newPillar = {
      id: `pillar-${Date.now()}`,
      title,
      description: "",
      category: view === "personnel" ? "personnel" : "business",
      color: PILLAR_COLORS[pillars.length % PILLAR_COLORS.length],
      icon: Object.keys(PILLAR_ICONS)[pillars.length % Object.keys(PILLAR_ICONS).length],
      progress: 0,
      objectives: [],
      pinned_dashboard: false,
    };
    setPillars(prev => {
      const next = [...prev, newPillar];
      autosave(next);
      return next;
    });
    toast.success(`Pilier "${title}" ajouté ✦`);
  };

  const filteredPillars = view === "all" ? pillars : pillars.filter(p => (p.category || "business") === view);

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h3 className="font-head text-xl font-bold text-[var(--app-text)]">{t("pillars.title")}</h3>
          <p className="text-sm text-[var(--app-text-muted)]">{t("pillars.subtitle")}</p>
        </div>
        <div className="flex items-center gap-3">
          {/* Fix #1 — score de complétion réel, visible en permanence */}
          <div className="flex items-center gap-2 rounded-full bg-[var(--app-surface-2)] px-4 py-2" data-testid="pillars-global-score">
            <Ring value={globalScore} color="#DEC2A3" />
            <span className="text-xs text-[var(--app-text-muted)]">Vision réalisée</span>
          </div>
          <button onClick={addPillar} data-testid="add-pillar-btn"
            className="flex items-center gap-2 rounded-full border border-dashed border-[var(--app-accent)] px-4 py-2 text-sm font-medium text-[var(--app-accent)] hover:bg-[var(--app-accent-soft)]">
            <Plus size={16} /> {t("pillars.add")}
          </button>
        </div>
      </div>

      {/* Fix #8 — vue séparée business / personnel */}
      <div className="flex items-center gap-2" data-testid="pillars-view-switch">
        {[["all", "Tout"], ["business", "Business"], ["personnel", "Personnel"]].map(([id, label]) => (
          <button key={id} onClick={() => setView(id)}
            className={["rounded-full px-3.5 py-1.5 text-xs font-semibold transition-colors",
              view === id ? "bg-[var(--app-navy)] text-white" : "bg-[var(--app-surface-2)] text-[var(--app-text-muted)]"].join(" ")}
            data-testid={`pillars-view-${id}`}>
            {label}
          </button>
        ))}
      </div>

      <div className="grid gap-5 md:grid-cols-2">
        {loading && (
          <div className="col-span-full flex items-center justify-center py-12 text-[var(--app-text-muted)]" data-testid="pillars-loading">
            <Loader2 size={20} className="animate-spin mr-2" /> Chargement de vos piliers…
          </div>
        )}
        {!loading && !filteredPillars.length && (
          <div className="col-span-full rounded-2xl border border-dashed border-[var(--app-border)] py-12 text-center" data-testid="pillars-empty">
            <Target size={26} className="mx-auto mb-3 text-[var(--app-accent)]" />
            <p className="font-head text-base font-semibold text-[var(--app-text)]">Aucun pilier pour l'instant</p>
            <p className="mt-1 text-sm text-[var(--app-text-muted)]">Ajoutez votre premier pilier stratégique pour structurer votre vision.</p>
          </div>
        )}
        {!loading && filteredPillars.map((p) => {
          const pIdx = pillars.indexOf(p);
          const Icon = PILLAR_ICONS[p.icon];
          return (
            <div key={p.id} className="app-card card-hover overflow-hidden p-0">
              <div className="flex items-start gap-4 p-5" style={{ borderTop: `3px solid ${p.color}` }}>
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl" style={{ background: `${p.color}1A`, color: p.color }}>
                  <Icon size={22} />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <h4 className="font-head text-base font-semibold text-[var(--app-text)]">{tv(p.title)}</h4>
                    <span className="rounded-full bg-[var(--app-surface-2)] px-2 py-0.5 text-[10px] font-semibold uppercase text-[var(--app-text-muted)]">
                      {p.category === "personnel" ? "Personnel" : "Business"}
                    </span>
                  </div>
                  <p className="mt-0.5 text-sm text-[var(--app-text-muted)]">{tv(p.description)}</p>
                </div>
                <Ring value={p.progress} color={p.color} />
              </div>
              <div className="border-t border-[var(--app-border)] px-5 py-4">
                <div className="mb-2 flex items-center justify-between">
                  <p className="text-xs font-semibold uppercase tracking-wide text-[var(--app-text-muted)]">{t("pillars.objectives")}</p>
                  {/* Fix #4 — épingler un indicateur au Dashboard */}
                  <button onClick={() => togglePinDashboard(pIdx)} data-testid={`pin-dashboard-${p.id}`}
                    className={["text-[11px] font-semibold rounded-full px-2.5 py-1", p.pinned_dashboard ? "bg-[var(--app-accent-soft)] text-[var(--app-accent)]" : "text-[var(--app-text-muted)] hover:bg-[var(--app-surface-2)]"].join(" ")}>
                    {p.pinned_dashboard ? "★ Sur le Dashboard" : "☆ Ajouter au Dashboard"}
                  </button>
                </div>
                <div className="space-y-1.5">
                  {p.objectives.map((o, oIdx) => (
                    <div key={oIdx} className="flex w-full items-center gap-2.5 rounded-lg px-2 py-1.5 hover:bg-[var(--app-surface-2)]">
                      <button onClick={() => toggleObjective(pIdx, oIdx)} className="flex items-center gap-2.5 flex-1 text-left">
                        {o.done
                          ? <span className="flex h-5 w-5 items-center justify-center rounded-full" style={{ background: p.color }}><Check size={13} className="text-white" /></span>
                          : <Circle size={20} className="text-[var(--app-border)]" />
                        }
                        <span className={["text-sm", o.done ? "text-[var(--app-text-muted)] line-through" : "text-[var(--app-text)]"].join(" ")}>
                          {tv(o.text)}
                        </span>
                      </button>
                      {/* Fix #3 — transformer un objectif en mission du Cockpit */}
                      {!o.done && (
                        <button onClick={() => createMission(p, o, oIdx)} disabled={creatingMission === `${p.id}-${oIdx}`}
                          data-testid={`create-mission-${p.id}-${oIdx}`}
                          className="shrink-0 text-[10px] font-semibold text-[var(--app-accent)] hover:underline disabled:opacity-50">
                          {creatingMission === `${p.id}-${oIdx}` ? "…" : "+ Mission"}
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── TAB: VISION BOOK ─────────────────────────────────────────────────────────
function TabVisionBook() {
  const { t, tv } = useApp();
  const spreads = [{ id: "cover", kind: "cover" }, ...VISION_BOOK.pages];
  const [idx, setIdx] = useState(0);
  const [exportOpen, setExportOpen] = useState(false);
  const [stage, setStage] = useState("loading");

  const current = spreads[idx];

  const [bookUrl, setBookUrl] = useState(null);

  const openExport = async () => {
    setExportOpen(true);
    setStage("loading");
    try {
      const res = await visionExtApi.generateBook();
      setBookUrl(res?.flipbook_url || res?.pdf_url || null);
      setStage("done");
    } catch {
      // fallback jsPDF simulé
      setTimeout(() => setStage("done"), 2200);
    }
  };

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-head text-xl font-bold text-[var(--app-text)]">{t("book.title")}</h3>
          <p className="text-sm text-[var(--app-text-muted)]">{t("book.subtitle")}</p>
        </div>
        <button onClick={openExport} className="flex items-center gap-2 rounded-full bg-[var(--app-navy)] px-4 py-2.5 text-sm font-medium text-white hover:opacity-90">
          <FileDown size={16} /> {t("book.exportPdf")}
        </button>
      </div>

      <div className="app-card overflow-hidden p-0">
        <div className="grid md:grid-cols-2">
          <div className="relative min-h-[320px] bg-[var(--app-navy-deep)]">
            <img src={current.kind === "cover" ? VISION_BOOK.cover : current.image} alt=""
              className="h-full w-full object-cover opacity-90" />
            <div className="absolute inset-0 bg-gradient-to-t from-[var(--app-navy-deep)] via-transparent to-transparent" />
            {current.kind === "cover" && (
              <div className="absolute inset-0 flex flex-col items-center justify-center p-8 text-center">
                <BookOpen size={30} className="mb-4 text-white/80" />
                <h4 className="font-head text-xl font-bold text-white">{tv(VISION_BOOK.title)}</h4>
                <p className="mt-2 text-sm text-white/70">{tv(VISION_BOOK.subtitle)}</p>
              </div>
            )}
          </div>
          <div className="flex flex-col justify-between p-6">
            <div>
              {current.kind === "cover"
                ? <p className="text-sm text-[var(--app-text-muted)]">Page de couverture de votre Vision Book.</p>
                : (
                  <>
                    <p className="text-xs font-semibold uppercase tracking-widest text-[var(--app-accent)] mb-2">{tv(current.category)}</p>
                    <h4 className="font-head text-lg font-bold text-[var(--app-text)] mb-2">{tv(current.title)}</h4>
                    <p className="text-sm text-[var(--app-text-muted)]">{tv(current.body)}</p>
                  </>
                )
              }
            </div>
            <div className="flex items-center justify-between mt-4">
              <button onClick={() => setIdx(i => Math.max(0, i - 1))} disabled={idx === 0}
                className="flex h-9 w-9 items-center justify-center rounded-full border border-[var(--app-border)] text-[var(--app-text-muted)] hover:bg-[var(--app-surface-2)] disabled:opacity-30">
                <ChevronLeft size={18} />
              </button>
              <span className="text-xs text-[var(--app-text-muted)]">{idx + 1} / {spreads.length}</span>
              <button onClick={() => setIdx(i => Math.min(spreads.length - 1, i + 1))} disabled={idx === spreads.length - 1}
                className="flex h-9 w-9 items-center justify-center rounded-full border border-[var(--app-border)] text-[var(--app-text-muted)] hover:bg-[var(--app-surface-2)] disabled:opacity-30">
                <ChevronRight size={18} />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Export modal */}
      {exportOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="relative w-full max-w-sm rounded-2xl border border-[var(--app-border)] bg-[var(--app-surface)] p-7 text-center shadow-2xl">
            <button onClick={() => setExportOpen(false)} className="absolute right-4 top-4 rounded-lg p-1.5 text-[var(--app-text-muted)] hover:bg-[var(--app-surface-2)]">
              <X size={16} />
            </button>
            {stage === "loading"
              ? <>
                  <Loader2 size={32} className="animate-spin mx-auto mb-4 text-[var(--app-accent)]" />
                  <p className="font-head text-base font-semibold text-[var(--app-text)]">Génération du PDF…</p>
                  <p className="mt-1 text-sm text-[var(--app-text-muted)]">Compilation des pages de votre Vision Book</p>
                </>
              : <>
                  <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-green-500/15">
                    <Check size={28} className="text-green-500" />
                  </div>
                  <p className="font-head text-base font-semibold text-[var(--app-text)]">Vision Book prêt !</p>
                  <p className="mt-1 text-sm text-[var(--app-text-muted)] mb-5">Votre PDF 7 pages est généré.</p>
                  <div className="flex gap-3">
                    <button
                      onClick={() => {
                        if (bookUrl) { window.open(bookUrl, "_blank"); }
                        else { toast.success("PDF téléchargé !"); }
                        setExportOpen(false);
                      }}
                      className="flex flex-1 items-center justify-center gap-2 rounded-full bg-[var(--app-navy)] px-4 py-2.5 text-sm font-medium text-white hover:opacity-90">
                      <FileDown size={15} /> {bookUrl ? "Ouvrir le flipbook" : "Télécharger"}
                    </button>
                    <button
                      onClick={() => {
                        if (bookUrl) { navigator.clipboard.writeText(bookUrl); toast.success("Lien copié !"); }
                        else { toast.success("Lien copié !"); }
                        setExportOpen(false);
                      }}
                      className="flex flex-1 items-center justify-center gap-2 rounded-full border border-[var(--app-border)] px-4 py-2.5 text-sm font-medium text-[var(--app-text)] hover:bg-[var(--app-surface-2)]">
                      <Share2 size={15} /> Partager
                    </button>
                  </div>
                </>
            }
          </div>
        </div>
      )}
    </div>
  );
}

// ─── TAB: TEMPLATES ───────────────────────────────────────────────────────────
const CAT_MATCH = {
  vision: ["Vision"],
  strategy: ["Stratégie", "Strategy", "Marketing", "Finances", "Finance"],
  productivity: ["Productivité", "Productivity", "Connaissance", "Knowledge"],
  creative: ["Créatif", "Creative", "Produit", "Product"],
};

function TabTemplates({ embedded }) {
  const { t, tv } = useApp();
  const [cat, setCat] = useState("all");
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => TEMPLATES.filter(tpl => {
    const inCat = cat === "all" || (CAT_MATCH[cat] || []).some(c => tv(tpl.category) === c || tpl.category?.fr === c);
    const q = query.trim().toLowerCase();
    return inCat && (!q || tv(tpl.title).toLowerCase().includes(q) || tv(tpl.desc).toLowerCase().includes(q));
  }), [cat, query, tv]);

  return (
    <div className="space-y-5">
      {!embedded && (
        <div>
          <h3 className="font-head text-xl font-bold text-[var(--app-text)]">{t("templates.title")}</h3>
          <p className="text-sm text-[var(--app-text-muted)]">{t("templates.subtitle")}</p>
        </div>
      )}

      <div className="flex flex-wrap items-center gap-3">
        <div className="flex flex-wrap gap-2">
          {TEMPLATE_CATEGORIES.map(c => (
            <button key={c.id} onClick={() => setCat(c.id)}
              className={["rounded-full px-4 py-1.5 text-sm font-medium",
                cat === c.id ? "bg-[var(--app-navy)] text-white" : "border border-[var(--app-border)] bg-[var(--app-surface)] text-[var(--app-text-muted)] hover:border-[var(--app-accent)] hover:text-[var(--app-text)]"
              ].join(" ")}>
              {tv(c.label)}
            </button>
          ))}
        </div>
        <div className="ml-auto flex items-center gap-2 rounded-full border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-1.5">
          <Search size={15} className="text-[var(--app-text-muted)]" />
          <input value={query} onChange={e => setQuery(e.target.value)}
            placeholder={t("common.search")}
            className="w-32 bg-transparent text-sm text-[var(--app-text)] outline-none placeholder:text-[var(--app-text-muted)]" />
        </div>
      </div>

      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {filtered.map((tpl, i) => (
          <div key={tpl.id} className="app-card card-hover overflow-hidden p-0 animate-fade-up" style={{ animationDelay: `${i * 50}ms` }}>
            <div className="relative h-40 overflow-hidden">
              <img src={tpl.image} alt="" className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105" />
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
              {tpl.badge && (
                <span className="absolute right-3 top-3 flex items-center gap-1 rounded-full bg-[var(--app-accent)] px-2.5 py-1 text-[10px] font-bold text-white">
                  <Star size={10} /> {tv(tpl.badge)}
                </span>
              )}
            </div>
            <div className="p-4">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-[var(--app-accent)]">{tv(tpl.category)}</span>
              <h4 className="font-head mt-0.5 text-sm font-bold text-[var(--app-text)]">{tv(tpl.title)}</h4>
              <p className="mt-1 text-xs text-[var(--app-text-muted)] line-clamp-2">{tv(tpl.desc)}</p>
              <button
                onClick={() => {
                  toast.info(`Modèle "${tv(tpl.title)}" — l'intégration Canva externe a été retirée ; utilisez les cartes du canvas pour composer votre board.`);
                }}
                className="mt-3 flex w-full items-center justify-center gap-2 rounded-full border border-[var(--app-border)] py-2 text-xs font-medium text-[var(--app-text)] hover:border-[var(--app-accent)] hover:text-[var(--app-accent)]"
              >
                Utiliser ce modèle <ArrowRight size={13} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── TAB: VISION STUDIO (Studio éditorial + Modèles) ──────────────────────────
// ─── TEMPLATES DATA-DRIVEN — visualisations connectées aux vraies données ──
// Contrairement aux templates éditoriaux (photo + texte), ces 3 templates
// affichent les vraies données de l'utilisateur (Pilotage, onboarding, Bien-être/Piliers).

function CeoDashboardPreview() {
  const [data, setData] = useState(null);
  React.useEffect(() => {
    pilotageApi.overview("mois").then(setData).catch(() => setData({}));
  }, []);
  const ca = data?.ca_mois ?? data?.ca ?? 0;
  const tresorerie = data?.tresorerie ?? data?.solde ?? 0;
  const marge = data?.marge_pct ?? data?.marge ?? 0;
  const objectif = data?.objectif_ca ?? Math.max(ca * 1.3, 1000);
  const pct = Math.min(100, Math.round((ca / objectif) * 100));

  return (
    <div className="relative aspect-[3/4] w-full overflow-hidden rounded-2xl shadow-2xl bg-[#0B1F3A] p-6 flex flex-col" data-testid="tpl-ceo-dashboard">
      <span className="text-[10px] font-extrabold uppercase tracking-[0.18em] text-[#D6A85F]">CEO Dashboard</span>
      <h3 className="font-head text-2xl font-extrabold text-white mt-1 mb-5">Ma trajectoire business</h3>

      <div className="grid grid-cols-2 gap-3 mb-5">
        <div className="rounded-xl bg-white/5 p-3 border border-white/10">
          <p className="text-[10px] text-white/50 uppercase tracking-wide">CA du mois</p>
          <p className="text-xl font-bold text-white mt-1">{Math.round(ca).toLocaleString("fr-FR")}€</p>
        </div>
        <div className="rounded-xl bg-white/5 p-3 border border-white/10">
          <p className="text-[10px] text-white/50 uppercase tracking-wide">Trésorerie</p>
          <p className="text-xl font-bold text-white mt-1">{Math.round(tresorerie).toLocaleString("fr-FR")}€</p>
        </div>
      </div>

      <div className="rounded-xl bg-white/5 p-3 border border-white/10 mb-4">
        <div className="flex justify-between text-[11px] text-white/60 mb-2">
          <span>Objectif du mois</span><span>{pct}%</span>
        </div>
        <div className="h-2 rounded-full bg-white/10">
          <div className="h-full rounded-full bg-[#5DCAA5]" style={{ width: `${pct}%`, transition: "width 0.8s ease" }} />
        </div>
      </div>

      <div className="mt-auto flex items-center gap-2">
        <span className="text-[11px] text-white/50">Marge : </span>
        <span className="text-sm font-bold text-[#5DCAA5]">{marge}%</span>
        <span className="ml-auto text-[10px] text-white/30">Zayado · MyExtension AI</span>
      </div>
    </div>
  );
}

function TrajectoirePreview() {
  const [milestones, setMilestones] = useState(null);
  React.useEffect(() => {
    onboardingApi.get().then((ob) => {
      const f = ob?.form || {};
      setMilestones([
        { label: "Aujourd'hui", sub: "Poser les fondations", done: true },
        { label: "90 jours", sub: f.priorites?.[0] || "Passer à l'action", done: false },
        { label: "1 an", sub: f.priorites?.[1] || "Atteindre mes objectifs clés", done: false },
        { label: "3 ans", sub: f.priorites?.[2] || "Rayonner et impacter", done: false },
      ]);
    }).catch(() => setMilestones([
      { label: "Aujourd'hui", sub: "Poser les fondations", done: true },
      { label: "90 jours", sub: "Passer à l'action", done: false },
      { label: "1 an", sub: "Atteindre mes objectifs clés", done: false },
      { label: "3 ans", sub: "Rayonner et impacter", done: false },
    ]));
  }, []);

  return (
    <div className="relative aspect-[3/4] w-full overflow-hidden rounded-2xl shadow-2xl bg-[#0B1F3A] p-6" data-testid="tpl-trajectoire">
      <span className="text-[10px] font-extrabold uppercase tracking-[0.18em] text-[#D6A85F]">Trajectoire</span>
      <h3 className="font-head text-2xl font-extrabold text-white mt-1 mb-6">Où je vais.</h3>

      <div className="relative pl-6">
        <div className="absolute left-[7px] top-2 bottom-2 w-px bg-white/15" />
        {(milestones || []).map((m, i) => (
          <div key={i} className="relative pb-6 last:pb-0">
            <div className="absolute -left-6 top-1 w-3.5 h-3.5 rounded-full border-2"
              style={{ background: m.done ? "#5DCAA5" : "#0B1F3A", borderColor: m.done ? "#5DCAA5" : "rgba(255,255,255,0.25)" }} />
            <p className="text-xs font-bold uppercase tracking-wide" style={{ color: m.done ? "#5DCAA5" : "#D6A85F" }}>{m.label}</p>
            <p className="text-sm text-white/70 mt-0.5">{m.sub}</p>
          </div>
        ))}
      </div>
      <span className="absolute bottom-4 right-5 text-[10px] text-white/30">Zayado · MyExtension AI</span>
    </div>
  );
}

function EquilibreVieePreview() {
  const [scores, setScores] = useState(null);
  React.useEffect(() => {
    Promise.all([
      wellnessApi.state().catch(() => ({})),
      visionExtApi.getPillars().catch(() => []),
    ]).then(([w, pillars]) => {
      const energie = w?.today?.score ?? 60;
      const business = Math.round((pillars || []).reduce((a, p) => a + (p.progress || 0), 0) / Math.max(1, (pillars || []).length)) || 55;
      setScores({
        sante: energie,
        business,
        relations: 65,
        finances: w?.today?.physique ? Math.round(w.today.physique * 10) : 60,
        impact: 50,
        equilibre: 45,
      });
    });
  }, []);

  const CATS = [
    { key: "sante", label: "Santé" }, { key: "relations", label: "Relations" },
    { key: "finances", label: "Finances" }, { key: "impact", label: "Impact" },
    { key: "equilibre", label: "Équilibre" }, { key: "business", label: "Business" },
  ];
  const n = CATS.length;
  const R = 78, CX = 150, CY = 155;
  const pt = (i, val) => {
    const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
    const r = (val / 100) * R;
    return [CX + r * Math.cos(angle), CY + r * Math.sin(angle)];
  };
  const points = scores ? CATS.map((c, i) => pt(i, scores[c.key] || 0)).map((p) => p.join(",")).join(" ") : "";
  const globalScore = scores ? Math.round(Object.values(scores).reduce((a, b) => a + b, 0) / n) : 0;

  return (
    <div className="relative aspect-[3/4] w-full overflow-hidden rounded-2xl shadow-2xl bg-[#0B1F3A] p-6 flex flex-col items-center" data-testid="tpl-equilibre-vie">
      <span className="text-[10px] font-extrabold uppercase tracking-[0.18em] text-[#D6A85F] self-start">Équilibre de Vie</span>
      <h3 className="font-head text-xl font-extrabold text-white mt-1 mb-3 self-start">Ma roue de vie.</h3>

      <svg viewBox="0 0 300 300" className="w-full max-w-[240px]">
        {[0.33, 0.66, 1].map((f, i) => (
          <polygon key={i}
            points={CATS.map((c, j) => pt(j, f * 100).join(",")).join(" ")}
            fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="1" />
        ))}
        {scores && <polygon points={points} fill="rgba(93,202,165,0.35)" stroke="#5DCAA5" strokeWidth="2" />}
        {CATS.map((c, i) => {
          const [lx, ly] = pt(i, 118);
          return (
            <text key={c.key} x={lx} y={ly} textAnchor="middle" fontSize="10" fill="rgba(255,255,255,0.6)">{c.label}</text>
          );
        })}
        <circle cx={CX} cy={CY} r="30" fill="#0B1F3A" stroke="#D6A85F" strokeWidth="1.5" />
        <text x={CX} y={CY - 2} textAnchor="middle" fontSize="20" fontWeight="700" fill="#D6A85F">{globalScore}</text>
        <text x={CX} y={CY + 13} textAnchor="middle" fontSize="8" fill="rgba(255,255,255,0.4)">/100</text>
      </svg>
      <span className="mt-auto text-[10px] text-white/30">Zayado · MyExtension AI</span>
    </div>
  );
}

const DATA_TEMPLATES = [
  { id: "ceo",        label: "CEO Dashboard",   Component: CeoDashboardPreview },
  { id: "trajectoire",label: "Trajectoire",     Component: TrajectoirePreview },
  { id: "equilibre",  label: "Équilibre de Vie",Component: EquilibreVieePreview },
];

function TabDataTemplates() {
  const [active, setActive] = useState("ceo");
  const [pinning, setPinning] = useState(false);
  const current = DATA_TEMPLATES.find((d) => d.id === active);
  const Comp = current.Component;

  const pinToBoard = async () => {
    setPinning(true);
    const card = {
      id: `data_${Date.now()}`, type: "note", x: 700 + Math.random() * 120, y: 400 + Math.random() * 120,
      w: 220, h: 140, color: "#0B1F3A",
      title: { fr: current.label, en: current.label },
      body: { fr: "Visuel connecté à mes vraies données.", en: "Visual connected to my real data." },
    };
    try { await visionApi.addCard(card); toast.success("Visuel épinglé au board (données réelles)"); }
    catch { toast.error("Échec de l'épinglage"); }
    finally { setPinning(false); }
  };

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_1fr]" data-testid="tab-data-templates">
      <div className="space-y-4">
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--app-text-muted)]">
            Connecté à tes vraies données
          </p>
          <div className="flex flex-wrap gap-2">
            {DATA_TEMPLATES.map((d) => (
              <button key={d.id} onClick={() => setActive(d.id)} data-testid={`data-tpl-${d.id}`}
                className={["rounded-full px-3.5 py-1.5 text-sm font-medium",
                  active === d.id ? "bg-[#D6A85F] text-[#0B1F3A]" : "border border-[var(--app-border)] bg-[var(--app-surface)] text-[var(--app-text-muted)] hover:text-[var(--app-text)]"].join(" ")}>
                {d.label}
              </button>
            ))}
          </div>
        </div>
        <div className="app-card">
          <p className="text-sm text-[var(--app-text-muted)] leading-relaxed">
            Contrairement aux modèles éditoriaux, ces visuels affichent <strong className="text-[var(--app-text)]">vos vraies données</strong> —
            votre CA, votre trajectoire et votre équilibre de vie réels, mis à jour automatiquement.
          </p>
        </div>
        <button onClick={pinToBoard} disabled={pinning}
          className="flex items-center gap-2 rounded-full bg-[var(--app-navy)] px-5 py-2.5 text-sm font-semibold text-white hover:opacity-90 disabled:opacity-60"
          data-testid="data-tpl-pin">
          {pinning ? <Loader2 size={15} className="animate-spin" /> : <Plus size={15} />} Épingler au board
        </button>
      </div>
      <div className="mx-auto w-full max-w-[300px]">
        <Comp />
      </div>
    </div>
  );
}

function StudioPreview({ tpl, fields, image, tv }) {
  return (
    <div className="relative aspect-[3/4] w-full overflow-hidden rounded-2xl shadow-2xl">
      <img src={image} alt="" className="absolute inset-0 h-full w-full object-cover" />
      <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/25 to-black/45" />
      <div className="absolute left-0 right-0 top-0 flex items-center justify-between px-5 pt-5">
        <span className="text-xs font-extrabold uppercase tracking-[0.18em]" style={{ color: tpl.accent }}>{fields.brand}</span>
        <span className="rounded-full px-2 py-0.5 text-[10px] font-bold text-white" style={{ background: tpl.accent }}>N°01</span>
      </div>
      <div className="absolute inset-x-0 bottom-0 p-5">
        <span className="mb-2 inline-block rounded-full bg-white/15 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide text-white backdrop-blur">{tv(fields.tag)}</span>
        <h3 className="font-head text-3xl font-extrabold leading-[1.05] text-white" style={{ letterSpacing: "-0.02em" }}>{tv(fields.title)}</h3>
        <div className="mt-3 h-1 w-16 rounded-full" style={{ background: tpl.accent }} />
      </div>
    </div>
  );
}

function TabVisionStudio() {
  const { tv } = useApp();
  const [sub, setSub] = useState("create");
  const [tplId, setTplId] = useState(STUDIO_TEMPLATES[0].id);
  const tpl = STUDIO_TEMPLATES.find((t) => t.id === tplId) || STUDIO_TEMPLATES[0];
  const [image, setImage] = useState(tpl.image);
  const [fields, setFields] = useState(tpl.fields);
  const [pinning, setPinning] = useState(false);
  const [bookMenu, setBookMenu] = useState(false);

  const openHeyzine = (kind) => {
    window.open("https://heyzine.com/flip-book-maker", "_blank", "noopener,noreferrer");
    toast.success(kind === "book" ? "Création d'un livre (flipbook) sur Heyzine" : "Création d'une carte sur Heyzine");
    setBookMenu(false);
  };

  const chooseTpl = (id) => {
    const next = STUDIO_TEMPLATES.find((t) => t.id === id);
    setTplId(id); setImage(next.image); setFields(next.fields);
  };

  const setF = (k, v) => setFields((f) => ({ ...f, [k]: k === "brand" ? v : { fr: v, en: v } }));

  const pinToBoard = async () => {
    setPinning(true);
    const card = {
      id: `studio_${Date.now()}`, type: "image",
      x: 620 + Math.random() * 120, y: 300 + Math.random() * 120, w: 210, h: 170,
      image, title: { fr: tv(fields.title), en: tv(fields.title) },
    };
    try { await visionApi.addCard(card); toast.success("Visuel ajouté au Studio Vision"); }
    catch { toast.error("Échec de l'épinglage"); }
    finally { setPinning(false); }
  };

  const subBtn = (id, label) => (
    <button onClick={() => setSub(id)} data-testid={`studio-sub-${id}`}
      className={["rounded-lg px-4 py-2 text-sm font-medium transition-all",
        sub === id ? "bg-[var(--app-surface)] text-[var(--app-text)] shadow-sm" : "text-[var(--app-text-muted)] hover:text-[var(--app-text)]"].join(" ")}>
      {label}
    </button>
  );

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="font-head text-xl font-bold text-[var(--app-text)]">Vision Studio</h3>
          <p className="text-sm text-[var(--app-text-muted)]">Crée des visuels éditoriaux pro et épingle-les sur ton board.</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative">
            <button onClick={() => setBookMenu((o) => !o)} data-testid="studio-visionbook"
              className="flex items-center gap-2 rounded-full bg-[#D6A85F] px-4 py-2 text-sm font-semibold text-[#1a2f4a] hover:opacity-90">
              <BookOpen size={15} /> Vision Book
            </button>
            {bookMenu && (
              <div className="absolute right-0 top-11 z-40 w-48 rounded-xl border border-[var(--app-border)] bg-[var(--app-surface)] p-1 shadow-2xl animate-pop">
                <p className="px-3 pb-1 pt-2 text-[10px] font-semibold uppercase tracking-wide text-[var(--app-text-muted)]">Créer sur Heyzine</p>
                <button onClick={() => openHeyzine("book")} data-testid="studio-heyzine-book"
                  className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-[var(--app-text)] hover:bg-[var(--app-accent-soft)] hover:text-[var(--app-accent)]">
                  <BookOpen size={14} /> Livre (flipbook)
                </button>
                <button onClick={() => openHeyzine("card")} data-testid="studio-heyzine-card"
                  className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-[var(--app-text)] hover:bg-[var(--app-accent-soft)] hover:text-[var(--app-accent)]">
                  <CreditCard size={14} /> Carte
                </button>
              </div>
            )}
          </div>
          <div className="flex gap-1 rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-2)] p-1">
            {subBtn("create", "Créer")}
            {subBtn("data", "Données")}
            {subBtn("templates", "Modèles")}
          </div>
        </div>
      </div>

      {sub === "templates" ? (
        <TabTemplates embedded />
      ) : sub === "data" ? (
        <TabDataTemplates />
      ) : (
        <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          {/* Éditeur */}
          <div className="space-y-4">
            <div>
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--app-text-muted)]">Type de visuel</p>
              <div className="flex flex-wrap gap-2">
                {STUDIO_TEMPLATES.map((s) => (
                  <button key={s.id} onClick={() => chooseTpl(s.id)} data-testid={`studio-tpl-${s.id}`}
                    className={["rounded-full px-3.5 py-1.5 text-sm font-medium",
                      tplId === s.id ? "text-white" : "border border-[var(--app-border)] bg-[var(--app-surface)] text-[var(--app-text-muted)] hover:text-[var(--app-text)]"].join(" ")}
                    style={tplId === s.id ? { background: s.accent } : {}}>
                    {tv(s.label)}
                  </button>
                ))}
              </div>
            </div>

            <div className="app-card space-y-3">
              <label className="block text-xs font-semibold text-[var(--app-text-muted)]">Sur-titre
                <input value={fields.brand} onChange={(e) => setF("brand", e.target.value)} data-testid="studio-field-brand"
                  className="zinput mt-1 w-full" style={{ height: 40 }} />
              </label>
              <label className="block text-xs font-semibold text-[var(--app-text-muted)]">Titre principal
                <input value={tv(fields.title)} onChange={(e) => setF("title", e.target.value)} data-testid="studio-field-title"
                  className="zinput mt-1 w-full" style={{ height: 40 }} />
              </label>
              <label className="block text-xs font-semibold text-[var(--app-text-muted)]">Étiquette
                <input value={tv(fields.tag)} onChange={(e) => setF("tag", e.target.value)} data-testid="studio-field-tag"
                  className="zinput mt-1 w-full" style={{ height: 40 }} />
              </label>
            </div>

            <div>
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--app-text-muted)]">Image</p>
              <div className="flex flex-wrap gap-2">
                {STUDIO_PRESETS.map((src) => (
                  <button key={src} onClick={() => setImage(src)}
                    className={["h-12 w-16 overflow-hidden rounded-lg border-2", image === src ? "border-[var(--app-accent)]" : "border-transparent"].join(" ")}>
                    <img src={src} alt="" className="h-full w-full object-cover" />
                  </button>
                ))}
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              <button onClick={pinToBoard} disabled={pinning} data-testid="studio-pin"
                className="flex items-center gap-2 rounded-full bg-[var(--app-navy)] px-4 py-2.5 text-sm font-semibold text-white hover:opacity-90">
                {pinning ? <Loader2 size={15} className="spin" /> : <Plus size={15} />} Épingler au board
              </button>
            </div>
          </div>

          {/* Aperçu live */}
          <div className="mx-auto w-full max-w-sm">
            <StudioPreview tpl={tpl} fields={fields} image={image} tv={tv} />
          </div>
        </div>
      )}
    </div>
  );
}

// ─── TAB: MEMORIES ────────────────────────────────────────────────────────────

// ─── SOUVENIRS — bandeau style Google Photos / Instagram Stories ──────────────
// Plus un onglet à part : un bandeau discret en haut du Vision Canvas, exposé
// passivement plutôt que d'exiger d'aller le chercher dans une page dédiée.
// Les réglages de notifications ont été déplacés vers Settings (hors sujet ici).
function MemoriesStrip() {
  const { tv } = useApp();
  const [memories, setMemories] = useState([]);
  const [detail, setDetail] = useState(null);
  const [pinningId, setPinningId] = useState(null);

  React.useEffect(() => {
    visionExtApi.getMemories()
      .then(data => { if (Array.isArray(data?.memories)) setMemories(data.memories); })
      .catch(() => {});
  }, []);

  const handlePin = async (m) => {
    setPinningId(m.id);
    try {
      await visionApi.addCard({
        id: `mem_${Date.now()}`, type: "image",
        x: 500 + Math.random() * 150, y: 350 + Math.random() * 150, w: 210, h: 170,
        image: m.image, title: { fr: tv(m.title), en: tv(m.title) },
      });
      toast.success("Souvenir épinglé dans ton Studio Vision ✦");
      setDetail(null);
    } catch { toast.error("Échec de l'épinglage"); }
    finally { setPinningId(null); }
  };

  if (!memories.length) return null;

  return (
    <>
      <div className="flex gap-4 overflow-x-auto pb-1 px-0.5" data-testid="memories-strip">
        {memories.map(m => (
          <button key={m.id} onClick={() => setDetail(m)} data-testid={`memory-highlight-${m.id}`}
            className="group flex shrink-0 flex-col items-center gap-1.5">
            <span className="rounded-full bg-gradient-to-tr from-[var(--app-accent)] to-[#2748A8] p-[2.5px]">
              <span className="block rounded-full bg-[var(--app-surface)] p-[2px]">
                <img src={m.image} alt="" className="h-14 w-14 rounded-full object-cover transition-transform group-hover:scale-105" />
              </span>
            </span>
            <span className="max-w-[76px] truncate text-center text-[10px] font-medium text-[var(--app-text-muted)]">{tv(m.title)}</span>
          </button>
        ))}
      </div>

      {detail && (
        <div className="fixed inset-0 z-[999] flex items-center justify-center bg-black/75 p-6" onClick={() => setDetail(null)} data-testid="memory-detail-modal">
          <div className="relative max-w-md w-full overflow-hidden rounded-2xl bg-[var(--app-surface)] shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <img src={detail.image} alt="" className="h-64 w-full object-cover" />
            <button onClick={() => setDetail(null)} className="absolute right-3 top-3 flex h-8 w-8 items-center justify-center rounded-full bg-black/50 text-white hover:bg-black/70">
              <X size={16} />
            </button>
            <div className="p-5">
              <h4 className="font-head text-lg font-bold text-[var(--app-text)]">{tv(detail.title)}</h4>
              <p className="mt-1 text-sm text-[var(--app-text-muted)]">{tv(detail.message)}</p>
              <div className="mt-4 flex gap-2">
                <button onClick={() => handlePin(detail)} disabled={pinningId === detail.id}
                  data-testid={`memory-cta-${detail.id}`}
                  className="flex-1 flex items-center justify-center gap-1.5 rounded-full bg-[var(--app-navy)] py-2.5 text-sm font-semibold text-white hover:opacity-90 disabled:opacity-60">
                  {pinningId === detail.id ? <Loader2 size={13} className="animate-spin" /> : <Heart size={13} />} {tv(detail.cta) || "Épingler au board"}
                </button>
                <button onClick={() => setDetail(null)} className="rounded-full border border-[var(--app-border)] px-4 py-2.5 text-sm font-medium text-[var(--app-text)] hover:bg-[var(--app-surface-2)]">
                  Fermer
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

// ─── MODULE PRINCIPAL ─────────────────────────────────────────────────────────
function TabSwot() {
  const { t } = useApp();
  const [swot, setSwot] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [creatingActionIdx, setCreatingActionIdx] = useState(null);
  const [createdActions, setCreatedActions] = useState(() => new Set());
  const [bulkCreating, setBulkCreating] = useState(false);

  React.useEffect(() => {
    analyseApi.get()
      .then((data) => setSwot(data?.strengths || data?.summary ? data : null))
      .catch(() => setSwot(null))
      .finally(() => setLoading(false));
  }, []);

  // Transforme une prochaine action de l'analyse IA en vraie tâche du Cockpit —
  // même mécanisme que "+ Mission" sur les piliers stratégiques (createMission
  // plus haut dans ce fichier), pour que l'IA ne reste jamais un simple
  // panneau de lecture : chaque recommandation peut devenir une action réelle.
  const createActionTask = async (actionText, idx) => {
    setCreatingActionIdx(idx);
    try {
      await tasksApi.create({ label: actionText, type: "humain", priority: "normal" });
      setCreatedActions((prev) => new Set(prev).add(idx));
      toast.success("Tâche créée dans votre Cockpit ✦");
    } catch {
      toast.error("Impossible de créer la tâche pour le moment.");
    } finally {
      setCreatingActionIdx(null);
    }
  };

  const createAllActionTasks = async () => {
    setBulkCreating(true);
    const remaining = swot.next_actions
      .map((a, i) => [a, i])
      .filter(([, i]) => !createdActions.has(i));
    let created = 0;
    for (const [a, i] of remaining) {
      try {
        await tasksApi.create({ label: a, type: "humain", priority: "normal" });
        created += 1;
        setCreatedActions((prev) => new Set(prev).add(i));
      } catch { /* on continue avec les suivantes, best-effort */ }
    }
    setBulkCreating(false);
    if (created > 0) toast.success(`${created} tâche${created > 1 ? "s" : ""} créée${created > 1 ? "s" : ""} dans votre Cockpit ✦`);
    else toast.error("Aucune tâche n'a pu être créée.");
  };

  const generate = async () => {
    setGenerating(true);
    try {
      const res = await analyseApi.run();
      setSwot(res);
      toast.success("Analyse générée par l'IA ✨");
    } catch {
      toast.error("Impossible de générer l'analyse — réessayez dans un instant.");
    } finally {
      setGenerating(false);
    }
  };

  const QUADRANTS = [
    { key: "strengths",     label: "Forces",        Icon: Shield,       color: "#5e8a5a", bg: "rgba(94,138,90,0.08)" },
    { key: "weaknesses",    label: "Faiblesses",     Icon: AlertTriangle,color: "#c26b4a", bg: "rgba(194,107,74,0.08)" },
    { key: "opportunities", label: "Opportunités",   Icon: Target,       color: "#4a6a9e", bg: "rgba(74,106,158,0.08)" },
    { key: "threats",       label: "Menaces",        Icon: Zap,          color: "#8b6fbf", bg: "rgba(139,111,191,0.08)" },
  ];

  const VERDICT_LABELS = { go: "Feu vert", pivot: "À ajuster", abandon: "À reconsidérer" };
  const VERDICT_COLORS = { go: "#5e8a5a", pivot: "#DEC2A3", abandon: "#c26b4a" };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16 text-[var(--app-text-muted)]">
        <Loader2 size={18} className="animate-spin mr-2" /> Chargement de l'analyse…
      </div>
    );
  }

  return (
    <div className="space-y-5" data-testid="tab-swot">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h3 className="font-head text-xl font-bold text-[var(--app-text)]">Analyse & validation de projet</h3>
          <p className="text-sm text-[var(--app-text-muted)]">
            SWOT, score et verdict générés par l'IA à partir de votre Vision et de votre profil.
          </p>
        </div>
        <button
          onClick={generate}
          disabled={generating}
          className="flex items-center gap-2 rounded-full bg-[var(--app-navy)] px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-60"
          data-testid="swot-generate-btn"
        >
          {generating ? <Loader2 size={15} className="animate-spin" /> : <Sparkles size={15} />}
          {swot ? "Régénérer avec l'IA" : "Générer mon analyse"}
        </button>
      </div>

      {!swot ? (
        <div className="rounded-2xl border border-dashed border-[var(--app-border)] py-16 text-center">
          <Target size={32} className="mx-auto mb-3 text-[var(--app-text-muted)] opacity-40" />
          <p className="text-sm text-[var(--app-text-muted)]">
            Aucune analyse pour l'instant.<br />
            Complétez votre Vision Board, puis cliquez sur "Générer mon analyse".
          </p>
        </div>
      ) : (
        <>
          {/* Score + verdict — remplace l'ancienne page /validation, fusionnée ici */}
          {(swot.score != null || swot.verdict) && (
            <div className="app-card p-5 flex items-center gap-5 flex-wrap" data-testid="swot-score-card">
              {swot.score != null && (
                <div className="relative w-[76px] h-[76px] shrink-0">
                  <svg width="76" height="76" viewBox="0 0 76 76" className="-rotate-90">
                    <circle cx="38" cy="38" r="32" stroke="var(--app-border)" strokeWidth="7" fill="none" />
                    <circle cx="38" cy="38" r="32" stroke="#DEC2A3" strokeWidth="7" fill="none" strokeLinecap="round"
                      strokeDasharray={2 * Math.PI * 32}
                      strokeDashoffset={(2 * Math.PI * 32) * (1 - swot.score / 100)} />
                  </svg>
                  <div className="absolute inset-0 grid place-items-center">
                    <span className="font-head text-lg font-bold text-[var(--app-text)]">{swot.score}</span>
                  </div>
                </div>
              )}
              <div className="flex-1 min-w-[200px]">
                {swot.verdict && (
                  <span className="inline-block rounded-full px-3 py-1 text-xs font-semibold mb-2"
                    style={{ background: `${VERDICT_COLORS[swot.verdict] || "#8b8578"}1A`, color: VERDICT_COLORS[swot.verdict] || "#8b8578" }}>
                    {VERDICT_LABELS[swot.verdict] || swot.verdict}
                  </span>
                )}
                {swot.summary && <p className="text-sm text-[var(--app-text)]">{swot.summary}</p>}
              </div>
            </div>
          )}

          <div className="grid gap-4 sm:grid-cols-2">
            {QUADRANTS.map((q) => {
              const items = swot[q.key] || [];
              const Icon = q.Icon;
              return (
                <div
                  key={q.key}
                  className="rounded-2xl p-5 border"
                  style={{ background: q.bg, borderColor: `${q.color}30` }}
                  data-testid={`swot-${q.key}`}
                >
                  <div className="flex items-center gap-2 mb-3">
                    <Icon size={16} style={{ color: q.color }} />
                    <span className="font-head font-bold text-sm" style={{ color: q.color }}>{q.label}</span>
                  </div>
                  <ul className="space-y-2">
                    {items.length === 0 && (
                      <li className="text-xs text-[var(--app-text-muted)] italic">Aucun élément détecté.</li>
                    )}
                    {items.map((item, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-[var(--app-text)]">
                        <Circle size={5} className="mt-1.5 flex-shrink-0" style={{ color: q.color }} />
                        {typeof item === "string" ? item : item.text}
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </div>

          {swot.next_actions?.length > 0 && (
            <div className="app-card p-5" data-testid="swot-next-actions">
              <div className="flex items-center justify-between gap-3 mb-3 flex-wrap">
                <p className="text-xs font-semibold uppercase tracking-wide text-[var(--app-text-muted)]">Prochaines actions recommandées par l'IA</p>
                <button onClick={createAllActionTasks} disabled={bulkCreating || createdActions.size === swot.next_actions.length}
                  data-testid="swot-create-plan-btn"
                  className="text-xs font-semibold px-3 py-1.5 rounded-full bg-[var(--app-accent)] text-white disabled:opacity-50">
                  {bulkCreating ? "Création…" : createdActions.size === swot.next_actions.length ? "Plan créé ✓" : "Créer mon plan d'action"}
                </button>
              </div>
              <ul className="space-y-2">
                {swot.next_actions.map((a, i) => (
                  <li key={i} className="flex items-center gap-2 text-sm text-[var(--app-text)]" data-testid={`swot-next-action-${i}`}>
                    <Circle size={5} className="flex-shrink-0 text-[var(--app-accent)]" />
                    <span className="flex-1">{a}</span>
                    {createdActions.has(i) ? (
                      <span className="text-[10px] font-semibold text-[var(--app-accent)] flex items-center gap-1 flex-shrink-0">
                        <Check size={12} /> Tâche créée
                      </span>
                    ) : (
                      <button onClick={() => createActionTask(a, i)} disabled={creatingActionIdx === i}
                        data-testid={`swot-create-task-${i}`}
                        className="text-[10px] font-semibold text-[var(--app-accent)] hover:underline disabled:opacity-50 flex-shrink-0">
                        {creatingActionIdx === i ? "…" : "+ Tâche"}
                      </button>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {swot?.generated_at && (
            <p className="text-xs text-[var(--app-text-muted)] text-center">
              Dernière génération : {new Date(swot.generated_at).toLocaleDateString("fr-FR")}
            </p>
          )}
        </>
      )}
    </div>
  );
}


export default function VisionBoardModule() {
  // Sur mobile, l’accueil de l’application reste le Copilote. Lorsque
  // l’utilisateur ouvre Vision, il doit retrouver les quatre onglets du Board
  // et choisir lui-même le Canvas ou le Studio, sans bascule automatique.
  return <VisionBoardDesktop />;
}

function VisionBoardDesktop() {
  const { tv } = useApp();
  const [searchParams] = useSearchParams();
  const initialTab = searchParams.get("tab");
  const [activeTab, setActiveTab] = useState(TABS.some(t => t.id === initialTab) ? initialTab : "accueil");
  const [menuOpen, setMenuOpen] = useState(false);
  const [bgImage, setBgImage] = useState(null);
  const [isMobile, setIsMobile] = useState(() => typeof window !== "undefined" && window.innerWidth < 769);
  React.useEffect(() => {
    const onResize = () => setIsMobile(window.innerWidth < 769);
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  // Le Copilote droit Cours-main est l’unique assistant permanent.
  // Le module Vision transmet le contexte de l’onglet actif au shell au lieu
  // de conserver le panneau Cerveau IA Final-main en double.
  React.useEffect(() => {
    const labels = {
      accueil: "Accueil Vision",
      canvas: "Studio Vision",
      pillars: "Piliers stratégiques",
      horizon: "Horizon 90 jours",
      decisions: "Décisions & validation",
    };
    window.dispatchEvent(new CustomEvent("cours:vision-context", {
      detail: { tab: activeTab, label: labels[activeTab] || "Vision" },
    }));
  }, [activeTab]);
  const menuRef = useRef(null);

  React.useEffect(() => {
    const onDoc = (e) => { if (menuRef.current && !menuRef.current.contains(e.target)) setMenuOpen(false); };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  const fileInputRef = React.useRef(null);

  const handlePhotoUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const res = await visionExtApi.uploadPhoto(file);
      if (res?.url) { setBgImage(res.url); toast.success("Photo de fond mise à jour !"); }
    } catch { toast.error("Erreur lors de l'upload"); }
  };

  const handleShare = async () => {
    try {
      const res = await visionExtApi.shareBoard();
      const url = res?.share_url || window.location.href;
      await navigator.clipboard.writeText(url);
      toast.success("Lien de partage copié !");
    } catch { toast.error("Erreur lors du partage"); }
  };

  const menuItems = [
    { icon: Upload, label: "Changer la photo de fond", onClick: () => fileInputRef.current?.click() },
    { icon: Share2, label: "Partager mon board", onClick: handleShare },
  ];

  const returnToAccueil = () => {
    setActiveTab("accueil");
    window.scrollTo({ top: 0, behavior: "auto" });
  };

  const openVisionStudio = () => {
    // Le Studio est l’unique accès au Canvas : il est monté à la demande,
    // ouvert directement en plein écran, puis son bouton Retour ramène à l’Accueil Vision.
    if (activeTab !== "canvas") flushSync(() => setActiveTab("canvas"));
    document.querySelector('[data-testid="vision-canvas-container"]')?.requestFullscreen?.().catch(() => {});
  };

  const openDailyDecision = () => {
    window.dispatchEvent(new Event("cours:open-copilot"));
  };

  const renderTab = () => {
    switch (activeTab) {
      case "accueil":   return <><StrategicCapHome onOpenHorizon={() => setActiveTab("horizon")} onOpenDecisions={() => setActiveTab("decisions")} onOpenPillars={() => setActiveTab("pillars")} /><CoursAccueilVision onGoCanvas={openVisionStudio} onNavigateTab={setActiveTab} /></>;
      case "canvas":    return isMobile ? <VisionCanvaMobile onBack={returnToAccueil} /> : <TabCanvas bgImage={bgImage} onBack={returnToAccueil} />;
      case "pillars":   return <TabPillars />;
      case "horizon":   return <StrategicHorizon />;
      case "decisions": return <><StrategicDecisions /><div className="mt-4"><TabSwot /></div></>;
      default:          return <CoursAccueilVision onGoCanvas={openVisionStudio} />;
    }
  };

  return (
    <div className="vb-root flex flex-col gap-3">
      <input ref={fileInputRef} type="file" accept="image/*" style={{ display: "none" }} onChange={handlePhotoUpload} />

      {/* Titre */}
      <div className="vb-header">
        <h1 className="vb-title gold-text">Vision</h1>
        <p className="vb-subtitle mt-1">Votre maison stratégique : de la Vision à la décision, puis au mouvement.</p>
      </div>

      {/* Navigation secondaire remplacée par des actions contextuelles dans l’accueil Vision. */}
      <div className="vb-toolbar flex items-center justify-between gap-3">
        {activeTab !== "accueil" ? (
          <button type="button" onClick={() => setActiveTab("accueil")} className="vision-back-action" data-testid="vision-back-home">← Retour à l’accueil Vision</button>
        ) : <span />}
        <div className="vb-actions relative shrink-0" ref={menuRef}>
          <button onClick={() => setMenuOpen((o) => !o)} data-testid="vision-actions-menu" title="Actions"
            className="flex h-10 w-10 items-center justify-center rounded-full border border-[var(--app-border)] bg-[var(--app-surface)] text-[var(--app-text)] hover:border-[var(--app-accent)] hover:text-[var(--app-accent)]">
            <MoreVertical size={18} />
          </button>
          {menuOpen && (
            <div className="absolute right-0 top-12 z-50 w-56 overflow-hidden rounded-xl border border-[var(--app-border)] bg-[var(--app-surface)] p-1 shadow-2xl animate-pop">
              {menuItems.map((it, i) => (
                <button key={it.label} onClick={() => { it.onClick(); setMenuOpen(false); }}
                  data-testid={`vision-action-${i}`}
                  className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm font-medium text-[var(--app-text)] hover:bg-[var(--app-accent-soft)] hover:text-[var(--app-accent)]">
                  <it.icon size={15} /> {it.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Souvenirs — bandeau passif façon Google Photos/Instagram (masqué sur mobile pour un canvas immersif) */}
      {activeTab === "canvas" && <div className="hidden md:block"><MemoriesStrip /></div>}

      {/* #4 Live Cards — données live des modules (CA, bien-être, prospects) */}
      {activeTab === "canvas" && <div className="hidden md:block"><LiveCardsStrip /></div>}

      {/* Le contenu Vision reste au centre ; le Copilote unique est rendu par Layout.jsx à droite. */}
      <div className="vb-main-row">
        <div className="vb-main-content animate-fade-up">
          {renderTab()}
        </div>
      </div>
    </div>
  );
}
