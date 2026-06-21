import React, { useEffect, useState } from "react";
import { FileText, Sparkles, Loader2, Trash2, Plus, X, Cloud, HardDrive, Link2, RefreshCw, FileUp, Workflow } from "lucide-react";
import { Link } from "react-router-dom";
import { documentsApi, integrationsApi } from "@fm/lib/api";

const TEMPLATES = [
  { name: "Pitch deck",      type: "Pitch" },
  { name: "Mini CRM Notion", type: "Stratégie" },
  { name: "Process onboarding client", type: "Processus" },
  { name: "Email de relance", type: "Email" },
];

export default function Documents() {
  const [items, setItems] = useState(null); // null=loading
  const [creating, setCreating] = useState(false);
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({ name: "", type: "Texte", prompt: "" });
  const [reading, setReading] = useState(null); // doc currently displayed

  // ── Statut sync cloud (Google Drive / OneDrive) ─────────────────────────
  const [cloud, setCloud] = useState({ loading: true, google: null, microsoft: null });
  const loadCloudStatus = () => {
    Promise.allSettled([integrationsApi.google.status(), integrationsApi.microsoft.status()])
      .then(([g, m]) => setCloud({
        loading: false,
        google: g.status === "fulfilled" ? g.value : { connected: false },
        microsoft: m.status === "fulfilled" ? m.value : { connected: false },
      }));
  };
  const connectCloud = async (provider) => {
    try {
      const { url } = await integrationsApi[provider].start();
      window.location.href = url;
    } catch {
      alert("Connexion impossible — réessayez depuis la page Intégrations.");
    }
  };

  const load = () => documentsApi.list().then((d) => setItems(d.items || [])).catch(() => setItems([]));
  useEffect(() => { load(); loadCloudStatus(); }, []);

  // ── Import de fichier (disposition reprise de l'ancien ProcessusMetier) ──
  const fileInputRef = React.useRef(null);
  const onFileSelected = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setBusy(true);
    try {
      const text = await file.text().catch(() => "");
      const r = await documentsApi.generate({
        name: file.name,
        type: "Texte",
        prompt: `Analyse ce document importé (${file.name}) et propose un résumé structuré et des actions concrètes.${text ? `\n\nContenu :\n${text.slice(0, 4000)}` : ""}`,
      });
      setItems((arr) => [r, ...(arr || [])]);
      setReading(r);
    } catch (err) {
      alert("Échec de l'import : " + (err?.detail || err?.message || "réessayez"));
    } finally {
      setBusy(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const generate = async () => {
    if (!form.name.trim() || !form.prompt.trim()) return;
    setBusy(true);
    try {
      const r = await documentsApi.generate(form);
      setItems((arr) => [r, ...(arr || [])]);
      setCreating(false);
      setForm({ name: "", type: "Texte", prompt: "" });
      setReading(r);
    } catch (e) {
      alert("Échec : " + (e?.detail || e?.message || "génération impossible"));
    } finally { setBusy(false); }
  };

  const remove = async (id) => {
    if (!confirm("Supprimer ce document ?")) return;
    await documentsApi.remove(id);
    setItems((arr) => (arr || []).filter((x) => x.id !== id));
  };

  const total = items?.length || 0;
  const iaCount = (items || []).filter((d) => d.source === "ia").length;

  return (
    <div className="space-y-5" data-testid="documents-content">
      {/* Header — aligné Missions */}
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
        <div>
          <p className="text-[11px] uppercase tracking-[0.22em] text-[#6B6358] font-semibold">Bibliothèque IA</p>
          
          <p className="mt-1 text-[14.5px] text-[#4A4538]">Pitch, devis, processus : laissez l&apos;IA rédiger, vous validez.</p>
        </div>
        <div className="bg-white border border-[#E8E2D8] rounded-2xl px-5 py-4 shadow-sm">
          <p className="text-[10.5px] tracking-[0.22em] uppercase text-[#6B6358] font-semibold">Documents</p>
          <p className="text-[28px] leading-tight text-[#1F2937] font-display">
            {total} <span className="text-[14px] text-[#6B6358]">/ {iaCount} IA</span>
          </p>
          <p className="text-[11px] text-[#6B6358] mt-1">Générés et personnels confondus</p>
        </div>
      </div>

      {/* Synchronisation cloud — Google Drive / OneDrive */}
      <div className="card-cream p-4 flex flex-wrap items-center justify-between gap-3" data-testid="doc-sync-banner">
        {cloud.loading ? (
          <p className="text-[12.5px] text-[#6B6358] inline-flex items-center gap-2">
            <Loader2 size={13} className="animate-spin" /> Vérification de la synchronisation…
          </p>
        ) : cloud.google?.connected || cloud.microsoft?.connected ? (
          <>
            <div className="flex items-center gap-2 text-[12.5px] text-[#1F2937]">
              <RefreshCw size={14} className="text-emerald-600" />
              <span>
                Synchronisé avec{" "}
                {cloud.google?.connected && <strong>Google Drive</strong>}
                {cloud.google?.connected && cloud.microsoft?.connected && " et "}
                {cloud.microsoft?.connected && <strong>OneDrive</strong>}
                {" "}— vos documents générés y sont sauvegardés automatiquement.
              </span>
            </div>
            <Link to="/integrations" className="text-[12px] text-navy hover:underline shrink-0" data-testid="doc-sync-manage">
              Gérer la connexion
            </Link>
          </>
        ) : (
          <>
            <div className="flex items-center gap-2 text-[12.5px] text-[#6B6358]">
              <Cloud size={14} className="text-[#9C7D40]" />
              <span>Connectez un stockage cloud pour sauvegarder vos documents automatiquement.</span>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <button onClick={() => connectCloud("google")} data-testid="doc-connect-google"
                className="inline-flex items-center gap-1.5 px-3.5 h-9 rounded-full bg-white border border-[#E8E2D8] text-[12.5px] font-medium hover:border-navy/30 transition">
                <HardDrive size={13} /> Google Drive
              </button>
              <button onClick={() => connectCloud("microsoft")} data-testid="doc-connect-onedrive"
                className="inline-flex items-center gap-1.5 px-3.5 h-9 rounded-full bg-white border border-[#E8E2D8] text-[12.5px] font-medium hover:border-navy/30 transition">
                <Cloud size={13} /> OneDrive
              </button>
            </div>
          </>
        )}
      </div>

      {/* ── Analyse IA + import (disposition reprise de l'ancien ProcessusMetier) ── */}
      <div className="rounded-2xl p-5" style={{ background: "var(--zayado-navy, #1F3A6A)", color: "white" }} data-testid="doc-ia-intro">
        <div className="flex items-start gap-3">
          <Sparkles size={17} className="mt-0.5 text-[#E5D5A2] flex-shrink-0" />
          <div>
            <div className="font-semibold mb-1 text-[13.5px]">Analyse IA</div>
            <div className="text-[12.5px] opacity-85">
              Importez vos documents ou connectez votre Drive pour que l&apos;IA détecte vos processus et propose des optimisations.
            </div>
          </div>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-3" data-testid="doc-import-cards">
        <button
          onClick={() => cloud.google?.connected || cloud.microsoft?.connected
            ? loadCloudStatus()
            : connectCloud(cloud.google ? "google" : "microsoft")}
          className="card-soft p-5 text-left hover:border-[#9C7D40]/40 transition"
          data-testid="doc-analyze-drive-btn"
        >
          <HardDrive size={18} className="text-[#264653] mb-2" />
          <div className="font-display text-[16px] mb-1 text-[#1F2937]">Analyser mon Drive</div>
          <div className="text-[12.5px] text-[#6B6358]">
            {cloud.google?.connected || cloud.microsoft?.connected
              ? "L'IA examine vos fichiers et recommande des processus."
              : "Connectez Google Drive ou OneDrive pour activer l'analyse automatique."}
          </div>
        </button>
        <button
          onClick={() => fileInputRef.current?.click()}
          className="card-soft p-5 text-left hover:border-[#9C7D40]/40 transition"
          data-testid="doc-import-file-btn"
        >
          <FileUp size={18} className="text-[#264653] mb-2" />
          <div className="font-display text-[16px] mb-1 text-[#1F2937]">Importer un document</div>
          <div className="text-[12.5px] text-[#6B6358]">PDF, Word, texte — l&apos;IA génère un résumé et des actions.</div>
          <input ref={fileInputRef} type="file" accept=".txt,.md,.pdf,.doc,.docx" className="hidden" onChange={onFileSelected} data-testid="doc-file-input" />
        </button>
      </div>

      {/* Ajout / Génération IA (en haut, aligné Missions) */}
      <div className="card-cream p-5" data-testid="doc-add-block">
        <div className="flex items-center gap-3 mb-3">
          <span className="w-10 h-10 rounded-2xl bg-[#264653] text-white grid place-items-center shrink-0">
            <Sparkles size={17} strokeWidth={2} />
          </span>
          <div className="flex-1 min-w-0">
            <p className="text-[15.5px] text-[#1F2937] font-display">Créer un document</p>
            <p className="text-[12.5px] text-[#6B6358]">Générez avec l&apos;IA ou démarrez à partir d&apos;un template prêt à l&apos;emploi.</p>
          </div>
          <button
            onClick={() => setCreating(true)}
            data-testid="doc-create-btn"
            className="px-4 h-11 rounded-full bg-navy text-cream text-[13.5px] font-semibold hover:bg-navy-bright transition inline-flex items-center justify-center gap-2 shrink-0"
          >
            <Sparkles size={14} /> Générer avec l&apos;IA
          </button>
        </div>
        {/* Templates inline (raccourci visuel) */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          {TEMPLATES.map((t, i) => (
            <button
              key={i}
              onClick={() => { setForm({ name: t.name, type: t.type, prompt: "" }); setCreating(true); }}
              className="bg-white border border-[#E8E2D8] rounded-xl p-2.5 text-left hover:border-[#264653]/30 transition flex items-center gap-2"
              data-testid={`tpl-${i}`}
            >
              <Plus className="w-3.5 h-3.5 text-[#9C7D40] shrink-0" />
              <span className="text-[12.5px] text-[#1F2937] truncate">{t.name}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Library */}
      {items === null ? (
        <div className="card-soft p-12 grid place-items-center text-ink-soft"><Loader2 className="animate-spin" /></div>
      ) : items.length === 0 ? (
        <div className="card-soft p-10 text-center" data-testid="doc-empty">
          <FileText size={28} className="mx-auto text-[#9C7D40] mb-3" />
          <p className="text-[15px] text-[#1F2937] font-medium">Aucun document pour le moment</p>
          <p className="text-[12.5px] text-[#6B6358] mt-1">Cliquez sur « Générer avec l&apos;IA » pour créer votre premier document.</p>
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="doc-list">
          {items.map((d) => (
            <div key={d.id} className="card-soft p-5 group">
              <div className="flex items-start justify-between mb-3">
                <FileText className="w-5 h-5 text-[#1F2937]" />
                <span className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full bg-[#F3E9D0] text-[#9C7D40]">{d.type}</span>
              </div>
              <button onClick={() => setReading(d)} className="text-left w-full" data-testid={`doc-open-${d.id}`}>
                <p className="text-[#1F2937] text-[15px] font-display tracking-tight mb-1 line-clamp-2">{d.name}</p>
                <p className="text-[11px] text-[#6B6358]">
                  {new Date(d.created_at).toLocaleDateString("fr-FR")} · source {d.source === "ia" ? "IA" : "humaine"}
                </p>
              </button>
              <button onClick={() => remove(d.id)} className="mt-3 text-[11px] text-rose-600 hover:underline opacity-0 group-hover:opacity-100 transition inline-flex items-center gap-1">
                <Trash2 size={11} /> Supprimer
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Create modal */}
      {creating && (
        <div className="fixed inset-0 z-50 bg-navy/40 backdrop-blur-sm grid place-items-center p-4">
          <div className="bg-cream rounded-3xl p-7 max-w-lg w-full border border-sand-200 shadow-soft">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2"><Sparkles className="text-gold-deep" size={18} /><p className="font-display text-[22px] text-navy">Nouveau document IA</p></div>
              <button onClick={() => setCreating(false)} className="text-ink-soft"><X size={18} /></button>
            </div>
            <p className="text-[13px] text-ink-soft mb-4">L&apos;IA rédige un document structuré en français à partir de votre contexte.</p>
            <div className="space-y-3">
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Nom du document" className="w-full bg-white border border-sand-200 rounded-2xl px-4 py-2.5 text-[14px]" data-testid="doc-name" />
              <select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })} className="w-full bg-white border border-sand-200 rounded-2xl px-4 py-2.5 text-[14px]" data-testid="doc-type">
                {["Pitch", "Stratégie", "Email", "Devis", "Lettre", "Processus", "Texte"].map((t) => <option key={t}>{t}</option>)}
              </select>
              <textarea value={form.prompt} onChange={(e) => setForm({ ...form, prompt: e.target.value })} placeholder="Contexte / instructions pour l&apos;IA. Ex : Pitch deck pour ma plateforme SaaS visant les solo-fondateurs, 8 slides, ton ambitieux." rows={5} className="w-full bg-white border border-sand-200 rounded-2xl p-3 text-[14px]" data-testid="doc-prompt" />
            </div>
            <div className="mt-4 flex gap-2">
              <button onClick={generate} disabled={busy || !form.name.trim() || !form.prompt.trim()} className="flex-1 px-4 h-11 rounded-full bg-navy text-cream text-[13px] font-semibold disabled:opacity-50" data-testid="doc-generate">
                {busy ? <><Loader2 size={14} className="animate-spin inline mr-1" />Génération…</> : <><Sparkles size={14} className="inline mr-1" />Générer le document</>}
              </button>
              <button onClick={() => setCreating(false)} className="px-4 h-11 rounded-full bg-cream-soft text-ink text-[13px] font-medium">Annuler</button>
            </div>
          </div>
        </div>
      )}

      {/* Read modal */}
      {reading && (
        <div className="fixed inset-0 z-50 bg-navy/40 backdrop-blur-sm grid place-items-center p-4">
          <div className="bg-cream rounded-3xl max-w-2xl w-full max-h-[85vh] flex flex-col border border-sand-200 shadow-soft">
            <div className="p-5 border-b border-sand-200 flex items-center justify-between">
              <div>
                <p className="text-[10.5px] uppercase tracking-wider text-gold-deep font-semibold">{reading.type}</p>
                <p className="font-display text-[20px] text-navy">{reading.name}</p>
              </div>
              <button onClick={() => setReading(null)} className="text-ink-soft" data-testid="doc-close-read"><X size={18} /></button>
            </div>
            <div className="p-6 overflow-y-auto flex-1 text-[14px] text-ink whitespace-pre-wrap" data-testid="doc-body">
              {reading.body || <span className="italic text-ink-soft">(document vide)</span>}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
