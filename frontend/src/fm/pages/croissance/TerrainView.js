import React, { useState } from "react";
import { leadsApi, integrationsApi } from "@fm/lib/api";
import { useAuth } from "@fm/context/AuthContext";
import { toast } from "sonner";
import {
  Search, Bot, MessageCircle, Plus, Filter, Trash2, X, GitBranch, List,
} from "lucide-react";
import AddLeadModal from "./AddLeadModal";
import WaComposer from "./WaComposer";
import PipelineView from "./PipelineView";

export const LEAD_STATUSES = ["Détecté", "Contacté", "En discussion", "RDV planifié", "Gagné", "Perdu"];

function FilterChip({ label, active, onClick, testId, small }) {
  return (
    <button data-testid={testId} onClick={onClick}
      className={`px-3 ${small ? "h-7 text-[11.5px]" : "h-8 text-[12.5px]"} rounded-full font-medium transition-colors ${active ? "bg-navy text-cream" : "bg-cream-soft text-ink-soft hover:bg-sand-200"}`}>
      {label}
    </button>
  );
}

export default function TerrainView({ leads, onLeadsChange }) {
  const { user } = useAuth();
  const isPremium = user?.plan === "premium" || user?.plan === "premium_yearly";
  const [view, setView] = useState("list");
  const [sendingTo, setSendingTo] = useState(null);
  const [filter, setFilter] = useState("all");
  const [sourceFilter, setSourceFilter] = useState("all");
  const [scoreFilter, setScoreFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("score-desc");
  const [selected, setSelected] = useState(new Set());
  const [showAdd, setShowAdd] = useState(false);
  const [waLead, setWaLead] = useState(null);

  const sources = ["all", ...Array.from(new Set(leads.map((l) => l.from).filter(Boolean)))];

  let filtered = leads.filter((l) => {
    if (filter !== "all" && l.status !== filter) return false;
    if (sourceFilter !== "all" && l.from !== sourceFilter) return false;
    if (scoreFilter === "fort" && (l.score || 0) < 70) return false;
    if (scoreFilter === "moyen" && ((l.score || 0) < 40 || (l.score || 0) >= 70)) return false;
    if (scoreFilter === "faible" && (l.score || 0) >= 40) return false;
    if (search) {
      const q = search.toLowerCase();
      if (!(l.name || "").toLowerCase().includes(q) && !(l.co || "").toLowerCase().includes(q)) return false;
    }
    return true;
  });
  filtered = [...filtered].sort((a, b) => {
    if (sort === "score-desc") return (b.score || 0) - (a.score || 0);
    if (sort === "score-asc") return (a.score || 0) - (b.score || 0);
    if (sort === "name") return (a.name || "").localeCompare(b.name || "");
    if (sort === "recent") return (b.created_at || "").localeCompare(a.created_at || "");
    return 0;
  });

  const toggleSelected = (id) => {
    const next = new Set(selected);
    if (next.has(id)) next.delete(id); else next.add(id);
    setSelected(next);
  };
  const bulkDelete = async () => {
    if (selected.size === 0) return;
    if (!window.confirm(`Supprimer ${selected.size} lead(s) ?`)) return;
    try {
      await Promise.all([...selected].map((id) => leadsApi.remove(id)));
      onLeadsChange(leads.filter((l) => !selected.has(l.id)));
      toast.success(`${selected.size} lead(s) supprimés`);
      setSelected(new Set());
    } catch (e) { toast.error(e.message); }
  };
  const bulkStatus = async (newStatus) => {
    if (selected.size === 0) return;
    try {
      await Promise.all([...selected].map((id) => leadsApi.patch(id, { status: newStatus })));
      onLeadsChange(leads.map((l) => selected.has(l.id) ? { ...l, status: newStatus } : l));
      toast.success(`${selected.size} lead(s) marqués "${newStatus}"`);
      setSelected(new Set());
    } catch (e) { toast.error(e.message); }
  };

  const updateStatus = async (lead, newStatus) => {
    try {
      const updated = await leadsApi.patch(lead.id, { status: newStatus });
      onLeadsChange(leads.map((l) => (l.id === lead.id ? { ...l, ...updated } : l)));
    } catch (e) {
      toast.error(e.message || "Mise à jour échouée");
    }
  };

  const removeLead = async (lead) => {
    if (!window.confirm(`Supprimer ${lead.name} ?`)) return;
    try {
      await leadsApi.remove(lead.id);
      onLeadsChange(leads.filter((l) => l.id !== lead.id));
      toast.success("Lead supprimé");
    } catch (e) { toast.error(e.message); }
  };

  const addLead = async (payload) => {
    try {
      const created = await leadsApi.create(payload);
      onLeadsChange([created, ...leads]);
      setShowAdd(false);
      toast.success("Lead ajouté");
    } catch (e) { toast.error(e.message || "Ajout échoué"); }
  };

  const openWA = (lead) => {
    const firstName = (lead?.name || "").split(" ")[0] || "";
    setWaLead({
      lead,
      phone: "",
      message: `Bonjour ${firstName ? firstName + ", " : ""}je reviens vers vous concernant notre échange. Avez-vous quelques minutes ?`,
    });
  };

  const sendWA = async () => {
    if (!waLead?.phone || !waLead?.message) { toast.error("Numéro et message requis"); return; }
    setSendingTo(waLead.lead.id);
    try {
      if (isPremium) {
        await integrationsApi.whatsapp.send(waLead.phone, waLead.message);
        toast.success(`Message envoyé à ${waLead.lead.name}`);
      } else {
        const phone = waLead.phone.replace(/[^0-9]/g, "");
        const text = encodeURIComponent(waLead.message);
        window.open(`https://wa.me/${phone}?text=${text}`, "_blank", "noopener,noreferrer");
        toast.success("WhatsApp ouvert dans un nouvel onglet");
      }
      setWaLead(null);
      if (waLead.lead.status === "Détecté") await updateStatus(waLead.lead, "Contacté");
    } catch (e) {
      toast.error(e.message || "Échec d'envoi");
    } finally {
      setSendingTo(null);
    }
  };

  return (
    <>
      <div className="card-cream p-7 rise">
        <div className="flex items-start justify-between gap-4 flex-wrap mb-5">
          <div>
            <p className="uppercase-eyebrow">Mes leads</p>
            <p className="font-display text-[22px] text-navy mt-1">{filtered.length} / {leads.length} prospects</p>
            <div className="mt-3 inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-cream-soft border border-sand-300 text-[11.5px] text-ink-soft" data-testid="terrain-auto-feed">
              <Bot size={12} className="text-navy" />
              <span>Alimenté automatiquement par <strong className="text-navy">Growth Agent</strong> · Ajout manuel possible</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="inline-flex p-1 rounded-full bg-cream-soft border border-sand-300" data-testid="terrain-view-toggle">
              <button onClick={() => setView("list")}
                className={`px-3 h-8 rounded-full text-[12px] font-semibold inline-flex items-center gap-1.5 transition ${view === "list" ? "bg-navy text-cream" : "text-ink-soft"}`}
                data-testid="terrain-view-list">
                <List size={13} /> Liste
              </button>
              <button onClick={() => setView("pipeline")}
                className={`px-3 h-8 rounded-full text-[12px] font-semibold inline-flex items-center gap-1.5 transition ${view === "pipeline" ? "bg-navy text-cream" : "text-ink-soft"}`}
                data-testid="terrain-view-pipeline">
                <GitBranch size={13} /> Pipeline IA
              </button>
            </div>
            <button data-testid="terrain-add-lead-btn" onClick={() => setShowAdd(true)}
              className="inline-flex items-center gap-2 px-4 h-10 rounded-full bg-navy text-cream text-[13px] font-semibold hover:bg-navy-bright transition-colors">
              <Plus size={14} /> Ajouter un lead
            </button>
          </div>
        </div>

        {view === "pipeline" && (
          <div data-testid="terrain-pipeline-inline">
            <PipelineView leads={leads} />
          </div>
        )}

        {view === "list" && (<>
          <div className="flex items-center gap-2 flex-wrap mb-4">
            <Filter size={13} className="text-ink-soft" />
            <FilterChip label="Tous" active={filter === "all"} onClick={() => setFilter("all")} testId="filter-status-all" />
            {LEAD_STATUSES.map((s) => (
              <FilterChip key={s} label={s} active={filter === s} onClick={() => setFilter(s)} testId={`filter-status-${s}`} />
            ))}
          </div>
          <div className="flex items-center gap-2 flex-wrap mb-3" data-testid="filter-score-row">
            <span className="text-[11px] uppercase tracking-wider text-ink-muted font-semibold mr-1">Score</span>
            <FilterChip label="Tous" active={scoreFilter === "all"} onClick={() => setScoreFilter("all")} testId="filter-score-all" small />
            <FilterChip label="🔥 Fort (70+)" active={scoreFilter === "fort"} onClick={() => setScoreFilter("fort")} testId="filter-score-fort" small />
            <FilterChip label="⚖️ Moyen (40-69)" active={scoreFilter === "moyen"} onClick={() => setScoreFilter("moyen")} testId="filter-score-moyen" small />
            <FilterChip label="❄️ Faible (<40)" active={scoreFilter === "faible"} onClick={() => setScoreFilter("faible")} testId="filter-score-faible" small />
          </div>
          <div className="flex items-center gap-2 mb-3 flex-wrap">
            <div className="relative flex-1 min-w-[200px]">
              <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-soft" />
              <input data-testid="terrain-search" value={search} onChange={(e) => setSearch(e.target.value)}
                placeholder="Rechercher un lead…" className="w-full h-9 pl-9 pr-3 rounded-full bg-cream-soft border border-sand-200 text-[13px] focus:outline-none focus:border-navy" />
            </div>
            <select data-testid="terrain-sort" value={sort} onChange={(e) => setSort(e.target.value)} className="h-9 px-3 rounded-full bg-cream-soft border border-sand-200 text-[13px]">
              <option value="score-desc">Score ↓</option>
              <option value="score-asc">Score ↑</option>
              <option value="name">Nom A-Z</option>
              <option value="recent">Plus récents</option>
            </select>
          </div>
          {selected.size > 0 && (
            <div className="flex items-center gap-2 mb-3 px-3 py-2 rounded-full bg-navy text-cream text-[12.5px] w-fit" data-testid="terrain-bulk-bar">
              <span className="font-semibold">{selected.size} sélectionné(s)</span>
              <button onClick={() => bulkStatus("Contacté")} className="px-3 h-7 rounded-full bg-white/15 hover:bg-white/25 text-[11.5px]">Marquer contacté</button>
              <button onClick={() => bulkStatus("RDV planifié")} className="px-3 h-7 rounded-full bg-white/15 hover:bg-white/25 text-[11.5px]">RDV planifié</button>
              <button onClick={bulkDelete} className="px-3 h-7 rounded-full bg-red-500/80 hover:bg-red-500 text-[11.5px]" data-testid="terrain-bulk-delete">Supprimer</button>
              <button onClick={() => setSelected(new Set())} className="ml-1 text-cream/70 hover:text-cream"><X size={13} /></button>
            </div>
          )}
          {sources.length > 2 && (
            <div className="flex items-center gap-2 flex-wrap mb-5">
              <span className="text-[11px] uppercase tracking-wider text-ink-muted font-semibold mr-1">Source</span>
              {sources.map((s) => (
                <FilterChip key={s} label={s === "all" ? "Toutes" : s} active={sourceFilter === s} onClick={() => setSourceFilter(s)} testId={`filter-source-${s}`} small />
              ))}
            </div>
          )}
          <ul className="space-y-2.5" data-testid="terrain-leads-list">
            {filtered.length === 0 && (
              <li className="text-center py-10 text-ink-soft text-[14px]">Aucun lead ne correspond aux filtres.</li>
            )}
            {filtered.map((l, idx) => (
              <li key={l.id || l.name || `lead-${idx}`} className="flex items-center gap-3 p-3.5 rounded-2xl bg-cream-soft border border-sand-200">
                <div className="w-10 h-10 rounded-full bg-navy text-cream grid place-items-center font-semibold shrink-0">
                  {(l.name || "?").split(" ").map((p) => p[0] || "").filter(Boolean).join("").slice(0, 2) || "?"}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-[14px] font-semibold text-navy">
                    {l.name || "(sans nom)"} {l.co && <span className="text-ink-soft font-normal">· {l.co}</span>}
                  </p>
                  <div className="flex items-center gap-2 text-[11.5px] text-ink-soft mt-0.5">
                    <span>{l.from || "Manuel"}</span>
                  </div>
                </div>
                <select data-testid={`lead-status-${l.id}`} value={l.status} onChange={(e) => updateStatus(l, e.target.value)}
                  className="text-[11.5px] bg-white border border-sand-300 rounded-full px-2.5 py-1.5 font-medium text-navy focus:outline-none focus:border-navy/50 cursor-pointer">
                  {LEAD_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
                <button data-testid={`lead-whatsapp-${l.id || l.name}`} onClick={() => openWA(l)} disabled={sendingTo === l.id}
                  className="inline-flex items-center gap-1.5 px-3 h-9 rounded-full bg-emerald-50 hover:bg-emerald-100 text-emerald-700 text-[12px] font-semibold border border-emerald-200 transition-colors disabled:opacity-50">
                  <MessageCircle size={13} /> WA
                </button>
                <div className="text-right shrink-0 w-12">
                  <p className="font-display text-[18px] text-navy tabular-nums">{l.score}</p>
                  <p className="text-[10px] uppercase text-ink-soft tracking-wider">Score</p>
                </div>
                <button data-testid={`lead-delete-${l.id}`} onClick={() => removeLead(l)}
                  className="w-8 h-8 grid place-items-center rounded-full text-ink-muted hover:bg-red-50 hover:text-red-600 transition-colors">
                  <Trash2 size={14} />
                </button>
              </li>
            ))}
          </ul>
        </>)}
      </div>

      {showAdd && <AddLeadModal onClose={() => setShowAdd(false)} onAdd={addLead} />}
      {waLead && <WaComposer waLead={waLead} setWaLead={setWaLead} onSend={sendWA} sending={sendingTo === waLead.lead.id} isPremium={isPremium} />}
    </>
  );
}
