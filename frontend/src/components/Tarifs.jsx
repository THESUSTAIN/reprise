import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { Check, Sparkles, ArrowRight, ExternalLink, Loader2, Crown, Building2, GraduationCap, Wrench } from "lucide-react";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { useWPPage, parseWPContent, getSection } from "@/lib/wpContent";

const ICONS = {
  free: Sparkles,
  pro: Crown,
  business: Building2,
  enterprise: Building2,
  service_setup_growth_agent: Wrench,
  service_formation: GraduationCap,
  service_maintenance_growth_agent: Wrench,
  service_creation_entreprise: Building2,
};

function PlanCard({ plan, billing, onCheckout, onContact, loading }) {
  const Icon = ICONS[plan.id] || Sparkles;
  const isFree = plan.id === "free";
  const isLead = plan.type === "enterprise_lead";
  // Services use a single `price` field, subscriptions use `price_monthly` / `price_yearly`.
  const isService = plan.type === "service" || plan.type === "maintenance" || plan.type === "service_recurring";
  const subPrice = billing === "yearly" ? plan.price_yearly : plan.price_monthly;
  const price = isService ? plan.price : subPrice;
  const hasPrice = price !== null && price !== undefined;
  // Display suffix: services without `_recurring` are one-shot (no /mois)
  const isRecurring = plan.billing === "recurring" || plan.type === "maintenance" || plan.type === "service_recurring";

  return (
    <div
      className={`relative rounded-2xl p-7 transition flex flex-col ${
        plan.highlight
          ? "bg-[var(--zayado-navy)] text-white shadow-lg scale-[1.02]"
          : "bg-white/70 border border-[var(--zayado-border)]"
      }`}
      data-testid={`plan-card-${plan.id}`}
    >
      {plan.popular && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 text-[10px] uppercase tracking-wider rounded-full bg-[var(--zayado-gold)] text-white font-semibold" data-testid={`popular-${plan.id}`}>
          Populaire
        </div>
      )}
      <div className="flex items-center gap-2 mb-3">
        <Icon size={18} className={plan.highlight ? "text-[var(--zayado-gold-soft)]" : "text-[var(--zayado-gold)]"} />
        <h3 className="font-display text-2xl italic">{plan.name}</h3>
      </div>
      <div className="mb-4">
        {isLead || !hasPrice ? (
          <div className="text-lg font-medium">Sur devis</div>
        ) : (
          <>
            <div className="text-4xl font-display">
              {price === 0 ? "0€" : `${price}€`}
              {isRecurring && price > 0 && (
                <span className="text-sm opacity-70">/{billing === "yearly" ? "an" : "mois"}</span>
              )}
            </div>
          </>
        )}
        <div className="text-xs opacity-70 mt-1">{plan.tagline}</div>
      </div>
      <ul className="space-y-2 mb-6 flex-1">
        {plan.features.map((f, i) => (
          <li key={i} className="flex items-start gap-2 text-sm">
            <Check size={14} className={`mt-0.5 shrink-0 ${plan.highlight ? "text-[var(--zayado-gold-soft)]" : "text-[var(--zayado-gold)]"}`} />
            <span>{f}</span>
          </li>
        ))}
      </ul>
      <button
        onClick={() => (isLead ? onContact(plan) : onCheckout(plan))}
        disabled={loading === plan.id}
        className={`w-full px-4 py-3 rounded-lg text-sm font-medium inline-flex items-center justify-center gap-2 transition disabled:opacity-50 ${
          plan.highlight
            ? "bg-[var(--zayado-gold)] text-white hover:bg-[var(--zayado-gold-dark)]"
            : isFree
            ? "bg-[var(--zayado-cream)] text-[var(--zayado-navy)] hover:bg-[var(--zayado-cream-dark)]"
            : "bg-[var(--zayado-navy)] text-white hover:opacity-90"
        }`}
        data-testid={`cta-${plan.id}`}
      >
        {loading === plan.id ? <Loader2 size={14} className="animate-spin" /> : null}
        {plan.cta}
        {!loading && !isFree && <ArrowRight size={14} />}
      </button>
    </div>
  );
}

export default function Tarifs() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [billing, setBilling] = useState("monthly");
  const [loading, setLoading] = useState(null);
  const [leadModal, setLeadModal] = useState(null);
  const [leadForm, setLeadForm] = useState({ name: "", email: "", company: "", message: "" });
  const [leadSent, setLeadSent] = useState(false);
  const { page: wpPage } = useWPPage("tarifs");
  const wp = wpPage ? parseWPContent(wpPage.content?.rendered || "") : null;
  const hero = getSection(wp, "default", {});
  const heroTitle = (wp?.title || hero.heading) || "Tarifs transparents et sans surprise";
  const heroSubtitle = (wp?.subtitle || hero.subtitle) || "Paiement Mollie · CB · SEPA · PayPal · API Claude incluse · Sans engagement";
  const servicesSec = getSection(wp, "prestations-complementaires", {});
  const servicesHeading = servicesSec.heading || "Prestations complémentaires";
  const servicesSubtitle = servicesSec.subtitle || "Setup, formation, accompagnement — réservez en un clic.";

  useEffect(() => {
    api.get("/payments/plans").then((r) => setData(r.data)).catch(() => setData({ plans: [], services: [] }));
  }, []);

  const checkout = async (plan) => {
    if (plan.id === "free") {
      // Free plan — just activate locally (no payment)
      navigate("/app");
      return;
    }
    if (!user) {
      window.location.href = "https://app.zayado.net/login?next=/app/tarifs";
      return;
    }
    setLoading(plan.id);
    try {
      const r = await api.post("/payments/checkout", {
        product_id: plan.id,
        billing,
        return_url: `${window.location.origin}/app/tarifs?payment=success`,
      });
      if (r.data?.checkout_url) {
        window.location.href = r.data.checkout_url;
      }
    } catch (e) {
      alert("Erreur paiement : " + (e?.response?.data?.detail || e.message));
    } finally {
      setLoading(null);
    }
  };

  const openLead = (plan) => {
    setLeadModal(plan);
    setLeadForm({ name: user?.name || "", email: user?.email || "", company: "", message: "" });
    setLeadSent(false);
  };

  const submitLead = async (e) => {
    e.preventDefault();
    setLoading(leadModal.id);
    try {
      await api.post("/payments/enterprise-lead", {
        product_id: leadModal.id,
        ...leadForm,
      });
      setLeadSent(true);
    } catch (err) {
      alert("Erreur : " + (err?.response?.data?.detail || err.message));
    } finally {
      setLoading(null);
    }
  };

  if (!data) {
    return <div className="p-8 text-center text-sm text-[var(--zayado-muted)]"><Loader2 size={16} className="inline animate-spin mr-2" />Chargement des tarifs…</div>;
  }

  return (
    <div className="space-y-10" data-testid="tarifs-page">
      <Helmet>
        <title>Tarifs Zayado — SaaS entrepreneur dès 0€ · Sans engagement</title>
        <meta name="description" content="Découvrez les tarifs transparents de Zayado : plan gratuit, Pro et Business pour entrepreneurs et solopreneurs. IA copilote, Expansion Agent, pilotage financier. Sans engagement." />
        <meta name="keywords" content="tarifs zayado, prix saas entrepreneur, abonnement solopreneur, logiciel entrepreneur, outil gestion indépendant, IA pour entrepreneur" />
        <link rel="canonical" href="https://app.zayado.net/tarifs" />
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://app.zayado.net/tarifs" />
        <meta property="og:title" content="Tarifs Zayado — SaaS entrepreneur dès 0€ · Sans engagement" />
        <meta property="og:description" content="Plan gratuit, Pro et Business pour solopreneurs. IA copilote, Expansion Agent, pilotage financier. Sans engagement." />
        <meta property="og:locale" content="fr_FR" />
        <meta name="twitter:card" content="summary_large_image" />
        <script type="application/ld+json">{JSON.stringify({
          "@context": "https://schema.org",
          "@type": "Product",
          "name": "Zayado — SaaS pour entrepreneurs",
          "url": "https://app.zayado.net/tarifs",
          "description": "Plateforme IA tout-en-un pour solopreneurs : copilote IA, Expansion Agent, pilotage financier.",
          "brand": { "@type": "Brand", "name": "Zayado" },
          "offers": [
            { "@type": "Offer", "name": "Gratuit", "price": "0", "priceCurrency": "EUR" },
            { "@type": "Offer", "name": "Pro", "price": "29", "priceCurrency": "EUR" },
            { "@type": "Offer", "name": "Business", "price": "79", "priceCurrency": "EUR" },
          ],
        })}</script>
      </Helmet>
      {/* Header */}
      <header className="text-center max-w-3xl mx-auto pt-2">
        <div className="chip mb-3 inline-flex"><Sparkles size={14} /> Tarifs Zayado</div>
        <h1 className="font-display text-4xl md:text-5xl italic mb-4" data-testid="tarifs-title" dangerouslySetInnerHTML={{ __html: heroTitle }} />
        <p className="text-[var(--zayado-muted)]" data-testid="tarifs-subtitle" dangerouslySetInnerHTML={{ __html: heroSubtitle }} />
        {data.mode === "test" && (
          <div className="mt-4 inline-block px-3 py-1.5 rounded-full bg-amber-100 text-amber-800 text-xs font-medium" data-testid="mode-badge-test">
            Mode test Mollie — aucun paiement réel
          </div>
        )}
        {data.mode === "disabled" && (
          <div className="mt-4 inline-block px-3 py-1.5 rounded-full bg-red-100 text-red-800 text-xs font-medium" data-testid="mode-badge-disabled">
            Paiements désactivés — contactez-nous
          </div>
        )}
        {user?.plan && user.plan !== "free" && (
          <div className="mt-3 inline-block px-3 py-1.5 rounded-full bg-[var(--zayado-gold)]/15 text-[var(--zayado-gold-dark)] text-xs font-medium" data-testid="current-plan-badge">
            Plan actuel : <strong className="uppercase">{user.plan}</strong>
            {user.plan_expires_at && (
              <> — jusqu'au {new Date(user.plan_expires_at).toLocaleDateString("fr-FR")}</>
            )}
            {user.has_subscription && (
              <button
                onClick={async () => {
                  if (!window.confirm("Résilier votre abonnement ? Vous gardez l'accès jusqu'à la date d'expiration.")) return;
                  try {
                    const r = await api.post("/payments/subscription/cancel");
                    alert(r.data?.message || "Abonnement résilié.");
                    window.location.reload();
                  } catch (e) {
                    alert("Erreur : " + (e?.response?.data?.detail || e.message));
                  }
                }}
                className="ml-3 text-[10px] underline underline-offset-2 hover:opacity-80"
                data-testid="cancel-subscription-btn"
              >
                Résilier
              </button>
            )}
          </div>
        )}
      </header>

      {/* Billing toggle */}
      <div className="flex items-center justify-center gap-3" data-testid="billing-toggle">
        <button
          onClick={() => setBilling("monthly")}
          className={`px-4 py-1.5 rounded-full text-sm transition ${billing === "monthly" ? "bg-[var(--zayado-navy)] text-white" : "bg-[var(--zayado-cream)] text-[var(--zayado-navy)]"}`}
          data-testid="billing-monthly"
        >
          Mensuel
        </button>
        <button
          onClick={() => setBilling("yearly")}
          className={`px-4 py-1.5 rounded-full text-sm transition relative ${billing === "yearly" ? "bg-[var(--zayado-navy)] text-white" : "bg-[var(--zayado-cream)] text-[var(--zayado-navy)]"}`}
          data-testid="billing-yearly"
        >
          Annuel
          <span className="absolute -top-2 -right-3 text-[9px] bg-[var(--zayado-gold)] text-white px-1.5 py-0.5 rounded-full font-semibold">-17%</span>
        </button>
      </div>

      {/* Plans */}
      <section className="grid md:grid-cols-2 lg:grid-cols-4 gap-5" data-testid="plans-grid">
        {data.plans.map((plan) => (
          <PlanCard key={plan.id} plan={plan} billing={billing} onCheckout={checkout} onContact={openLead} loading={loading} />
        ))}
      </section>

      {/* External tarifs link */}
      {data.external_tarifs_url && (
        <div className="text-center">
          <a
            href={data.external_tarifs_url}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 text-sm text-[var(--zayado-navy)] underline underline-offset-4 hover:opacity-80"
            data-testid="external-tarifs-link"
          >
            Voir la page tarifs publique <ExternalLink size={14} />
          </a>
        </div>
      )}

      {/* Services */}
      <section className="pt-4" data-testid="services-section">
        <header className="text-center mb-6">
          <h2 className="font-display text-3xl italic mb-2" dangerouslySetInnerHTML={{ __html: servicesHeading }} />
          <p className="text-sm text-[var(--zayado-muted)]" dangerouslySetInnerHTML={{ __html: servicesSubtitle }} />
        </header>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-5">
          {data.services.map((s) => (
            <PlanCard key={s.id} plan={s} billing={billing} onCheckout={checkout} onContact={openLead} loading={loading} />
          ))}
        </div>
      </section>

      {/* Lead modal */}
      {leadModal && (
        <div
          className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4"
          onClick={() => !loading && setLeadModal(null)}
          data-testid="lead-modal"
        >
          <div
            className="bg-[var(--zayado-cream)] rounded-2xl p-7 max-w-md w-full"
            onClick={(e) => e.stopPropagation()}
          >
            {leadSent ? (
              <div className="text-center" data-testid="lead-sent">
                <div className="w-12 h-12 rounded-full bg-[var(--zayado-gold)]/20 text-[var(--zayado-gold)] flex items-center justify-center mx-auto mb-3">
                  <Check size={24} />
                </div>
                <h3 className="font-display text-2xl italic mb-2">Merci !</h3>
                <p className="text-sm text-[var(--zayado-muted)] mb-5">
                  Nous revenons vers vous sous 24h ouvrées pour discuter de <strong>{leadModal.name}</strong>.
                </p>
                <button
                  onClick={() => setLeadModal(null)}
                  className="px-4 py-2 rounded-lg bg-[var(--zayado-navy)] text-white text-sm"
                  data-testid="lead-close"
                >
                  Fermer
                </button>
              </div>
            ) : (
              <form onSubmit={submitLead} className="space-y-3" data-testid="lead-form">
                <h3 className="font-display text-2xl italic mb-1">{leadModal.name}</h3>
                <p className="text-xs text-[var(--zayado-muted)] mb-3">{leadModal.tagline}</p>
                <input
                  type="text" placeholder="Votre nom" value={leadForm.name}
                  onChange={(e) => setLeadForm({ ...leadForm, name: e.target.value })}
                  required
                  className="w-full px-3 py-2 rounded-lg border border-[var(--zayado-border)] bg-white text-sm"
                  data-testid="lead-name"
                />
                <input
                  type="email" placeholder="Email" value={leadForm.email}
                  onChange={(e) => setLeadForm({ ...leadForm, email: e.target.value })}
                  required
                  className="w-full px-3 py-2 rounded-lg border border-[var(--zayado-border)] bg-white text-sm"
                  data-testid="lead-email"
                />
                <input
                  type="text" placeholder="Société (optionnel)" value={leadForm.company}
                  onChange={(e) => setLeadForm({ ...leadForm, company: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border border-[var(--zayado-border)] bg-white text-sm"
                  data-testid="lead-company"
                />
                <textarea
                  placeholder="Votre projet en 1-2 phrases" value={leadForm.message}
                  onChange={(e) => setLeadForm({ ...leadForm, message: e.target.value })}
                  rows={3}
                  className="w-full px-3 py-2 rounded-lg border border-[var(--zayado-border)] bg-white text-sm"
                  data-testid="lead-message"
                />
                <div className="flex gap-2 pt-1">
                  <button
                    type="button" onClick={() => setLeadModal(null)} disabled={loading}
                    className="flex-1 px-4 py-2 rounded-lg bg-white border border-[var(--zayado-border)] text-sm"
                  >
                    Annuler
                  </button>
                  <button
                    type="submit" disabled={loading}
                    className="flex-1 px-4 py-2 rounded-lg bg-[var(--zayado-navy)] text-white text-sm inline-flex items-center justify-center gap-2 disabled:opacity-50"
                    data-testid="lead-submit"
                  >
                    {loading ? <Loader2 size={14} className="animate-spin" /> : null}
                    Envoyer
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
