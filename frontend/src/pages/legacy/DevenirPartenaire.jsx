/* /devenir-partenaire — Formulaire candidature partenaire Zayado.
   Reprend la section du modèle TheSustain en page dédiée avec un
   processus en 4 étapes + formulaire de candidature.

   Backend MVP : envoie un enterprise_lead via /api/payments/enterprise-lead
   (product_id="join_partner_network", type=enterprise_lead, déjà supporté). */
import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import {
  ArrowRight, ArrowLeft, Check, Globe, Percent, Crown,
  Loader2, Sparkles, Users, Shield, Send,
} from "lucide-react";
import api from "@/lib/api";
import { useMarketingStats } from "@/hooks/useMarketingStats";
import TheSustainHeader from "@/components/TheSustainHeader";
import TheSustainFooter from "@/components/TheSustainFooter";

const NAVY = "#3B5998";
const GOLD = "#AF1C1A";
const MUTED = "#4B5563";

const PROCESS_STEPS = [
  { num: "01", title: "Candidature", desc: "Remplissez le formulaire ci-dessous (5 min)." },
  { num: "02", title: "Premier appel", desc: "Notre équipe vous contacte sous 48h pour qualifier votre dossier." },
  { num: "03", title: "Vérification", desc: "Audit qualité, références clients, conformité ORIAS/CCI/INPI." },
  { num: "04", title: "Onboarding", desc: "Mise en ligne sur l'annuaire + brief tarifs groupement (2 semaines)." },
];

const BENEFITS = [
  { icon: Globe, title: "Visibilité internationale", desc: "Exposition à 17,8k+ entrepreneurs solos en France, Belgique, Suisse, Canada, Maroc, Sénégal." },
  { icon: Percent, title: "Groupement d'achat", desc: "Bénéficiez des tarifs négociés Zayado sur VOS propres services externes (compta, juridique, etc.)." },
  { icon: Users, title: "Communauté engagée", desc: "Pas du B2C mass-market — des fondateurs solos engagés avec un taux de fidélité élevé." },
  { icon: Crown, title: "Statut Vérifié Zayado", desc: "Le badge ShieldCheck qui rassure et convertit. Avec lien direct depuis l'annuaire." },
  { icon: Shield, title: "Indépendance garantie", desc: "Nous ne prenons aucun pourcentage sur vos prestations. Zéro commission, zéro intermédiation forcée." },
  { icon: Sparkles, title: "Lead qualifiés", desc: "Vous recevez les demandes des membres Zayado déjà briefés. Pas de spam, pas de chasseurs de devis." },
];

const CRITERIA = [
  "Vous êtes une structure légale immatriculée (SASU, EURL, SARL, micro, association)",
  "Vous exercez en France ou dans un pays francophone (BE/CH/CA/MA/SN/etc.)",
  "Vous disposez d'agréments / certifications si requis (ORIAS, CNCEF, OEC, RGE…)",
  "Vous acceptez la charte qualité Zayado (transparence, devis détaillé, garantie remboursement 30j)",
  "Vous fournissez au moins 3 références clients sur les 12 derniers mois",
];

export default function DevenirPartenaire({ embedded = false }) {
  const mstats = useMarketingStats();
  const partnersLabel = (mstats?.partners?.total ?? 1240) + "+ prestataires";
  const [form, setForm] = useState({
    name: "", email: "", company: "", category: "",
    country: "France", message: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState("");

  const onChange = (k, v) => setForm({ ...form, [k]: v });

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (!form.email || !form.name || !form.company || !form.category) {
      setError("Veuillez remplir tous les champs obligatoires.");
      return;
    }
    setSubmitting(true);
    try {
      await api.post("/payments/enterprise-lead", {
        product_id: "join_partner_network",
        email: form.email,
        name: form.name,
        company: form.company,
        message: `Catégorie: ${form.category}\nPays: ${form.country}\n\n${form.message}`,
      });
      setSubmitted(true);
    } catch (e) {
      setError(e.response?.data?.detail || "Erreur — réessayez ou contactez-nous directement.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen ts-page" style={{ background: "#FFFFFF" }} data-testid="devenir-partenaire-page">
      <Helmet>
        <title>Devenir partenaire · Presta-Partenaire TheSustain</title>
        <meta name="description" content="Rejoignez le réseau chrétien TheSustain : visibilité, communauté engagée, sélection à l'entrée." />
      </Helmet>
      {!embedded && <TheSustainHeader />}

      {/* HERO */}
      <section className="max-w-[1100px] mx-auto px-4 md:px-6 pt-12 pb-10 text-center">
        <Link to="/partenaires" className="text-xs hover:underline inline-flex items-center gap-1 mb-5" style={{ color: MUTED }}>
          <ArrowLeft size={11} /> Réseau Zayado
        </Link>
        <div className="text-[11px] uppercase tracking-[0.3em] mb-3" style={{ color: GOLD }}>
          — Partenariat
        </div>
        <h1 className="font-bold mb-5 mx-auto max-w-3xl"
            style={{ fontFamily: "'DM Serif Display', serif",
                     fontSize: "clamp(2.2rem, 5vw, 3.8rem)", lineHeight: 1.05, color: NAVY }}>
          Rejoindre le réseau <em>Zayado.</em>
        </h1>
        <p className="text-base md:text-lg max-w-2xl mx-auto leading-relaxed" style={{ color: MUTED }}>
          Sélection à entrée, indépendance garantie, communauté engagée et fidèle.
          <strong style={{ color: NAVY }} data-testid="partners-count"> {partnersLabel}</strong> déjà membres.
        </p>
      </section>

      {/* BÉNÉFICES (6 cards) */}
      <section className="max-w-[1200px] mx-auto px-4 md:px-6 py-10" data-testid="partner-benefits">
        <div className="text-[11px] uppercase tracking-[0.25em] mb-6 text-center" style={{ color: GOLD }}>
          — Ce que vous gagnez
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {BENEFITS.map((b) => {
            const Icon = b.icon;
            return (
              <div key={b.title} className="bg-white border border-[var(--zayado-border)] rounded-2xl p-6">
                <div className="w-11 h-11 rounded-xl flex items-center justify-center mb-4"
                     style={{ background: "var(--zayado-cream)" }}>
                  <Icon size={19} style={{ color: NAVY }} />
                </div>
                <div className="font-bold text-base mb-2" style={{ color: NAVY }}>{b.title}</div>
                <div className="text-sm leading-relaxed" style={{ color: MUTED }}>{b.desc}</div>
              </div>
            );
          })}
        </div>
      </section>

      {/* PROCESSUS 4 ÉTAPES */}
      <section className="bg-white border-y border-[var(--zayado-border)] py-14" data-testid="partner-process">
        <div className="max-w-[1100px] mx-auto px-4 md:px-6">
          <div className="text-[11px] uppercase tracking-[0.25em] mb-2 text-center" style={{ color: GOLD }}>
            — Comment ça marche
          </div>
          <h2 className="font-bold text-center mb-10"
              style={{ fontFamily: "'DM Serif Display', serif",
                       fontSize: "clamp(1.8rem, 4vw, 2.6rem)", color: NAVY }}>
            En 4 étapes, sur 2 semaines.
          </h2>
          <div className="grid md:grid-cols-4 gap-6">
            {PROCESS_STEPS.map((s) => (
              <div key={s.num} className="text-center">
                <div className="font-bold mb-3 mx-auto"
                     style={{ fontFamily: "'DM Serif Display', serif",
                              fontSize: "clamp(2.2rem, 4vw, 3rem)", color: GOLD }}>
                  {s.num}
                </div>
                <div className="font-bold text-base mb-2" style={{ color: NAVY }}>{s.title}</div>
                <div className="text-sm leading-relaxed" style={{ color: MUTED }}>{s.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CRITÈRES D'ÉLIGIBILITÉ */}
      <section className="max-w-[900px] mx-auto px-4 md:px-6 py-14" data-testid="partner-criteria">
        <div className="text-[11px] uppercase tracking-[0.25em] mb-2" style={{ color: GOLD }}>
          — Critères
        </div>
        <h2 className="font-bold mb-7"
            style={{ fontFamily: "'DM Serif Display', serif",
                     fontSize: "clamp(1.6rem, 3.5vw, 2.2rem)", color: NAVY }}>
          Êtes-vous éligible ?
        </h2>
        <ul className="space-y-3 bg-white border border-[var(--zayado-border)] rounded-2xl p-7">
          {CRITERIA.map((c) => (
            <li key={c} className="flex items-start gap-3 text-sm" style={{ color: "var(--zayado-text)" }}>
              <Check size={16} className="shrink-0 mt-0.5" style={{ color: GOLD }} />
              <span>{c}</span>
            </li>
          ))}
        </ul>
      </section>

      {/* FORMULAIRE CANDIDATURE */}
      <section className="bg-white border-y border-[var(--zayado-border)] py-14" data-testid="partner-form-section">
        <div className="max-w-[700px] mx-auto px-4 md:px-6">
          <div className="text-[11px] uppercase tracking-[0.25em] mb-2 text-center" style={{ color: GOLD }}>
            — Candidature
          </div>
          <h2 className="font-bold text-center mb-3"
              style={{ fontFamily: "'DM Serif Display', serif",
                       fontSize: "clamp(1.8rem, 4vw, 2.6rem)", color: NAVY }}>
            Postuler en 5 minutes.
          </h2>
          <p className="text-sm text-center mb-8" style={{ color: MUTED }}>
            Réponse sous 48h ouvrées. Nous vous expliquerons clairement si votre profil
            correspond, sans laisser de demande sans réponse.
          </p>

          {submitted ? (
            <div className="bg-[var(--zayado-cream)] rounded-2xl p-8 text-center" data-testid="partner-form-success">
              <Check size={28} className="mx-auto mb-3" style={{ color: GOLD }} />
              <h3 className="font-bold text-lg mb-2" style={{ color: NAVY }}>Candidature envoyée 🎉</h3>
              <p className="text-sm mb-5" style={{ color: MUTED }}>
                Nous vous recontactons à <strong style={{ color: NAVY }}>{form.email}</strong> sous 48h ouvrées.
              </p>
              <Link to="/partenaires" className="text-sm hover:underline" style={{ color: NAVY }}>
                ← Retour au réseau Zayado
              </Link>
            </div>
          ) : (
            <form onSubmit={onSubmit} className="space-y-4" data-testid="partner-form">
              <div className="grid sm:grid-cols-2 gap-4">
                <label className="block">
                  <span className="text-[11px] uppercase tracking-wider font-medium" style={{ color: NAVY }}>
                    Votre nom *
                  </span>
                  <input type="text" required value={form.name}
                         onChange={(e) => onChange("name", e.target.value)}
                         className="mt-1.5 w-full px-4 py-3 border border-[var(--zayado-border)] rounded-xl text-sm focus:outline-none focus:border-[var(--zayado-navy)] bg-white"
                         data-testid="partner-form-name" />
                </label>
                <label className="block">
                  <span className="text-[11px] uppercase tracking-wider font-medium" style={{ color: NAVY }}>
                    Email pro *
                  </span>
                  <input type="email" required value={form.email}
                         onChange={(e) => onChange("email", e.target.value)}
                         placeholder="vous@entreprise.fr"
                         className="mt-1.5 w-full px-4 py-3 border border-[var(--zayado-border)] rounded-xl text-sm focus:outline-none focus:border-[var(--zayado-navy)] bg-white"
                         data-testid="partner-form-email" />
                </label>
              </div>

              <label className="block">
                <span className="text-[11px] uppercase tracking-wider font-medium" style={{ color: NAVY }}>
                  Société / Cabinet *
                </span>
                <input type="text" required value={form.company}
                       onChange={(e) => onChange("company", e.target.value)}
                       className="mt-1.5 w-full px-4 py-3 border border-[var(--zayado-border)] rounded-xl text-sm focus:outline-none focus:border-[var(--zayado-navy)] bg-white"
                       data-testid="partner-form-company" />
              </label>

              <div className="grid sm:grid-cols-2 gap-4">
                <label className="block">
                  <span className="text-[11px] uppercase tracking-wider font-medium" style={{ color: NAVY }}>
                    Catégorie *
                  </span>
                  <select required value={form.category}
                          onChange={(e) => onChange("category", e.target.value)}
                          className="mt-1.5 w-full px-4 py-3 border border-[var(--zayado-border)] rounded-xl text-sm focus:outline-none focus:border-[var(--zayado-navy)] bg-white"
                          data-testid="partner-form-category">
                    <option value="">Choisir…</option>
                    <option value="protection">Protection sociale (mutuelle, prévoyance)</option>
                    <option value="creation">Création & juridique</option>
                    <option value="compta">Comptabilité / Expert-comptable</option>
                    <option value="tech">Tech / IA / Web</option>
                    <option value="artisans">Artisans & BTP</option>
                    <option value="spirituel">Bien-être & spirituel</option>
                    <option value="autre">Autre</option>
                  </select>
                </label>
                <label className="block">
                  <span className="text-[11px] uppercase tracking-wider font-medium" style={{ color: NAVY }}>
                    Pays
                  </span>
                  <select value={form.country}
                          onChange={(e) => onChange("country", e.target.value)}
                          className="mt-1.5 w-full px-4 py-3 border border-[var(--zayado-border)] rounded-xl text-sm focus:outline-none focus:border-[var(--zayado-navy)] bg-white">
                    {["France", "Belgique", "Suisse", "Canada", "Maroc", "Sénégal", "Autre"].map((c) =>
                      <option key={c} value={c}>{c}</option>)}
                  </select>
                </label>
              </div>

              <label className="block">
                <span className="text-[11px] uppercase tracking-wider font-medium" style={{ color: NAVY }}>
                  Présentez-vous brièvement
                </span>
                <textarea value={form.message}
                          onChange={(e) => onChange("message", e.target.value)}
                          rows={5}
                          placeholder="Votre activité, vos certifications, vos références…"
                          className="mt-1.5 w-full px-4 py-3 border border-[var(--zayado-border)] rounded-xl text-sm focus:outline-none focus:border-[var(--zayado-navy)] bg-white resize-none"
                          data-testid="partner-form-message" />
              </label>

              {error && <div className="text-xs text-red-700">{error}</div>}

              <p className="text-[11px]" style={{ color: MUTED }}>
                En soumettant, vous acceptez notre{" "}
                <Link to="/legal/confidentialite" className="underline">politique de confidentialité</Link>.
                Aucune donnée vendue à des tiers.
              </p>

              <button type="submit" disabled={submitting}
                      className="w-full inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-full text-white text-base font-medium disabled:opacity-50"
                      style={{ background: NAVY }}
                      data-testid="partner-form-submit">
                {submitting ? <Loader2 size={15} className="animate-spin" /> : <Send size={15} />}
                Envoyer ma candidature
              </button>
            </form>
          )}
        </div>
      </section>

      {!embedded && <TheSustainFooter />}
    </div>
  );
}
