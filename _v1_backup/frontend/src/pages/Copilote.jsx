import React, { useRef, useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Sparkles, Send, Check, X, Clock, Zap } from "lucide-react";
import { toast } from "sonner";
import { GlassCard } from "@/components/common/GlassCard";
import { PageHeader } from "@/components/common/PageHeader";
import {
  copiloteThread, copiloteSuggestions, deliverables as mockDeliverables, copilote,
} from "@/data/mock";
import { cn } from "@/lib/utils";

const cannedReplies = [
  "Bien reçu. Je prépare une proposition et je la déposerai dans vos livrables à valider. Vous gardez la décision finale ✍️",
  "Voici ce que je recommande : prioriser les 2 prospects à fort score, puis relancer les factures en retard. Je peux tout préparer ?",
  "Analyse terminée. Votre trésorerie est saine (+6%). Je vous suggère de sécuriser 1 600 € de MRR pour atteindre votre palier.",
  "J'ai rédigé un brouillon. Dites-moi si vous voulez un ton plus direct ou plus chaleureux, je l'ajuste en un instant.",
];

export default function Copilote() {
  const [messages, setMessages] = useState(copiloteThread);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const [deliverables, setDeliverables] = useState(mockDeliverables);
  const endRef = useRef(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, typing]);

  const send = (text) => {
    const value = (text ?? input).trim();
    if (!value) return;
    setMessages((m) => [...m, { id: Date.now(), role: "user", text: value }]);
    setInput("");
    setTyping(true);
    setTimeout(() => {
      setTyping(false);
      const reply = cannedReplies[Math.floor(Math.random() * cannedReplies.length)];
      setMessages((m) => [...m, { id: Date.now() + 1, role: "assistant", text: reply }]);
    }, 900);
  };

  const actOnDeliverable = (id, accept) => {
    setDeliverables((list) => list.filter((d) => d.id !== id));
    toast[accept ? "success" : "message"](accept ? "Livrable validé ✅" : "Renvoyé au Copilote");
  };

  return (
    <div data-testid="copilote-page">
      <PageHeader
        icon={Sparkles}
        title="Copilote IA"
        subtitle="Votre bras droit stratégique. L'IA prépare, vous décidez. (réponses simulées en V1)"
        action={
          <div className="hidden sm:flex items-center gap-2 rounded-full bg-gold/10 border border-gold/25 px-3 py-1.5 text-xs text-gold">
            <Zap className="h-3.5 w-3.5" /> {copilote.timeSavedHours}h gagnées cette semaine
          </div>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Chat */}
        <GlassCard hover={false} className="lg:col-span-2 flex flex-col !p-0 overflow-hidden" style={{ height: "calc(100vh - 220px)", minHeight: 480 }}>
          <div className="flex-1 overflow-y-auto p-5 space-y-4">
            {messages.map((m) => (
              <motion.div
                key={m.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className={cn("flex gap-3", m.role === "user" ? "justify-end" : "justify-start")}
              >
                {m.role === "assistant" && (
                  <span className="h-8 w-8 shrink-0 rounded-lg grid place-items-center bg-gradient-to-br from-gold to-gold-light text-night-800">
                    <Sparkles className="h-4 w-4" />
                  </span>
                )}
                <div className={cn(
                  "max-w-[78%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
                  m.role === "user"
                    ? "bg-gold text-night-800 rounded-br-sm font-medium"
                    : "bg-secondary/70 rounded-bl-sm"
                )}>
                  {m.text}
                </div>
              </motion.div>
            ))}
            {typing && (
              <div className="flex gap-3">
                <span className="h-8 w-8 shrink-0 rounded-lg grid place-items-center bg-gradient-to-br from-gold to-gold-light text-night-800"><Sparkles className="h-4 w-4" /></span>
                <div className="bg-secondary/70 rounded-2xl rounded-bl-sm px-4 py-3 flex gap-1">
                  {[0, 1, 2].map((i) => (
                    <span key={i} className="h-2 w-2 rounded-full bg-muted-foreground/60 animate-pulse-glow" style={{ animationDelay: `${i * 0.2}s` }} />
                  ))}
                </div>
              </div>
            )}
            <div ref={endRef} />
          </div>

          {/* Suggestions + input */}
          <div className="border-t border-border/60 p-4">
            <div className="flex flex-wrap gap-2 mb-3">
              {copiloteSuggestions.map((s, i) => (
                <button
                  key={i}
                  data-testid={`copilote-suggestion-${i}`}
                  onClick={() => send(s)}
                  className="text-xs rounded-full border border-border/60 bg-secondary/40 px-3 py-1.5 hover:border-gold/40 hover:text-gold transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2">
              <input
                data-testid="copilote-input"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && send()}
                placeholder="Demandez quelque chose au Copilote…"
                className="flex-1 rounded-full bg-secondary/60 border border-border/60 px-4 py-2.5 text-sm outline-none focus:border-gold/50 focus:ring-2 focus:ring-gold/15 transition-colors"
              />
              <button data-testid="copilote-send-btn" onClick={() => send()} className="h-11 w-11 shrink-0 grid place-items-center rounded-full bg-gradient-to-br from-gold to-gold-light text-night-800 hover:shadow-[0_0_20px_rgba(212,175,55,0.4)] transition-shadow">
                <Send className="h-4 w-4" />
              </button>
            </div>
          </div>
        </GlassCard>

        {/* Deliverables side */}
        <div className="space-y-4">
          <GlassCard glow="emerald">
            <div className="grid grid-cols-3 gap-2 text-center">
              {[
                { l: "% avec IA", v: `${copilote.aiWorkPercent}%`, c: "text-gold" },
                { l: "Validés", v: copilote.validated, c: "text-emerald-400" },
                { l: "En attente", v: deliverables.length, c: "text-cyan-400" },
              ].map((s) => (
                <div key={s.l}>
                  <p className={cn("font-serif text-2xl font-semibold", s.c)}>{s.v}</p>
                  <p className="text-[11px] text-muted-foreground">{s.l}</p>
                </div>
              ))}
            </div>
          </GlassCard>

          <GlassCard hover={false}>
            <h2 className="font-serif text-lg font-medium mb-3">À valider</h2>
            <div className="space-y-3">
              {deliverables.length === 0 && <p className="text-sm text-muted-foreground py-4 text-center">Boîte vide 🎯</p>}
              {deliverables.map((d) => (
                <motion.div key={d.id} layout initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="rounded-xl border border-border/60 bg-secondary/30 p-3" data-testid={`copilote-deliverable-${d.id}`}>
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-sm font-medium">{d.title}</span>
                    <span className="text-[10px] text-emerald-400 shrink-0"><Clock className="inline h-3 w-3 mr-0.5" />{d.confidence}%</span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{d.preview}</p>
                  <div className="flex gap-2 mt-2.5">
                    <button data-testid={`copilote-accept-${d.id}`} onClick={() => actOnDeliverable(d.id, true)} className="flex-1 flex items-center justify-center gap-1 rounded-lg bg-emerald-500/15 text-emerald-400 text-xs py-1.5 hover:bg-emerald-500/25 transition-colors font-medium">
                      <Check className="h-3.5 w-3.5" /> Valider
                    </button>
                    <button data-testid={`copilote-reject-${d.id}`} onClick={() => actOnDeliverable(d.id, false)} className="flex-1 flex items-center justify-center gap-1 rounded-lg bg-secondary text-muted-foreground text-xs py-1.5 hover:bg-rose-500/15 hover:text-rose-400 transition-colors font-medium">
                      <X className="h-3.5 w-3.5" /> Rejeter
                    </button>
                  </div>
                </motion.div>
              ))}
            </div>
          </GlassCard>
        </div>
      </div>
    </div>
  );
}
