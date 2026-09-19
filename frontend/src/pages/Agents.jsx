import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import api from "@/lib/api";
import {
  Bot, Briefcase, PenTool, Calculator, Scale, Search, Mail, FileText, Code,
  Languages, Globe, Share2, TrendingUp, Shield, Users, Calendar, Plus, X,
  QrCode, Send as TelegramIcon, MessageCircle, Loader2, RefreshCw, Unplug,
  ArrowLeft, Inbox,
} from "lucide-react";

/* Palette claire, cohérente avec EspaceVendeur.jsx — un agent qu'on configure
 * et qu'on connecte se manipule comme une fiche produit, pas comme un écran
 * de pilotage sombre. */
const C = {
  encre: "#111827", texte: "#374151", doux: "#6B7280",
  bord: "#E5E7EB", fond: "#FFFFFF", fond2: "#F9FAFB", navy: "#0B1B3A",
};

const ICON_MAP = {
  bot: Bot, briefcase: Briefcase, "pen-tool": PenTool, calculator: Calculator,
  scale: Scale, search: Search, mail: Mail, "file-text": FileText, code: Code,
  languages: Languages, globe: Globe, "share-2": Share2, "trending-up": TrendingUp,
  shield: Shield, users: Users, calendar: Calendar,
};
function AgentIcon({ name, className, color }) {
  const Icon = ICON_MAP[name] || Bot;
  return <Icon className={className} style={color ? { color } : undefined} />;
}

const bouton = {
  width: "100%", textAlign: "left", borderRadius: 12, border: `1px solid ${C.bord}`,
  background: C.fond, padding: "12px 14px", fontSize: 14, cursor: "pointer",
};
const saisie = {
  width: "100%", borderRadius: 10, border: `1px solid ${C.bord}`, background: C.fond,
  padding: "9px 12px", fontSize: 14, color: C.encre, outline: "none",
};

/* ── WhatsApp Web (scan QR) ────────────────────────────────────
 * C'est l'option principale demandée : pas de compte Meta Business,
 * on scanne le QR avec son WhatsApp perso ou pro, comme WhatsApp Web
 * sur ordinateur, mais piloté par l'agent. */
function WhatsAppQR({ agent, onClose, onDeployed }) {
  const [state, setState] = useState({ status: "idle" }); // idle | qr_pending | ready | error
  const [qr, setQr] = useState(null);
  const [error, setError] = useState("");
  const pollRef = useRef(null);

  const stopPolling = () => { if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; } };
  useEffect(() => () => stopPolling(), []);

  const poll = useCallback(() => {
    stopPolling();
    let attempts = 0;
    pollRef.current = setInterval(async () => {
      attempts += 1;
      try {
        const r = await api.get(`/custom-agents/${agent.id}/whatsapp-web-status`);
        const d = r.data || {};
        if (d.status === "qr_pending" && d.qr) setQr(d.qr);
        if (d.status === "ready") {
          setState({ status: "ready", phone_number: d.phone_number });
          stopPolling();
          onDeployed?.();
        }
        if (d.status === "error" || d.status === "service_unreachable") {
          setError("La session a échoué. Réessayez ou cliquez sur Réinitialiser.");
          stopPolling();
        }
      } catch {
        // best-effort — on retente au prochain tick
      }
      if (attempts > 40) stopPolling(); // ~2 min max
    }, 3000);
  }, [agent.id, onDeployed]);

  const start = async () => {
    setError("");
    setState({ status: "qr_pending" });
    try {
      const r = await api.post(`/custom-agents/${agent.id}/whatsapp-web-connect`);
      const d = r.data || {};
      if (d.status === "ready") { setState({ status: "ready", phone_number: d.phone_number }); onDeployed?.(); return; }
      if (d.qr) setQr(d.qr);
      poll();
    } catch (e) {
      const msg = e?.response?.data?.detail || "Service WhatsApp indisponible pour le moment.";
      setError(msg);
      setState({ status: "error" });
    }
  };

  const reset = async () => {
    stopPolling();
    setQr(null); setError(""); setState({ status: "idle" });
    try { await api.post(`/custom-agents/${agent.id}/whatsapp-web-reset`); } catch { /* best-effort */ }
    toast.info("Session réinitialisée — relancez la connexion.");
  };

  const disconnect = async () => {
    stopPolling();
    try { await api.delete(`/custom-agents/${agent.id}/whatsapp-web-disconnect`); } catch { /* best-effort */ }
    setState({ status: "idle" }); setQr(null);
    toast.success("WhatsApp déconnecté de cet agent.");
    onDeployed?.();
  };

  return (
    <div className="space-y-4">
      <p className="text-[13px]" style={{ color: C.doux }}>
        Connectez votre WhatsApp personnel ou professionnel. Aucun compte Meta Business requis —
        scannez simplement le QR code, exactement comme WhatsApp Web sur un ordinateur, mais piloté par « {agent.name} ».
      </p>

      {state.status === "ready" && (
        <div className="rounded-2xl p-4" style={{ background: "#ECFDF5", border: "1px solid #A7F3D0" }}>
          <p className="text-sm font-semibold" style={{ color: "#047857" }}>✓ Connecté{state.phone_number ? ` — ${state.phone_number}` : ""}</p>
          <p className="text-[13px] mt-1" style={{ color: C.doux }}>L'agent répond désormais aux messages reçus sur ce numéro.</p>
          <button onClick={disconnect} style={{ ...bouton, marginTop: 12, display: "inline-flex", alignItems: "center", gap: 6, width: "auto" }}>
            <Unplug size={14} /> Déconnecter
          </button>
        </div>
      )}

      {state.status === "idle" && (
        <button onClick={start} style={{ ...bouton, display: "flex", alignItems: "center", gap: 10, justifyContent: "center", background: "#25D366", color: "#fff", border: "none", fontWeight: 600 }}>
          <QrCode size={18} /> Générer le QR code WhatsApp
        </button>
      )}

      {state.status === "qr_pending" && (
        <div className="text-center space-y-3">
          {qr ? (
            <img src={qr} alt="QR WhatsApp" style={{ width: 220, height: 220, margin: "0 auto", borderRadius: 12, border: `1px solid ${C.bord}` }} />
          ) : (
            <div className="flex items-center justify-center" style={{ height: 220 }}><Loader2 className="animate-spin" size={28} /></div>
          )}
          <p className="text-[13px]" style={{ color: C.doux }}>Ouvrez WhatsApp → ⋮ (ou Réglages) → Appareils connectés → Connecter un appareil.</p>
          <button onClick={reset} style={{ ...bouton, width: "auto", display: "inline-flex", alignItems: "center", gap: 6 }}><RefreshCw size={14} /> Réinitialiser</button>
        </div>
      )}

      {error && (
        <div className="rounded-2xl p-3 text-[13px]" style={{ background: "#FEF2F2", color: "#B91C1C", border: "1px solid #FECACA" }}>
          {error}
          <button onClick={reset} style={{ ...bouton, marginTop: 8, width: "auto" }}>Réessayer</button>
        </div>
      )}

      <button onClick={onClose} style={{ ...bouton, width: "auto" }}>Retour</button>
    </div>
  );
}

/* ── Telegram — nécessite un Bot Token créé via @BotFather ── */
function TelegramDeploy({ agent, onClose, onDeployed }) {
  const [botToken, setBotToken] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null);

  const deploy = async () => {
    if (!botToken.trim()) { toast.error("Collez le Bot Token fourni par @BotFather."); return; }
    setLoading(true);
    try {
      await api.post("/connections", { provider: "telegram", credentials: { bot_token: botToken.trim() } });
      const r = await api.post(`/custom-agents/${agent.id}/deploy`, { channels: ["telegram"] });
      setStatus(r.data?.telegram_status || "active");
      toast.success("Agent connecté à Telegram.");
      onDeployed?.();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Connexion Telegram impossible.");
    } finally { setLoading(false); }
  };

  return (
    <div className="space-y-3">
      <p className="text-[13px]" style={{ color: C.doux }}>
        1. Ouvrez Telegram, parlez à <strong>@BotFather</strong>, créez un bot (/newbot).<br />
        2. Collez ici le token qu'il vous donne.
      </p>
      <input style={saisie} placeholder="Bot Token (@BotFather)" value={botToken} onChange={(e) => setBotToken(e.target.value)} />
      <button onClick={deploy} disabled={loading} style={{ ...bouton, background: "#0088CC", color: "#fff", border: "none", fontWeight: 600, display: "flex", justifyContent: "center", gap: 8 }}>
        {loading ? <Loader2 className="animate-spin" size={16} /> : <TelegramIcon size={16} />} Connecter Telegram
      </button>
      {status && <p className="text-[13px]" style={{ color: status === "active" ? "#047857" : "#B45309" }}>Statut : {status}</p>}
      <button onClick={onClose} style={{ ...bouton, width: "auto" }}>Retour</button>
    </div>
  );
}

/* ── WhatsApp Business (Cloud API Meta officielle) — pour un vrai numéro pro ── */
function WhatsAppCloudDeploy({ agent, onClose, onDeployed }) {
  const [phoneId, setPhoneId] = useState("");
  const [token, setToken] = useState("");
  const [loading, setLoading] = useState(false);

  const deploy = async () => {
    if (!phoneId.trim() || !token.trim()) { toast.error("Renseignez le Phone Number ID et l'Access Token."); return; }
    setLoading(true);
    try {
      await api.post("/connections", { provider: "whatsapp", credentials: { phone_number_id: phoneId.trim(), access_token: token.trim() } });
      await api.post(`/custom-agents/${agent.id}/deploy`, { channels: ["whatsapp"] });
      toast.success("Agent connecté à WhatsApp Business.");
      onDeployed?.();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Connexion WhatsApp Business impossible.");
    } finally { setLoading(false); }
  };

  return (
    <div className="space-y-3">
      <p className="text-[13px]" style={{ color: C.doux }}>
        Nécessite un compte Meta Business déjà configuré (developers.facebook.com → votre app → WhatsApp).
        Vos clients écrivent sur votre numéro WhatsApp Business, l'agent répond automatiquement.
      </p>
      <input style={saisie} placeholder="Phone Number ID" value={phoneId} onChange={(e) => setPhoneId(e.target.value)} />
      <input style={saisie} type="password" placeholder="Access Token (permanent)" value={token} onChange={(e) => setToken(e.target.value)} />
      <button onClick={deploy} disabled={loading} style={{ ...bouton, background: C.navy, color: "#fff", border: "none", fontWeight: 600, display: "flex", justifyContent: "center", gap: 8 }}>
        {loading ? <Loader2 className="animate-spin" size={16} /> : <MessageCircle size={16} />} Connecter WhatsApp Business
      </button>
      <button onClick={onClose} style={{ ...bouton, width: "auto" }}>Retour</button>
    </div>
  );
}

/* ── Panneau de déploiement : choix du canal ── */
function DeployPanel({ agent, onClose, onDeployed }) {
  const [channel, setChannel] = useState(null); // null | whatsapp_web | telegram | whatsapp_cloud
  const deployed = agent.deployed_channels || [];

  if (channel === "whatsapp_web") return <WhatsAppQR agent={agent} onClose={() => setChannel(null)} onDeployed={onDeployed} />;
  if (channel === "telegram") return <TelegramDeploy agent={agent} onClose={() => setChannel(null)} onDeployed={onDeployed} />;
  if (channel === "whatsapp_cloud") return <WhatsAppCloudDeploy agent={agent} onClose={() => setChannel(null)} onDeployed={onDeployed} />;

  return (
    <div className="space-y-2">
      <button onClick={() => setChannel("whatsapp_web")} style={{ ...bouton, display: "flex", alignItems: "center", gap: 12 }}>
        <QrCode size={20} style={{ color: "#25D366" }} />
        <div>
          <div style={{ fontWeight: 700, color: C.encre }}>WhatsApp — scan du QR code {deployed.includes("whatsapp_web") && "✓"}</div>
          <div style={{ fontSize: 12, color: C.doux }}>Votre WhatsApp perso ou pro, sans compte Meta Business.</div>
        </div>
      </button>
      <button onClick={() => setChannel("telegram")} style={{ ...bouton, display: "flex", alignItems: "center", gap: 12 }}>
        <TelegramIcon size={20} style={{ color: "#0088CC" }} />
        <div>
          <div style={{ fontWeight: 700, color: C.encre }}>Telegram {deployed.includes("telegram") && "✓"}</div>
          <div style={{ fontSize: 12, color: C.doux }}>Un bot créé via @BotFather.</div>
        </div>
      </button>
      <button onClick={() => setChannel("whatsapp_cloud")} style={{ ...bouton, display: "flex", alignItems: "center", gap: 12 }}>
        <MessageCircle size={20} style={{ color: C.navy }} />
        <div>
          <div style={{ fontWeight: 700, color: C.encre }}>WhatsApp Business (compte pro Meta) {deployed.includes("whatsapp") && "✓"}</div>
          <div style={{ fontSize: 12, color: C.doux }}>Un vrai numéro professionnel via l'API Cloud officielle.</div>
        </div>
      </button>
      <button onClick={onClose} style={{ ...bouton, width: "auto", marginTop: 8 }}>Fermer</button>
    </div>
  );
}

/* ── Carte agent ── */
function AgentCard({ agent, onDeploy, onOpenConversations }) {
  const deployed = agent.deployed_channels || [];
  return (
    <div className="rounded-2xl p-4" style={{ background: C.fond, border: `1px solid ${C.bord}` }}>
      <div className="flex items-start gap-3">
        <div className="rounded-xl p-2.5" style={{ background: `${agent.color || C.navy}1A` }}>
          <AgentIcon name={agent.avatar} color={agent.color} className="h-5 w-5" />
        </div>
        <div className="min-w-0 flex-1">
          <div style={{ fontWeight: 700, color: C.encre }}>{agent.name}</div>
          <div className="text-[13px]" style={{ color: C.doux }}>{agent.description}</div>
          {deployed.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-2">
              {deployed.map((c) => (
                <span key={c} className="text-[11px] px-2 py-0.5 rounded-full" style={{ background: C.fond2, color: C.texte }}>
                  {{ whatsapp_web: "WhatsApp (QR)", whatsapp: "WhatsApp Business", telegram: "Telegram" }[c] || c}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
      <div className="flex gap-2 mt-3">
        <button onClick={() => onDeploy(agent)} style={{ ...bouton, width: "auto", fontWeight: 600 }}>Déployer</button>
        {deployed.length > 0 && (
          <button onClick={() => onOpenConversations(agent)} style={{ ...bouton, width: "auto", display: "inline-flex", alignItems: "center", gap: 6 }}>
            <Inbox size={14} /> Conversations
          </button>
        )}
      </div>
    </div>
  );
}

/* ── Écran conversations d'un agent (WhatsApp/Telegram) ── */
function ConversationsPanel({ agent, onClose }) {
  const [threads, setThreads] = useState([]);
  const [active, setActive] = useState(null);
  const [reply, setReply] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get(`/custom-agents/${agent.id}/conversations`)
      .then((r) => setThreads(Array.isArray(r.data) ? r.data : (r.data?.items || [])))
      .catch(() => setThreads([]))
      .finally(() => setLoading(false));
  }, [agent.id]);

  const sendReply = async () => {
    if (!reply.trim() || !active) return;
    try {
      await api.post(`/custom-agents/${agent.id}/conversations/${encodeURIComponent(active.contact)}/reply`, { message: reply.trim() });
      setReply("");
      toast.success("Message envoyé.");
    } catch {
      toast.error("Envoi impossible.");
    }
  };

  return (
    <div className="space-y-3">
      <button onClick={onClose} style={{ ...bouton, width: "auto", display: "inline-flex", alignItems: "center", gap: 6 }}>
        <ArrowLeft size={14} /> Retour aux agents
      </button>
      {loading ? (
        <div className="flex justify-center py-8"><Loader2 className="animate-spin" size={22} /></div>
      ) : threads.length === 0 ? (
        <p className="text-[13px]" style={{ color: C.doux }}>Aucune conversation reçue pour l'instant.</p>
      ) : (
        <div className="grid md:grid-cols-3 gap-3">
          <div className="space-y-1.5">
            {threads.map((t) => (
              <button key={t.contact} onClick={() => setActive(t)} style={{ ...bouton, background: active?.contact === t.contact ? C.fond2 : C.fond }}>
                <div style={{ fontWeight: 600, fontSize: 13 }}>{t.contact_name || t.contact}</div>
                <div style={{ fontSize: 12, color: C.doux }}>{t.channel_label || t.channel}</div>
              </button>
            ))}
          </div>
          <div className="md:col-span-2 space-y-2">
            {active ? (
              <>
                <textarea rows={3} style={{ ...saisie, resize: "none" }} placeholder="Répondre manuellement (sans passer par l'IA)…" value={reply} onChange={(e) => setReply(e.target.value)} />
                <button onClick={sendReply} style={{ ...bouton, width: "auto", background: C.navy, color: "#fff", border: "none" }}>Envoyer</button>
              </>
            ) : <p className="text-[13px]" style={{ color: C.doux }}>Sélectionnez une conversation.</p>}
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Page principale ── */
export default function Agents() {
  const [agents, setAgents] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deployAgent, setDeployAgent] = useState(null);
  const [convAgent, setConvAgent] = useState(null);
  const [showTemplates, setShowTemplates] = useState(false);
  const [creating, setCreating] = useState(false);

  const load = useCallback(async () => {
    try {
      const [a, t] = await Promise.all([api.get("/custom-agents"), api.get("/custom-agents/templates")]);
      setAgents(Array.isArray(a.data) ? a.data : []);
      setTemplates(Array.isArray(t.data) ? t.data : []);
    } catch {
      setAgents([]); setTemplates([]);
    } finally { setLoading(false); }
  }, []);
  useEffect(() => { load(); }, [load]);

  const createFromTemplate = async (templateId) => {
    setCreating(true);
    try {
      await api.post("/custom-agents/from-template", { template_id: templateId });
      toast.success("Agent créé.");
      setShowTemplates(false);
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Création impossible — vérifiez votre plan.");
    } finally { setCreating(false); }
  };

  if (convAgent) return <div className="p-4 md:p-6"><ConversationsPanel agent={convAgent} onClose={() => setConvAgent(null)} /></div>;

  return (
    <div className="p-4 md:p-6 space-y-5" data-testid="agents-page">
      <header>
        <h1 className="font-display text-2xl md:text-3xl" style={{ color: C.encre }}>Mes agents</h1>
        <p className="text-[13px] mt-1" style={{ color: C.doux }}>
          Créez un agent, puis connectez-le à WhatsApp ou Telegram pour qu'il discute directement avec vos clients.
        </p>
      </header>

      {loading ? (
        <div className="flex justify-center py-10"><Loader2 className="animate-spin" size={24} /></div>
      ) : (
        <>
          <div className="grid md:grid-cols-2 gap-3">
            {agents.map((a) => (
              <AgentCard key={a.id} agent={a} onDeploy={setDeployAgent} onOpenConversations={setConvAgent} />
            ))}
            <button onClick={() => setShowTemplates(true)} style={{ ...bouton, display: "flex", alignItems: "center", justifyContent: "center", gap: 8, minHeight: 96, borderStyle: "dashed" }}>
              <Plus size={18} /> Nouvel agent
            </button>
          </div>

          {agents.length === 0 && (
            <p className="text-[13px]" style={{ color: C.doux }}>
              Aucun agent pour l'instant — partez d'un modèle prêt à l'emploi (assistant commercial, rédacteur, comptable IA…) puis connectez-le à WhatsApp.
            </p>
          )}
        </>
      )}

      {showTemplates && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ background: "rgba(15,23,42,0.45)" }}>
          <div className="rounded-2xl p-5 w-full max-w-lg space-y-3" style={{ background: C.fond, maxHeight: "80vh", overflowY: "auto" }}>
            <div className="flex items-center justify-between">
              <h3 style={{ fontWeight: 700 }}>Choisir un modèle</h3>
              <button onClick={() => setShowTemplates(false)}><X size={18} /></button>
            </div>
            {templates.map((t) => (
              <button key={t.id} disabled={creating} onClick={() => createFromTemplate(t.id)} style={{ ...bouton, display: "flex", alignItems: "center", gap: 12 }}>
                <AgentIcon name={t.avatar} color={t.color} className="h-5 w-5" />
                <div>
                  <div style={{ fontWeight: 600 }}>{t.name}</div>
                  <div style={{ fontSize: 12, color: C.doux }}>{t.description}</div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {deployAgent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ background: "rgba(15,23,42,0.45)" }}>
          <div className="rounded-2xl p-5 w-full max-w-md space-y-3" style={{ background: C.fond, maxHeight: "85vh", overflowY: "auto" }}>
            <div className="flex items-center justify-between">
              <h3 style={{ fontWeight: 700 }}>Déployer « {deployAgent.name} »</h3>
              <button onClick={() => setDeployAgent(null)}><X size={18} /></button>
            </div>
            <DeployPanel agent={deployAgent} onClose={() => setDeployAgent(null)} onDeployed={() => { load(); }} />
          </div>
        </div>
      )}
    </div>
  );
}
