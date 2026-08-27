import React, { useState, useMemo, useEffect } from "react";
import { X, Search, FileText, Image as ImageIcon, Video, Link2, MousePointer2, Folder } from "lucide-react";

/**
 * Documents Drawer — Panneau latéral droit rétractable (style Storyflow / Figma).
 * Deux tabs : "Ce board" (documents du board courant) / "Tous" (cross-boards).
 * Search bar dans le drawer (pas dans le header canvas).
 *
 * Props :
 * - open (bool)
 * - onClose ()
 * - currentItems (array) : items du board courant
 * - allItems (array | null) : items de tous les boards (si null → chargé lazy)
 * - onFocus (id) : scroll/highlight la card correspondante dans le canvas
 */
export default function DocumentsDrawer({ open, onClose, currentItems = [], allItems = null, onFocus }) {
  const [tab, setTab] = useState("current");
  const [query, setQuery] = useState("");

  useEffect(() => { if (open) setQuery(""); }, [open]);

  const source = tab === "current" ? currentItems : (allItems || currentItems);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    const list = source.filter((it) => {
      // On expose : ai-doc, image (uploads), video, note longue, link
      return ["ai-doc", "image", "video", "note", "link"].includes(it.type);
    });
    if (!q) return list;
    return list.filter((it) => {
      const title = (it.title?.fr || it.title?.en || "").toLowerCase();
      const body = (it.body?.fr || it.body?.en || "").toLowerCase();
      return title.includes(q) || body.includes(q);
    });
  }, [source, query]);

  const iconFor = (it) => {
    if (it.type === "ai-doc") return <FileText size={14} className="text-[var(--app-accent)]" />;
    if (it.type === "image") return <ImageIcon size={14} className="text-[#B784E0]" />;
    if (it.type === "video") return <Video size={14} className="text-[#E0A93B]" />;
    if (it.type === "link") return <Link2 size={14} className="text-[#3B6FE0]" />;
    return <FileText size={14} className="text-[var(--app-text-muted)]" />;
  };

  return (
    <>
      {/* Backdrop */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-[1px]"
          onClick={onClose}
        />
      )}
      {/* Drawer */}
      {open && (
      <aside
        data-testid="documents-drawer"
        className="fixed top-0 right-0 z-50 h-screen w-[320px] max-w-[92vw] border-l border-[var(--app-border)] bg-[var(--app-surface)] shadow-2xl flex flex-col animate-slide-in-right"
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[var(--app-border)] px-4 py-3">
          <div className="flex items-center gap-2">
            <Folder size={16} className="text-[var(--app-accent)]" />
            <h3 className="font-head text-sm font-semibold text-[var(--app-text)]">Documents</h3>
          </div>
          <button onClick={onClose} data-testid="documents-drawer-close" className="rounded-lg p-1.5 text-[var(--app-text-muted)] hover:bg-[var(--app-surface-2)]">
            <X size={15} />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 border-b border-[var(--app-border)] px-3 pt-2">
          {[
            { id: "current", label: "Ce board" },
            { id: "all", label: "Tous" },
          ].map((t) => {
            const active = tab === t.id;
            return (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                data-testid={`documents-tab-${t.id}`}
                className={[
                  "border-b-2 px-2.5 py-2 text-xs font-medium transition",
                  active
                    ? "border-[var(--app-accent)] text-[var(--app-text)]"
                    : "border-transparent text-[var(--app-text-muted)] hover:text-[var(--app-text)]",
                ].join(" ")}
              >
                {t.label}
              </button>
            );
          })}
        </div>

        {/* Search */}
        <div className="px-3 py-2">
          <div className="flex items-center gap-2 rounded-lg border border-[var(--app-border)] bg-[var(--app-surface-2)] px-2.5 py-1.5">
            <Search size={13} className="text-[var(--app-text-muted)]" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Rechercher…"
              data-testid="documents-search"
              className="flex-1 bg-transparent text-xs text-[var(--app-text)] outline-none placeholder:text-[var(--app-text-muted)]"
            />
          </div>
        </div>

        {/* List */}
        <div className="flex-1 overflow-y-auto px-2 pb-3">
          {filtered.length === 0 && (
            <p className="px-2 py-6 text-center text-xs text-[var(--app-text-muted)]">
              {query ? "Aucun résultat." : "Aucun document dans ce board.\nAjoute via le menu +."}
            </p>
          )}
          {filtered.map((it) => {
            const title = it.title?.fr || it.title?.en || "Sans titre";
            const body = it.body?.fr || it.body?.en || "";
            const preview = body.slice(0, 90).replace(/\n+/g, " ");
            return (
              <button
                key={it.id}
                onClick={() => { onFocus?.(it.id); }}
                data-testid={`documents-item-${it.id}`}
                className="mb-1 flex w-full items-start gap-2 rounded-lg border border-transparent px-2 py-2 text-left transition hover:border-[var(--app-border)] hover:bg-[var(--app-surface-2)]"
              >
                <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-[var(--app-surface-2)]">
                  {iconFor(it)}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="truncate text-[12px] font-semibold text-[var(--app-text)]">{title}</div>
                  {preview && <div className="mt-0.5 line-clamp-2 text-[10.5px] text-[var(--app-text-muted)]">{preview}</div>}
                  <div className="mt-0.5 text-[9px] uppercase tracking-wider text-[var(--app-text-muted)]">
                    {it.type === "ai-doc" ? `AI · ${it.docType || "doc"}` : it.type}
                  </div>
                </div>
                <MousePointer2 size={12} className="mt-0.5 shrink-0 opacity-0 group-hover:opacity-100 transition text-[var(--app-text-muted)]" />
              </button>
            );
          })}
        </div>

        {/* Footer */}
        <div className="border-t border-[var(--app-border)] px-4 py-2.5 text-[10.5px] text-[var(--app-text-muted)]">
          {filtered.length} document{filtered.length > 1 ? "s" : ""} · {tab === "current" ? "board courant" : "tous les boards"}
        </div>
      </aside>
      )}
    </>
  );
}
