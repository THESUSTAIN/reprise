import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search, Bell, MessageSquare, Menu, Moon, Sun, Zap, Leaf,
} from "lucide-react";
import { useApp } from "@/context/AppContext";
import { user, deliverables, recentActivity } from "@/data/mock";
import { cn } from "@/lib/utils";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel,
  DropdownMenuSeparator, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useNavigate } from "react-router-dom";

export function Header({ onMenu }) {
  const { theme, toggleTheme, ambiance, toggleAmbiance, logout } = useApp();
  const navigate = useNavigate();
  const [query, setQuery] = useState("");

  return (
    <header className="sticky top-0 z-30 backdrop-blur-xl bg-white/70 dark:bg-night-800/70 border-b border-border/70 px-4 sm:px-6 py-3 flex items-center gap-3">
      <button
        data-testid="header-menu-btn"
        onClick={onMenu}
        className="md:hidden h-9 w-9 grid place-items-center rounded-lg hover:bg-secondary transition-colors"
        aria-label="Menu"
      >
        <Menu className="h-5 w-5" />
      </button>

      {/* Search */}
      <div className="relative flex-1 max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input
          data-testid="header-search-input"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Rechercher un prospect, une action…"
          className="w-full rounded-full bg-secondary/60 border border-border/60 pl-10 pr-14 py-2 text-sm outline-none focus:border-gold/50 focus:ring-2 focus:ring-gold/15 transition-colors"
        />
        <span className="hidden sm:flex absolute right-2.5 top-1/2 -translate-y-1/2 items-center gap-0.5 text-[10px] text-muted-foreground bg-background/70 border border-border/60 rounded px-1.5 py-0.5">
          Ctrl K
        </span>
      </div>

      <div className="ml-auto flex items-center gap-1.5 sm:gap-2">
        {/* Ambiance toggle */}
        <button
          data-testid="ambiance-mode-toggle"
          onClick={toggleAmbiance}
          className={cn(
            "hidden sm:flex items-center gap-2 rounded-full pl-2.5 pr-3 py-1.5 text-xs font-medium border transition-colors",
            ambiance === "elan"
              ? "bg-gold/10 text-gold border-gold/30"
              : "bg-teal-500/10 text-teal-400 border-teal-500/30"
          )}
          title="Basculer Mode Élan / Refuge"
        >
          {ambiance === "elan" ? <Zap className="h-3.5 w-3.5" /> : <Leaf className="h-3.5 w-3.5" />}
          {ambiance === "elan" ? "Élan" : "Refuge"}
        </button>

        {/* Theme */}
        <button
          data-testid="theme-toggle"
          onClick={toggleTheme}
          className="h-9 w-9 grid place-items-center rounded-full hover:bg-secondary transition-colors"
          aria-label="Thème"
        >
          <AnimatePresence mode="wait" initial={false}>
            {theme === "dark" ? (
              <motion.span key="moon" initial={{ rotate: -90, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }} exit={{ rotate: 90, opacity: 0 }}>
                <Moon className="h-[18px] w-[18px]" />
              </motion.span>
            ) : (
              <motion.span key="sun" initial={{ rotate: 90, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }} exit={{ rotate: -90, opacity: 0 }}>
                <Sun className="h-[18px] w-[18px]" />
              </motion.span>
            )}
          </AnimatePresence>
        </button>

        {/* Notifications */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button data-testid="header-notifications-btn" className="relative h-9 w-9 grid place-items-center rounded-full hover:bg-secondary transition-colors">
              <Bell className="h-[18px] w-[18px]" />
              <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-rose-500 ring-2 ring-background" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-80">
            <DropdownMenuLabel>Notifications</DropdownMenuLabel>
            <DropdownMenuSeparator />
            {recentActivity.map((a) => (
              <DropdownMenuItem key={a.id} className="flex-col items-start gap-0.5 py-2">
                <span className="text-sm">{a.label}</span>
                <span className="text-xs text-muted-foreground">{a.time}</span>
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Messages */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button data-testid="header-messages-btn" className="relative h-9 w-9 grid place-items-center rounded-full hover:bg-secondary transition-colors">
              <MessageSquare className="h-[18px] w-[18px]" />
              <span className="absolute top-1 right-1 h-4 min-w-4 px-1 grid place-items-center rounded-full bg-gold text-[10px] font-semibold text-night-800">
                {deliverables.length}
              </span>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-80">
            <DropdownMenuLabel>Livrables du Copilote à valider</DropdownMenuLabel>
            <DropdownMenuSeparator />
            {deliverables.map((d) => (
              <DropdownMenuItem key={d.id} onClick={() => navigate("/copilote")} className="flex-col items-start gap-0.5 py-2">
                <span className="text-sm">{d.title}</span>
                <span className="text-xs text-muted-foreground">{d.type} · confiance {d.confidence}%</span>
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Profile */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button data-testid="header-profile-btn" className="flex items-center gap-2 rounded-full pl-1 pr-2.5 py-1 hover:bg-secondary transition-colors">
              <Avatar className="h-8 w-8 border border-gold/40">
                <AvatarImage src={user.avatar} alt={user.firstName} />
                <AvatarFallback>{user.firstName[0]}</AvatarFallback>
              </Avatar>
              <span className="hidden sm:block text-sm font-medium">{user.firstName}</span>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel className="flex flex-col">
              <span>{user.firstName} {user.lastName}</span>
              <span className="text-xs font-normal text-muted-foreground">{user.role}</span>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem data-testid="profile-menu-settings" onClick={() => navigate("/parametres")}>Paramètres</DropdownMenuItem>
            <DropdownMenuItem data-testid="profile-menu-logout" onClick={() => { logout(); navigate("/"); }} className="text-rose-400 focus:text-rose-400">
              Déconnexion
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}

export default Header;
