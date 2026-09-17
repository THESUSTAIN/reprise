import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowLeft, ArrowRight, Camera, Check, CheckCircle2, ChevronDown, Clock, Compass, Copy, ExternalLink, FileText, Folder, Globe, Handshake, HeartPulse, Image, Loader2,
  MessageCircle, Moon, Newspaper, Paperclip, Plus, RefreshCw, Send, ShieldCheck,
  Sparkles, Sun, Wallet, X,
} from "lucide-react";
import { NextSequence } from "./CockpitSections";
import {
  applyCopilotDecision, getChatHistory, getCopilotBrief, getCopilotConfig,
  getCopilotDecision, getCopilotNews, getNewsHistory, getSavedNews, saveNewsItem, deleteSavedNews, archiveNewsEdition,
  sendCopilotWorkRequest, streamChatMessage, sendCopilotMessage, uploadChatFile, generateChatImage,
  getDriveStatus, connectDrive, listDriveFiles, importDriveFileToChat,
  getLastSeenNewsId, setLastSeenNewsId, getDashboardSummary, getDashboardFusion,
} from "../lib/api";

const SUGGESTIONS = [
  "Quelles sont mes priorités aujourd'hui ?",
  "Aide-moi à relancer une facture en retard.",
  "Comment améliorer ma trésorerie ?",
];

function getSessionId() {
  const key = "mx_copilot_session_id";
  let sessionId = localStorage.getItem(key);
  if (!sessionId) {
    sessionId = window.crypto?.randomUUID?.() || `local-${Date.now()}-${Math.random().toString(16).slice(2)}`;
    localStorage.setItem(key, sessionId);
  }
  return sessionId;
}

function renderInline(text, keyBase) {
  const tokens = String(text).split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g);
  return tokens.map((part, i) => {
    if (/^\*\*[^*]+\*\*$/.test(part)) return <strong key={`${keyBase}-b${i}`}>{part.slice(2, -2)}</strong>;
    if (/^\*[^*]+\*$/.test(part)) return <em key={`${keyBase}-i${i}`}>{part.slice(1, -1)}</em>;
    if (/^`[^`]+`$/.test(part)) return <code key={`${keyBase}-c${i}`} className="copilot-md-code">{part.slice(1, -1)}</code>;
    return part;
  });
}

function renderMarkdownLite(text) {
  const lines = String(text || "").split("\n");
  return lines.map((raw, index) => {
    const line = raw.replace(/\s+$/, "");
    const key = `md-${index}`;
    if (/^\s*---+\s*$/.test(line)) return <hr key={key} className="copilot-md-hr" />;
    const heading = line.match(/^\s*(#{1,3})\s+(.*)$/);
    if (heading) {
      const level = heading[1].length;
      const cls = level === 1 ? "copilot-md-h1" : level === 2 ? "copilot-md-h2" : "copilot-md-h3";
      return <div key={key} className={cls}>{renderInline(heading[2], key)}</div>;
    }
    const quote = line.match(/^\s*>\s?(.*)$/);
    if (quote) return <div key={key} className="copilot-md-quote">{renderInline(quote[1], key)}</div>;
    const ordered = line.match(/^\s*(\d+)\.\s+(.*)$/);
    if (ordered) return <div key={key} className="copilot-md-li"><span className="copilot-md-num">{ordered[1]}.</span><span>{renderInline(ordered[2], key)}</span></div>;
    const bullet = line.match(/^\s*[-*]\s+(.*)$/) || line.match(/^\s*\u2022\s+(.*)$/);
    if (bullet) return <div key={key} className="copilot-md-li"><span className="copilot-md-dot">{"\u2022"}</span><span>{renderInline(bullet[1], key)}</span></div>;
    if (!line.trim()) return <div key={key} className="copilot-md-gap" />;
    return <p className="m-0" key={key}>{renderInline(line, key)}</p>;
  });
}


function renderMarkdownLiteOld(text) {
  const lines = String(text || "").split("\n");
  return lines.map((line, index) => {
    const isList = /^[-•]\s+/.test(line);
    const cleanLine = isList ? line.replace(/^[-•]\s+/, "") : line;
    const content = cleanLine.split(/(\*\*[^*]+\*\*)/g).map((part, partIndex) => (
      /^\*\*[^*]+\*\*$/.test(part)
        ? <strong key={partIndex}>{part.slice(2, -2)}</strong>
        : part
    ));
    if (isList) {
      return <div className="flex gap-2" key={index}><span className="text-[#DEC2A3]">•</span><span>{content}</span></div>;
    }
    return <p className="m-0" key={index}>{content.length ? content : " "}</p>;
  });
}

function compactEuro(value) {
  return new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(value || 0);
}

function BriefCard({ data }) {
  if (!data) return null;
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Bonjour" : hour < 18 ? "Bel après-midi" : "Bonsoir";
  const dateLabel = (() => {
    const d = new Date().toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long" });
    return d.charAt(0).toUpperCase() + d.slice(1);
  })();
  const kpis = [
    { label: "CA du mois", value: compactEuro(data.ca_month), detail: data.ca_objective ? `Objectif ${compactEuro(data.ca_objective)}` : "Sans objectif défini", progress: data.pilotage?.progress_percent },
    { label: "Énergie", value: `${data.energy_score || 0}%`, detail: data.bien_etre_label || "À renseigner", progress: data.energy_score || 0 },
    { label: "Alignement", value: `${data.vision?.alignment_percent || 0}%`, detail: "Vision", progress: data.vision?.alignment_percent || 0 },
  ];
  return (
    <div className="glass mb-3 overflow-hidden border-[#DEC2A3]/20 p-3" data-testid="copilot-brief-card">
      <div className="mb-2 flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-[#E8C96A]"><Sun size={13} /> Le point du jour</div>
        <div className="text-[10px] font-medium text-white/55" data-testid="brief-date">{dateLabel}</div>
      </div>
      <div className="text-[14px] font-semibold text-white">{greeting}{data.user?.first_name ? ` ${data.user.first_name}` : ""}</div>
      <p className="m-0 mt-0.5 text-[11.5px] leading-relaxed text-white/75">Voici l’essentiel de ton cockpit en un coup d’œil.</p>
      <div className="mt-3 grid grid-cols-3 gap-1.5">
        {kpis.map((kpi) => (
            <div key={kpi.label} className="rounded-xl border border-white/20 bg-[rgba(66,102,162,0.24)] p-2">
            <div className="text-[9px] uppercase tracking-wide text-white/65">{kpi.label}</div>
            <div className="mt-0.5 truncate text-[12px] font-semibold text-white">{kpi.value}</div>
            <div className="mt-0.5 truncate text-[9px] text-white/65">{kpi.detail}</div>
            <div className="mt-1.5 h-1 overflow-hidden rounded-full bg-white/10"><span className="block h-full rounded-full bg-[#DEC2A3]" style={{ width: `${Math.min(100, Math.max(0, kpi.progress || 0))}%` }} /></div>
          </div>
        ))}
      </div>
      {data.vision?.next_step && <div className="mt-2.5 rounded-xl border border-[#DEC2A3]/20 bg-[#DEC2A3]/10 p-2 text-[11.5px] text-white/80"><strong className="text-[#F0DCA5]">Prochaine étape. </strong>{data.vision.next_step}</div>}
    </div>
  );
}

function formatEventTime(value) {
  if (!value) return "maintenant";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "maintenant";
  return parsed.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
}

function EventStamp({ actor = "MyExtension Business", at, ai = false }) {
  return <div className="copilot-event-stamp" data-testid="copilot-event-stamp"><span className="copilot-event-dot" />{actor} · {formatEventTime(at)}{ai && <span className="copilot-ai-badge">IA</span>}</div>;
}

function DailyFlowSummary({ brief, dashboard, fusion, decisions }) {
  const generated = dashboard?.value_generated;
  const hasGeneratedData = Boolean(generated?.has_data);
  const automated = hasGeneratedData ? Number(generated?.automated_tasks || 0) : null;
  const aiTasks = hasGeneratedData ? Number(generated?.ai_tasks || 0) : null;
  const decisionCount = Array.isArray(decisions) ? decisions.length : 0;
  const priority = fusion?.today_priority?.label || dashboard?.vision?.next_step || brief?.headline || "";
  const items = [];
  if (automated !== null) items.push(`${automated} élément${automated > 1 ? "s" : ""} préparé${automated > 1 ? "s" : ""}`);
  if (aiTasks !== null) items.push(`${aiTasks} action${aiTasks > 1 ? "s" : ""} IA`);
  if (decisionCount) items.push(`${decisionCount} décision${decisionCount > 1 ? "s" : ""} à valider`);
  if (!brief && !dashboard && !fusion) return null;
  return <div className="copilot-daily-summary" data-testid="copilot-daily-summary"><EventStamp at={brief?.generated_at || fusion?.generated_at || null} ai /><div className="copilot-daily-summary-title"><Sparkles size={14} /> Point du jour <span className="copilot-ai-badge">IA</span></div>{brief?.date_label && <div className="copilot-daily-date">{brief.date_label}</div>}<p>{items.length ? `${items.join(" · ")}.` : "Votre point du jour est prêt ; connectez vos données pour enrichir ce résumé."}</p>{priority && <div className="copilot-daily-priority"><strong>Prochain pas :</strong> {priority}</div>}</div>;
}

function RecentTimeline({ items }) {
  const timeline = Array.isArray(items) ? items.filter((item) => item?.label).slice(0, 3) : [];
  if (!timeline.length) return null;
  return <div className="copilot-recent-timeline" data-testid="copilot-recent-timeline"><div className="copilot-result-title"><Clock size={15} /> Derniers mouvements</div>{timeline.map((item, index) => <div className="copilot-timeline-row" key={`${item.at || "event"}-${index}`}><EventStamp at={item.at} /><span>{item.label}</span></div>)}</div>;
}

function ActionResultCard({ result, onOpenTasks }) {
  if (!result?.message) return null;
  return <div className="copilot-action-result" data-testid="copilot-action-result"><EventStamp at={result.at} ai /><div className="copilot-result-title"><CheckCircle2 size={15} /> Résultat préparé</div><p>{result.message}</p>{result.status === "approved" && <button type="button" onClick={onOpenTasks}>Ouvrir Mon Mouvement <ArrowRight size={13} /></button>}</div>;
}

function EmptyDecisionQueue({ onOpenTasks }) {
  return <section className="copilot-decision-empty" data-testid="copilot-decisions-empty">
    <EventStamp actor="MyExtension Business" at={new Date().toISOString()} />
    <div className="copilot-decision-empty-title"><ShieldCheck size={16} /> Validations</div>
    <p>Aucune validation n’est requise pour le moment. Les tâches et décisions à confirmer apparaîtront ici dès qu’elles seront disponibles.</p>
    <button type="button" onClick={onOpenTasks}>Voir les tâches et missions <ArrowRight size={14} /></button>
  </section>;
}

function InlineNewsSources({ sources = [] }) {
  if (!sources.length) return null;
  return <div className="news-inline-sources" data-testid="news-inline-sources"><span>Sources</span>{sources.slice(0, 4).map((source, index) => source?.url ? <a key={`${source.url}-${index}`} href={source.url} target="_blank" rel="noopener noreferrer"><Globe size={11} />{source.source || source.title || "Référence"}</a> : <span key={`${source?.label || "source"}-${index}`}>{source?.label || source?.source || "Référence"}</span>)}</div>;
}

function NewsConversation({ digest, sources, scope, generatedAt, messages, loading, error, status, onRefresh, onAsk, onSaveEdition, history, saved, onRemoveSaved, userName = "Vous" }) {
  // Les quatre actions du Signal du jour posent la question dans la
  // conversation principale (onglet Discussion) au lieu d'ouvrir un second fil.
  const submit = (question) => {
    const nextQuestion = String(question || "").trim();
    if (!nextQuestion || loading) return;
    onAsk(nextQuestion);
  };
  const scopeLabel = [scope?.sector || "entrepreneuriat PME", scope?.region || "France"].join(" · ");
  return <div className="news-conversation flex-1 overflow-y-auto px-4 py-4" data-testid="copilot-news-conversation">
    <div className="news-conversation-intro">
      <EventStamp actor="MyExtension Business · Veille" at={generatedAt} />
      <p>J’ai analysé les évolutions de votre secteur. Voici le signal qui peut influencer votre activité.</p>
      <button type="button" onClick={onRefresh} disabled={loading} data-testid="news-refresh"><RefreshCw size={14} className={loading ? "animate-spin" : ""} /> {loading ? "Actualisation…" : "Actualiser la veille"}</button>
    </div>
    {status && <div className="news-conversation-status">{status}</div>}
    {error && <div className="news-conversation-error">{error}</div>}
    {digest ? <section className="news-signal-card" data-testid="news-signal-card"><EventStamp actor="MyExtension Business · Signal du jour" at={generatedAt} ai /><div className="news-signal-heading"><Newspaper size={15} /> Signal du jour</div><div className="news-signal-scope">{scopeLabel}</div><div className="news-signal-copy">{renderMarkdownLite(digest)}</div><InlineNewsSources sources={sources} /><div className="news-signal-actions"><button type="button" onClick={() => submit("Quel impact concret cette actualité peut-elle avoir sur mon activité ?")}>Quel impact pour moi ?</button><button type="button" onClick={() => submit("Résume cette actualité en trois actions concrètes et proportionnées.")}>3 actions concrètes</button><button type="button" onClick={() => submit("Prépare un brouillon de publication LinkedIn fondé sur cette actualité, sans inventer de faits.")}>Préparer une publication</button><button type="button" onClick={onSaveEdition}>Enregistrer</button></div></section> : !loading && <div className="news-empty-state">Aucun signal de veille n’est disponible pour le moment. Actualisez lorsque vos sources seront connectées.</div>}
    {messages.map((message, index) => <div key={message.id || `${message.created_at || "news"}-${index}`} className={`news-message ${message.role === "user" ? "is-user" : "is-assistant"}`}><EventStamp actor={message.role === "user" ? userName : "MyExtension Business · Veille"} at={message.created_at || message.updated_at} /><div className="news-message-bubble">{message.pending ? <Loader2 size={16} className="animate-spin" /> : renderMarkdownLite(message.content)}{message.role === "assistant" && <InlineNewsSources sources={message.sources || []} />}</div></div>)}
    <details className="news-secondary-panel"><summary>Éditions précédentes <span>{history.length}</span></summary><div>{history.slice(0, 8).map((item) => <details key={item.id} className="news-history-item"><summary>{item.title || "Édition de veille"}</summary><p>{item.published_at ? new Date(item.published_at).toLocaleString("fr-FR", { dateStyle: "medium", timeStyle: "short" }) : "Date indisponible"}</p><div>{renderMarkdownLite(item.digest || item.content || "Contenu détaillé indisponible.")}</div></details>) || <p>Aucune édition précédente.</p>}</div></details>
    <details className="news-secondary-panel"><summary>Éléments enregistrés <span>{saved.length}</span></summary><div>{saved.slice(0, 12).map((item) => <div className="news-saved-item" key={item.id}><div><strong>{item.title}</strong><small>{item.source || "Veille Copilote"}</small></div><div>{item.url && <a href={item.url} target="_blank" rel="noopener noreferrer">Ouvrir</a>}<button type="button" onClick={() => onRemoveSaved(item.id)}>Retirer</button></div></div>) || <p>Aucun élément enregistré.</p>}</div></details>
    {/* Le second champ de saisie a été retiré : deux barres de chat dans le
        même panneau (une par onglet) rendaient impossible de savoir dans
        quelle conversation on écrivait. Une seule barre, dans Discussion. */}
  </div>;
}

const DECISION_DOMAIN = {
  vision: { label: "Vision", icon: Compass, color: "#93c5fd" },
  pilotage: { label: "Pilotage", icon: Wallet, color: "#6ee7b7" },
  bienetre: { label: "Bien-être", icon: HeartPulse, color: "#fca5a5" },
};

function DraftMessage({ content }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    try { await navigator.clipboard.writeText(content); setCopied(true); setTimeout(() => setCopied(false), 2000); } catch {}
  };
  // Sépare "Objet : ..." du corps si l'IA l'a inclus — sinon, tout part dans
  // le corps avec un objet générique. mailto: ouvre le client mail de
  // l'utilisateur (Gmail, Outlook…) avec le brouillon prérempli : la seule
  // vraie option d'envoi possible aujourd'hui, sans service email ni adresse
  // stockée côté serveur.
  const lines = content.split("\n");
  const subjectLine = lines.find((l) => /^objet\s*:/i.test(l.trim()));
  const subject = subjectLine ? subjectLine.replace(/^objet\s*:/i, "").trim() : "Relance de facture";
  const body = subjectLine ? lines.filter((l) => l !== subjectLine).join("\n").trim() : content;
  const mailtoHref = `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  return (
    <div className="rounded-xl border border-[#DEC2A3]/35 bg-[#0c1d33]/40 p-3" data-testid="copilot-draft-message">
      <div className="mb-1.5 flex items-center justify-between gap-2">
        <span className="text-[10px] font-bold uppercase tracking-wide text-[#E8C96A]">Brouillon rédigé par l'IA — prêt à envoyer</span>
        <div className="flex shrink-0 items-center gap-2">
          <button onClick={copy} className="inline-flex items-center gap-1 text-[11px] font-semibold text-[#E8C96A] hover:text-white" data-testid="draft-copy">
            {copied ? <Check size={12} /> : <Copy size={12} />} {copied ? "Copié" : "Copier"}
          </button>
          <a href={mailtoHref} className="inline-flex items-center gap-1 rounded-full bg-[#DEC2A3] px-2.5 py-1 text-[11px] font-semibold text-[#0c1d33] hover:opacity-90" data-testid="draft-transmit">
            <Send size={12} /> Transmettre
          </a>
        </div>
      </div>
      <p className="m-0 whitespace-pre-wrap text-[12px] leading-relaxed text-white/85">{content}</p>
    </div>
  );
}

function ActionCard({ card, onDecision, busy, index = 0 }) {
  const rank = index + 1;
  const [expanded, setExpanded] = useState(rank === 1);
  if (!card) return null;
  const decided = card.status && card.status !== "pending";
  const approved = card.status === "approved";
  const domain = DECISION_DOMAIN[card.source_key] || DECISION_DOMAIN.vision;
  const DomainIcon = domain.icon;
  const urgent = card.priority === "urgent" || card.urgency === "high" || card.is_urgent === true;
  const whyNow = card.why_now || card.reason || "Cette décision est proposée à partir de votre Vision et des signaux actuellement disponibles.";
  const pillar = card.pillar || card.vision_pillar || domain.label;
  const impact = card.impact || card.expected_impact || "Impact à confirmer après validation";
  const delayCost = card.cost_of_delay || card.delay_cost;
  return (
    <div className={`rounded-2xl border p-3.5 transition-all duration-500 ${rank === 1 ? "border-[#DEC2A3]/65 bg-[#DEC2A3]/[0.09] shadow-[0_0_24px_rgba(222, 194, 163,0.08)]" : "border-white/30 bg-white/[0.08]"} ${urgent ? "border-rose-400/80 bg-rose-400/10" : ""} ${card.justCreated ? "mission-created-exit" : ""}`} data-testid={`copilot-action-card-${card.source_key}`} data-urgent={urgent ? "true" : "false"} data-priority-rank={rank}>
      <button type="button" className="mb-2 flex w-full items-center gap-2.5 text-left" onClick={() => setExpanded((value) => !value)} aria-expanded={expanded} data-testid={`copilot-action-toggle-${rank}`}>
        <span className={`inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-xl ${rank === 1 ? "bg-[#DEC2A3] text-[#0c1d33]" : "bg-[#DEC2A3]/20 text-[#E8C96A]"}`}><strong className="text-[13px]">{rank}</strong></span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wide" style={{ color: domain.color }}><DomainIcon size={11} /> {domain.label} · {rank === 1 ? "Aujourd’hui" : "Ensuite"} <span className="copilot-ai-badge">IA</span></div>
          <div className="text-[11px] text-white/75">{rank === 1 ? "Priorité principale — pourquoi maintenant ?" : "Priorité secondaire à traiter après la précédente."}</div>
        </div>
        <ChevronDown size={18} className={`shrink-0 text-white/65 transition-transform ${expanded ? "rotate-180" : ""}`} />
      </button>
      {expanded && <div className="decision-card-body">
        <p className="m-0 text-[12.5px] font-medium leading-relaxed text-white">{card.title}</p>
        <p className="m-0 mb-2 mt-1 text-[11.5px] leading-relaxed text-white/75">{card.detail}</p>
        <div className="mb-3 grid gap-1.5 rounded-xl border border-white/10 bg-white/[0.04] p-2.5 text-[10.5px] leading-relaxed text-white/70">
          <span><strong className="text-[#F0DCA5]">Pourquoi maintenant ?</strong> {whyNow}</span>
          <span><strong className="text-[#F0DCA5]">Pilier Vision :</strong> {pillar} · <strong className="text-[#F0DCA5]">Impact :</strong> {impact}</span>
          {delayCost && <span><strong className="text-[#F0DCA5]">Coût du report :</strong> {delayCost}</span>}
          <span className="inline-flex items-center gap-1 text-white/50"><Compass size={11} /> Vision → {pillar} → Décision → Mission</span>
        </div>
        {decided ? (
          <div className="flex flex-col gap-2">
            <div className={`inline-flex items-center gap-1.5 text-[12px] font-semibold ${approved ? "text-emerald-300" : "text-white/65"}`}>
              {approved ? <CheckCircle2 size={14} /> : <Clock size={14} />}{approved ? "Approuvé — mission créée" : "Reporté — à revoir dans le prochain point du jour"}
            </div>
            {approved && card.draft_content && <DraftMessage content={card.draft_content} />}
          </div>
        ) : (
          <div className="flex gap-2">
            <button onClick={() => onDecision(card.id, "approve")} disabled={busy} className="flex-1 inline-flex h-9 items-center justify-center gap-1.5 rounded-xl bg-[#DEC2A3] text-[12px] font-semibold text-[#0c1d33] transition-opacity hover:opacity-90 disabled:opacity-60" data-testid="copilot-action-approve">{busy ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />} Approuver</button>
            <button onClick={() => onDecision(card.id, "defer")} disabled={busy} className="flex-1 inline-flex h-9 items-center justify-center gap-1.5 rounded-xl border border-white/15 bg-white/5 text-[12px] font-semibold text-white/75 transition-colors hover:bg-white/10 disabled:opacity-60" data-testid="copilot-action-defer"><Clock size={14} /> Reporter</button>
          </div>
        )}
      </div>}
    </div>
  );
}

export default function ChatPanel({ context, initialAsk, onBack }) {
  const navigate = useNavigate();
  const sessionId = useMemo(getSessionId, []);
  const visionContextLabel = String(context || "").match(/Onglet Vision actif : ([^.]+)/)?.[1] || null;
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [attachments, setAttachments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [hubLight, setHubLight] = useState(() => document.documentElement.classList.contains("ambiance-clarte"));
  const [uploading, setUploading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [tab, setTab] = useState("chat");
  const [brief, setBrief] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [fusion, setFusion] = useState(null);
  const [dailyDecisions, setDailyDecisions] = useState([]);
  const [actionResults, setActionResults] = useState([]);
  const [decisionBusyId, setDecisionBusyId] = useState(null);
  const [newsText, setNewsText] = useState("");
  const [newsSources, setNewsSources] = useState([]);
  const [newsMessages, setNewsMessages] = useState([]);
  const [newsConversationLoading, setNewsConversationLoading] = useState(false);
  const [newsError, setNewsError] = useState("");
  const [newsLoading, setNewsLoading] = useState(false);
  const [newsScope, setNewsScope] = useState({ sector: "", region: "", frequency_per_week: 1, next_refresh_at: "" });
  // L’endpoint Final-main growth/news-digest ne retourne pas toujours generated_at.
  // Initialiser avec l’instant de chargement permet d’afficher une édition datée,
  // sans prétendre qu’il s’agit de la date de publication de la source.
  const [newsGeneratedAt, setNewsGeneratedAt] = useState(() => new Date().toISOString());
  const [newsStatusMessage, setNewsStatusMessage] = useState("");
  const [newsRefsOpen, setNewsRefsOpen] = useState(false);
  const [savedNews, setSavedNews] = useState([]);
  const [newsHistory, setNewsHistory] = useState([]);
  const [selectedNewsEdition, setSelectedNewsEdition] = useState(null);
  // Compteur d'éditions non vues sur l'onglet Actualité — un vrai nombre,
  // pas juste un point rouge, pour savoir combien de nouvelles éditions
  // sont arrivées depuis la dernière consultation.
  const [unseenNewsCount, setUnseenNewsCount] = useState(0);
  const toggleHubTheme = () => {
    const next = !hubLight;
    document.documentElement.classList.toggle("ambiance-clarte", next);
    setHubLight(next);
    try {
      const raw = JSON.parse(localStorage.getItem("cours-main-settings-preferences") || "{}");
      localStorage.setItem("cours-main-settings-preferences", JSON.stringify({ ...raw, theme: next ? "light" : "dark", ambiance: next ? "clarte" : "sens" }));
    } catch { /* noop */ }
  };
  useEffect(() => {
    if (!newsHistory.length) return;
    getLastSeenNewsId().then((lastSeen) => {
      if (!lastSeen) { setUnseenNewsCount(newsHistory.length); return; }
      const idx = newsHistory.findIndex((item) => item.id === lastSeen);
      setUnseenNewsCount(idx === -1 ? newsHistory.length : idx);
    }).catch(() => {});
  }, [newsHistory]);
  const markNewsTabSeen = () => {
    if (!newsHistory.length) return;
    setUnseenNewsCount(0);
    setLastSeenNewsId(newsHistory[0].id).catch(() => {});
  };
  const [contactOpen, setContactOpen] = useState(false);
  const [decisionView, setDecisionView] = useState(null);
  useEffect(() => {
    if (!contactOpen) return undefined;
    const onKeyDown = (event) => { if (event.key === "Escape") setContactOpen(false); };
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    document.addEventListener("keydown", onKeyDown);
    return () => { document.body.style.overflow = previousOverflow; document.removeEventListener("keydown", onKeyDown); };
  }, [contactOpen]);
  const [contactMessage, setContactMessage] = useState("");
  const [contactSent, setContactSent] = useState(false);
  const [whatsappUrl, setWhatsappUrl] = useState("");
  const scrollRef = useRef(null);
  const fileRef = useRef(null);
  const initialChatPositionedRef = useRef(false);
  const keepChatAtBottomRef = useRef(false);
  const lastAutoAskRef = useRef(null);

  useEffect(() => {
    let active = true;
    // Chacun de ces appels est isolé (son propre .catch) plutôt que dans un
    // seul Promise.all : /chat/decision, /chat/news-history et /chat/news-saved
    // n'ont AUCUNE route backend dans ce projet (vérifié) — avant ce correctif,
    // un seul de ces appels en échec (404) rejetait le Promise.all entier et
    // vidait TOUT l'historique de conversation (setMessages([])), même quand
    // getChatHistory lui-même avait réussi. Le Copilote pouvait donc paraître
    // vide à chaque ouverture alors que l'historique existait bel et bien.
    Promise.allSettled([
      getChatHistory(sessionId), getCopilotBrief(sessionId), getDashboardSummary(), getDashboardFusion(), getCopilotConfig(),
      getCopilotDecision(sessionId), getSavedNews(sessionId), getNewsHistory(sessionId),
    ]).then(([history, dailyBrief, dashboardResult, fusionResult, config, decision, saved, newsHistoryResult]) => {
        if (!active) return;
        setMessages(history.status === "fulfilled" ? history.value : []);
        setBrief(dailyBrief.status === "fulfilled" ? dailyBrief.value : null);
        setDashboard(dashboardResult.status === "fulfilled" ? dashboardResult.value : null);
        setFusion(fusionResult.status === "fulfilled" ? fusionResult.value : null);
        setWhatsappUrl(config.status === "fulfilled" ? (config.value?.whatsapp_url || "") : "");
        const loadedDecisions = decision.status === "fulfilled" && Array.isArray(decision.value?.decisions) ? decision.value.decisions : [];
        setDailyDecisions(loadedDecisions.filter((item) => item.status !== "approved"));
        setSavedNews(saved.status === "fulfilled" && Array.isArray(saved.value?.items) ? saved.value.items : []);
        setNewsHistory(newsHistoryResult.status === "fulfilled" && Array.isArray(newsHistoryResult.value?.items) ? newsHistoryResult.value.items : []);
      })
      .catch(() => { if (active) setMessages([]); })
      .finally(() => { if (active) setHistoryLoading(false); });
    return () => { active = false; };
  }, [sessionId]);

  useEffect(() => {
    if (!scrollRef.current || tab !== "chat") return;
    // À l’ouverture, la priorité est la boucle Vision → Décision → Mission,
    // notamment sur téléphone. On ne la masque donc jamais sous le fil de discussion.
    if (!initialChatPositionedRef.current) {
      scrollRef.current.scrollTop = 0;
      initialChatPositionedRef.current = true;
      return;
    }
    // Ensuite seulement, une vraie interaction de l’utilisateur suit naturellement le dernier message.
    if (keepChatAtBottomRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, loading, attachments, tab]);

  useEffect(() => {
    const openFromApp = (event) => {
      const question = event?.detail?.ask;
      if (question) setTimeout(() => send(question), 50);
    };
    window.addEventListener("cours:open-copilot", openFromApp);
    return () => window.removeEventListener("cours:open-copilot", openFromApp);
  });

  const send = async (rawMessage) => {
    const message = (rawMessage ?? input).trim();
    if (imageMode) { await generateImageFromChat(message); return; }
    if ((!message && attachments.length === 0) || loading || uploading) return;
    keepChatAtBottomRef.current = true;
    const attachmentLabels = attachments.map((file) => `📎 ${file.name}`);
    const visibleMessage = [message, ...attachmentLabels].filter(Boolean).join("\n");
    // Le contenu extrait des pièces jointes (texte de PDF, DOCX, etc.) n'était
    // jamais transmis à l'IA — seul le nom du fichier apparaissait, l'IA ne
    // "voyait" donc jamais ce qu'il y avait dedans. Corrigé : injecté dans le
    // message envoyé (pas dans le message affiché, pour ne pas polluer la vue).
    const attachmentContext = attachments
      .filter((file) => file.extracted_text && file.extracted_text.trim())
      .map((file) => `--- Fichier joint : ${file.name} ---\n${file.extracted_text.slice(0, 6000)}`)
      .join("\n\n");
    const messageForAI = [message, attachmentContext].filter(Boolean).join("\n\n");
    const priorHistory = messages;
    const requestedAt = new Date().toISOString();
    setInput(""); setAttachments([]); setTab("chat"); setLoading(true);
    setMessages((current) => [...current, { role: "user", content: visibleMessage, created_at: requestedAt }, { role: "assistant", content: "", pending: true, created_at: requestedAt }]);
    try {
      // sendCopilotMessage() (POST /api/growth/copilote) est le vrai backend —
      // pas de streaming token-par-token (contrairement à l'ancien appel
      // /chat/messages, qui n'a jamais eu de route serveur). La réponse arrive
      // en un bloc ; on l'affiche directement.
      const replyData = await sendCopilotMessage({
        message: messageForAI || "Analyse les pièces jointes et indique-moi la prochaine action utile.",
        session: sessionId,
        history: priorHistory,
      });
      const reply = typeof replyData === "string" ? replyData : (replyData?.reply || "");
      const sources = typeof replyData === "string" ? [] : (replyData?.sources || []);
      setMessages((current) => {
        const next = [...current]; next[next.length - 1] = { role: "assistant", content: reply, sources, created_at: new Date().toISOString() }; return next;
      });
    } catch (error) {
      setMessages((current) => {
        const next = [...current]; next[next.length - 1] = { role: "assistant", content: error?.message || "Désolé, le copilote est indisponible pour le moment. Réessaie dans un instant.", created_at: new Date().toISOString() }; return next;
      });
    } finally { setLoading(false); }
  };

  // Ouvert depuis un autre écran (bouton "Transformer en action" sur Vision,
  // "Parler au copilote" sur Bien-être) — voir Layout.jsx qui écoute
  // "cours:open-copilot" et transmet la question ici.
  useEffect(() => {
    if (!initialAsk || initialAsk === lastAutoAskRef.current) return;
    lastAutoAskRef.current = initialAsk;
    send(initialAsk);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialAsk]);

  const handleUpload = async (event) => {
    const files = Array.from(event.target.files || []); event.target.value = "";
    if (!files.length) return;
    setUploading(true);
    try {
      const uploaded = [];
      for (const file of files.slice(0, Math.max(0, 5 - attachments.length))) uploaded.push(await uploadChatFile(file));
      setAttachments((current) => [...current, ...uploaded]);
    } catch (error) {
      setMessages((current) => [...current, { role: "assistant", content: error?.response?.data?.detail || "Impossible d’ajouter ce fichier. Vérifie son format et sa taille." }]);
    } finally { setUploading(false); }
  };

  // Capture d'écran — repris du même mécanisme que app-main (getDisplayMedia +
  // canvas), rebranché sur le vrai endpoint d'upload de ce projet. L'utilisateur
  // choisit quoi partager (onglet, fenêtre, écran) via la boîte native du
  // navigateur ; rien n'est capturé sans son geste explicite.
  const handleScreenCapture = async () => {
    try {
      const stream = await navigator.mediaDevices.getDisplayMedia({ video: true });
      const video = document.createElement("video");
      video.srcObject = stream;
      await video.play();
      await new Promise((resolve) => setTimeout(resolve, 250));
      const canvas = document.createElement("canvas");
      canvas.width = video.videoWidth; canvas.height = video.videoHeight;
      canvas.getContext("2d").drawImage(video, 0, 0);
      stream.getTracks().forEach((track) => track.stop());
      canvas.toBlob(async (blob) => {
        if (!blob) return;
        const file = new File([blob], `capture-${Date.now()}.png`, { type: "image/png" });
        setUploading(true);
        try {
          const uploaded = await uploadChatFile(file);
          setAttachments((current) => [...current, uploaded]);
        } catch {
          setMessages((current) => [...current, { role: "assistant", content: "Impossible d’ajouter la capture d’écran." }]);
        } finally { setUploading(false); }
      }, "image/png");
    } catch (error) {
      if (error?.name !== "AbortError" && error?.name !== "NotAllowedError") {
        setMessages((current) => [...current, { role: "assistant", content: "Capture d’écran non disponible sur cet appareil/navigateur." }]);
      }
    }
  };

  // Génération d'image — vrai endpoint /chat/image (coûte des crédits, géré
  // côté serveur). Le prompt saisi devient un message utilisateur normal dans
  // l'historique, et l'image générée s'affiche directement dans la conversation.
  const [generatingImage, setGeneratingImage] = useState(false);
  const generateImageFromChat = async (prompt) => {
    const clean = prompt.trim();
    if (!clean || generatingImage) return;
    keepChatAtBottomRef.current = true;
    setInput(""); setTab("chat"); setGeneratingImage(true);
    setMessages((current) => [...current, { role: "user", content: `🎨 ${clean}` }, { role: "assistant", content: "", pending: true, generatingImage: true }]);
    try {
      const result = await generateChatImage(clean);
      const imageUrl = result?.image_url || result?.url;
      setMessages((current) => {
        const next = [...current];
        next[next.length - 1] = imageUrl
          ? { role: "assistant", content: result?.text || "Voici votre image.", imageUrl }
          : { role: "assistant", content: "Je n’ai pas réussi à générer d’image cette fois — réessaie avec une description différente." };
        return next;
      });
    } catch (error) {
      setMessages((current) => {
        const next = [...current];
        next[next.length - 1] = { role: "assistant", content: error?.response?.data?.detail || "Génération d’image indisponible pour le moment." };
        return next;
      });
    } finally { setGeneratingImage(false); }
  };
  const [imageMode, setImageMode] = useState(false);
  // Menu "+" : regroupe Capture / Générer une image / Drive, plutôt que
  // 3 icônes séparées qui prenaient toute la largeur de la barre — pattern
  // repris des chats "+" (ChatGPT/Claude) plutôt que 3 boutons permanents.
  const [plusOpen, setPlusOpen] = useState(false);
  const plusRef = useRef(null);
  const [driveConnected, setDriveConnected] = useState(null); // null = pas encore vérifié
  const [driveOpen, setDriveOpen] = useState(false);
  const [driveFiles, setDriveFiles] = useState([]);
  const [driveLoading, setDriveLoading] = useState(false);
  useEffect(() => {
    getDriveStatus().then((r) => setDriveConnected(Boolean(r?.connected))).catch(() => setDriveConnected(false));
  }, []);
  useEffect(() => {
    if (!plusOpen) return undefined;
    const onClickOutside = (event) => { if (plusRef.current && !plusRef.current.contains(event.target)) setPlusOpen(false); };
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, [plusOpen]);
  const openDrive = async () => {
    setPlusOpen(false);
    if (!driveConnected) {
      try { const { authorization_url } = await connectDrive(); if (authorization_url) window.location.href = authorization_url; }
      catch { setMessages((current) => [...current, { role: "assistant", content: "Connexion à Google Drive indisponible pour le moment." }]); }
      return;
    }
    setDriveOpen(true);
    setDriveLoading(true);
    try { const r = await listDriveFiles("root"); setDriveFiles(r?.files || []); }
    catch { setDriveFiles([]); }
    finally { setDriveLoading(false); }
  };
  const importDriveFile = async (file) => {
    setDriveOpen(false);
    setUploading(true);
    try { const uploaded = await importDriveFileToChat(file.id, file.name); setAttachments((current) => [...current, uploaded]); }
    catch { setMessages((current) => [...current, { role: "assistant", content: `Impossible d'importer "${file.name}" depuis Drive.` }]); }
    finally { setUploading(false); }
  };

  const decideCard = async (decisionId, decision) => {
    if (!decisionId || decisionBusyId) return;
    setDecisionBusyId(decisionId);
    try {
      const currentDecision = dailyDecisions.find((item) => item.id === decisionId);
      const result = await applyCopilotDecision({ id: decisionId, session: sessionId, decision });
      setDailyDecisions((current) => decision === "approve"
        ? current.map((d) => d.id === decisionId ? { ...d, justCreated: true, status: result.status } : d)
        : current.map((d) => (d.id === decisionId ? { ...d, ...result } : d)));
      setMessages((current) => [...current, { role: "assistant", content: result.message, created_at: new Date().toISOString() }]);
      setActionResults((current) => [{ id: `${decisionId}-${Date.now()}`, title: currentDecision?.title || "Décision", message: result.message, status: result.status, at: new Date().toISOString() }, ...current].slice(0, 3));
      if (decision === "approve") setTimeout(() => setDailyDecisions((current) => current.filter((d) => d.id !== decisionId)), 520);
    } catch (error) {
      setMessages((current) => [...current, { role: "assistant", content: error?.response?.data?.detail || "Impossible d’enregistrer cette décision pour le moment." }]);
    } finally {
      setDecisionBusyId(null);
    }
  };

  const loadNews = async (manualRefresh = false) => {
    if (newsLoading) return;
    setNewsLoading(true); setNewsError("");
    try {
      const previousGeneratedAt = newsGeneratedAt;
      const result = await getCopilotNews(sessionId, manualRefresh);
      if (!result?.ok || !result?.digest) {
        if (newsText) setNewsError("Impossible d’actualiser pour le moment : la veille précédente est conservée.");
        else {
          setNewsText(result?.digest || "Aucune actualité disponible pour le moment.");
          setNewsGeneratedAt(new Date().toISOString());
        }
      } else {
        setNewsText(result.digest); setNewsSources(Array.isArray(result.sources) ? result.sources : []);
        // growth/news-digest ne fournit pas toujours generated_at : la date de réception
        // est alors la seule date honnête à afficher pour l'édition rendue.
        setNewsGeneratedAt(result.generated_at || new Date().toISOString());
        if (manualRefresh) setNewsStatusMessage(previousGeneratedAt && previousGeneratedAt === result.generated_at ? "Aucune nouvelle actualité pertinente depuis la dernière édition. Votre veille reste à jour." : "Une nouvelle édition de votre veille vient d’être publiée.");
        setNewsScope({ sector: result.sector || "entrepreneuriat PME", region: result.region || "France", frequency_per_week: Number(result.frequency_per_week) === 2 ? 2 : 1, next_refresh_at: result.next_refresh_at || "" });
        await archiveNewsEdition(sessionId, {
          digest: result.digest, sources: Array.isArray(result.sources) ? result.sources : [],
          generated_at: result.generated_at || new Date().toISOString(),
          sector: result.sector || "", region: result.region || "",
        }).catch(() => {});
        getNewsHistory(sessionId).then((historyResult) => setNewsHistory(Array.isArray(historyResult?.items) ? historyResult.items : [])).catch(() => {});
      }
    } catch {
      if (newsText) setNewsError("Impossible d’actualiser pour le moment : la veille précédente est conservée.");
      else {
        setNewsText("Impossible de récupérer l’actualité à l’instant. Réessaie plus tard.");
        setNewsGeneratedAt(new Date().toISOString());
      }
    } finally { setNewsLoading(false); }
  };

  // Charge automatiquement la veille à l’ouverture. Le backend respecte la cadence
  // enregistrée : il réutilise le digest jusqu’à la prochaine échéance, puis le régénère.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { loadNews(false); }, [sessionId]);

  const saveNews = async (item) => {
    if (!item?.title && !newsText) return;
    try {
      const result = await saveNewsItem(sessionId, {
        kind: item ? "article" : "edition",
        title: item?.title || `Veille sectorielle — ${new Date().toLocaleDateString("fr-FR")}`,
        url: item?.url || "",
        source: item?.source || "Veille Copilote",
        published_at: item?.published_at || new Date().toISOString(),
        sector: newsScope.sector,
        region: newsScope.region,
        digest: item ? "" : newsText,
      });
      if (result?.item && !result.duplicate) setSavedNews((current) => [result.item, ...current]);
    } catch { setNewsError("Impossible d’enregistrer cet élément pour le moment."); }
  };

  const removeSavedNews = async (itemId) => {
    try {
      const result = await deleteSavedNews(sessionId, itemId);
      setSavedNews(Array.isArray(result?.items) ? result.items : []);
    } catch { setNewsError("Impossible de supprimer cet élément pour le moment."); }
  };

  const askNews = async (question) => {
    const cleanQuestion = String(question || "").trim();
    if (!cleanQuestion || newsConversationLoading) return;
    const requestedAt = new Date().toISOString();
    const contextSources = newsSources.slice(0, 6).map((source) => `${source.title || source.source || "Source"}${source.url ? ` (${source.url})` : ""}`).join("\n");
    const newsContext = [
      "Tu es le Copilote de MyExtension Business, produit de la marque ZAYADO, spécialisé dans la veille. Réponds uniquement à partir de la veille ci-dessous et signale explicitement toute incertitude.",
      `Secteur : ${newsScope.sector || "entrepreneuriat PME"} · Région : ${newsScope.region || "France"}`,
      `Veille actuelle :\n${newsText || "Aucune édition disponible."}`,
      contextSources ? `Sources disponibles :\n${contextSources}` : "",
      `Question de l’utilisateur : ${cleanQuestion}`,
    ].filter(Boolean).join("\n\n");
    setNewsMessages((current) => [...current, { role: "user", content: cleanQuestion, created_at: requestedAt }, { role: "assistant", content: "", pending: true, created_at: requestedAt }]);
    setNewsConversationLoading(true);
    try {
      const replyData = await sendCopilotMessage({ message: newsContext, session: `${sessionId}:news`, history: newsMessages });
      const reply = typeof replyData === "string" ? replyData : (replyData?.reply || "");
      const replySources = typeof replyData === "string" ? newsSources : (replyData?.sources || newsSources);
      setNewsMessages((current) => { const next = [...current]; next[next.length - 1] = { role: "assistant", content: reply || "Je n’ai pas assez d’éléments fiables pour répondre à cette question.", sources: replySources, created_at: new Date().toISOString() }; return next; });
    } catch (error) {
      setNewsMessages((current) => { const next = [...current]; next[next.length - 1] = { role: "assistant", content: error?.message || "La conversation de veille est indisponible pour le moment. Réessaie dans un instant.", created_at: new Date().toISOString() }; return next; });
    } finally { setNewsConversationLoading(false); }
  };

  const sendWorkRequest = async () => {
    const message = contactMessage.trim();
    if (!message || contactSent) return;
    try {
      const result = await sendCopilotWorkRequest({ session: sessionId, message, channel: "chat" });
      setContactSent(true); setContactMessage("");
      setMessages((current) => [...current, { role: "assistant", content: result.message || "Votre demande est bien enregistrée." }]);
      setTimeout(() => { setContactOpen(false); setContactSent(false); }, 1800);
    } catch { setMessages((current) => [...current, { role: "assistant", content: "Impossible d’envoyer la demande pour le moment. Réessaie plus tard." }]); }
  };

  return (
    <div className="relative flex h-full w-full flex-col" data-testid="copilot-panel">
      <div className="border-b border-white/10 px-5 py-3.5">
        <div className="flex items-center justify-between gap-3">
          <div className="flex min-w-0 items-center gap-2.5" data-testid="hub-product-identity">
            <div className="hub-product-mark flex h-9 w-9 shrink-0 items-center justify-center rounded-xl"><img src="/logo-zayado.png" alt="" className="hub-product-logo" /></div><div className="min-w-0"><div className="hub-product-name">MyExtension Business</div><p className="hub-product-subtitle">Hub IA · par ZAYADO</p>{visionContextLabel && <div className="hub-context-label mt-1 inline-flex max-w-full truncate rounded-full px-2 py-0.5">Vision · {visionContextLabel}</div>}</div></div>
          <div className="flex shrink-0 items-center gap-2">
            {onBack && <button type="button" onClick={onBack} className="inline-flex h-8 items-center gap-1.5 rounded-full border border-white/25 bg-white/10 px-3 text-[11px] font-semibold text-white hover:border-[#DEC2A3]/60 hover:text-[#F0DCA5]" title="Retour" aria-label="Retour" data-testid="copilot-back"><ArrowLeft size={14} /> <span>Retour</span></button>}
            <button type="button" onClick={toggleHubTheme} className="hub-theme-toggle" title={hubLight ? "Activer le mode dark" : "Activer le mode clair"} aria-label={hubLight ? "Activer le mode dark" : "Activer le mode clair"} data-testid="hub-theme-toggle">{hubLight ? <Moon size={16} /> : <Sun size={16} />}</button>
            <button onClick={() => setContactOpen((value) => !value)} className={`copilot-contact-button inline-flex h-9 items-center gap-1.5 rounded-full border px-3 text-[11px] font-semibold transition-colors ${contactOpen ? "is-open" : ""}`} title="Travailler avec l’équipe" aria-label="Travailler avec l’équipe" data-testid="copilot-contact"><Handshake size={16} /> <span>Collaborer</span></button>
          </div>
        </div>
        <div className="mt-3 grid grid-cols-2 border-b border-white/10" data-testid="copilot-tabs">
          <button onClick={() => setTab("chat")} className={`copilot-tab inline-flex h-9 items-center justify-center gap-1.5 border-b-2 text-[11.5px] font-medium transition-colors ${tab === "chat" ? "is-active" : ""}`}><MessageCircle size={14} /> Discussion</button>
          <button onClick={() => { setTab("news-conversation"); markNewsTabSeen(); }} className={`copilot-tab inline-flex h-9 items-center justify-center gap-1.5 border-b-2 text-[11.5px] font-medium transition-colors ${tab === "news-conversation" ? "is-active" : ""}`}><Newspaper size={14} /> Actualité{unseenNewsCount > 0 && <span className="ml-0.5 inline-flex h-4 min-w-[16px] items-center justify-center rounded-full bg-rose-500 px-1 text-[9px] font-bold text-white" data-testid="copilot-news-count">{unseenNewsCount}</span>}</button>
        </div>
      </div>

      {tab === "news-conversation" && <NewsConversation digest={newsText} sources={newsSources} scope={newsScope} generatedAt={newsGeneratedAt} messages={newsMessages} loading={newsLoading || newsConversationLoading} error={newsError} status={newsStatusMessage} onRefresh={() => loadNews(true)} onAsk={(question) => { setTab("chat"); send(question); }} onSaveEdition={() => saveNews()} history={newsHistory} saved={savedNews} onRemoveSaved={removeSavedNews} userName={dashboard?.user?.first_name || dashboard?.user?.name || "Vous"} />}

      {contactOpen && <div className="copilot-collab-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setContactOpen(false); }}><section className="copilot-collab-modal" role="dialog" aria-modal="true" aria-labelledby="copilot-collab-title" data-testid="copilot-contact-panel"><div className="copilot-collab-modal-header"><div><div className="copilot-collab-eyebrow">Collaboration</div><h2 id="copilot-collab-title">Avancer avec l’équipe</h2></div><button type="button" onClick={() => setContactOpen(false)} className="copilot-collab-close" aria-label="Fermer la fenêtre Collaborer"><X size={18} /></button></div><p className="copilot-collab-description">Décrivez votre besoin. Votre demande reste séparée du fil IA et sera envoyée à l’équipe sans exécution automatique.</p>{whatsappUrl && <a className="copilot-collab-whatsapp" href={whatsappUrl} target="_blank" rel="noopener noreferrer"><ExternalLink size={13} /> Discuter sur WhatsApp</a>}<label className="copilot-collab-label" htmlFor="copilot-contact-message">Votre besoin</label><textarea id="copilot-contact-message" value={contactMessage} onChange={(event) => setContactMessage(event.target.value)} rows={4} placeholder="Décrivez votre besoin en une phrase…" className="copilot-collab-textarea" data-testid="copilot-contact-message" /><button onClick={sendWorkRequest} disabled={!contactMessage.trim() || contactSent} className="copilot-collab-submit" data-testid="copilot-contact-send">{contactSent ? "Demande enregistrée" : "Envoyer la demande"} <ArrowRight size={15} /></button><button type="button" className="copilot-collab-link" data-testid="copilot-contact-open-page" onClick={() => { setContactOpen(false); navigate("/collaborateur"); }}>Voir mes demandes et leur suivi <ArrowRight size={13} /></button></section></div>}

      {tab === "chat" && <>
        <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto px-4 py-4" data-testid="copilot-messages">
          {!historyLoading && messages.length === 0 && <div className="flex justify-start" data-testid="copilot-opening-greeting"><div className="copilot-message-shell max-w-[87%]" style={{ background: "transparent" }}><EventStamp actor="MyExtension Business" at={new Date().toISOString()} /><div className="copilot-chat-bubble is-assistant rounded-2xl px-3.5 py-2.5 text-[13px] leading-relaxed glass"><p className="m-0">Bonjour. J’ai veillé sur votre activité. Voici votre point du jour et les actions qui méritent votre attention.</p></div></div></div>}
          {!historyLoading && <RecentTimeline items={fusion?.timeline} />}
          {!historyLoading && dailyDecisions.length > 0 && (
            <div className="space-y-2.5" data-testid="copilot-decisions-list">
              <div className="flex items-center justify-between gap-2">
                <p className="m-0 text-[10px] font-bold uppercase tracking-wide text-white/62">Priorités du jour · {dailyDecisions.length} priorité{dailyDecisions.length > 1 ? "s" : ""}</p>
                <span className="text-[10px] text-white/55">Vision → Décision → Mission</span>
              </div>
              {dailyDecisions.map((d, index) => (
                <ActionCard key={d.id} card={d} index={index} onDecision={decideCard} busy={decisionBusyId === d.id} />
              ))}
            </div>
          )}
          {actionResults.map((result) => <ActionResultCard key={result.id} result={result} onOpenTasks={() => navigate("/mouvement")} />)}
          <BriefCard data={dashboard} />
          {!historyLoading && (dashboard || brief) && <NextSequence data={dashboard || brief} />}
          {/* « Ce que l'IA a fait pour vous » a été déplacé sur la page
              d'accueil (pages/Aujourdhui.jsx) : c'est un bilan de la journée,
              pas un tour de conversation — il alourdissait le fil du Copilote
              à chaque ouverture. */}
          {!historyLoading && messages.length === 0 && <div className="copilot-suggestions" data-testid="copilot-suggestions-list"><div className="copilot-suggestions-title"><Sparkles size={14} /> Continuer avec le Copilote</div>{SUGGESTIONS.map((suggestion) => <button key={suggestion} onClick={() => send(suggestion)} className="w-full rounded-xl border border-white/15 bg-white/5 px-3.5 py-2.5 text-left text-[13px] text-white/75 transition-colors hover:border-[#DEC2A3]/40 hover:bg-white/10" data-testid="copilot-suggestion">{suggestion}</button>)}</div>}
          {messages.map((message, index) => <div key={message.id || index} className={`copilot-message-event ${message.role === "user" ? "is-user" : "is-assistant"}`}><EventStamp actor={message.role === "user" ? (dashboard?.user?.first_name || dashboard?.user?.name || "Vous") : "MyExtension Business"} at={message.created_at || message.updated_at} /><div className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}><div className={`copilot-chat-bubble max-w-[87%] rounded-2xl px-3.5 py-2.5 text-[13px] leading-relaxed whitespace-pre-wrap ${message.role === "user" ? "is-user" : "is-assistant"}`}>{message.pending && (loading || generatingImage) && !message.content ? <Loader2 size={16} className="animate-spin text-[#DEC2A3]" /> : renderMarkdownLite(message.content)}{message.imageUrl && <img src={message.imageUrl} alt="Générée par le Copilote" className="mt-2 max-w-full rounded-xl border border-white/10" />}{message.role === "assistant" && Array.isArray(message.sources) && message.sources.length > 0 && <div className="mt-3 flex flex-wrap gap-1.5 border-t border-white/10 pt-2" data-testid="copilot-response-sources"><span className="text-[9px] font-bold uppercase tracking-wide text-[#E8C96A]">Sources</span>{message.sources.map((source, sourceIndex) => <span key={`${source.type}-${sourceIndex}`} className="rounded-full border border-white/15 bg-white/[0.05] px-2 py-1 text-[9px] text-white/55">{source.label}</span>)}</div>}</div></div></div>)}
        </div>
        <button type="button" onClick={() => { const el = scrollRef.current; if (el && el.scrollHeight > el.clientHeight + 8) { el.scrollTo({ top: el.scrollHeight, behavior: "smooth" }); } else { window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" }); } }} className="copilot-jump-latest" data-testid="copilot-jump-latest" aria-label="Aller à la conversation" title="Aller à la conversation"><ChevronDown size={16} /></button>
        <div className="border-t border-white/10 p-4">
          {attachments.length > 0 && <div className="mb-2 flex flex-wrap gap-1.5">{attachments.map((file) => <span key={file.id} className="inline-flex max-w-full items-center gap-1 rounded-lg border border-[#DEC2A3]/25 bg-[#DEC2A3]/10 px-2 py-1 text-[11px] text-[#F0DCA5]"><FileText size={12} /><span className="max-w-[150px] truncate">{file.name}</span><button onClick={() => setAttachments((current) => current.filter((item) => item.id !== file.id))} aria-label={`Retirer ${file.name}`}><X size={12} /></button></span>)}</div>}
          <div className={`copilot-composer-shell relative flex items-center gap-1.5 rounded-2xl border py-1.5 pl-2 pr-1.5 transition-colors ${imageMode ? "is-image-mode" : ""}`}>
            <input ref={fileRef} type="file" className="hidden" multiple onChange={handleUpload} accept=".txt,.md,.csv,.json,.pdf,.docx,.png,.jpg,.jpeg,.webp" />
            <button onClick={() => fileRef.current?.click()} disabled={uploading || attachments.length >= 5} className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-white/55 transition-colors hover:bg-white/10 hover:text-[#E8C96A] disabled:opacity-40" aria-label="Ajouter un fichier" data-testid="copilot-upload">{uploading ? <Loader2 size={16} className="animate-spin" /> : <Paperclip size={16} />}</button>
            <div className="relative shrink-0" ref={plusRef}>
              <button onClick={() => setPlusOpen((v) => !v)} disabled={uploading} className={`flex h-9 w-9 items-center justify-center rounded-full transition-colors ${plusOpen || imageMode ? "bg-white/15 text-[#E8C96A]" : "text-white/55 hover:bg-white/10 hover:text-[#E8C96A]"} disabled:opacity-40`} aria-label="Plus d'options" title="Capture, image IA, Drive" data-testid="copilot-plus">
                <Plus size={16} className={`transition-transform ${plusOpen ? "rotate-45" : ""}`} />
              </button>
              {plusOpen && (
                <div className="absolute bottom-11 left-0 z-20 w-56 overflow-hidden rounded-2xl border border-white/15 bg-[#102945] shadow-2xl" data-testid="copilot-plus-menu">
                  <button onClick={() => { setPlusOpen(false); handleScreenCapture(); }} className="flex w-full items-center gap-2.5 px-3.5 py-2.5 text-left text-[13px] text-white/85 hover:bg-white/10" data-testid="copilot-capture">
                    <Camera size={15} className="text-white/60" /> Capturer l'écran
                  </button>
                  <button onClick={() => { setImageMode((v) => !v); setPlusOpen(false); }} className="flex w-full items-center gap-2.5 px-3.5 py-2.5 text-left text-[13px] text-white/85 hover:bg-white/10" data-testid="copilot-image-mode">
                    <Image size={15} className="text-white/60" /> Générer une image
                  </button>
                  <button onClick={openDrive} disabled={driveConnected === null} className="flex w-full items-center gap-2.5 px-3.5 py-2.5 text-left text-[13px] text-white/85 hover:bg-white/10 disabled:opacity-50" data-testid="copilot-drive">
                    <Folder size={15} className="text-white/60" /> Drive
                    <span
                      className={`ml-auto h-2 w-2 rounded-full ${driveConnected ? "bg-sky-400 animate-pulse" : "bg-red-500"}`}
                      title={driveConnected ? "Drive synchronisé" : "Drive non connecté"}
                      data-testid="copilot-drive-status"
                    />
                  </button>
                </div>
              )}
            </div>
            <input value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); send(); } }} placeholder={imageMode ? "Décrivez l'image à générer…" : "Écrivez à votre copilote…"} className="min-w-0 flex-1 bg-transparent text-sm text-white placeholder:text-white/40 focus:outline-none" data-testid="copilot-input" />
            <button onClick={() => send()} disabled={loading || uploading || generatingImage || (!input.trim() && attachments.length === 0)} className="copilot-send-button flex h-9 w-9 shrink-0 items-center justify-center rounded-full disabled:opacity-50" aria-label="Envoyer" data-testid="copilot-send">{loading || generatingImage ? <Loader2 size={16} className="animate-spin text-[#0c1d33]" /> : <Send size={16} className="text-[#0c1d33]" />}</button>
          </div>
          {driveOpen && (
            <div className="fixed inset-0 z-[80] flex items-end justify-center bg-black/60 sm:items-center" onClick={() => setDriveOpen(false)}>
              <div className="max-h-[70vh] w-full max-w-sm overflow-hidden rounded-t-2xl border border-white/15 bg-[#102945] sm:rounded-2xl" onClick={(e) => e.stopPropagation()}>
                <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
                  <span className="text-sm font-semibold text-white">Importer depuis Drive</span>
                  <button onClick={() => setDriveOpen(false)} aria-label="Fermer"><X size={18} className="text-white/60" /></button>
                </div>
                <div className="max-h-[55vh] overflow-y-auto p-2">
                  {driveLoading && <div className="flex justify-center py-8"><Loader2 size={18} className="animate-spin text-[#DEC2A3]" /></div>}
                  {!driveLoading && driveFiles.length === 0 && <div className="px-3 py-8 text-center text-[13px] text-white/50">Aucun fichier trouvé dans ce dossier.</div>}
                  {!driveLoading && driveFiles.filter((f) => !f.isFolder).map((f) => (
                    <button key={f.id} onClick={() => importDriveFile(f)} className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-left text-[13px] text-white/85 hover:bg-white/10">
                      <FileText size={15} className="shrink-0 text-white/50" /> <span className="truncate">{f.name}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </>}

      {tab === "news" && <div className="flex-1 overflow-y-auto px-4 py-4" data-testid="copilot-news"><div className="glass p-4"><div className="mb-2 flex items-center justify-between gap-2"><div className="flex items-center gap-1.5 text-[12px] font-semibold text-[#F0DCA5]"><Newspaper size={14} /> Veille sectorielle</div><div className="flex items-center gap-1.5"><button type="button" onClick={() => loadNews(true)} disabled={newsLoading} className="rounded-full border border-[#DEC2A3]/35 bg-[#DEC2A3]/10 px-2.5 py-1 text-[10px] font-semibold text-[#F0DCA5] disabled:opacity-50" data-testid="copilot-news-refresh">{newsLoading ? "..." : "Actualiser"}</button></div></div><p className="m-0 text-[12.5px] leading-relaxed text-white/60">Une synthèse des actualités utiles aux entrepreneurs, avec ses sources.</p>{(newsScope.sector || newsScope.region) && <div className="mt-2 rounded-lg border border-[#DEC2A3]/20 bg-[#DEC2A3]/10 px-2.5 py-2 text-[10.5px] text-[#F0DCA5]">Flux appliqué : {newsScope.sector || "entrepreneuriat PME"} · {newsScope.region || "France"} · actualisation auto {newsScope.frequency_per_week === 2 ? "2×/semaine" : "1×/semaine"}{newsScope.next_refresh_at ? <div className="mt-1 text-white/55">Prochaine actualisation : {new Date(newsScope.next_refresh_at).toLocaleDateString("fr-FR")}</div> : null}</div>}
        {newsStatusMessage && <div className="mt-3 rounded-xl border border-[#DEC2A3]/25 bg-[#DEC2A3]/10 px-3 py-2 text-[11px] leading-relaxed text-[#F0DCA5]">{newsStatusMessage}</div>}{newsLoading && <div className="mt-3 inline-flex h-8 w-full items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/5 text-[11px] text-white/55"><Loader2 size={14} className="animate-spin" /> Veille automatique en préparation…</div>}{newsError && <p className="mb-0 mt-2 rounded-xl border border-[#DEC2A3]/25 bg-[#DEC2A3]/10 p-2 text-[11px] text-[#F0DCA5]">{newsError}</p>}{newsText && <div className="mt-4 rounded-xl border border-white/15 bg-white/[0.06] p-3 text-[12.5px] leading-relaxed text-white/80" data-testid="copilot-news-edition-message">{newsGeneratedAt && <div className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-[#F0DCA5]">Édition du {new Date(newsGeneratedAt).toLocaleString("fr-FR", { dateStyle: "medium", timeStyle: "short" })}</div>}<div className="space-y-2">{renderMarkdownLite(newsText)}</div></div>}{!newsText && !newsLoading && <p className="mb-0 mt-5 text-center text-[12px] text-white/60">Aucune actualité chargée pour le moment.</p>}<div className="mt-5 flex items-center justify-end gap-2 border-t border-white/10 pt-4"><button type="button" onClick={() => setNewsRefsOpen((open) => !open)} className="rounded-full border border-white/15 bg-white/[0.06] px-3 py-1.5 text-[11px] font-semibold text-white/75 hover:border-[#DEC2A3]/45 hover:text-[#F0DCA5]" data-testid="copilot-news-refs-toggle">{newsRefsOpen ? "Réf. masquées" : "Réf."}</button>{newsText && <button type="button" onClick={() => saveNews()} className="rounded-full border border-[#DEC2A3]/35 bg-[#DEC2A3]/10 px-3 py-1.5 text-[11px] font-semibold text-[#F0DCA5]" data-testid="copilot-news-save-edition"><FileText size={13} /> Enregistrer</button>}</div>{newsRefsOpen && (newsText || newsSources.length > 0) && <div className="mt-3 border-t border-white/10 pt-3"><div className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-white/60">Références</div><div className="flex flex-wrap gap-2" data-testid="copilot-news-refs"><button type="button" onClick={() => { setTab("chat"); send(`Aide-moi à agir sur cette actualité : ${newsSources[0]?.title || "la veille du jour"}`); }} className="inline-flex items-center gap-1.5 rounded-full border border-[#DEC2A3]/45 bg-[#DEC2A3]/12 px-3 py-1.5 text-[11px] font-semibold text-[#F0DCA5] transition-colors hover:bg-[#DEC2A3]/20" data-testid="copilot-news-talk"><Sparkles size={12} /> En parler au Copilote</button>{newsSources.map((source, index) => { const saved = savedNews.some((item) => item.url && item.url === source.url); return <div key={`${source.url}-${index}`} className="flex max-w-full items-center gap-1.5 rounded-full border border-white/15 bg-white/[0.05] px-2.5 py-1.5 text-[11px] text-white/80"><a href={source.url} target="_blank" rel="noopener noreferrer" title={source.title} className="inline-flex min-w-0 flex-1 items-center gap-1.5 hover:text-[#F0DCA5]" data-testid="copilot-news-source"><Globe size={12} className="shrink-0 text-[#E8C96A]" /><span className="truncate">{source.source || source.title}</span><ExternalLink size={12} className="shrink-0 text-[#E8C96A]" /></a><button type="button" onClick={() => saveNews(source)} disabled={saved} className="shrink-0 text-[10px] font-semibold text-[#E8C96A] disabled:text-white/60" data-testid="copilot-news-save-source">{saved ? "Enregistré" : "Enregistrer"}</button></div>; })}</div></div>}{newsHistory.length > 0 && <div className="mt-5 border-t border-white/10 pt-3" data-testid="copilot-news-history"><div className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-white/60">Éditions précédentes</div><div className="space-y-1.5">{newsHistory.slice(0, 8).map((item) => { const saved = savedNews.some((savedItem) => savedItem.title === item.title && savedItem.kind === "edition"); return <div key={item.id} className="flex flex-wrap items-center gap-2 rounded-lg border border-white/10 bg-white/[0.04] px-2.5 py-2"><button type="button" onClick={() => setSelectedNewsEdition(selectedNewsEdition?.id === item.id ? null : item)} className="min-w-0 flex-1 text-left" data-testid="copilot-news-open-history"><div className="truncate text-[11px] text-white/85">{item.title}</div><div className="truncate text-[9px] text-white/62">{item.published_at ? new Date(item.published_at).toLocaleString("fr-FR", { dateStyle: "medium", timeStyle: "short" }) : "Date indisponible"} · {item.sector || "Entrepreneuriat PME"} · {item.region || "France"}</div></button><button type="button" onClick={() => saveNews(item)} disabled={saved} className="shrink-0 text-[10px] font-semibold text-[#E8C96A] disabled:text-white/60" data-testid="copilot-news-save-history">{saved ? "Enregistré" : "Enregistrer"}</button>{selectedNewsEdition?.id === item.id && <div className="basis-full mt-2 rounded-xl border border-white/15 bg-white/[0.06] p-3 text-[12px] leading-relaxed text-white/80">{item.digest || item.content || "Le contenu détaillé de cette édition n’est pas disponible dans l’historique."}</div>}</div>; })}</div></div>}{savedNews.length > 0 && <div className="mt-5 border-t border-white/10 pt-3" data-testid="copilot-news-saved"><div className="mb-2 flex items-center justify-between"><div className="text-[10px] font-semibold uppercase tracking-wide text-white/60">Documents enregistrés</div><span className="text-[10px] text-white/55">{savedNews.length}</span></div><div className="space-y-1.5">{savedNews.slice(0, 12).map((item) => <div key={item.id} className="flex items-center gap-2 rounded-lg border border-white/10 bg-white/[0.04] px-2.5 py-2"><div className="min-w-0 flex-1"><div className="truncate text-[11px] text-white/80">{item.title}</div><div className="truncate text-[9px] text-white/55">{item.source || "Veille Copilote"}{item.saved_at ? ` · ${new Date(item.saved_at).toLocaleDateString("fr-FR")}` : ""}</div></div>{item.url && <a href={item.url} target="_blank" rel="noopener noreferrer" className="text-[10px] text-[#E8C96A]">Ouvrir</a>}<button type="button" onClick={() => removeSavedNews(item.id)} className="text-[10px] text-white/62 hover:text-rose-300" data-testid="copilot-news-delete-saved">Supprimer</button></div>)}</div></div>}</div></div>}
    </div>
  );
}
