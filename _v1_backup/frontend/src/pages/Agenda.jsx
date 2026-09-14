import React, { useState } from "react";
import { motion } from "framer-motion";
import {
  CalendarDays, Filter, Mail, MessageSquare, Phone, Sparkles, Check, Clock, Bot,
} from "lucide-react";
import { GlassCard } from "@/components/common/GlassCard";
import { PageHeader } from "@/components/common/PageHeader";
import { agendaSlots, reminderCascade, weeklyDebrief } from "@/data/mock";
import { cn } from "@/lib/utils";
import { Switch } from "@/components/ui/switch";

const days = ["Lun", "Mar", "Mer", "Jeu", "Ven"];
const hours = ["09:00", "09:30", "10:00", "11:00", "14:00", "15:00", "16:00"];
const typeColor = {
  vente: "bg-gold/15 text-gold border-gold/30",
  focus: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  croissance: "bg-cyan-500/15 text-cyan-400 border-cyan-500/30",
  pilotage: "bg-indigo-500/15 text-indigo-400 border-indigo-500/30",
};
const channelIcon = { Email: Mail, SMS: MessageSquare, WhatsApp: MessageSquare, "Appel Copilote": Phone };
const statusColor = {
  "envoyé": "text-emerald-400", "planifié": "text-gold", "en attente": "text-muted-foreground",
};

export default function Agenda() {
  const [qualifiedOnly, setQualifiedOnly] = useState(false);
  const visible = qualifiedOnly ? agendaSlots.filter((s) => s.qualified) : agendaSlots;

  return (
    <div data-testid="agenda-page">
      <PageHeader
        icon={CalendarDays}
        title="Agenda"
        subtitle="Vos créneaux, la qualification IA et la cascade de rappels multicanaux. (interface — non connectée en V1)"
        action={
          <label className="flex items-center gap-2.5 rounded-full bg-secondary/50 border border-border/60 px-3 py-2 text-sm cursor-pointer">
            <Filter className="h-4 w-4 text-gold" />
            <span className="hidden sm:inline">Qualifiés IA</span>
            <Switch data-testid="agenda-qualified-toggle" checked={qualifiedOnly} onCheckedChange={setQualifiedOnly} />
          </label>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Calendar */}
        <GlassCard hover={false} className="lg:col-span-2 overflow-x-auto">
          <h2 className="font-serif text-lg font-medium mb-3">Semaine en cours</h2>
          <div className="min-w-[560px]">
            <div className="grid grid-cols-[56px_repeat(5,1fr)] gap-1.5">
              <div />
              {days.map((d) => <div key={d} className="text-center text-xs font-medium text-muted-foreground pb-1">{d}</div>)}
              {hours.map((h) => (
                <React.Fragment key={h}>
                  <div className="text-[11px] text-muted-foreground tabular-nums pt-2">{h}</div>
                  {days.map((d) => {
                    const slot = visible.find((s) => s.day === d && s.time === h);
                    return (
                      <div key={d + h} className="min-h-[42px] rounded-lg border border-border/40">
                        {slot && (
                          <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} data-testid={`agenda-slot-${slot.id}`} className={cn("h-full rounded-lg border p-1.5 text-[11px] leading-tight", typeColor[slot.type])}>
                            <span className="block truncate font-medium">{slot.label}</span>
                            {slot.qualified && <span className="inline-flex items-center gap-0.5 mt-0.5 text-[9px] opacity-80"><Sparkles className="h-2.5 w-2.5" />IA</span>}
                          </motion.div>
                        )}
                      </div>
                    );
                  })}
                </React.Fragment>
              ))}
            </div>
          </div>
        </GlassCard>

        <div className="space-y-4">
          {/* Reminder cascade */}
          <GlassCard glow="gold">
            <h2 className="font-serif text-lg font-medium mb-3">Cascade de rappels</h2>
            <div className="relative pl-4">
              <div className="absolute left-[6px] top-2 bottom-2 w-px bg-gold/30" />
              {reminderCascade.map((r) => {
                const Icon = channelIcon[r.channel] || Mail;
                return (
                  <div key={r.id} className="relative pb-3.5 last:pb-0">
                    <span className="absolute -left-[13px] top-0.5 h-3 w-3 rounded-full bg-gold ring-4 ring-gold/15" />
                    <div className="flex items-center gap-2">
                      <Icon className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm font-medium">{r.channel}</span>
                      <span className="text-xs text-muted-foreground">· {r.delay}</span>
                      <span className={cn("ml-auto text-[11px]", statusColor[r.status])}>{r.status}</span>
                    </div>
                  </div>
                );
              })}
            </div>
            <p className="text-[11px] text-muted-foreground mt-2 flex items-center gap-1">
              <Clock className="h-3 w-3" /> Slot prêt à brancher (Make / natif)
            </p>
          </GlassCard>

          {/* Weekly AI debrief */}
          <GlassCard glow="emerald">
            <div className="flex items-center gap-2 mb-3">
              <Bot className="h-4 w-4 text-gold" />
              <h2 className="font-serif text-lg font-medium">Débrief hebdo IA</h2>
            </div>
            <ul className="space-y-2">
              {weeklyDebrief.map((d, i) => (
                <li key={i} className="flex items-start gap-2 text-sm">
                  <Check className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
                  <span className="text-muted-foreground">{d}</span>
                </li>
              ))}
            </ul>
          </GlassCard>
        </div>
      </div>
    </div>
  );
}
