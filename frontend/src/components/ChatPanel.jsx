import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowLeft, ArrowRight, Camera, Check, CheckCircle2, ChevronDown, Clock, Compass, Copy, ExternalLink, FileText, Folder, Globe, Handshake, HeartPulse, Image, Loader2,
  Menu, MessageCircle, Newspaper, Paperclip, Plus, Send, ShieldCheck,
  Sparkles, Sun, Wallet, X,
} from "lucide-react";
import { NightRecap, NextSequence } from "./CockpitSections";
import {
  applyCopilotDecision, getChatHistory, getCopilotBrief, getCopilotConfig,
  getCopilotDecision, getCopilotNews, getNewsHistory, getSavedNews, saveNewsItem, deleteSavedNews, archiveNewsEdition,
  sendCopilotWorkRequest, streamChatMessage, sendCopilotMessage, uploadChatFile, generateChatImage,
  getDriveStatus, connectDrive, listDriveFiles, importDriveFileToChat,
  getLastSeenNewsId, setLastSeenNewsId,
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

function renderMarkdownLite(text) {
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
    <div className="rounded-xl border border-[#DEC2A3]/35 bg-[#0A1128]/40 p-3" data-testid="copilot-draft-message">
      <div className="mb-1.5 flex items-center justify-between gap-2">
        <span className="text-[10px] font-bold uppercase tracking-wide text-[#E8C96A]">Brouillon rédigé par l'IA — prêt à envoyer</span>
        <div className="flex shrink-0 items-center gap-2">
          <button onClick={copy} className="inline-flex items-center gap-1 text-[11px] font-semibold text-[#E8C96A] hover:text-white" data-testid="draft-copy">
            {copied ? <Check size={12} /> : <Copy size={12} />} {copied ? "Copié" : "Copier"}
          </button>
          <a href={mailtoHref} className="inline-flex items-center gap-1 rounded-full bg-[#DEC2A3] px-2.5 py-1 text-[11px] font-semibold text-[#0A1128] hover:opacity-90" data-testid="draft-transmit">
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
        <span className={`inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-xl ${rank === 1 ? "bg-[#DEC2A3] text-[#0A1128]" : "bg-[#DEC2A3]/20 text-[#E8C96A]"}`}><strong className="text-[13px]">{rank}</strong></span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wide" style={{ color: domain.color }}><DomainIcon size={11} /> {domain.label} · {rank === 1 ? "Aujourd’hui" : "Ensuite"}</div>
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
            <button onClick={() => onDecision(card.id, "approve")} disabled={busy} className="flex-1 inline-flex h-9 items-center justify-center gap-1.5 rounded-xl bg-[#DEC2A3] text-[12px] font-semibold text-[#0A1128] transition-opacity hover:opacity-90 disabled:opacity-60" data-testid="copilot-action-approve">{busy ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />} Approuver</button>
            <button onClick={() => onDecision(card.id, "defer")} disabled={busy} className="flex-1 inline-flex h-9 items-center justify-center gap-1.5 rounded-xl border border-white/15 bg-white/5 text-[12px] font-semibold text-white/75 transition-colors hover:bg-white/10 disabled:opacity-60" data-testid="copilot-action-defer"><Clock size={14} /> Reporter</button>
          </div>
        )}
      </div>}
    </div>
  );
}

export default function ChatPanel({ context, initialAsk, onBack, onMenu }) {
  const navigate = useNavigate();
  const sessionId = useMemo(getSessionId, []);
  const visionContextLabel = String(context || "").match(/Onglet Vision actif : ([^.]+)/)?.[1] || null;
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [attachments, setAttachments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [tab, setTab] = useState("chat");
  const [brief, setBrief] = useState(null);
  const [dailyDecisions, setDailyDecisions] = useState([]);
  const [decisionBusyId, setDecisionBusyId] = useState(null);
  const [newsText, setNewsText] = useState("");
  const [newsSources, setNewsSources] = useState([]);
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
      getChatHistory(sessionId), getCopilotBrief(sessionId), getCopilotConfig(),
      getCopilotDecision(sessionId), getSavedNews(sessionId), getNewsHistory(sessionId),
    ]).then(([history, dailyBrief, config, decision, saved, newsHistoryResult]) => {
        if (!active) return;
        setMessages(history.status === "fulfilled" ? history.value : []);
        setBrief(dailyBrief.status === "fulfilled" ? dailyBrief.value : null);
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
    setInput(""); setAttachments([]); setTab("chat"); setLoading(true);
    setMessages((current) => [...current, { role: "user", content: visibleMessage }, { role: "assistant", content: "", pending: true }]);
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
        const next = [...current]; next[next.length - 1] = { role: "assistant", content: reply, sources }; return next;
      });
    } catch (error) {
      setMessages((current) => {
        const next = [...current]; next[next.length - 1] = { role: "assistant", content: error?.message || "Désolé, le copilote est indisponible pour le moment. Réessaie dans un instant." }; return next;
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
      const result = await applyCopilotDecision({ id: decisionId, session: sessionId, decision });
      setDailyDecisions((current) => decision === "approve"
        ? current.map((d) => d.id === decisionId ? { ...d, justCreated: true, status: result.status } : d)
        : current.map((d) => (d.id === decisionId ? { ...d, ...result } : d)));
      setMessages((current) => [...current, { role: "assistant", content: result.message }]);
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
    <div className="flex h-full w-full flex-col" data-testid="copilot-panel">
      <div className="border-b border-white/10 px-5 py-3.5">
        <div className="flex items-center justify-between gap-3">
          <div className="flex min-w-0 items-center gap-2.5">
            {onMenu && <button type="button" onClick={onMenu} className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-white/20 bg-white/10 text-white/80 hover:border-[#DEC2A3]/60 hover:text-[#F0DCA5]" title="Menu" aria-label="Ouvrir le menu" data-testid="copilot-menu">
              <Menu size={16} />
            </button>}
            <div className="gold-bg flex h-9 w-9 shrink-0 items-center justify-center rounded-xl"><Sparkles size={18} className="text-[#0A1128]" /></div><div className="min-w-0"><div className="font-head text-[15px] font-semibold">Cockpit</div><p className="m-0 text-[11px] text-white/55">Votre co-pilote IA</p>{visionContextLabel && <div className="mt-1 inline-flex max-w-full truncate rounded-full border border-[#DEC2A3]/25 bg-[#DEC2A3]/10 px-2 py-0.5 text-[10px] font-medium text-[#F0DCA5]">Vision · {visionContextLabel}</div>}</div></div>
          <div className="flex shrink-0 items-center gap-2">
            {onBack && <button type="button" onClick={onBack} className="inline-flex h-8 items-center gap-1.5 rounded-full border border-white/25 bg-white/10 px-3 text-[11px] font-semibold text-white hover:border-[#DEC2A3]/60 hover:text-[#F0DCA5]" title="Retour" aria-label="Retour" data-testid="copilot-back"><ArrowLeft size={14} /> <span>Retour</span></button>}
            <button onClick={() => setContactOpen((value) => !value)} className={`inline-flex h-9 items-center gap-1.5 rounded-full border px-3 text-[11px] font-semibold transition-colors ${contactOpen ? "border-[#DEC2A3]/60 bg-[#DEC2A3]/20 text-[#F0DCA5]" : "border-[#DEC2A3]/45 bg-[#DEC2A3]/12 text-[#F0DCA5] hover:bg-[#DEC2A3]/20"}`} title="Travailler avec l’équipe" aria-label="Travailler avec l’équipe" data-testid="copilot-contact"><Handshake size={16} /> <span>Collaborer</span></button>
          </div>
        </div>
        <div className="mt-3 grid grid-cols-2 border-b border-white/10" data-testid="copilot-tabs">
          <button onClick={() => setTab("chat")} className={`inline-flex h-9 items-center justify-center gap-1.5 border-b-2 text-[11.5px] font-medium transition-colors ${tab === "chat" ? "border-[#F1E2CC] text-[#F0DCA5]" : "border-transparent text-white/50 hover:text-white/75"}`}><MessageCircle size={14} /> Discussion</button>
          <button onClick={() => { setTab("news"); markNewsTabSeen(); }} className={`inline-flex h-9 items-center justify-center gap-1.5 border-b-2 text-[11.5px] font-medium transition-colors ${tab === "news" ? "border-[#F1E2CC] text-[#F0DCA5]" : "border-transparent text-white/50 hover:text-white/75"}`}><Newspaper size={14} /> Actualité{unseenNewsCount > 0 && <span className="ml-0.5 inline-flex h-4 min-w-[16px] items-center justify-center rounded-full bg-rose-500 px-1 text-[9px] font-bold text-white" data-testid="copilot-news-count">{unseenNewsCount}</span>}</button>
        </div>
      </div>

      {contactOpen && <div className="mx-4 mt-3 rounded-2xl border border-[#DEC2A3]/35 bg-[#DEC2A3]/10 p-3" data-testid="copilot-contact-panel"><div className="mb-2 text-[12.5px] text-white/80">Envie d’avancer <strong>avec l’équipe</strong> sur ton projet ?</div>{whatsappUrl && <a className="mb-2 inline-flex h-8 items-center gap-1.5 rounded-full bg-emerald-400 px-3 text-[11.5px] font-semibold text-[#0A1128]" href={whatsappUrl} target="_blank" rel="noopener noreferrer"><ExternalLink size={13} /> Discuter sur WhatsApp</a>}<textarea value={contactMessage} onChange={(event) => setContactMessage(event.target.value)} rows={2} placeholder="Décris ton besoin en une phrase…" className="mb-2 block w-full resize-y rounded-xl border border-white/15 bg-white/[0.06] px-3 py-2 text-[12px] text-white placeholder:text-white/35 focus:border-[#DEC2A3]/50 focus:outline-none" data-testid="copilot-contact-message" /><button onClick={sendWorkRequest} disabled={!contactMessage.trim() || contactSent} className="h-8 w-full rounded-xl bg-[#DEC2A3] text-[11.5px] font-semibold text-[#0A1128] disabled:opacity-50" data-testid="copilot-contact-send">{contactSent ? "Demande envoyée" : "Envoyer ma demande"}</button></div>}

      {tab === "chat" && <>
        <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto px-4 py-4" data-testid="copilot-messages">
          {!historyLoading && dailyDecisions.length > 0 && (
            <div className="space-y-2.5" data-testid="copilot-decisions-list">
              <div className="flex items-center justify-between gap-2">
                <p className="m-0 text-[10px] font-bold uppercase tracking-wide text-white/45">Le point du jour · {dailyDecisions.length} priorité{dailyDecisions.length > 1 ? "s" : ""}</p>
                <span className="text-[10px] text-white/35">Vision → Décision → Mission</span>
              </div>
              {dailyDecisions.map((d, index) => (
                <ActionCard key={d.id} card={d} index={index} onDecision={decideCard} busy={decisionBusyId === d.id} />
              ))}
            </div>
          )}
          <BriefCard data={brief} />
          {!historyLoading && brief && <NextSequence data={brief} />}
          {!historyLoading && brief && <NightRecap data={brief} onSeeTasks={() => navigate("/bien-etre#missions")} />}
          {!historyLoading && messages.length === 0 && <div className="space-y-3"><div className="glass p-4"><div className="mb-1 text-sm font-medium">Bonjour</div><p className="m-0 text-[13px] leading-relaxed text-white/60">Je garde le fil de nos échanges, peux lire tes documents et t’aider à décider de la prochaine action.</p></div><div className="space-y-2">{SUGGESTIONS.map((suggestion) => <button key={suggestion} onClick={() => send(suggestion)} className="w-full rounded-xl border border-white/15 bg-white/5 px-3.5 py-2.5 text-left text-[13px] text-white/75 transition-colors hover:border-[#DEC2A3]/40 hover:bg-white/10" data-testid="copilot-suggestion">{suggestion}</button>)}</div></div>}
          {messages.map((message, index) => {
            return <div key={message.id || index} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}><div className={`max-w-[87%] rounded-2xl px-3.5 py-2.5 text-[13px] leading-relaxed whitespace-pre-wrap ${message.role === "user" ? "border border-[#DEC2A3]/30 bg-[#DEC2A3]/20 text-white" : "glass text-white/85"}`}>{message.pending && (loading || generatingImage) && !message.content ? <Loader2 size={16} className="animate-spin text-[#DEC2A3]" /> : renderMarkdownLite(message.content)}{message.imageUrl && <img src={message.imageUrl} alt="Générée par le Copilote" className="mt-2 max-w-full rounded-xl border border-white/10" />}{message.role === "assistant" && Array.isArray(message.sources) && message.sources.length > 0 && <div className="mt-3 flex flex-wrap gap-1.5 border-t border-white/10 pt-2" data-testid="copilot-response-sources"><span className="text-[9px] font-bold uppercase tracking-wide text-[#E8C96A]">Sources</span>{message.sources.map((source, sourceIndex) => <span key={`${source.type}-${sourceIndex}`} className="rounded-full border border-white/15 bg-white/[0.05] px-2 py-1 text-[9px] text-white/55">{source.label}</span>)}</div>}</div></div>;
          })}
        </div>
        <div className="border-t border-white/10 p-4">
          {attachments.length > 0 && <div className="mb-2 flex flex-wrap gap-1.5">{attachments.map((file) => <span key={file.id} className="inline-flex max-w-full items-center gap-1 rounded-lg border border-[#DEC2A3]/25 bg-[#DEC2A3]/10 px-2 py-1 text-[11px] text-[#F0DCA5]"><FileText size={12} /><span className="max-w-[150px] truncate">{file.name}</span><button onClick={() => setAttachments((current) => current.filter((item) => item.id !== file.id))} aria-label={`Retirer ${file.name}`}><X size={12} /></button></span>)}</div>}
          <div className={`relative flex items-center gap-1.5 rounded-2xl border py-1.5 pl-2 pr-1.5 transition-colors ${imageMode ? "border-[#DEC2A3]/60 bg-[#DEC2A3]/10" : "border-white/15 bg-white/5 focus-within:border-[#DEC2A3]/50"}`}>
            <input ref={fileRef} type="file" className="hidden" multiple onChange={handleUpload} accept=".txt,.md,.csv,.json,.pdf,.docx,.png,.jpg,.jpeg,.webp" />
            <button onClick={() => fileRef.current?.click()} disabled={uploading || attachments.length >= 5} className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-white/55 transition-colors hover:bg-white/10 hover:text-[#E8C96A] disabled:opacity-40" aria-label="Ajouter un fichier" data-testid="copilot-upload">{uploading ? <Loader2 size={16} className="animate-spin" /> : <Paperclip size={16} />}</button>
            <div className="relative shrink-0" ref={plusRef}>
              <button onClick={() => setPlusOpen((v) => !v)} disabled={uploading} className={`flex h-9 w-9 items-center justify-center rounded-full transition-colors ${plusOpen || imageMode ? "bg-white/15 text-[#E8C96A]" : "text-white/55 hover:bg-white/10 hover:text-[#E8C96A]"} disabled:opacity-40`} aria-label="Plus d'options" title="Capture, image IA, Drive" data-testid="copilot-plus">
                <Plus size={16} className={`transition-transform ${plusOpen ? "rotate-45" : ""}`} />
              </button>
              {plusOpen && (
                <div className="absolute bottom-11 left-0 z-20 w-56 overflow-hidden rounded-2xl border border-white/15 bg-[#0B1F3A] shadow-2xl" data-testid="copilot-plus-menu">
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
            <button onClick={() => send()} disabled={loading || uploading || generatingImage || (!input.trim() && attachments.length === 0)} className="gold-bg flex h-9 w-9 shrink-0 items-center justify-center rounded-full disabled:opacity-50" aria-label="Envoyer" data-testid="copilot-send">{loading || generatingImage ? <Loader2 size={16} className="animate-spin text-[#0A1128]" /> : <Send size={16} className="text-[#0A1128]" />}</button>
          </div>
          {driveOpen && (
            <div className="fixed inset-0 z-[80] flex items-end justify-center bg-black/60 sm:items-center" onClick={() => setDriveOpen(false)}>
              <div className="max-h-[70vh] w-full max-w-sm overflow-hidden rounded-t-2xl border border-white/15 bg-[#0B1F3A] sm:rounded-2xl" onClick={(e) => e.stopPropagation()}>
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
          <p className="m-0 mt-2 text-center text-[10px] text-white/35">Conversations · Documents · Décisions</p>
        </div>
      </>}

      {tab === "news" && <div className="flex-1 overflow-y-auto px-4 py-4" data-testid="copilot-news"><div className="glass p-4"><div className="mb-2 flex items-center justify-between gap-2"><div className="flex items-center gap-1.5 text-[12px] font-semibold text-[#F0DCA5]"><Newspaper size={14} /> Veille sectorielle</div><div className="flex items-center gap-1.5"><button type="button" onClick={() => loadNews(true)} disabled={newsLoading} className="rounded-full border border-[#DEC2A3]/35 bg-[#DEC2A3]/10 px-2.5 py-1 text-[10px] font-semibold text-[#F0DCA5] disabled:opacity-50" data-testid="copilot-news-refresh">{newsLoading ? "..." : "Actualiser"}</button></div></div><p className="m-0 text-[12.5px] leading-relaxed text-white/60">Une synthèse des actualités utiles aux entrepreneurs, avec ses sources.</p>{(newsScope.sector || newsScope.region) && <div className="mt-2 rounded-lg border border-[#DEC2A3]/20 bg-[#DEC2A3]/10 px-2.5 py-2 text-[10.5px] text-[#F0DCA5]">Flux appliqué : {newsScope.sector || "entrepreneuriat PME"} · {newsScope.region || "France"} · actualisation auto {newsScope.frequency_per_week === 2 ? "2×/semaine" : "1×/semaine"}{newsScope.next_refresh_at ? <div className="mt-1 text-white/55">Prochaine actualisation : {new Date(newsScope.next_refresh_at).toLocaleDateString("fr-FR")}</div> : null}</div>}
	{newsStatusMessage && <div className="mt-3 rounded-xl border border-[#DEC2A3]/25 bg-[#DEC2A3]/10 px-3 py-2 text-[11px] leading-relaxed text-[#F0DCA5]">{newsStatusMessage}</div>}{newsLoading && <div className="mt-3 inline-flex h-8 w-full items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/5 text-[11px] text-white/55"><Loader2 size={14} className="animate-spin" /> Veille automatique en préparation…</div>}{newsError && <p className="mb-0 mt-2 rounded-xl border border-[#DEC2A3]/25 bg-[#DEC2A3]/10 p-2 text-[11px] text-[#F0DCA5]">{newsError}</p>}{newsText && <div className="mt-4 rounded-xl border border-white/15 bg-white/[0.06] p-3 text-[12.5px] leading-relaxed text-white/80" data-testid="copilot-news-edition-message">{newsGeneratedAt && <div className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-[#F0DCA5]">Édition du {new Date(newsGeneratedAt).toLocaleString("fr-FR", { dateStyle: "medium", timeStyle: "short" })}</div>}<div className="space-y-2">{renderMarkdownLite(newsText)}</div></div>}{!newsText && !newsLoading && <p className="mb-0 mt-5 text-center text-[12px] text-white/40">Aucune actualité chargée pour le moment.</p>}<div className="mt-5 flex items-center justify-end gap-2 border-t border-white/10 pt-4"><button type="button" onClick={() => setNewsRefsOpen((open) => !open)} className="rounded-full border border-white/15 bg-white/[0.06] px-3 py-1.5 text-[11px] font-semibold text-white/75 hover:border-[#DEC2A3]/45 hover:text-[#F0DCA5]" data-testid="copilot-news-refs-toggle">{newsRefsOpen ? "Réf. masquées" : "Réf."}</button>{newsText && <button type="button" onClick={() => saveNews()} className="rounded-full border border-[#DEC2A3]/35 bg-[#DEC2A3]/10 px-3 py-1.5 text-[11px] font-semibold text-[#F0DCA5]" data-testid="copilot-news-save-edition"><FileText size={13} /> Enregistrer</button>}</div>{newsRefsOpen && (newsText || newsSources.length > 0) && <div className="mt-3 border-t border-white/10 pt-3"><div className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-white/40">Références</div><div className="flex flex-wrap gap-2" data-testid="copilot-news-refs"><button type="button" onClick={() => { setTab("chat"); send(`Aide-moi à agir sur cette actualité : ${newsSources[0]?.title || "la veille du jour"}`); }} className="inline-flex items-center gap-1.5 rounded-full border border-[#DEC2A3]/45 bg-[#DEC2A3]/12 px-3 py-1.5 text-[11px] font-semibold text-[#F0DCA5] transition-colors hover:bg-[#DEC2A3]/20" data-testid="copilot-news-talk"><Sparkles size={12} /> En parler au Copilote</button>{newsSources.map((source, index) => { const saved = savedNews.some((item) => item.url && item.url === source.url); return <div key={`${source.url}-${index}`} className="flex max-w-full items-center gap-1.5 rounded-full border border-white/15 bg-white/[0.05] px-2.5 py-1.5 text-[11px] text-white/80"><a href={source.url} target="_blank" rel="noopener noreferrer" title={source.title} className="inline-flex min-w-0 flex-1 items-center gap-1.5 hover:text-[#F0DCA5]" data-testid="copilot-news-source"><Globe size={12} className="shrink-0 text-[#E8C96A]" /><span className="truncate">{source.source || source.title}</span><ExternalLink size={12} className="shrink-0 text-[#E8C96A]" /></a><button type="button" onClick={() => saveNews(source)} disabled={saved} className="shrink-0 text-[10px] font-semibold text-[#E8C96A] disabled:text-white/40" data-testid="copilot-news-save-source">{saved ? "Enregistré" : "Enregistrer"}</button></div>; })}</div></div>}{newsHistory.length > 0 && <div className="mt-5 border-t border-white/10 pt-3" data-testid="copilot-news-history"><div className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-white/40">Éditions précédentes</div><div className="space-y-1.5">{newsHistory.slice(0, 8).map((item) => { const saved = savedNews.some((savedItem) => savedItem.title === item.title && savedItem.kind === "edition"); return <div key={item.id} className="flex flex-wrap items-center gap-2 rounded-lg border border-white/10 bg-white/[0.04] px-2.5 py-2"><button type="button" onClick={() => setSelectedNewsEdition(selectedNewsEdition?.id === item.id ? null : item)} className="min-w-0 flex-1 text-left" data-testid="copilot-news-open-history"><div className="truncate text-[11px] text-white/85">{item.title}</div><div className="truncate text-[9px] text-white/45">{item.published_at ? new Date(item.published_at).toLocaleString("fr-FR", { dateStyle: "medium", timeStyle: "short" }) : "Date indisponible"} · {item.sector || "Entrepreneuriat PME"} · {item.region || "France"}</div></button><button type="button" onClick={() => saveNews(item)} disabled={saved} className="shrink-0 text-[10px] font-semibold text-[#E8C96A] disabled:text-white/40" data-testid="copilot-news-save-history">{saved ? "Enregistré" : "Enregistrer"}</button>{selectedNewsEdition?.id === item.id && <div className="basis-full mt-2 rounded-xl border border-white/15 bg-white/[0.06] p-3 text-[12px] leading-relaxed text-white/80">{item.digest || item.content || "Le contenu détaillé de cette édition n’est pas disponible dans l’historique."}</div>}</div>; })}</div></div>}{savedNews.length > 0 && <div className="mt-5 border-t border-white/10 pt-3" data-testid="copilot-news-saved"><div className="mb-2 flex items-center justify-between"><div className="text-[10px] font-semibold uppercase tracking-wide text-white/40">Documents enregistrés</div><span className="text-[10px] text-white/35">{savedNews.length}</span></div><div className="space-y-1.5">{savedNews.slice(0, 12).map((item) => <div key={item.id} className="flex items-center gap-2 rounded-lg border border-white/10 bg-white/[0.04] px-2.5 py-2"><div className="min-w-0 flex-1"><div className="truncate text-[11px] text-white/80">{item.title}</div><div className="truncate text-[9px] text-white/35">{item.source || "Veille Copilote"}{item.saved_at ? ` · ${new Date(item.saved_at).toLocaleDateString("fr-FR")}` : ""}</div></div>{item.url && <a href={item.url} target="_blank" rel="noopener noreferrer" className="text-[10px] text-[#E8C96A]">Ouvrir</a>}<button type="button" onClick={() => removeSavedNews(item.id)} className="text-[10px] text-white/45 hover:text-rose-300" data-testid="copilot-news-delete-saved">Supprimer</button></div>)}</div></div>}</div></div>}
    </div>
  );
}
