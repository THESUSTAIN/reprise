import React from "react";
import { toast } from "sonner";
import {
  Settings, Moon, Sun, Heart, Bell, Globe, Zap, Leaf, User,
} from "lucide-react";
import { GlassCard } from "@/components/common/GlassCard";
import { PageHeader } from "@/components/common/PageHeader";
import { Switch } from "@/components/ui/switch";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useApp } from "@/context/AppContext";
import { user } from "@/data/mock";
import { cn } from "@/lib/utils";

function Row({ icon: Icon, title, desc, children }) {
  return (
    <div className="flex items-center justify-between gap-4 py-3.5 border-b border-border/50 last:border-0">
      <div className="flex items-start gap-3">
        <span className="h-9 w-9 shrink-0 rounded-lg grid place-items-center bg-secondary/60 text-gold"><Icon className="h-4 w-4" /></span>
        <div>
          <p className="text-sm font-medium">{title}</p>
          {desc && <p className="text-xs text-muted-foreground mt-0.5">{desc}</p>}
        </div>
      </div>
      <div className="shrink-0">{children}</div>
    </div>
  );
}

export default function Parametres() {
  const { theme, toggleTheme, ambiance, toggleAmbiance, faith, toggleFaith } = useApp();

  return (
    <div data-testid="parametres-page">
      <PageHeader icon={Settings} title="Paramètres" subtitle="Personnalisez votre cockpit. Vos préférences sont mémorisées localement." />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Profile */}
        <GlassCard hover={false}>
          <div className="flex flex-col items-center text-center">
            <Avatar className="h-20 w-20 border-2 border-gold/40">
              <AvatarImage src={user.avatar} alt={user.firstName} />
              <AvatarFallback>{user.firstName[0]}</AvatarFallback>
            </Avatar>
            <h2 className="font-serif text-xl font-medium mt-3">{user.firstName} {user.lastName}</h2>
            <p className="text-sm text-muted-foreground">{user.role}</p>
            <span className="mt-3 text-xs rounded-full bg-gold/10 text-gold border border-gold/25 px-3 py-1">{user.company} · écosystème Zayado</span>
          </div>
        </GlassCard>

        {/* Preferences */}
        <GlassCard hover={false} className="lg:col-span-2">
          <h2 className="font-serif text-lg font-medium mb-1">Préférences</h2>
          <div>
            <Row icon={theme === "dark" ? Moon : Sun} title="Thème" desc={theme === "dark" ? "Bleu nuit (dark)" : "Clair (light)"}>
              <Switch data-testid="settings-theme-toggle" checked={theme === "dark"} onCheckedChange={toggleTheme} />
            </Row>

            <Row icon={ambiance === "elan" ? Zap : Leaf} title="Ambiance de l'interface" desc={ambiance === "elan" ? "Mode Élan — actionnable & dynamique" : "Mode Refuge — apaisant & ancrage"}>
              <button
                data-testid="settings-ambiance-toggle"
                onClick={toggleAmbiance}
                className={cn(
                  "flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium border transition-colors",
                  ambiance === "elan" ? "bg-gold/10 text-gold border-gold/30" : "bg-teal-500/10 text-teal-400 border-teal-500/30"
                )}
              >
                {ambiance === "elan" ? <Zap className="h-3.5 w-3.5" /> : <Leaf className="h-3.5 w-3.5" />}
                {ambiance === "elan" ? "Élan" : "Refuge"}
              </button>
            </Row>

            <Row icon={Heart} title="Faith-Toggle" desc="Affiche des versets & un ancrage spirituel en Mode Refuge">
              <Switch
                data-testid="faith-toggle-switch"
                checked={faith}
                onCheckedChange={() => { toggleFaith(); toast.message(!faith ? "Faith-Toggle activé" : "Faith-Toggle désactivé"); }}
              />
            </Row>

            <Row icon={Globe} title="Langue" desc="Français (V1)">
              <span className="text-sm rounded-full bg-secondary/60 border border-border/60 px-3 py-1.5">FR</span>
            </Row>

            <Row icon={Bell} title="Notifications" desc="Rappels, livrables IA et alertes financières">
              <Switch data-testid="settings-notifications-toggle" defaultChecked />
            </Row>
          </div>
        </GlassCard>
      </div>

      <p className="text-xs text-muted-foreground mt-5 text-center">
        MyExtension Business · V1 démo — données mockées, aucun backend ni IA réellement branché. Zones automations & marketplace maquettées comme « slots prêts à brancher ».
      </p>
    </div>
  );
}
