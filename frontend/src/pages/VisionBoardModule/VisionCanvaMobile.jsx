import React, { useState, useEffect, useRef, useCallback } from "react";
import { createPortal } from "react-dom";
import { useNavigate } from "react-router-dom";
import {
  ChevronLeft, Share2, Plus, MoreHorizontal, Sparkles, X, Send, Loader2,
  Trash2, Copy, Palette, Type, Target, Image as ImageIcon, Search, ListChecks,
  FileText, Check, FileDown, Wand2, RotateCcw, Maximize2, Bell, BellOff,
  LayoutTemplate, PlusCircle,
} from "lucide-react";
import { toast } from "sonner";
import { useApp } from "./useApp";
import { visionApi, visionExtApi, studioApi } from "../../lib/finalVisionModuleApi";

const backendBase = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");
const fullUrl = (u) => (!u ? u : u.startsWith("http") || u.startsWith("data:") ? u : `${backendBase}${u}`);
const uid = () => `${Date.now()}_${Math.floor(Math.random() * 9999)}`;

// Palette cohérente charte Zayado (marine / or / sable / vert / terracotta / ardoise)
const SWATCHES = ["#0a1f4e", "#DEC2A3", "#d8c9a3", "#3f7d63", "#c26b4a", "#4a6a9e", "#2a2f45", "#8a5a83"];

const BOARD_W = 1400, BOARD_H = 2600;

function cleanError(e, fallback) {
  const d = e?.response?.data?.detail;
  if (typeof d === "string" && d.length < 160 && !/<[a-z!]/i.test(d)) return d;
  return fallback;
}

// ─── Rendu d'une carte ─────────────────────────────────────────
function Card({ card, tv, selected, onSelect, onPointerDown, onToggleObjective, onEdit }) {
  const title = tv(card.title);
  const body = tv(card.body);
  const bg = card.color || "var(--app-surface)";
  return (
    <div
      data-testid={`m-card-${card.id}`}
      onPointerDown={(e) => onPointerDown(e, card)}
      onClick={(e) => { e.stopPropagation(); onSelect(card.id); }}
      onDoubleClick={() => (card.type === "note" || card.type === "ai-doc" || card.type === "objective") && onEdit(card)}
      className={[
        "absolute overflow-hidden rounded-2xl shadow-lg text-[var(--app-text)] transition-[box-shadow,transform] duration-150",
        selected ? "ring-2 ring-[var(--app-accent)] ring-offset-2 ring-offset-[var(--app-navy)] z-30" : "z-10",
      ].join(" ")}
      style={{ left: card.x, top: card.y, width: card.w || 240, touchAction: "none" }}
    >
      {card.type === "image" && <img src={fullUrl(card.image)} alt="" className="w-full object-cover" draggable={false} />}
      {card.type === "video" && <video src={fullUrl(card.video)} muted loop playsInline className="w-full bg-black object-cover" />}

      {card.type === "color" ? (
        <div className="bg-[var(--app-surface)] p-3">
          <p className="mb-2 text-xs font-semibold text-[var(--app-text-muted)]">{title || "Palette"}</p>
          <div className="flex gap-2">
            {(card.colors || SWATCHES.slice(0, 4)).map((c, i) => (
              <div key={i} className="h-12 flex-1 rounded-lg" style={{ background: c }} />
            ))}
          </div>
        </div>
      ) : (title || body || card.type === "objective") && (
        <div className="p-4" style={{ background: card.type === "note" ? bg : "var(--app-surface)" }}>
          {card.type === "ai-doc" && (
            <span className="mb-2 inline-flex items-center gap-1 rounded-full bg-[var(--app-accent-soft)] px-2 py-0.5 text-[9px] font-bold uppercase tracking-wide text-[var(--app-accent)]"><FileText size={9} /> Doc IA</span>
          )}
          {card.type === "objective" && (
            <span className="mb-2 inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[9px] font-bold uppercase tracking-wide text-white" style={{ background: card.color || "#DEC2A3" }}><Target size={9} /> Objectif</span>
          )}
          {title && <p className={`font-head text-[15px] font-semibold leading-snug ${card.type === "note" && card.color ? "text-white" : "text-[var(--app-text)]"}`}>{title}</p>}
          {body && <p className={`mt-1 whitespace-pre-wrap text-[13px] leading-relaxed ${card.type === "note" && card.color ? "text-white/80" : "text-[var(--app-text-muted)]"}`}>{body}</p>}
          {card.type === "objective" && Array.isArray(card.checklist) && (
            <div className="mt-3 space-y-1.5">
              {card.checklist.map((it, i) => (
                <button key={i} onClick={(e) => { e.stopPropagation(); onToggleObjective(card.id, i); }} className="flex w-full items-start gap-2 text-left">
                  <span className={`mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full border-2 ${it.done ? "border-[var(--app-accent)] bg-[var(--app-accent)] text-[var(--app-navy)]" : "border-[var(--app-border)]"}`}>{it.done && <Check size={10} />}</span>
                  <span className={`text-[13px] ${it.done ? "text-[var(--app-text-muted)] line-through" : "text-[var(--app-text)]"}`}>{tv(it.text)}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Bottom sheet générique ────────────────────────────────────
function Sheet({ open, onClose, title, children }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-[240] flex items-end" data-testid="m-sheet">
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full rounded-t-3xl border-t border-[var(--app-accent)]/20 bg-[var(--app-surface)] p-5 pb-[calc(1.25rem+env(safe-area-inset-bottom))] animate-[sheetUp_0.28s_cubic-bezier(0.16,1,0.3,1)]" style={{ maxHeight: "80vh", overflowY: "auto" }}>
        <div className="mx-auto mb-4 h-1 w-10 rounded-full bg-[var(--app-border)]" />
        {title && <p className="mb-3 font-head text-lg font-semibold text-[var(--app-text)]">{title}</p>}
        {children}
      </div>
    </div>
  );
}

// ─── Chat / Ask AI plein écran ─────────────────────────────────
const AI_MODES = [
  { id: "board", label: "Vision complète", icon: Wand2 },
  { id: "image", label: "Image IA", icon: ImageIcon },
  { id: "note", label: "Document", icon: FileText },
];

function AskAI({ open, onClose, onCards }) {
  const [prompt, setPrompt] = useState("");
  const [mode, setMode] = useState("board");
  const [loading, setLoading] = useState(false);
  const [log, setLog] = useState([]);
  const inputRef = useRef(null);
  useEffect(() => { if (open) setTimeout(() => inputRef.current?.focus(), 250); }, [open]);

  const submit = async () => {
    const v = prompt.trim();
    if (v.length < 3) return toast.error("Décris ton idée en quelques mots.");
    setLoading(true); setLog((l) => [...l, { role: "user", text: v }]); setPrompt("");
    try {
      if (mode === "board") {
        const res = await visionExtApi.generateFromPrompt(v);
        const cards = (res.cards || []).map((c) => ({ ...c, id: uid() }));
        if (!cards.length) throw new Error("empty");
        onCards(cards); setLog((l) => [...l, { role: "ai", text: `✦ ${cards.length} élément(s) posé(s) sur ton canvas.` }]);
        toast.success(`${cards.length} élément(s) ajouté(s) ✨`);
        setTimeout(onClose, 700);
      } else if (mode === "image") {
        const res = await studioApi.generateImage(v, "custom");
        if (!res?.url) throw new Error("empty");
        onCards([{ id: uid(), type: "image", image: res.url, w: 260, title: { fr: v.slice(0, 40), en: v.slice(0, 40) } }]);
        setLog((l) => [...l, { role: "ai", text: "✦ Image générée et ajoutée au canvas." }]);
        toast.success("Image IA ajoutée ✦"); setTimeout(onClose, 700);
      } else {
        const res = await visionApi.generateDoc(v, mode);
        if (!res?.content) throw new Error("empty");
        onCards([{ id: uid(), type: "ai-doc", w: 260, title: { fr: res.title, en: res.title }, body: { fr: res.content, en: res.content } }]);
        setLog((l) => [...l, { role: "ai", text: `✦ Document « ${res.title} » ajouté.` }]);
        toast.success("Document IA ajouté ✦"); setTimeout(onClose, 700);
      }
    } catch (e) {
      const msg = cleanError(e, "Génération impossible — réessaie dans un instant.");
      setLog((l) => [...l, { role: "ai", text: `⚠︎ ${msg}` }]); toast.error(msg);
    } finally { setLoading(false); }
  };

  return createPortal(
    <div data-testid="m-askai" className={["vb-tokens fixed inset-0 z-[260] flex flex-col bg-[var(--app-navy)] transition-transform duration-300", open ? "translate-y-0" : "translate-y-full pointer-events-none"].join(" ")} style={{ transitionTimingFunction: "cubic-bezier(0.16,1,0.3,1)" }}>
      <div className="flex items-center justify-between border-b border-[var(--app-accent)]/20 px-4 py-3.5 pt-[calc(0.875rem+env(safe-area-inset-top))]">
        <div className="flex items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[var(--app-accent)] text-[var(--app-navy)]"><Sparkles size={17} /></span>
          <div><p className="font-head text-base font-semibold text-white">Ask AI</p><p className="text-[11px] text-white/55">Décris, l'IA crée ta vision</p></div>
        </div>
        <button onClick={onClose} data-testid="m-askai-close" className="flex h-9 w-9 items-center justify-center rounded-full bg-white/10 text-white active:scale-90"><X size={18} /></button>
      </div>
      <div className="flex-1 space-y-3 overflow-y-auto px-4 py-5">
        {log.length === 0 && (
          <div className="mx-auto mt-6 max-w-xs text-center">
            <span className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-[var(--app-accent-soft)] text-[var(--app-accent)]"><Wand2 size={24} /></span>
            <p className="font-head text-lg font-semibold text-white">Que veux-tu créer&nbsp;?</p>
            <p className="mt-1.5 text-sm text-white/60">« Cabinet de conseil pour dirigeants, lancement Q2 » — l'IA génère ta vision, tes piliers et tes premières cartes.</p>
          </div>
        )}
        {log.map((m, i) => (
          <div key={i} className={m.role === "user" ? "flex justify-end" : "flex justify-start"}>
            <div className={["max-w-[82%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed", m.role === "user" ? "bg-[var(--app-accent)] font-medium text-[var(--app-navy)]" : "bg-white/10 text-white/90"].join(" ")}>{m.text}</div>
          </div>
        ))}
        {loading && <div className="flex justify-start"><div className="flex items-center gap-2 rounded-2xl bg-white/10 px-3.5 py-2.5 text-sm text-white/80"><Loader2 size={14} className="animate-spin" /> L'IA réfléchit…</div></div>}
      </div>
      <div className="border-t border-[var(--app-accent)]/20 px-3 pb-[calc(0.75rem+env(safe-area-inset-bottom))] pt-3">
        <div className="mb-2.5 flex gap-1.5 overflow-x-auto pb-1" style={{ scrollbarWidth: "none" }}>
          {AI_MODES.map((q) => (
            <button key={q.id} onClick={() => setMode(q.id)} data-testid={`m-askai-mode-${q.id}`} className={["flex shrink-0 items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium transition", mode === q.id ? "border-[var(--app-accent)] bg-[var(--app-accent)] text-[var(--app-navy)]" : "border-white/20 text-white/70"].join(" ")}><q.icon size={13} /> {q.label}</button>
          ))}
        </div>
        <div className="flex items-end gap-2 rounded-2xl border border-white/15 bg-white/5 p-1.5">
          <textarea ref={inputRef} value={prompt} onChange={(e) => setPrompt(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submit(); } }} rows={1} placeholder="Décris ce que l'IA doit créer…" data-testid="m-askai-input" className="max-h-28 flex-1 resize-none bg-transparent px-2.5 py-2 text-sm text-white outline-none placeholder:text-white/40" />
          <button onClick={submit} disabled={loading || !prompt.trim()} data-testid="m-askai-send" className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[var(--app-accent)] text-[var(--app-navy)] active:scale-90 disabled:opacity-40">{loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}</button>
        </div>
      </div>
    </div>, document.body);
}

// ─── Edit sheet (note / doc / objectif) ────────────────────────
function EditSheet({ card, onClose, onSave }) {
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  useEffect(() => {
    if (card) {
      const t = card.title; setTitle(typeof t === "object" ? (t?.fr || "") : (t || ""));
      const b = card.body; setBody(typeof b === "object" ? (b?.fr || "") : (b || ""));
    }
  }, [card]);
  return (
    <Sheet open={!!card} onClose={onClose} title="Modifier la carte">
      <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Titre" data-testid="m-edit-title" className="mb-3 w-full rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-2)] px-3 py-2.5 text-sm text-[var(--app-text)] outline-none focus:border-[var(--app-accent)]" />
      <textarea value={body} onChange={(e) => setBody(e.target.value)} placeholder="Contenu" rows={5} data-testid="m-edit-body" className="mb-4 w-full resize-none rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-2)] px-3 py-2.5 text-sm text-[var(--app-text)] outline-none focus:border-[var(--app-accent)]" />
      <button onClick={() => { onSave({ title: { fr: title, en: title }, body: { fr: body, en: body } }); onClose(); }} data-testid="m-edit-save" className="w-full rounded-full bg-[var(--app-accent)] py-3 text-sm font-semibold text-[var(--app-navy)] active:scale-95">Enregistrer</button>
    </Sheet>
  );
}

// ─── Composant principal ───────────────────────────────────────
export default function VisionCanvaMobile({ onBack }) {
  const { tv } = useApp();
  const navigate = useNavigate();
  const [cards, setCards] = useState([]);
  const [loaded, setLoaded] = useState(false);
  const [selected, setSelected] = useState(null);
  const [aiOpen, setAiOpen] = useState(false);
  const [addOpen, setAddOpen] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);
  const [paletteFor, setPaletteFor] = useState(null);
  const [photoQuery, setPhotoQuery] = useState("");
  const [imgPrompt, setImgPrompt] = useState("");
  const [busy, setBusy] = useState(false);
  const [editCard, setEditCard] = useState(null);
  const [zoom, setZoom] = useState(1);
  const zoomRef = useRef(1);
  useEffect(() => { zoomRef.current = zoom; }, [zoom]);
  const [coachOpen, setCoachOpen] = useState(false);
  const [coachLoading, setCoachLoading] = useState(false);
  const [coachData, setCoachData] = useState(null);
  // ── Rappels Doux (opt-in weekly email) ──
  const [notifSettings, setNotifSettings] = useState({ weekly_reminder: true, include_coach_actions: true });
  // ── Modèles de Départ (starter templates) ──
  const [templatesOpen, setTemplatesOpen] = useState(false);
  const [starterTemplates, setStarterTemplates] = useState([]);
  const [templatesLoading, setTemplatesLoading] = useState(false);
  const scrollRef = useRef(null);
  const dragRef = useRef(null);
  const [dragId, setDragId] = useState(null);

  useEffect(() => {
    visionApi.getBoard().then((r) => setCards(Array.isArray(r.cards) ? r.cards.map((c) => ({ ...c, id: c.id || uid() })) : [])).catch(() => setCards([])).finally(() => setLoaded(true));
  }, []);

  // Charge les préférences de rappel (opt-in / opt-out)
  useEffect(() => {
    visionExtApi.getNotifSettings().then((r) => {
      if (r?.settings) setNotifSettings((s) => ({ ...s, ...r.settings }));
    }).catch(() => {});
  }, []);
  useEffect(() => {
    if (!loaded) return;
    const t = setTimeout(() => visionApi.saveBoard(cards).catch(() => {}), 600);
    return () => clearTimeout(t);
  }, [cards, loaded]);

  // Centre la vue sur le barycentre d'une liste de cartes (en tenant compte du zoom)
  const focusCards = useCallback((list) => {
    const el = scrollRef.current;
    if (!el || !list || !list.length) return;
    const xs = list.map((c) => c.x || 0), ys = list.map((c) => c.y || 0);
    const cx = (Math.min(...xs) + Math.max(...xs)) / 2 + 120;
    const cy = (Math.min(...ys) + Math.max(...ys)) / 2 + 90;
    const z = zoomRef.current;
    el.scrollTo({ left: Math.max(0, cx * z - el.clientWidth / 2), top: Math.max(0, cy * z - el.clientHeight / 2), behavior: "smooth" });
  }, []);

  // Au chargement : cadrer sur le contenu existant
  const didInitScroll = useRef(false);
  useEffect(() => {
    if (loaded && !didInitScroll.current && cards.length) {
      didInitScroll.current = true;
      setTimeout(() => focusCards(cards), 150);
    }
  }, [loaded, cards, focusCards]);

  // Placement en cascade au centre du viewport courant (coordonnées board = écran / zoom)
  const cascadeRef = useRef(0);
  const centerPos = useCallback(() => {
    const el = scrollRef.current;
    const z = zoomRef.current;
    const i = cascadeRef.current++ % 6;
    const x = ((el?.scrollLeft || 0) + (el?.clientWidth || 360) / 2) / z - 110 + i * 26;
    const y = ((el?.scrollTop || 0) + (el?.clientHeight || 600) / 2) / z - 70 + i * 26;
    return { x: Math.max(20, Math.min(BOARD_W - 260, x)), y: Math.max(20, Math.min(BOARD_H - 200, y)) };
  }, []);

  const addCards = useCallback((newCards) => {
    const withPos = newCards.map((c) => (c.x != null ? c : { ...c, ...centerPos() }));
    setCards((prev) => [...prev, ...withPos]);
    setTimeout(() => focusCards(withPos), 130);
  }, [centerPos, focusCards]);

  const patchCard = useCallback((id, patch) => setCards((p) => p.map((c) => (c.id === id ? { ...c, ...patch } : c))), []);
  const deleteCard = useCallback((id) => { setCards((p) => p.filter((c) => c.id !== id)); setSelected(null); toast("Carte supprimée"); }, []);
  const duplicateCard = useCallback((id) => setCards((p) => {
    const c = p.find((x) => x.id === id); if (!c) return p;
    return [...p, { ...c, id: uid(), x: (c.x || 40) + 24, y: (c.y || 40) + 24 }];
  }), []);
  const toggleObjective = useCallback((id, idx) => setCards((p) => p.map((c) => {
    if (c.id !== id || !Array.isArray(c.checklist)) return c;
    const checklist = c.checklist.map((it, i) => (i === idx ? { ...it, done: !it.done } : it));
    return { ...c, checklist, progress: Math.round((checklist.filter((x) => x.done).length / checklist.length) * 100) };
  })), []);

  // drag tactile
  const onCardPointerDown = useCallback((e, card) => {
    if (e.target.closest("button")) return; // laisser les checkbox/objectifs
    dragRef.current = { id: card.id, sx: e.clientX, sy: e.clientY, ox: card.x || 0, oy: card.y || 0, moved: false };
    setDragId(card.id);
    try { e.currentTarget.setPointerCapture?.(e.pointerId); } catch {}
  }, []);
  useEffect(() => {
    const move = (e) => {
      const d = dragRef.current; if (!d) return;
      const z = zoomRef.current || 1;
      const dx = (e.clientX - d.sx) / z, dy = (e.clientY - d.sy) / z;
      if (Math.abs(e.clientX - d.sx) > 3 || Math.abs(e.clientY - d.sy) > 3) d.moved = true;
      setCards((p) => p.map((c) => c.id === d.id ? { ...c, x: Math.max(0, Math.min(BOARD_W - (c.w || 240), d.ox + dx)), y: Math.max(0, Math.min(BOARD_H - 80, d.oy + dy)) } : c));
    };
    const up = () => { dragRef.current = null; setDragId(null); };
    window.addEventListener("pointermove", move); window.addEventListener("pointerup", up); window.addEventListener("pointercancel", up);
    return () => { window.removeEventListener("pointermove", move); window.removeEventListener("pointerup", up); window.removeEventListener("pointercancel", up); };
  }, []);

  // ── Zoom pincer (2 doigts) + double-tap pour recadrer ──
  const fitToContent = useCallback(() => {
    const el = scrollRef.current; if (!el) return;
    if (!cards.length) { setZoom(1); el.scrollTo({ left: (BOARD_W - el.clientWidth) / 2, top: (BOARD_H - el.clientHeight) / 3, behavior: "smooth" }); return; }
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    cards.forEach((c) => {
      const x = c.x || 0, y = c.y || 0, w = c.w || 240;
      minX = Math.min(minX, x); minY = Math.min(minY, y);
      maxX = Math.max(maxX, x + w); maxY = Math.max(maxY, y + 200);
    });
    minX -= 40; minY -= 40; maxX += 40; maxY += 40;
    const bw = Math.max(1, maxX - minX), bh = Math.max(1, maxY - minY);
    const z = Math.max(0.5, Math.min(1.4, Math.min(el.clientWidth / bw, el.clientHeight / bh)));
    setZoom(z);
    setTimeout(() => el.scrollTo({ left: Math.max(0, minX * z), top: Math.max(0, minY * z), behavior: "smooth" }), 60);
  }, [cards]);

  useEffect(() => {
    const el = scrollRef.current; if (!el) return;
    const pinch = { active: false, dist0: 0, zoom0: 1 };
    let lastTap = 0;
    const dist = (t) => Math.hypot(t[0].clientX - t[1].clientX, t[0].clientY - t[1].clientY);
    const onStart = (e) => {
      if (e.touches.length === 2) { pinch.active = true; pinch.dist0 = dist(e.touches); pinch.zoom0 = zoomRef.current; }
      else if (e.touches.length === 1) {
        const now = Date.now();
        if (now - lastTap < 300) { e.preventDefault(); fitToContent(); lastTap = 0; } else { lastTap = now; }
      }
    };
    const onMove = (e) => {
      if (pinch.active && e.touches.length === 2) {
        e.preventDefault();
        const z = Math.max(0.5, Math.min(2.5, pinch.zoom0 * (dist(e.touches) / (pinch.dist0 || 1))));
        setZoom(z);
      }
    };
    const onEnd = (e) => { if (e.touches.length < 2) pinch.active = false; };
    el.addEventListener("touchstart", onStart, { passive: false });
    el.addEventListener("touchmove", onMove, { passive: false });
    el.addEventListener("touchend", onEnd);
    return () => { el.removeEventListener("touchstart", onStart); el.removeEventListener("touchmove", onMove); el.removeEventListener("touchend", onEnd); };
  }, [fitToContent]);

  // ── Coach Vision ──
  const runCoach = useCallback(() => {
    setMoreOpen(false); setCoachOpen(true); setCoachLoading(true); setCoachData(null);
    visionExtApi.coach(cards)
      .then((d) => setCoachData(d))
      .catch((e) => { toast.error(cleanError(e, "Coach indisponible pour l'instant.")); setCoachData({ actions: [] }); })
      .finally(() => setCoachLoading(false));
  }, [cards]);

  // ── Coach en Cartes : transforme une action du Coach en carte objectif sur le canvas ──
  const addCoachActionAsCard = useCallback((action) => {
    if (!action?.title) return;
    const title = String(action.title).trim();
    const why = String(action.why || "").trim();
    addCards([{
      id: uid(),
      type: "objective",
      w: 260,
      color: "#DEC2A3",
      title: { fr: title, en: title },
      body: why ? { fr: why, en: why } : undefined,
      checklist: [
        { text: { fr: "Première étape", en: "First step" }, done: false },
        { text: { fr: "Point de contrôle", en: "Checkpoint" }, done: false },
        { text: { fr: "Action terminée", en: "Done" }, done: false },
      ],
      progress: 0,
    }]);
    toast.success("Objectif posé sur le canvas ✦");
    setCoachOpen(false);
  }, [addCards]);

  // ── Modèles de Départ : charge la liste et remplit le canvas en un tap ──
  const openTemplates = useCallback(() => {
    setAddOpen(false);
    setTemplatesOpen(true);
    if (starterTemplates.length === 0) {
      setTemplatesLoading(true);
      visionExtApi.getStarterTemplates()
        .then((r) => setStarterTemplates(r?.templates || []))
        .catch(() => toast.error("Modèles indisponibles pour l'instant."))
        .finally(() => setTemplatesLoading(false));
    }
  }, [starterTemplates.length]);

  const applyTemplate = useCallback((tpl) => {
    if (!tpl?.cards?.length) return;
    // Si le canvas contient déjà des cartes, on demande confirmation
    if (cards.length > 0 && !window.confirm(`Remplacer le canvas actuel par le modèle "${tpl.label}" ? Tes cartes actuelles seront supprimées.`)) return;
    const newCards = tpl.cards.map((c) => ({ ...c, id: uid() }));
    setCards(newCards);
    setSelected(null);
    setTemplatesOpen(false);
    setTimeout(() => focusCards(newCards), 130);
    toast.success(`Modèle "${tpl.label}" appliqué ✦`);
  }, [cards.length, focusCards]);

  // ── Rappels Doux : toggle opt-in/opt-out ──
  const toggleWeeklyReminder = useCallback(() => {
    const next = { ...notifSettings, weekly_reminder: !notifSettings.weekly_reminder };
    setNotifSettings(next);
    visionExtApi.saveNotifSettings(next)
      .then(() => toast.success(next.weekly_reminder ? "Rappels doux activés ✦" : "Rappels doux mis en pause"))
      .catch(() => { toast.error("Impossible de sauvegarder."); setNotifSettings(notifSettings); });
  }, [notifSettings]);

  const addNote = () => { addCards([{ id: uid(), type: "note", w: 220, color: "", title: { fr: "Nouvelle note", en: "New note" }, body: { fr: "", en: "" } }]); setAddOpen(false); };
  const addObjective = () => { addCards([{ id: uid(), type: "objective", w: 250, color: "#DEC2A3", title: { fr: "Nouvel objectif", en: "New goal" }, checklist: [{ text: { fr: "Première étape", en: "First step" }, done: false }], progress: 0 }]); setAddOpen(false); };
  const addPalette = () => { addCards([{ id: uid(), type: "color", w: 240, title: { fr: "Palette", en: "Palette" }, colors: SWATCHES.slice(0, 4) }]); setAddOpen(false); };

  const genImage = async () => {
    const p = imgPrompt.trim(); if (p.length < 3) return toast.error("Décris l'image souhaitée.");
    setBusy(true);
    try { const res = await studioApi.generateImage(p, "custom"); if (!res?.url) throw new Error(); addCards([{ id: uid(), type: "image", image: res.url, w: 260, title: { fr: p.slice(0, 40), en: p.slice(0, 40) } }]); toast.success("Image IA ajoutée ✦"); setImgPrompt(""); setAddOpen(false); }
    catch (e) { toast.error(cleanError(e, "Génération d'image indisponible (quota atteint ?).")); } finally { setBusy(false); }
  };
  const searchPhoto = async () => {
    const q = photoQuery.trim(); if (!q) return;
    setBusy(true);
    try { const res = await visionApi.photos(q); const url = res?.photos?.[0]?.url || res?.[0]?.url; if (!url) throw new Error(); addCards([{ id: uid(), type: "image", image: url, w: 260 }]); toast.success("Photo ajoutée"); setPhotoQuery(""); setAddOpen(false); }
    catch (e) { toast.error("Aucune photo trouvée."); } finally { setBusy(false); }
  };
  const exportBook = async () => {
    setBusy(true);
    try { const res = await visionExtApi.generateBook(); const u = res?.flipbook_url || res?.pdf_url; if (u) { window.open(u, "_blank"); toast.success("Vision Book généré ✦"); } else throw new Error(); }
    catch { toast.error("Export indisponible pour l'instant."); } finally { setBusy(false); setMoreOpen(false); }
  };
  const shareBoard = async () => {
    try { const res = await visionExtApi.shareBoard(); const u = res?.share_url || res?.url; if (u) { try { await navigator.clipboard.writeText(u.startsWith("http") ? u : `${window.location.origin}${u}`); } catch {} toast.success("Lien de partage copié ✦"); } else throw new Error(); }
    catch { toast.error("Partage indisponible."); }
  };

  const selCard = cards.find((c) => c.id === selected);

  return createPortal(
    <div data-testid="m-vision-root" className="vb-tokens fixed inset-0 z-[200] bg-[var(--app-navy)]">
      {/* Canvas scrollable */}
      <div ref={scrollRef} className="absolute inset-0 overflow-auto vb-scroll" onClick={() => { setSelected(null); setPaletteFor(null); }} style={{ WebkitOverflowScrolling: "touch" }}>
        <div style={{ width: BOARD_W * zoom, height: BOARD_H * zoom }}>
          <div className="relative" style={{ width: BOARD_W, height: BOARD_H, transform: `scale(${zoom})`, transformOrigin: "0 0", backgroundImage: "radial-gradient(rgba(222, 194, 163,0.14) 1px, transparent 1px)", backgroundSize: "26px 26px" }}>
          {!loaded && <div className="absolute left-1/2 top-40 -translate-x-1/2 text-white/60"><Loader2 className="animate-spin" /></div>}
          {cards.map((c) => (
            <React.Fragment key={c.id}>
              <Card card={c} tv={tv} selected={selected === c.id && !dragId} onSelect={setSelected} onPointerDown={onCardPointerDown} onToggleObjective={toggleObjective} onEdit={setEditCard} />
              {/* Toolbar contextuelle flottante au-dessus de la carte sélectionnée */}
              {selected === c.id && !dragId && (
                <div data-testid="m-ctx-toolbar" onClick={(e) => e.stopPropagation()} className="absolute z-40 flex items-center gap-1 rounded-2xl border border-[var(--app-accent)]/25 bg-[var(--app-navy)]/95 p-1 shadow-xl backdrop-blur" style={{ left: c.x, top: Math.max(4, (c.y || 0) - 46), transform: `scale(${1 / zoom})`, transformOrigin: "0 100%" }}>
                  {(c.type === "note" || c.type === "ai-doc" || c.type === "objective") && (
                    <CtxBtn testid="m-ctx-edit" onClick={() => setEditCard(c)} icon={Type} />
                  )}
                  <CtxBtn testid="m-ctx-ai" onClick={() => { setSelected(null); setAiOpen(true); }} icon={Sparkles} />
                  <CtxBtn testid="m-ctx-palette" onClick={() => setPaletteFor(paletteFor === c.id ? null : c.id)} icon={Palette} />
                  <CtxBtn testid="m-ctx-duplicate" onClick={() => duplicateCard(c.id)} icon={Copy} />
                  <CtxBtn testid="m-ctx-delete" onClick={() => deleteCard(c.id)} icon={Trash2} danger />
                </div>
              )}
              {/* Palette de couleurs */}
              {paletteFor === c.id && (
                <div onClick={(e) => e.stopPropagation()} className="absolute z-40 flex flex-wrap gap-2 rounded-2xl border border-[var(--app-accent)]/25 bg-[var(--app-navy)]/95 p-2 shadow-xl" style={{ left: c.x, top: (c.y || 0) + 6, width: 200 }} data-testid="m-palette">
                  {SWATCHES.map((s) => (
                    <button key={s} data-testid={`m-swatch-${s.slice(1)}`} onClick={() => { patchCard(c.id, c.type === "color" ? { colors: [s, ...SWATCHES.filter((x) => x !== s).slice(0, 3)] } : { color: s }); setPaletteFor(null); }} className="h-8 w-8 rounded-full border-2 border-white/20 active:scale-90" style={{ background: s }} />
                  ))}
                </div>
              )}
            </React.Fragment>
          ))}
          </div>
        </div>
      </div>

      {/* État vide — overlay centré viewport (au-dessus du canvas, sous les barres) */}
      {loaded && cards.length === 0 && (
        <div className="pointer-events-none absolute left-1/2 top-1/2 z-[110] w-72 -translate-x-1/2 -translate-y-1/2 text-center" data-testid="m-empty">
          <span className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-white/5 text-[var(--app-accent)]"><Sparkles size={28} /></span>
          <p className="font-head text-lg font-semibold text-white">Ta vision, page blanche</p>
          <p className="mx-auto mt-1.5 text-sm text-white/55">Touche <b className="text-[var(--app-accent)]">Ask AI</b> ou <b className="text-[var(--app-accent)]">+</b> pour composer ton canvas.</p>
        </div>
      )}

      {/* Top overlay : retour + partage (pas d'en-tête d'app → immersif) */}
      <div className="pointer-events-none absolute inset-x-0 top-0 z-[120] flex items-start justify-between p-3 pt-[calc(0.75rem+env(safe-area-inset-top))]">
        <button onClick={() => (onBack ? onBack() : navigate(-1))} data-testid="m-back" className="pointer-events-auto flex h-11 w-11 items-center justify-center rounded-full bg-white/10 text-white backdrop-blur active:scale-90"><ChevronLeft size={22} /></button>
        <button onClick={shareBoard} data-testid="m-share" className="pointer-events-auto flex items-center gap-1.5 rounded-full bg-[var(--app-accent)] px-4 py-2.5 text-sm font-semibold text-[var(--app-navy)] active:scale-95"><Share2 size={15} /> Partager</button>
      </div>

      {/* Bottom bar façon Storyflow : [⋮] · [✦ Ask AI] · [+] */}
      <div className="absolute inset-x-0 bottom-0 z-[120] flex items-center justify-center gap-4 px-6 pb-[calc(1rem+env(safe-area-inset-bottom))] pt-2">
        <button onClick={() => setMoreOpen(true)} data-testid="m-more" className="flex h-12 w-12 items-center justify-center rounded-full bg-[var(--app-surface)]/90 text-[var(--app-text)] shadow-lg backdrop-blur active:scale-90"><MoreHorizontal size={22} /></button>
        <button onClick={() => setAiOpen(true)} data-testid="m-askai-open" className="flex items-center gap-2 rounded-full bg-[var(--app-accent)] px-6 py-3.5 text-base font-semibold text-[var(--app-navy)] shadow-xl shadow-[var(--app-accent)]/30 active:scale-95"><Sparkles size={19} /> Ask AI</button>
        <button onClick={() => setAddOpen(true)} data-testid="m-add" className="flex h-12 w-12 items-center justify-center rounded-full bg-[var(--app-surface)]/90 text-[var(--app-text)] shadow-lg backdrop-blur active:scale-90"><Plus size={24} /></button>
      </div>

      {/* Sheet: ajouter */}
      <Sheet open={addOpen} onClose={() => setAddOpen(false)} title="Ajouter au canvas">
        <div className="grid grid-cols-4 gap-3">
          <AddTile testid="m-add-note" icon={Type} label="Note" onClick={addNote} />
          <AddTile testid="m-add-objective" icon={Target} label="Objectif" onClick={addObjective} />
          <AddTile testid="m-add-palette" icon={Palette} label="Palette" onClick={addPalette} />
          <AddTile testid="m-add-templates" icon={LayoutTemplate} label="Modèles" onClick={openTemplates} />
        </div>
        <div className="mt-4 space-y-3">
          <div className="rounded-2xl border border-[var(--app-border)] bg-[var(--app-surface-2)] p-3">
            <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-[var(--app-text-muted)]"><ImageIcon size={13} className="text-[var(--app-accent)]" /> Image IA (Nano Banana)</p>
            <div className="flex gap-2">
              <input value={imgPrompt} onChange={(e) => setImgPrompt(e.target.value)} placeholder="ex : bureau avec vue mer" data-testid="m-add-image-input" className="flex-1 rounded-xl border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-[var(--app-text)] outline-none" />
              <button onClick={genImage} disabled={busy} data-testid="m-add-image-go" className="flex h-9 w-9 items-center justify-center rounded-xl bg-[var(--app-accent)] text-[var(--app-navy)] disabled:opacity-40">{busy ? <Loader2 size={15} className="animate-spin" /> : <Wand2 size={15} />}</button>
            </div>
          </div>
          <div className="rounded-2xl border border-[var(--app-border)] bg-[var(--app-surface-2)] p-3">
            <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-[var(--app-text-muted)]"><Search size={13} className="text-[var(--app-accent)]" /> Photo (Unsplash)</p>
            <div className="flex gap-2">
              <input value={photoQuery} onChange={(e) => setPhotoQuery(e.target.value)} placeholder="ex : océan, réussite" data-testid="m-add-photo-input" className="flex-1 rounded-xl border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-[var(--app-text)] outline-none" />
              <button onClick={searchPhoto} disabled={busy} data-testid="m-add-photo-go" className="flex h-9 w-9 items-center justify-center rounded-xl bg-[var(--app-accent)] text-[var(--app-navy)] disabled:opacity-40">{busy ? <Loader2 size={15} className="animate-spin" /> : <Search size={15} />}</button>
            </div>
          </div>
        </div>
      </Sheet>

      {/* Sheet: plus (actions) */}
      <Sheet open={moreOpen} onClose={() => setMoreOpen(false)} title="Actions">
        <div className="space-y-2">
          <ActionRow testid="m-action-coach" icon={Sparkles} label="Coach Vision — 3 prochaines actions" onClick={runCoach} />
          <ActionRow testid="m-action-templates" icon={LayoutTemplate} label="Modèles de départ" onClick={() => { setMoreOpen(false); openTemplates(); }} />
          <ActionRow
            testid="m-action-reminder"
            icon={notifSettings.weekly_reminder ? Bell : BellOff}
            label={notifSettings.weekly_reminder ? "Rappels doux hebdo — activés" : "Rappels doux hebdo — en pause"}
            onClick={toggleWeeklyReminder}
          />
          <ActionRow testid="m-action-fit" icon={Maximize2} label="Recadrer le canvas" onClick={() => { setMoreOpen(false); fitToContent(); }} />
          <ActionRow testid="m-action-export" icon={FileDown} label="Exporter en Vision Book (PDF)" onClick={exportBook} busy={busy} />
          <ActionRow testid="m-action-clear" icon={RotateCcw} label="Vider le canvas" danger onClick={() => { if (window.confirm("Vider le canvas ? Action irréversible.")) { setCards([]); setSelected(null); setMoreOpen(false); toast("Canvas vidé"); } }} />
        </div>
      </Sheet>

      {/* Sheet: Modèles de départ */}
      <Sheet open={templatesOpen} onClose={() => setTemplatesOpen(false)} title="Modèles de départ">
        {templatesLoading ? (
          <div className="flex items-center justify-center gap-2 py-10 text-[var(--app-text-muted)]"><Loader2 className="animate-spin" size={18} /> Chargement…</div>
        ) : (
          <div className="space-y-3" data-testid="m-templates-panel">
            <p className="text-xs text-[var(--app-text-muted)]">Un tap pour poser un canevas prêt à l'emploi. Tu ajustes ensuite librement chaque carte.</p>
            {starterTemplates.map((tpl) => (
              <button
                key={tpl.id}
                data-testid={`m-template-${tpl.id}`}
                onClick={() => applyTemplate(tpl)}
                className="flex w-full items-start gap-3 rounded-2xl border border-[var(--app-border)] bg-[var(--app-surface-2)] p-4 text-left transition active:scale-[0.98] hover:border-[var(--app-accent)]/40"
              >
                <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[var(--app-accent-soft)] text-xl">{tpl.emoji}</span>
                <div className="min-w-0 flex-1">
                  <p className="font-head text-[15px] font-semibold text-[var(--app-text)]">{tpl.label}</p>
                  <p className="mt-0.5 text-[13px] text-[var(--app-text-muted)]">{tpl.description}</p>
                  <p className="mt-1.5 text-[11px] uppercase tracking-wider text-[var(--app-accent)]">{tpl.cards?.length || 0} cartes prêtes</p>
                </div>
                <PlusCircle size={18} className="mt-1 shrink-0 text-[var(--app-accent)]" />
              </button>
            ))}
            {!starterTemplates.length && <p className="py-6 text-center text-sm text-[var(--app-text-muted)]">Aucun modèle disponible.</p>}
          </div>
        )}
      </Sheet>

      {/* Sheet: Coach Vision */}
      <Sheet open={coachOpen} onClose={() => setCoachOpen(false)} title="Coach Vision">
        {coachLoading ? (
          <div className="flex items-center justify-center gap-2 py-10 text-[var(--app-text-muted)]"><Loader2 className="animate-spin" size={18} /> Analyse de ton canvas…</div>
        ) : (
          <div data-testid="m-coach-panel">
            {coachData?.summary && <p className="mb-4 rounded-2xl bg-[var(--app-surface-2)] px-4 py-3 text-sm text-[var(--app-text)]">{coachData.summary}</p>}
            <div className="space-y-3">
              {(coachData?.actions || []).map((a, i) => (
                <div key={i} data-testid={`m-coach-action-${i}`} className="flex gap-3 rounded-2xl border border-[var(--app-accent)]/20 bg-[var(--app-surface)] p-3.5">
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[var(--app-accent)] text-sm font-bold text-[var(--app-navy)]">{i + 1}</span>
                  <div className="min-w-0 flex-1">
                    <p className="font-head text-[15px] font-semibold text-[var(--app-text)]">{a.title}</p>
                    {a.why && <p className="mt-0.5 text-[13px] text-[var(--app-text-muted)]">{a.why}</p>}
                    <button
                      onClick={() => addCoachActionAsCard(a)}
                      data-testid={`m-coach-add-card-${i}`}
                      className="mt-2 inline-flex items-center gap-1.5 rounded-full border border-[var(--app-accent)]/40 bg-[var(--app-accent-soft)] px-3 py-1.5 text-[12px] font-semibold text-[var(--app-accent)] transition active:scale-95 hover:bg-[var(--app-accent)]/15"
                    >
                      <PlusCircle size={13} /> Ajouter comme objectif
                    </button>
                  </div>
                </div>
              ))}
              {!coachData?.actions?.length && <p className="py-6 text-center text-sm text-[var(--app-text-muted)]">Aucune suggestion pour l'instant.</p>}
            </div>
            <button onClick={runCoach} data-testid="m-coach-refresh" className="mt-4 flex w-full items-center justify-center gap-2 rounded-full border border-[var(--app-accent)]/30 py-2.5 text-sm font-semibold text-[var(--app-accent)] active:scale-95"><RotateCcw size={15} /> Régénérer</button>
          </div>
        )}
      </Sheet>

      <AskAI open={aiOpen} onClose={() => setAiOpen(false)} onCards={addCards} />
      <EditSheet card={editCard} onClose={() => setEditCard(null)} onSave={(patch) => patchCard(editCard.id, patch)} />
    </div>, document.body);
}

function CtxBtn({ onClick, icon: Icon, danger, testid }) {
  return <button onClick={onClick} data-testid={testid} className={`flex h-9 w-9 items-center justify-center rounded-xl active:scale-90 ${danger ? "text-[#e08a6a]" : "text-white"} hover:bg-white/10`}><Icon size={16} /></button>;
}
function AddTile({ icon: Icon, label, onClick, testid }) {
  return <button onClick={onClick} data-testid={testid} className="flex flex-col items-center gap-2 rounded-2xl border border-[var(--app-border)] bg-[var(--app-surface-2)] py-4 active:scale-95"><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--app-accent-soft)] text-[var(--app-accent)]"><Icon size={18} /></span><span className="text-xs font-medium text-[var(--app-text)]">{label}</span></button>;
}
function ActionRow({ icon: Icon, label, onClick, danger, busy, testid }) {
  return <button onClick={onClick} disabled={busy} data-testid={testid} className={`flex w-full items-center gap-3 rounded-2xl border border-[var(--app-border)] bg-[var(--app-surface-2)] px-4 py-3.5 text-left text-sm font-medium active:scale-[0.98] ${danger ? "text-[#c26b4a]" : "text-[var(--app-text)]"}`}><Icon size={17} className={danger ? "" : "text-[var(--app-accent)]"} /> {label}{busy && <Loader2 size={14} className="ml-auto animate-spin" />}</button>;
}
