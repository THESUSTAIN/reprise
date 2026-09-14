import {
  LayoutDashboard, Sparkles, Compass, TrendingUp, Wallet,
  HeartPulse, Layers, Brain, Target, CalendarDays, Settings,
} from "lucide-react";

export const navItems = [
  { to: "/cockpit", label: "Cockpit du jour", short: "Cockpit", icon: LayoutDashboard, testid: "cockpit" },
  { to: "/copilote", label: "Copilote IA", short: "Copilote", icon: Sparkles, testid: "copilote" },
  { to: "/vision", label: "Vision", short: "Vision", icon: Compass, testid: "vision" },
  { to: "/croissance", label: "Croissance", short: "Croissance", icon: TrendingUp, testid: "croissance" },
  { to: "/pilotage", label: "Pilotage / DAF IA", short: "Pilotage", icon: Wallet, testid: "pilotage" },
  { to: "/bien-etre", label: "Bien-être", short: "Bien-être", icon: HeartPulse, testid: "bien-etre" },
  { to: "/contexte", label: "Contexte", short: "Contexte", icon: Layers, testid: "contexte" },
  { to: "/mindset", label: "Mindset", short: "Mindset", icon: Brain, testid: "mindset" },
  { to: "/vision-board", label: "Vision Board", short: "Board", icon: Target, testid: "vision-board" },
  { to: "/agenda", label: "Agenda", short: "Agenda", icon: CalendarDays, testid: "agenda" },
  { to: "/parametres", label: "Paramètres", short: "Réglages", icon: Settings, testid: "parametres" },
];
