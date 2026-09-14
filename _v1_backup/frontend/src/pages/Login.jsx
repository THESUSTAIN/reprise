import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Feather, ArrowRight, Sparkles } from "lucide-react";
import { useApp } from "@/context/AppContext";
import { user } from "@/data/mock";

export default function Login() {
  const { login } = useApp();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  const enter = () => {
    setLoading(true);
    setTimeout(() => {
      login();
      navigate("/cockpit");
    }, 650);
  };

  return (
    <div className="grain min-h-screen relative grid place-items-center bg-gradient-to-br from-[#050A18] via-[#0A1228] to-[#0F1A36] text-slate-100 px-5 overflow-hidden">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -top-32 right-0 h-[28rem] w-[28rem] rounded-full bg-gold/20 blur-3xl" />
        <div className="absolute bottom-0 -left-24 h-[26rem] w-[26rem] rounded-full bg-emerald-500/15 blur-3xl" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
        className="relative z-10 w-full max-w-md glass p-8 sm:p-10 text-center"
      >
        <motion.div
          initial={{ scale: 0.7, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.15, type: "spring", stiffness: 220 }}
          className="mx-auto h-16 w-16 rounded-2xl grid place-items-center bg-gradient-to-br from-gold to-gold-light shadow-[0_0_30px_rgba(212,175,55,0.4)]"
        >
          <Feather className="h-8 w-8 text-night-800" />
        </motion.div>

        <p className="mt-5 text-[11px] uppercase tracking-[0.28em] text-gold/80">écosystème Zayado</p>
        <h1 className="mt-2 text-3xl sm:text-4xl font-semibold tracking-tight">
          MyExtension <span className="gold-gradient-text">Business</span>
        </h1>
        <p className="mt-3 text-sm text-slate-400 leading-relaxed">
          Le cockpit holistique du solopreneur.
          <br />
          <span className="inline-flex items-center gap-1.5 mt-2 text-gold">
            <Sparkles className="h-3.5 w-3.5" /> « L'IA prépare, vous décidez. »
          </span>
        </p>

        <button
          data-testid="login-enter-cockpit-btn"
          onClick={enter}
          disabled={loading}
          className="group mt-8 w-full flex items-center justify-center gap-2 rounded-full bg-gradient-to-r from-gold to-gold-light text-night-800 font-semibold py-3.5 shadow-[0_8px_30px_rgba(212,175,55,0.3)] hover:shadow-[0_10px_40px_rgba(212,175,55,0.45)] transition-shadow disabled:opacity-70"
        >
          {loading ? "Ouverture du cockpit…" : `Entrer dans le cockpit`}
          {!loading && <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />}
        </button>

        <p className="mt-5 text-xs text-slate-500">
          Connectée en tant que <span className="text-slate-300">{user.firstName} {user.lastName}</span> · démo
        </p>
      </motion.div>
    </div>
  );
}
