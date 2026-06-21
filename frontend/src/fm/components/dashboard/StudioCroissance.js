import React from "react";
import { ArrowRight, TrendingUp, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";

/**
 * StudioCroissance — widget Croissance prominant sur le Dashboard
 * (pendant de StudioSerenite, focus business plutôt que bien-être).
 *
 * Affiche la mission Croissance du jour + CTA vers /croissance.
 */
export default function StudioCroissance({ kpis }) {
  const prospects = kpis?.prospects ?? 0;
  const conversations = kpis?.conversations ?? 0;
  const leads = kpis?.leads ?? 0;

  return (
    <section
      className="mb-5 rounded-3xl p-5 sm:p-6 shadow-md flex flex-col sm:flex-row items-start sm:items-center gap-5"
      style={{ background: "linear-gradient(135deg, #b89855 0%, #d4b982 100%)", color: "#1a1815" }}
      data-testid="studio-croissance"
    >
      <div className="flex items-center gap-4 flex-1 min-w-0">
        <div className="w-12 h-12 rounded-2xl grid place-items-center shrink-0 shadow-md"
             style={{ background: "rgba(26,58,110,0.92)", color: "#f3e9d0" }}>
          <TrendingUp size={22} />
        </div>
        <div className="min-w-0">
          <div className="text-[11px] tracking-[0.22em] uppercase font-bold mb-0.5 opacity-80">
            Studio CROISSANCE · 70 % IA
          </div>
          <h3 className="font-display text-[20px] sm:text-[22px] leading-tight font-bold">
            « Aujourd&apos;hui, on transforme un prospect en client. »
          </h3>
          <p className="text-[13px] opacity-85 leading-snug mt-1">
            {prospects > 0 || conversations > 0 || leads > 0
              ? `${prospects} prospects · ${conversations} convos · ${leads} leads chauds`
              : "L'IA analyse votre marché et prépare 3 actions à fort impact."}
          </p>
        </div>
      </div>
      <Link
        to="/croissance"
        className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full text-[13px] font-semibold transition shadow-md shrink-0"
        style={{ background: "#1a3a6e", color: "#f6f3ee" }}
        data-testid="studio-croissance-cta"
      >
        <Sparkles size={14} /> Ouvrir le studio <ArrowRight size={13} />
      </Link>
    </section>
  );
}
