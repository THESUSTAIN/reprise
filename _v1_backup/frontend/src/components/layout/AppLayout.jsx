import React, { useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import Sidebar from "./Sidebar";
import Header from "./Header";
import { useApp } from "@/context/AppContext";
import { cn } from "@/lib/utils";

export function AppLayout() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  const { ambiance } = useApp();

  return (
    <div
      className={cn(
        "grain min-h-screen relative bg-gradient-to-br",
        "from-[#F1F5F9] via-[#E7EDF5] to-[#F8FAFC]",
        "dark:from-[#050A18] dark:via-[#0A1228] dark:to-[#0F1A36]"
      )}
    >
      {/* Ambient glows */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden z-0">
        <div className={cn(
          "absolute -top-40 -right-32 h-96 w-96 rounded-full blur-3xl opacity-30 transition-colors duration-700",
          ambiance === "elan" ? "bg-gold/25" : "bg-teal-500/20"
        )} />
        <div className={cn(
          "absolute -bottom-40 -left-20 h-96 w-96 rounded-full blur-3xl opacity-20 transition-colors duration-700",
          ambiance === "elan" ? "bg-emerald-500/20" : "bg-indigo-500/20"
        )} />
      </div>

      <Sidebar mobileOpen={mobileOpen} onClose={() => setMobileOpen(false)} />

      <div className="relative z-10 md:pl-20 lg:pl-64">
        <Header onMenu={() => setMobileOpen(true)} />
        <main className="px-4 sm:px-6 lg:px-8 py-6 max-w-[1500px]">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.28, ease: "easeOut" }}
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}

export default AppLayout;
