import { useEffect, useState, useCallback } from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles, LayoutDashboard, Eye, MessageCircle, ListChecks, TrendingUp,
  Rocket, ArrowRight, ArrowLeft, X, Check,
} from "lucide-react";

// Guide de première connexion — « Voici ce que fait l'appli ».
// Objectif UX : lever la confusion en 30 secondes en expliquant, en langage
// simple, ce qu'est le cockpit et à quoi sert chaque zone de navigation.
// S'affiche une seule fois (clé localStorage), réouvrable via l'événement
// global "cours:open-tour" (menu Aide & Support).
const SEEN_KEY = "mx_welcome_tour_v1";

const STEPS = [
  {
    id: "intro",
    Icon: Sparkles,
    kicker: "Bienvenue 👋",
    title: "Voici ce que fait MyExtension",
    text: "Votre cockpit unique pour piloter vos finances, votre vision, votre croissance et votre énergie — sans jongler entre 10 outils.",
    highlight: "« L'IA prépare, vous décidez. »",
  },
  {
    id: "aujourdhui",
    Icon: LayoutDashboard,
    kicker: "Aujourd'hui",
    title: "Votre journée en un coup d'œil",
    text: "Dès l'ouverture : votre énergie du jour, vos priorités et vos chiffres clés. Le point de départ chaque matin.",
  },
  {
    id: "vision",
    Icon: Eye,
    kicker: "Vision",
    title: "Votre cap & vos décisions",
    text: "Clarifiez où vous allez (vision, valeurs, objectifs) et vérifiez que vos actions restent alignées avec ce qui compte.",
  },
  {
    id: "copilote",
    Icon: MessageCircle,
    kicker: "Copilote",
    title: "L'IA prépare, vous décidez",
    text: "Le Copilote rédige vos relances, vos contenus et vos analyses. Il vous propose, vous validez d'un clic. Vous gardez le contrôle.",
  },
  {
    id: "action",
    Icon: ListChecks,
    kicker: "Mouvement & Croissance",
    title: "Passez à l'action",
    text: "Vos tâches, vos projets, vos prospects et vos ventes réunis au même endroit pour avancer concrètement, chaque jour.",
  },
  {
    id: "start",
    Icon: Rocket,
    kicker: "C'est parti",
    title: "Prêt à décoller ?",
    text: "Commencez par regarder votre journée. Le Copilote est toujours à portée de clic si vous avez besoin d'un coup de main.",
    cta: "Entrer dans le cockpit",
  },
];

export default function WelcomeTour() {
  const [open, setOpen] = useState(false);
  const [i, setI] = useState(0);

  useEffect(() => {
    // Première connexion : on ouvre automatiquement.
    let seen = true;
    try { seen = localStorage.getItem(SEEN_KEY) === "1"; } catch { /* noop */ }
    if (!seen) setOpen(true);
    // Réouverture manuelle depuis « Aide & Support ».
    const onOpen = () => { setI(0); setOpen(true); };
    window.addEventListener("cours:open-tour", onOpen);
    return () => window.removeEventListener("cours:open-tour", onOpen);
  }, []);

  const close = useCallback(() => {
    try { localStorage.setItem(SEEN_KEY, "1"); } catch { /* noop */ }
    setOpen(false);
  }, []);

  const next = () => (i < STEPS.length - 1 ? setI((n) => n + 1) : close());
  const prev = () => setI((n) => Math.max(0, n - 1));

  useEffect(() => {
    if (!open) return;
    const onKey = (e) => {
      if (e.key === "Escape") close();
      if (e.key === "ArrowRight") next();
      if (e.key === "ArrowLeft") prev();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, i, close]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!open) return null;
  const step = STEPS[i];
  const Icon = step.Icon;
  const isLast = i === STEPS.length - 1;

  return createPortal(
    <AnimatePresence>
      <motion.div
        key="tour-overlay"
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
        className="fixed inset-0 z-[200] flex items-center justify-center p-4"
        style={{ background: "rgba(4,10,24,0.72)", backdropFilter: "blur(6px)" }}
        data-testid="welcome-tour"
        onClick={close}
      >
        <motion.div
          initial={{ opacity: 0, y: 24, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 12, scale: 0.98 }}
          transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
          onClick={(e) => e.stopPropagation()}
          className="relative w-full max-w-lg overflow-hidden rounded-3xl border border-white/12 text-white shadow-2xl"
          style={{ background: "linear-gradient(160deg,#0B1F3A 0%,#0A1730 60%,#0C1226 100%)" }}
        >
          {/* Glows */}
          <div className="pointer-events-none absolute -top-24 -right-16 h-56 w-56 rounded-full blur-3xl" style={{ background: "rgba(232,201,106,0.22)" }} />
          <div className="pointer-events-none absolute -bottom-24 -left-16 h-56 w-56 rounded-full blur-3xl" style={{ background: "rgba(16,185,129,0.14)" }} />

          <button
            onClick={close}
            data-testid="welcome-tour-skip"
            className="absolute right-4 top-4 z-10 flex h-8 w-8 items-center justify-center rounded-full border border-white/15 text-white/70 hover:text-white hover:bg-white/10 transition-colors"
            aria-label="Passer le guide"
          >
            <X size={16} />
          </button>

          <div className="relative px-7 pt-9 pb-6">
            <AnimatePresence mode="wait">
              <motion.div
                key={step.id}
                initial={{ opacity: 0, x: 18 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -18 }}
                transition={{ duration: 0.28 }}
              >
                <div
                  className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl"
                  style={{ background: "linear-gradient(135deg,#F4D77B,#D4AF37)", boxShadow: "0 0 26px rgba(212,175,55,0.4)" }}
                >
                  <Icon size={26} className="text-[#0A1128]" strokeWidth={2} />
                </div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#E8C96A]">{step.kicker}</p>
                <h2 className="mt-1.5 text-2xl font-semibold leading-tight" style={{ fontFamily: "'Fraunces',Georgia,serif" }}>{step.title}</h2>
                <p className="mt-3 text-sm leading-relaxed text-white/75">{step.text}</p>
                {step.highlight && (
                  <p className="mt-4 inline-flex items-center gap-2 rounded-full border border-[#E8C96A]/30 bg-[#E8C96A]/10 px-3.5 py-1.5 text-sm font-medium text-[#E8C96A]">
                    <Sparkles size={14} /> {step.highlight}
                  </p>
                )}
              </motion.div>
            </AnimatePresence>
          </div>

          {/* Footer : progression + navigation */}
          <div className="relative flex items-center justify-between gap-3 border-t border-white/10 px-7 py-4">
            <div className="flex items-center gap-1.5" data-testid="welcome-tour-progress">
              {STEPS.map((s, idx) => (
                <button
                  key={s.id}
                  onClick={() => setI(idx)}
                  aria-label={`Étape ${idx + 1}`}
                  className="h-1.5 rounded-full transition-all duration-300"
                  style={{
                    width: idx === i ? 22 : 7,
                    background: idx === i ? "#E8C96A" : "rgba(255,255,255,0.25)",
                  }}
                />
              ))}
            </div>

            <div className="flex items-center gap-2">
              {i > 0 && (
                <button
                  onClick={prev}
                  data-testid="welcome-tour-prev"
                  className="flex h-9 items-center gap-1 rounded-full border border-white/15 px-3 text-sm text-white/80 hover:bg-white/10 transition-colors"
                >
                  <ArrowLeft size={15} /> Retour
                </button>
              )}
              <button
                onClick={next}
                data-testid="welcome-tour-next"
                className="flex h-9 items-center gap-1.5 rounded-full px-4 text-sm font-semibold text-[#0A1128] transition-transform hover:scale-[1.03]"
                style={{ background: "linear-gradient(135deg,#F4D77B,#D4AF37)", boxShadow: "0 6px 20px rgba(212,175,55,0.35)" }}
              >
                {isLast ? (<><Check size={16} /> {step.cta || "Terminer"}</>) : (<>Suivant <ArrowRight size={15} /></>)}
              </button>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>,
    document.body
  );
}
