import React from "react";
import { Link } from "react-router-dom";
import { Lock, Crown, ArrowRight } from "lucide-react";
import usePlan from "@fm/hooks/usePlan";

/**
 * Wrapper qui masque un contenu derrière un plan minimum.
 *
 * Usage :
 *   <PaywallGate feature="croissance_agent">
 *     <MyProBlock />
 *   </PaywallGate>
 */
const PLAN_LABEL = { start: "START · 29 €/mo", grow: "GROW · 79 €/mo", serenity: "SERENITY · 149 €/mo" };

export default function PaywallGate({ feature, children, minLabel, compact = false }) {
  const { has, minRequired } = usePlan();
  if (has(feature)) return children;

  const required = minRequired(feature);
  const label = minLabel || PLAN_LABEL[required] || "Plan supérieur";

  if (compact) {
    return (
      <div
        className="rounded-2xl p-4 flex items-center gap-3 shadow-md"
        style={{ background: "#f6f3ee" }}
        data-testid={`paywall-${feature}`}
      >
        <div className="w-9 h-9 rounded-xl grid place-items-center shrink-0"
             style={{ background: "#f3e9d0", color: "#b89855" }}>
          <Lock size={15} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-[13px] font-semibold" style={{ color: "#1a1815" }}>Réservé au plan {label}</div>
        </div>
        <Link
          to="/settings?section=plan"
          className="px-3 py-1.5 rounded-full text-[12px] font-semibold shadow-sm"
          style={{ background: "#1a3a6e", color: "#f6f3ee" }}
        >
          Upgrader
        </Link>
      </div>
    );
  }

  return (
    <div
      className="rounded-3xl p-8 text-center shadow-md"
      style={{ background: "#f6f3ee" }}
      data-testid={`paywall-${feature}`}
    >
      <div className="w-14 h-14 rounded-2xl grid place-items-center mx-auto mb-4"
           style={{ background: "#f3e9d0", color: "#b89855" }}>
        <Crown size={22} />
      </div>
      <div className="text-[11px] tracking-[0.22em] uppercase font-semibold mb-2" style={{ color: "#1a3a6e" }}>
        Fonctionnalité Premium
      </div>
      <h3 className="text-[24px] font-bold mb-2" style={{ color: "#1a1815", letterSpacing: "-0.02em" }}>
        Disponible avec {label}
      </h3>
      <p className="text-[14px] mb-6 max-w-md mx-auto" style={{ color: "#6b6358" }}>
        Cette zone du cockpit est incluse dans les plans supérieurs. Upgradez en un clic depuis vos paramètres.
      </p>
      <Link
        to="/settings?section=plan"
        className="inline-flex items-center gap-2 px-6 py-3 rounded-full text-[13.5px] font-semibold shadow-md transition"
        style={{ background: "#1a3a6e", color: "#f6f3ee" }}
      >
        Voir les plans <ArrowRight size={14} />
      </Link>
    </div>
  );
}
