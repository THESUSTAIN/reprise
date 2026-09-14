import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { PartyPopper, Share2, X } from "lucide-react";
import { toast } from "sonner";

const MILESTONES = [50, 75, 100];
const STORAGE_KEY = "zayado_alignment_milestones_seen";

function seenMilestones() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]"); } catch { return []; }
}

// Détecte le franchissement d'un palier (50/75/100%) et affiche une célébration
// une seule fois par palier (mémorisé en localStorage).
export default function AlignmentCelebration({ score }) {
  const [milestone, setMilestone] = useState(null);

  useEffect(() => {
    if (score == null) return;
    const seen = seenMilestones();
    const hit = MILESTONES.filter((m) => score >= m).find((m) => !seen.includes(m));
    if (hit) {
      setMilestone(hit);
      localStorage.setItem(STORAGE_KEY, JSON.stringify([...seen, hit]));
    }
  }, [score]);

  if (!milestone) return null;

  const shareBadge = async () => {
    const text = `Je viens d'atteindre ${milestone}% d'alignement sur mon projet avec Zayado 🎉`;
    if (navigator.share) {
      try { await navigator.share({ text }); return; } catch { /* fallback */ }
    }
    try { await navigator.clipboard.writeText(text); toast.success("Message copié — colle-le où tu veux le partager !"); }
    catch { toast.info(text); }
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, scale: 0.9, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.9 }}
        style={{
          position: "fixed", bottom: 24, left: "50%", transform: "translateX(-50%)",
          zIndex: 300, maxWidth: 340, width: "calc(100% - 32px)",
        }}
        data-testid="alignment-celebration">
        <div className="glass-card" style={{
          background: "linear-gradient(135deg, rgba(222, 194, 163,0.25), rgba(30,60,130,0.35))",
          border: "1px solid rgba(222, 194, 163,0.5)", textAlign: "center", position: "relative",
        }}>
          <button onClick={() => setMilestone(null)} data-testid="alignment-celebration-close"
            style={{ position: "absolute", top: 10, right: 10, background: "none", border: "none", color: "rgba(255,255,255,0.6)", cursor: "pointer" }}>
            <X size={16} />
          </button>
          <PartyPopper size={28} style={{ color: "#F1E2CC", marginBottom: 8 }} />
          <p style={{ fontSize: 15, fontWeight: 600, color: "var(--txt)", margin: "0 0 4px" }}>
            {milestone}% d'alignement atteint !
          </p>
          <p className="muted" style={{ fontSize: 12.5, margin: "0 0 14px" }}>
            {milestone === 100 ? "Ton projet est parfaitement aligné avec ta vision." : "Continue, tu es sur la bonne trajectoire."}
          </p>
          <button onClick={shareBadge} className="zbtn zbtn-primary" style={{ height: 36, padding: "0 14px", gap: 6, fontSize: 12.5, margin: "0 auto" }} data-testid="alignment-celebration-share">
            <Share2 size={14} /> Partager mon badge
          </button>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
