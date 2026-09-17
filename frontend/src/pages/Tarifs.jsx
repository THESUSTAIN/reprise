import React, { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import useWpContent from "@/hooks/useWpContent";
import { Check, ArrowRight, Sparkles, Building2, Crown, Loader2 } from "lucide-react";
import api from "@/lib/api";
import { PublicHeader, UnifiedFooter } from "@/pages/LandingHub";

const fmt = (v) => `${v}€`;

// ── 1. Hero: Two entry doors ────────────────────────────────────────────────
function EntryDoors() {
  return (
    <section className="max-w-6xl mx-auto px-6 pt-12 pb-10" data-testid="entry-doors">
      <div className="text-center mb-10">
        <div className="text-[11px] tracking-[0.22em] uppercase font-semibold mb-2" style={{ color: "var(--zayado-navy)" }}>
          Par où démarrer ?
        </div>
        <h2 className="font-display text-3xl sm:text-4xl" style={{ color: "var(--zayado-text)" }}>
          Deux portes d'entrée. Une seule méthode.
        </h2>
      </div>
      <div className="grid md:grid-cols-2 gap-5">
        <Link
          to="/creation-entreprise"
          data-testid="door-creation"
          className="group bg-white rounded-3xl p-7 shadow-md hover:shadow-xl hover:-translate-y-1 transition flex flex-col"
        >
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-2xl grid place-items-center shadow-md"
                 style={{ background: "linear-gradient(135deg, #1F3B73 0%, #2A4D8F 100%)", color: "#F6F3EE", boxShadow: "0 4px 12px rgba(31,59,115,0.25)" }}>
              <Building2 size={22} />
            </div>
            <div>
              <h3 className="font-display text-2xl" style={{ color: "var(--zayado-text)" }}>Je crée mon entreprise</h3>
              <p className="text-[12.5px] opacity-65 mt-0.5" style={{ color: "var(--zayado-text)" }}>SASU · EURL · MICRO · BIC LMNP/LMP</p>
            </div>
          </div>
          <p className="text-[14px] opacity-75 leading-relaxed mb-5 flex-1" style={{ color: "var(--zayado-text)" }}>
            Formalités juridiques accompagnées par notre cabinet partenaire. Statuts, dépôt Guichet Unique, banque pro.
          </p>
          <div className="flex items-center justify-between pt-4 border-t border-[var(--zayado-border)]">
            <div>
              <div className="text-[11px] uppercase tracking-wider opacity-65" style={{ color: "var(--zayado-text)" }}>À partir de</div>
              <div className="font-display text-3xl" style={{ color: "var(--zayado-navy)" }}>1 €</div>
              <div className="text-[12px] opacity-65" style={{ color: "var(--zayado-text)" }}>symbolique · conditionné au plan START</div>
            </div>
            <span className="inline-flex items-center gap-1.5 text-[13px] font-semibold group-hover:gap-2.5 transition-all" style={{ color: "var(--zayado-navy)" }}>
              Démarrer <ArrowRight size={14} />
            </span>
          </div>
        </Link>
        <a
          href={(typeof window !== "undefined" && window.location.origin.includes("preview.emergentagent")
            ? `${window.location.origin}/login`
            : "https://app.zayado.net/login")}
          data-testid="door-existante"
          className="group bg-white rounded-3xl p-7 shadow-md hover:shadow-xl hover:-translate-y-1 transition flex flex-col"
        >
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-2xl grid place-items-center shadow-md"
                 style={{ background: "linear-gradient(135deg, #1F3B73 0%, #2A4D8F 100%)", color: "#F6F3EE", boxShadow: "0 4px 12px rgba(31,59,115,0.25)" }}>
              <Sparkles size={22} />
            </div>
            <div>
              <h3 className="font-display text-2xl" style={{ color: "var(--zayado-text)" }}>J'ai déjà une entreprise</h3>
              <p className="text-[12.5px] opacity-65 mt-0.5" style={{ color: "var(--zayado-text)" }}>Solo, TPE, indé · à piloter sans rester seul</p>
            </div>
          </div>
          <p className="text-[14px] opacity-75 leading-relaxed mb-4 flex-1" style={{ color: "var(--zayado-text)" }}>
            Branchez votre activité au cockpit MyExtension AI. Co-pilote IA, mutualisation, 30 % humain.
          </p>

          {/* Liste — Ce qui est inclus en découverte (0 €) */}
          <div className="mb-5 p-4 rounded-2xl" style={{ background: "rgba(212,185,130,0.08)" }} data-testid="discovery-includes">
            <div className="text-[10.5px] tracking-[0.18em] uppercase font-bold mb-2.5" style={{ color: "var(--zayado-navy)" }}>
              Inclus en découverte gratuite
            </div>
            <ul className="space-y-1.5">
              {[
                "Dashboard cockpit complet",
                "Vision Board (mission, why, who)",
                "10 messages IA Claude / mois",
                "Module Bien-être & rituels",
              ].map((f, i) => (
                <li key={i} className="flex items-center gap-2 text-[12.5px]" style={{ color: "var(--zayado-text)" }}>
                  <span className="w-4 h-4 shrink-0 rounded-full grid place-items-center"
                        style={{ background: "#f3e9d0", color: "#b89855" }}>
                    <Check size={9} strokeWidth={3} />
                  </span>
                  <span>{f}</span>
                </li>
              ))}
            </ul>
            <p className="text-[11px] mt-2.5 italic opacity-70" style={{ color: "var(--zayado-text)" }}>
              Pour débloquer Pilotage, Croissance et l'IA illimitée : passez à START (29 €/mo, 1er mois à 1 €).
            </p>
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-[var(--zayado-border)]">
            <div>
              <div className="text-[11px] uppercase tracking-wider opacity-65" style={{ color: "var(--zayado-text)" }}>Activation</div>
              <div className="font-display text-3xl" style={{ color: "var(--zayado-navy)" }}>0 €</div>
              <div className="text-[12px] opacity-65" style={{ color: "var(--zayado-text)" }}>essai sans CB · puis abonnement mensuel</div>
            </div>
            <span className="inline-flex items-center gap-1.5 text-[13px] font-semibold group-hover:gap-2.5 transition-all" style={{ color: "var(--zayado-navy)" }}>
              Activer <ArrowRight size={14} />
            </span>
          </div>
        </a>
      </div>
    </section>
  );
}

// ── 2. Plan card (style simple / blanc / CTA en haut · inspiré maquette) ────
function PlanCard({ plan, billing, onCheckout, loading }) {
  const price = billing === "yearly"
    ? Math.round(plan.price * (1 - (plan.annual_discount_pct || 0) / 100))
    : plan.price;
  const welcome = plan.first_month_price ?? plan.price;
  const showWelcome = billing === "monthly" && welcome !== null && welcome !== plan.price;
  const isHighlight = plan.highlight === true;

  return (
    <div
      data-testid={`plan-${plan.id}`}
      className="relative rounded-3xl p-8 flex flex-col bg-white transition shadow-md hover:shadow-xl hover:-translate-y-1"
      style={{
        outline: isHighlight ? "2px solid var(--zayado-navy)" : "none",
        border: "none",
      }}
    >
      {/* Header: Plan name + popular badge */}
      <div className="flex items-center gap-2 mb-5">
        <h3 className="font-display text-3xl leading-none" style={{ color: "var(--zayado-text)" }}>
          {plan.name}
        </h3>
        {isHighlight && (
          <span
            className="text-[11px] font-medium px-3 py-1 rounded-full"
            style={{ background: "var(--zayado-navy)", color: "#F6F3EE" }}
          >
            Les plus populaires
          </span>
        )}
      </div>

      {/* Price */}
      <div className="mb-6">
        <div className="flex items-baseline gap-1">
          <span className="font-display text-6xl leading-none" style={{ color: "var(--zayado-text)" }}>
            {price}
          </span>
          <span className="font-display text-3xl" style={{ color: "var(--zayado-text)" }}>€</span>
          <span className="text-[15px] ml-1" style={{ color: "#6B7280" }}>/ mois</span>
        </div>
        {billing === "yearly" && (
          <div className="text-[12px] mt-2" style={{ color: "#6B7280" }}>
            Facturé annuellement · économisez {plan.annual_discount_pct || 20} %
          </div>
        )}
        {showWelcome && (
          <div className="text-[12.5px] mt-2 italic" style={{ color: "#6B7280" }}>
            1er mois : {welcome === 0 ? "gratuit" : `${welcome} €`}
          </div>
        )}
      </div>

      {/* CTA — en haut comme dans la maquette */}
      <button
        onClick={() => onCheckout(plan, billing)}
        disabled={loading === plan.id}
        data-testid={`cta-plan-${plan.id}`}
        className="w-full px-4 py-3.5 rounded-xl text-[14px] font-medium inline-flex items-center justify-center gap-2 transition disabled:opacity-60 mb-7 shadow-sm hover:shadow-md"
        style={
          isHighlight
            ? { background: "var(--zayado-navy)", color: "#F6F3EE" }
            : { background: "white", color: "var(--zayado-navy)", border: "none", outline: "1.5px solid var(--zayado-border)" }
        }
      >
        {loading === plan.id ? <Loader2 size={14} className="animate-spin" /> : null}
        Essai gratuit
      </button>

      {/* Features list with line separator */}
      <div className="border-t border-[var(--zayado-border)] pt-6">
        <ul className="space-y-4">
          {(plan.features_list || []).map((f, i) => (
            <li key={i} className="flex items-start gap-3 text-[14px] leading-relaxed" style={{ color: "#374151" }}>
              <span
                className="w-5 h-5 shrink-0 rounded-md grid place-items-center mt-0.5"
                style={{ background: "#f3e9d0", color: "#b89855" }}
              >
                <Check size={11} strokeWidth={2.5} />
              </span>
              <span>{f}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

// ── 3. Billing toggle (Monthly / Yearly) ───────────────────────────────────
function BillingToggle({ billing, setBilling }) {
  return (
    <div className="inline-flex items-center gap-1 p-1 rounded-full border border-[var(--zayado-border)] bg-white" data-testid="billing-toggle">
      <button
        onClick={() => setBilling("monthly")}
        data-testid="billing-monthly"
        className="px-5 h-9 rounded-full text-[13px] font-medium transition"
        style={billing === "monthly" ? { background: "var(--zayado-navy)", color: "#F6F3EE" } : { color: "var(--zayado-text)" }}
      >
        Mensuel
      </button>
      <button
        onClick={() => setBilling("yearly")}
        data-testid="billing-yearly"
        className="px-5 h-9 rounded-full text-[13px] font-medium transition inline-flex items-center gap-1.5"
        style={billing === "yearly" ? { background: "var(--zayado-navy)", color: "#F6F3EE" } : { color: "var(--zayado-text)" }}
      >
        Annuel
        <span className="text-[10px] px-1.5 py-0.5 rounded-full font-bold"
              style={{ background: billing === "yearly" ? "#C9A66B" : "var(--zayado-cream)", color: billing === "yearly" ? "#1F3B73" : "var(--zayado-navy)" }}>
          -20 %
        </span>
      </button>
    </div>
  );
}

// ── 4. Add-ons strip ────────────────────────────────────────────────────────
function AddOnsStrip() {
  const addons = [
    { name: "Mutuelle & Prévoyance", price: "Sur devis", desc: "Santé + prévoyance dirigeant mutualisée" },
    { name: "RC Pro", price: "Sur devis", desc: "Responsabilité civile négociée" },
    { name: "Adresse de Prestige Paris", price: "29 €/mo", desc: "10 Rue de la Paix · Paris 2e + courrier" },
    { name: "DAF à la carte", price: "190 €/mo", desc: "Reporting mensuel + prévisionnel" },
    { name: "Supervision compta", price: "120 €/mo", desc: "Bilan annuel inclus" },
    { name: "Crédits IA additionnels", price: "Dès 4.99 €", desc: "Packs 1 000 / 5 000 / 10 000" },
  ];
  return (
    <section className="max-w-6xl mx-auto px-6 py-14" data-testid="addons">
      <div className="text-center mb-8">
        <div className="text-[11px] tracking-[0.22em] uppercase font-semibold mb-2" style={{ color: "var(--zayado-navy)" }}>
          À la carte
        </div>
        <h2 className="font-display text-3xl" style={{ color: "var(--zayado-text)" }}>
          Add-ons mutualisés
        </h2>
      </div>
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {addons.map((a, i) => (
          <div key={i} className="bg-white rounded-2xl p-5 shadow-md hover:shadow-lg transition flex items-start gap-3" data-testid={`addon-${i}`}>
            <div className="w-9 h-9 shrink-0 rounded-lg grid place-items-center"
                 style={{ background: "#f3e9d0", color: "#b89855" }}>
              <div className="w-2.5 h-2.5 rounded-sm" style={{ background: "#b89855" }} />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-baseline justify-between gap-2 mb-1">
                <h3 className="font-semibold text-[14px] leading-tight" style={{ color: "var(--zayado-text)" }}>{a.name}</h3>
                <span className="font-display text-[14px] shrink-0" style={{ color: "var(--zayado-navy)" }}>{a.price}</span>
              </div>
              <p className="text-[12.5px] opacity-70 leading-snug" style={{ color: "var(--zayado-text)" }}>{a.desc}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

// ── 5. Comparateur (#comparateur anchor) ───────────────────────────────────
function Comparateur({ plans }) {
  // Order: start, grow, serenity
  const cmp = ["start", "grow", "serenity"].map((id) => plans.find((p) => p.id === id)).filter(Boolean);
  if (cmp.length === 0) return null;
  const rows = [
    { label: "Prix mensuel",                  get: (p) => `${p.price} €/mo` },
    { label: "1er mois (welcome)",            get: (p) => p.first_month_price === p.price ? "—" : `${p.first_month_price} €` },
    { label: "Annuel −20 %",                  get: (p) => p.annual_discount_pct ? `${Math.round(p.price*0.8)} €/mo` : "—" },
    { label: "Crédits IA /mois",              get: (p) => `${(p.credits_per_month || 0).toLocaleString("fr-FR")}` },
    { label: "Bilan création offert",         get: (p) => p.features?.bilan_creation_offert ? "✓" : "—" },
    { label: "Création 1€ éligible",          get: (p) => p.features?.creation_eligible ? "✓" : "—" },
    { label: "Expansion Agent (leads)",       get: (p) => p.features?.expansion_agent ? "✓" : "—" },
    { label: "Coach humain (min/mois)",       get: (p) => p.features?.humain_quota_min ? `${p.features.humain_quota_min} min` : "—" },
    { label: "Mutuelle + RC Pro inclus",      get: (p) => p.features?.mutualisation_premium ? "✓" : "—" },
    { label: "Adresse de Prestige Paris",    get: (p) => p.features?.domiciliation_paris ? "✓" : "—" },
    { label: "Supervision DAF/compta",        get: (p) => p.features?.daf_supervision ? "✓" : "—" },
    { label: "Sièges (utilisateurs)",         get: (p) => `${p.seats || 1}` },
    { label: "Support SLA",                   get: (p) => p.features?.sla_hours ? `< ${p.features.sla_hours}h` : "Communautaire" },
  ];
  return (
    <section id="comparateur" className="max-w-6xl mx-auto px-6 py-16" data-testid="comparateur">
      <div className="text-center mb-8">
        <div className="text-[11px] tracking-[0.22em] uppercase font-semibold mb-2" style={{ color: "var(--zayado-navy)" }}>
          Comparateur de plans
        </div>
        <h2 className="font-display text-3xl sm:text-4xl" style={{ color: "var(--zayado-text)" }}>
          Tous les détails, en un coup d'œil.
        </h2>
      </div>
      <div className="overflow-x-auto bg-white rounded-3xl shadow-md">
        <table className="w-full text-[13.5px]" data-testid="comparateur-table">
          <thead>
            <tr className="border-b border-[var(--zayado-border)]">
              <th className="text-left p-4 text-[11px] uppercase tracking-[0.18em] font-bold opacity-65" style={{ color: "var(--zayado-text)" }}>Caractéristiques</th>
              {cmp.map((p) => (
                <th key={p.id} className="text-center p-4">
                  <div className="font-display text-xl" style={{ color: "var(--zayado-navy)" }}>{p.name}</div>
                  <div className="text-[12px] opacity-65 mt-0.5" style={{ color: "var(--zayado-text)" }}>{p.price} €/mo</div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i} className="border-b border-[var(--zayado-border)] last:border-b-0 hover:bg-[var(--zayado-cream)]/40">
                <td className="p-4 font-medium" style={{ color: "var(--zayado-text)" }}>{r.label}</td>
                {cmp.map((p) => (
                  <td key={p.id} className="p-4 text-center font-medium" style={{ color: r.get(p) === "✓" ? "var(--zayado-navy)" : "var(--zayado-text)" }}>
                    {r.get(p)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

// ── 6. FAQ short ────────────────────────────────────────────────────────────
function FAQ() {
  const items = [
    { q: "Puis-je changer de plan à tout moment ?", a: "Oui. Vous pouvez upgrader instantanément (les jours déjà payés sont prorata-tés) ou downgrader au prochain renouvellement, sans frais." },
    { q: "Que comprend exactement le 30 % Humain de SERENITY ?", a: "2 h de coach humain par mois (focus business, mental, équilibre), mutualisation premium (mutuelle + RC Pro), Adresse de Prestige (10 Rue de la Paix · Paris 2e), supervision DAF/compta." },
    { q: "Pourquoi START est à 29 € et pas moins ?", a: "Parce que dès le 1er mois vous accédez aux IA pro, à l'image IA, au cockpit complet et à un bilan création offert. Le 1er mois est à 1 € pour vous laisser tester sans risque." },
    { q: "L'annuel −20 %, c'est ferme ?", a: "Oui, sur START et GROW : l'engagement annuel donne 20 % de remise immédiate. SERENITY ne profite pas de remise — l'humain ne se brade pas." },
    { q: "Et la création d'entreprise à 1 € ?", a: "Conditionnée à l'activation d'un plan START (ou +). Vous payez 1 € symbolique pour le suivi formalités, et vos statuts sont rédigés par notre cabinet partenaire." },
  ];
  return (
    <section className="max-w-4xl mx-auto px-6 py-14" data-testid="faq-tarifs">
      <div className="text-center mb-8">
        <div className="text-[11px] tracking-[0.22em] uppercase font-semibold mb-2" style={{ color: "var(--zayado-navy)" }}>
          Questions fréquentes
        </div>
        <h2 className="font-display text-3xl" style={{ color: "var(--zayado-text)" }}>Tout ce qu'on vous a déjà demandé.</h2>
      </div>
      <div className="space-y-3">
        {items.map((it, i) => (
          <details key={i} className="bg-white rounded-2xl shadow-md hover:shadow-lg transition p-5 group" data-testid={`faq-${i}`}>
            <summary className="font-semibold text-[15px] cursor-pointer list-none flex items-center justify-between" style={{ color: "var(--zayado-text)" }}>
              {it.q}
              <span className="text-[var(--zayado-navy)] text-xl group-open:rotate-45 transition-transform">+</span>
            </summary>
            <p className="mt-3 text-[14px] leading-relaxed opacity-80" style={{ color: "var(--zayado-text)" }}>{it.a}</p>
          </details>
        ))}
      </div>
    </section>
  );
}

// ── Main page ───────────────────────────────────────────────────────────────
export default function Tarifs() {
  const [allPlans, setAllPlans] = useState([]);
  const [billing, setBilling] = useState("monthly");
  const [loading, setLoading] = useState(null);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    api.get("/payments/plans")
      .then(({ data }) => setAllPlans(data || []))
      .catch((e) => setError(e?.response?.data?.detail || "Plans indisponibles"));
  }, []);

  // Keep only NEW strategy plans, hide legacy
  const plans = useMemo(
    () => allPlans.filter((p) => !p.legacy && ["start", "grow", "serenity"].includes(p.id)),
    [allPlans]
  );

  const onCheckout = async (plan, bill) => {
    setLoading(plan.id);
    try {
      const { data } = await api.post("/payments/subscribe", {
        plan_id: plan.id,
        billing: bill === "yearly" ? "yearly" : "monthly",
      });
      if (data?.checkout_url) {
        window.location.href = data.checkout_url;
      } else {
        navigate("/login");
      }
    } catch (e) {
      const status = e?.response?.status;
      if (status === 401) {
        navigate("/login?next=/tarifs");
      } else {
        setError(e?.response?.data?.detail || "Erreur lors du checkout");
      }
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="min-h-screen flex flex-col" style={{ background: "var(--zayado-cream)" }}>
      <TarifsHelmet />

      <PublicHeader />

      <main className="flex-1" data-testid="page-tarifs">
        {/* Hero — simple, signal-desk style */}
        <section className="max-w-6xl mx-auto px-6 pt-16 sm:pt-24 pb-8 text-center">
          <h1 className="font-display text-5xl sm:text-6xl lg:text-7xl leading-[1.05] mb-4" style={{ color: "var(--zayado-text)" }}>
            Simple. <em className="italic" style={{ color: "var(--zayado-navy)" }}>Sans surprise.</em>
          </h1>
          <p className="text-lg sm:text-xl mb-8" style={{ color: "#6B7280" }}>
            1er mois symbolique. Annulation possible à tout moment.
          </p>
          <BillingToggle billing={billing} setBilling={setBilling} />
        </section>

        {/* Entry doors */}
        <EntryDoors />

        {/* Plans */}
        <section className="max-w-6xl mx-auto px-6 pb-10" data-testid="plans-grid">
          {error && (
            <div className="text-center text-[13px] mb-4 px-3 py-2 rounded-lg inline-block" style={{ background: "#FEE2E2", color: "#991B1B" }} data-testid="plans-error">
              {error}
            </div>
          )}
          {plans.length === 0 && !error ? (
            <div className="text-center py-16"><Loader2 className="animate-spin mx-auto" /></div>
          ) : (
            <div className="grid md:grid-cols-3 gap-6">
              {plans.map((p) => (
                <PlanCard key={p.id} plan={p} billing={billing} onCheckout={onCheckout} loading={loading} />
              ))}
            </div>
          )}
        </section>

        {/* Bandeau offre Pro — Instance Dédiée */}
        <section className="max-w-6xl mx-auto px-6 pb-4" data-testid="tarifs-instance-dediee-banner">
          <a href="/instance-dediee"
             className="group flex flex-col sm:flex-row items-start sm:items-center justify-between gap-5 rounded-3xl p-7 border-2 transition"
             style={{ borderColor: "rgba(26,58,110,0.18)", background: "linear-gradient(135deg, rgba(184,152,85,0.08), rgba(26,58,110,0.06))" }}>
            <div>
              <div className="inline-flex items-center gap-2 text-[11px] uppercase tracking-wider font-semibold mb-2" style={{ color: "#b89855" }}>
                ★ Offre Pro · Souveraineté
              </div>
              <h3 className="font-display text-2xl mb-1" style={{ color: "var(--zayado-text)" }}>
                Besoin d'une instance rien qu'à vous ?
              </h3>
              <p className="text-sm" style={{ color: "#6b6358" }}>
                Données isolées, hébergées en Europe, managées par nous. Dès 89 €/mois + mise en service.
              </p>
            </div>
            <span className="inline-flex items-center gap-2 px-6 py-3 rounded-full text-white text-sm font-medium shrink-0 group-hover:opacity-90 transition"
                  style={{ background: "var(--zayado-navy)" }}>
              Découvrir l'Instance Dédiée →
            </span>
          </a>
        </section>


        {/* Add-ons */}
        <AddOnsStrip />

        {/* Comparateur */}
        <Comparateur plans={plans} />

        {/* FAQ */}
        <FAQ />

        {/* Final CTA */}
        <section className="max-w-4xl mx-auto px-6 pb-20 text-center">
          <div className="bg-[var(--zayado-navy)] rounded-3xl p-10 sm:p-14" style={{ color: "#F6F3EE" }}>
            <h2 className="font-display text-3xl sm:text-4xl mb-4">
              Pas encore décidé ?
            </h2>
            <p className="text-base sm:text-lg opacity-85 mb-7 max-w-xl mx-auto">
              Testez START pour 1 € pendant 30 jours. Sans engagement, sans CB requise au démarrage.
            </p>
            <Link to="/creation-entreprise"
              className="inline-flex items-center gap-2 px-8 py-3.5 rounded-full font-semibold transition shadow-lg"
              style={{ background: "#C9A66B", color: "var(--zayado-navy)" }}
              data-testid="tarifs-bottom-cta">
              Démarrer pour 1 € <ArrowRight size={15} />
            </Link>
          </div>
        </section>
      </main>

      <UnifiedFooter />
    </div>
  );
}

/**
 * Helmet meta — synchronisé avec WordPress via /wp/page/tarifs.
 * Fallback hardcodé si WP n'a pas de meta Yoast pour cette page.
 */
function TarifsHelmet() {
  const wp = useWpContent("tarifs", {
    title: "Tarifs MyExtension AI — START · GROW · SERENITY | Zayado",
    subtitle: "3 plans pour entreprendre sereinement : START 29€, GROW 79€, SERENITY 149€. Création d'entreprise à 1€. Engagement annuel −20%.",
  });
  return (
    <Helmet>
      <title>{wp.seo.title}</title>
      <meta name="description" content={wp.seo.description} />
      {wp.seo.og_image && <meta property="og:image" content={wp.seo.og_image} />}
      <link rel="canonical" href={wp.seo.canonical || "https://zayado.net/tarifs"} />
    </Helmet>
  );
}
