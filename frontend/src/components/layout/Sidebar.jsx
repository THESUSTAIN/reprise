import React from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { LogOut, Feather } from "lucide-react";
import { navItems } from "./navConfig";
import { useApp } from "@/context/AppContext";
import { cn } from "@/lib/utils";

export function Sidebar({ mobileOpen, onClose }) {
  const { logout, ambiance } = useApp();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  const content = (
    <div className="flex h-full flex-col justify-between py-5">
      <div className="flex-1 min-h-0 flex flex-col">
        {/* Brand */}
        <div className="px-4 flex items-center gap-3 mb-6">
          <div className="h-10 w-10 shrink-0 rounded-xl grid place-items-center bg-gradient-to-br from-gold to-gold-light shadow-[0_0_18px_rgba(212,175,55,0.35)]">
            <Feather className="h-5 w-5 text-night-800" />
          </div>
          <div className="hidden lg:block leading-tight">
            <p className="font-serif font-semibold text-[15px]">MyExtension</p>
            <p className="text-[10px] uppercase tracking-[0.18em] text-gold/80">écosystème Zayado</p>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 min-h-0 overflow-y-auto px-3 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onClose}
              data-testid={`sidebar-nav-${item.testid}`}
              className={({ isActive }) =>
                cn(
                  "group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-colors duration-200",
                  isActive
                    ? "bg-gold/12 text-gold"
                    : "text-muted-foreground hover:text-foreground hover:bg-secondary/60"
                )
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <motion.span
                      layoutId="sidebar-active"
                      className="absolute left-0 top-1/2 -translate-y-1/2 h-6 w-1 rounded-full bg-gold"
                    />
                  )}
                  <item.icon className="h-[18px] w-[18px] shrink-0" />
                  <span className="hidden lg:block truncate">{item.label}</span>
                </>
              )}
            </NavLink>
          ))}
        </nav>
      </div>

      {/* Ambiance + logout */}
      <div className="px-3 pt-3 space-y-2">
        <div className="hidden lg:flex items-center gap-2 rounded-xl px-3 py-2 bg-secondary/40 border border-border/60">
          <span className={cn("h-2 w-2 rounded-full animate-pulse-glow", ambiance === "elan" ? "bg-gold" : "bg-teal-400")} />
          <span className="text-xs text-muted-foreground">
            Mode {ambiance === "elan" ? "Élan" : "Refuge"}
          </span>
        </div>
        <button
          data-testid="sidebar-logout-btn"
          onClick={handleLogout}
          className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-muted-foreground hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
        >
          <LogOut className="h-[18px] w-[18px]" />
          <span className="hidden lg:block">Déconnexion</span>
        </button>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop */}
      <aside className="hidden md:block fixed left-0 top-0 h-screen z-40 w-20 lg:w-64 backdrop-blur-xl bg-white/70 dark:bg-night-900/85 border-r border-border/70">
        {content}
      </aside>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="md:hidden fixed inset-0 z-50">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
          <motion.aside
            initial={{ x: -300 }}
            animate={{ x: 0 }}
            transition={{ type: "spring", stiffness: 320, damping: 32 }}
            className="absolute left-0 top-0 h-full w-64 backdrop-blur-xl bg-white/95 dark:bg-night-900/95 border-r border-border/70"
          >
            <div className="lg:!block [&_.hidden]:!block">{content}</div>
          </motion.aside>
        </div>
      )}
    </>
  );
}

export default Sidebar;
