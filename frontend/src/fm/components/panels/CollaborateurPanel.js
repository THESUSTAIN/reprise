import React, { useState, useEffect, useRef } from "react";
import { Sparkles } from "lucide-react";
import { collaborateurApi, api, getUserId } from "@fm/lib/api";
import { useI18n } from "@fm/context/I18nContext";
import SidePanel from "./SidePanel";

const MAX_HISTORY = 10;           // Nombre de tours à relire au démarrage
const STORAGE_KEY = (uid) => `collab_history_${uid}`;

// Suggestions multilingues — chips cliquables affichés tant qu'aucun
// message utilisateur n'a été envoyé.
const SUGGESTIONS = {
  fr: ["Quelle est ma priorité du jour ?", "Résume mon avancement Vision", "Idées pour atteindre 10k€/mois"],
  en: ["What's my priority today?", "Summarise my Vision progress", "Ideas to reach 10k€/month"],
  es: ["¿Cuál es mi prioridad de hoy?", "Resume mi progreso Visión", "Ideas para alcanzar 10k€/mes"],
  de: ["Was ist heute meine Priorität?", "Fasse meinen Visions-Fortschritt zusammen", "Ideen für 10k€/Monat"],
  it: ["Qual è la mia priorità di oggi?", "Riassumi i miei progressi sulla Visione", "Idee per arrivare a 10k€/mese"],
  pt: ["Qual é a minha prioridade hoje?", "Resuma o meu progresso na Visão", "Ideias para chegar a 10k€/mês"],
};

const greeting = (t, name, context) => ({
  from: "ai",
  text: t("collab.greeting", { name, context }),
});

export default function CollaborateurPanel({
  open,
  onClose,
  context = "Tableau de bord",
  userFirstName = "Julien",
  lang = "fr",
}) {
  const { t } = useI18n();
  const uid = getUserId();

  // ── Charger l'historique persistant au premier mount ──────────────────
  const loadHistory = () => {
    if (!uid) return [greeting(t, userFirstName, context)];
    try {
      const raw = localStorage.getItem(STORAGE_KEY(uid));
      if (!raw) return [greeting(t, userFirstName, context)];
      const saved = JSON.parse(raw);
      // Ajouter un message système indiquant qu'on relit le contexte
      return [
        greeting(t, userFirstName, context),
        {
          from: "ai",
          text: `Je me souviens de notre dernière conversation. Continuons là où nous en étions.`,
          isMemoryHint: true,
        },
        ...saved,
      ];
    } catch {
      return [greeting(t, userFirstName, context)];
    }
  };

  const [messages, setMessages] = useState(loadHistory);
  const [input,    setInput]    = useState("");
  const [thinking, setThinking] = useState(false);
  const bottomRef = useRef(null);
  const openRef = useRef(open);

  // Track open state to decide if AI replies should trigger the "unread" badge
  useEffect(() => {
    openRef.current = open;
    if (open) {
      try { localStorage.setItem("zay_collab_unread", "0"); } catch { /* ignore */ }
    }
  }, [open]);

  // Reset greeting quand le contexte change
  useEffect(() => {
    setMessages([greeting(t, userFirstName, context)]);
  }, [context, userFirstName, lang]);

  // Auto-scroll
  useEffect(() => {
    if (open) bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, thinking, open]);

  // ── Persister l'historique à chaque nouveau message ───────────────────
  const persistHistory = (msgs) => {
    if (!uid) return;
    const toSave = msgs
      .filter(m => !m.isMemoryHint) // ne pas sauvegarder le hint système
      .slice(1)                      // skip le greeting initial
      .slice(-MAX_HISTORY * 2);      // garder les 20 derniers msgs (10 tours)
    try {
      localStorage.setItem(STORAGE_KEY(uid), JSON.stringify(toSave));
    } catch { /* quota dépassé → ignorer */ }
  };

  // ── Envoyer un message ────────────────────────────────────────────────
  const send = async (text) => {
    const value = (text ?? input).trim();
    if (!value || thinking) return;

    const newMessages = [...messages, { from: "user", text: value }];
    setMessages(newMessages);
    setInput("");
    setThinking(true);

    // Construire l'historique à envoyer au backend
    // On inclut les 10 derniers échanges (depuis localStorage) en contexte
    const savedRaw = uid ? localStorage.getItem(STORAGE_KEY(uid)) : null;
    const savedHistory = savedRaw ? (() => { try { return JSON.parse(savedRaw); } catch { return []; } })() : [];

    // Fusionner : historique persistant + échanges courants de la session
    const sessionMsgs = newMessages
      .filter(m => !m.isMemoryHint)
      .slice(1) // skip greeting
      .map(m => ({ role: m.from === "user" ? "user" : "assistant", content: m.text }));

    const historyMsgs = savedHistory
      .slice(-MAX_HISTORY * 2)
      .map(m => ({ role: m.from === "user" ? "user" : "assistant", content: m.text }));

    // Dédupliquer : si la session courante recouvre l'historique, pas de doublon
    const apiMessages = historyMsgs.length > 0 && sessionMsgs.length > historyMsgs.length
      ? sessionMsgs
      : [...historyMsgs, ...sessionMsgs.slice(historyMsgs.length)];

    try {
      // Bug #18 — abort après 28s côté frontend pour éviter le crash Chrome
      const _ctrl = new AbortController();
      const _timer = setTimeout(() => _ctrl.abort(), 28000);
      let res;
      try {
        res = await collaborateurApi.chat(apiMessages, context, lang);
      } finally {
        clearTimeout(_timer);
      }
      const aiMsg = { from: "ai", text: res.reply || "…" };
      const updated = [...newMessages, aiMsg];
      setMessages(updated);
      persistHistory(updated); // 💾 Sauvegarder après chaque réponse IA
      // Si le panel est fermé quand l'IA répond → badge rouge sur FloatingBottomBar
      if (!openRef.current) {
        try { localStorage.setItem("zay_collab_unread", "1"); } catch { /* ignore */ }
      }
    } catch (e) {
      // Bug #5 : toujours afficher l'erreur ET reset thinking
      const errMsg = e?.response?.status === 402
        ? "Quota IA atteint — upgradez votre plan pour continuer."
        : e?.message || "Erreur réseau — réessayez.";
      setMessages(m => [
        ...m,
        { from: "ai", text: `⚠️ ${errMsg}` },
      ]);
    } finally {
      // Bug #5 : reset TOUJOURS pour débloquer le 2e message
      setThinking(false);
    }
  };

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
  };

  // ── Vider la mémoire ──────────────────────────────────────────────────
  const clearMemory = () => {
    if (!uid) return;
    localStorage.removeItem(STORAGE_KEY(uid));
    setMessages([greeting(t, userFirstName, context)]);
  };

  return (
    <SidePanel
      open={open}
      onClose={onClose}
      title={t("collab.title")}
      subtitle={context}
      action={
        <button
          onClick={clearMemory}
          title="Réinitialiser la mémoire"
          data-testid="collab-clear-memory"
          className="text-[11px] text-ink-soft/60 hover:text-ink-soft underline underline-offset-2 transition"
        >
          Effacer la mémoire
        </button>
      }
    >
      {/* Fil de messages */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
        {messages.map((m, i) => (
          <div
            key={i}
            data-testid={m.from === "user" ? "collab-user-msg" : "collab-ai-msg"}
            className={`flex ${m.from === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[82%] px-3.5 py-2.5 rounded-2xl text-[13.5px] leading-[1.55] ${
                m.from === "user"
                  ? "bg-navy text-cream rounded-br-sm"
                  : m.isMemoryHint
                  ? "bg-gold/10 text-ink-soft text-[12px] italic border border-gold/20 rounded-bl-sm"
                  : "bg-sand-100 text-ink rounded-bl-sm"
              }`}
            >
              {m.text}
            </div>
          </div>
        ))}
        {thinking && (
          <div className="flex justify-start">
            <div className="bg-sand-100 text-ink-soft text-[13.5px] px-3.5 py-2.5 rounded-2xl rounded-bl-sm">
              <span className="inline-flex gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-ink-soft/40 animate-bounce [animation-delay:0ms]" />
                <span className="w-1.5 h-1.5 rounded-full bg-ink-soft/40 animate-bounce [animation-delay:120ms]" />
                <span className="w-1.5 h-1.5 rounded-full bg-ink-soft/40 animate-bounce [animation-delay:240ms]" />
              </span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Zone de saisie + suggestions */}
      <div className="shrink-0 px-4 pb-4 pt-2 border-t border-sand-200">
        {/* Suggestions chips — visibles uniquement avant le 1er message utilisateur */}
        {!messages.some((m) => m.from === "user") && !thinking && (
          <div className="flex flex-wrap gap-2 mb-3" data-testid="collab-suggestions">
            {(SUGGESTIONS[lang] || SUGGESTIONS.fr).map((s, i) => (
              <button
                key={i}
                type="button"
                onClick={() => send(s)}
                data-testid={`collab-suggestion-${i}`}
                className="text-[12.5px] text-ink/85 px-3 py-1.5 rounded-full bg-white/70 hover:bg-white border border-sand-300 hover:border-navy/30 transition shadow-sm"
              >
                {s}
              </button>
            ))}
          </div>
        )}
        <div className="flex items-end gap-2">
          <div className="flex-1 relative">
            <Sparkles
              size={14}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-gold-deep pointer-events-none"
            />
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKey}
              placeholder={t("collab.placeholder")}
              rows={1}
              data-testid="collab-input"
              className="w-full resize-none rounded-2xl border border-sand-300 bg-white pl-9 pr-3.5 py-2.5 text-[13.5px] leading-[1.55] focus:outline-none focus:border-navy/40 transition max-h-[120px] overflow-y-auto"
              style={{ fieldSizing: "content" }}
              disabled={thinking}
            />
          </div>
          <button
            type="button"
            onClick={() => send()}
            disabled={thinking || !input.trim()}
            data-testid="collab-send"
            className="shrink-0 w-9 h-9 flex items-center justify-center rounded-xl bg-navy text-cream hover:bg-navy/90 disabled:opacity-40 transition"
            aria-label="Envoyer"
          >
            ↑
          </button>
        </div>
      </div>
    </SidePanel>
  );
}
