/* /partenaires — Zayado Prestataires (modèle TheSustain × Zayado).
   Design DARK NAVY + AMBER (imitation pixel-near du site preview).
   - Fond navy très foncé partout
   - Accent amber vif (titres italiques, badges, boutons)
   - Cards prestataires : fond blanc lisible
   - Police titres : DM Serif Display italique
   - Police body : Manrope */
import React, { useState, useEffect } from "react";
import api from "@/lib/api";
import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import {
  ArrowRight, Search, Sparkles, Globe, MapPin,
  Heart, Wrench, FileSignature, Briefcase, Cpu, BookOpen,
  Zap, Shield, Landmark, Wifi, Hammer, Scale, GraduationCap,
  PartyPopper, Home, Calculator, Star, Check, Handshake, CheckCircle2,
} from "lucide-react";
import { PARTNER as P, PARTNER_FONT } from "./partners-theme";
import TheSustainHeader from "@/components/TheSustainHeader";
import TheSustainFooter from "@/components/TheSustainFooter";
import TheSustainCTA from "@/components/TheSustainCTA";

// ── Données ────────────────────────────────────────────────────────────
const CATEGORIES = [
  { key: "energie", label: "Énergie", icon: Zap },
  { key: "assurance", label: "Assurance", icon: Shield },
  { key: "banque", label: "Banque & Finance", icon: Landmark },
  { key: "telecom", label: "Télécom / Internet", icon: Wifi },
  { key: "travaux", label: "Travaux & Rénovation", icon: Hammer },
  { key: "juridique", label: "Juridique", icon: Scale },
  { key: "sante", label: "Santé & Bien-être", icon: Heart },
  { key: "education", label: "Éducation & Formation", icon: GraduationCap },
  { key: "evenementiel", label: "Événementiel", icon: PartyPopper },
  { key: "immobilier", label: "Immobilier", icon: Home },
  { key: "tech", label: "Tech & Digital", icon: Cpu },
  { key: "compta", label: "Comptabilité", icon: Calculator },
];

const FEATURED = [
  { tag: "VU PAR ZAYADO", saving: "jusqu'à 22%", name: "LumièreEnergie", owner: "Jean-Marc Bonnet", desc: "Énergie verte certifiée pour foyers et entreprises engagées.", city: "Lyon, France", rating: 4.8, reviews: 124, img: "https://images.unsplash.com/photo-1521791136064-7986c2920216?auto=format&w=600&q=80" },
  { tag: "VU PAR ZAYADO", saving: "jusqu'à 30%", name: "Béthel Assurances", owner: "Esther Lecoq", desc: "Courtier indépendant — Auto, habitation, santé, pro.", city: "Paris, France", rating: 4.9, reviews: 287, img: "https://images.unsplash.com/photo-1450101499163-c8848c66ca85?auto=format&w=600&q=80" },
  { tag: "VU PAR ZAYADO", saving: "tarif groupé -15%", name: "Foi & Patrimoine", owner: "Daniel Mwangi", desc: "Gestion de patrimoine éthique et conseil en investissement.", city: "Bruxelles, Belgique", rating: 4.7, reviews: 92, img: "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?auto=format&w=600&q=80" },
  { tag: "VU PAR ZAYADO", saving: "remise groupée -18%", name: "Maison Emmanuel", owner: "Pierre Lambert", desc: "Rénovation, isolation, artisanat — équipe à votre service.", city: "Genève, Suisse", rating: 4.9, reviews: 211, img: "https://images.unsplash.com/photo-1581244277943-fe4a9c777189?auto=format&w=600&q=80" },
  { tag: "VU PAR ZAYADO", saving: "-20% membres", name: "Academia Maranatha", owner: "Esther Dubois", desc: "Soutien scolaire, formations pros et langues.", city: "Montréal, Canada", rating: 4.9, reviews: 189, img: "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?auto=format&w=600&q=80" },
  { tag: "VU PAR ZAYADO", saving: "forfait -25%", name: "Eden Digital", owner: "Caleb Nguyen", desc: "Agence web & marketing — sites, SEO, IA.", city: "Toulouse, France", rating: 4.9, reviews: 134, img: "https://images.unsplash.com/photo-1551434678-e076c223a692?auto=format&w=600&q=80" },
];

const TESTIMONIALS = [
  { quote: "Grâce à Zayado, j'ai réduit ma facture d'énergie de 28% en gardant un fournisseur fidèle à mes valeurs.", name: "Sarah K.", role: "Entrepreneure · France" },
  { quote: "J'ai trouvé un expert-comptable de confiance et un avocat en moins d'une semaine. Service gratuit pour moi !", name: "Emmanuel A.", role: "Entrepreneur · Côte d'Ivoire" },
  { quote: "Assurance habitation -30%, et le courtier nous a vraiment écoutés. Une bénédiction.", name: "Mélanie D.", role: "Famille · Belgique" },
];

const STATS = [
  { value: "1240+", label: "prestataires partenaires" },
  { value: "38", label: "pays couverts" },
  { value: "17,8k", label: "membres communauté" },
  { value: "-22%", label: "économie moyenne" },
];

// ── Header dédié partenaires ──────────────────────────────────────────
// Remplacé par le composant partagé /components/TheSustainHeader.jsx
// (logo officiel TheSustain + lien "Propulsé par Zayado")

// ── Page ───────────────────────────────────────────────────────────────
export default function Partenaires({ embedded = false }) {
  const [apiFeatured, setApiFeatured] = React.useState(null);
  const [apiStats, setApiStats] = React.useState(null);

  useEffect(() => {
    api.get("/partners/featured?limit=6").then((r) => {
      if (r.data && r.data.length > 0) setApiFeatured(r.data);
    }).catch(() => {});
    // Use /marketing/stats (single source of truth, env-configurable floor)
    // rather than /partners/stats (DB-only, may be 0 while seeding).
    api.get("/marketing/stats").then((r) => {
      if (r.data) setApiStats(r.data);
    }).catch(() => {});
  }, []);

  // Données affichées : API si disponible, sinon mocks
  const displayFeatured = apiFeatured || FEATURED;
  const displayStats = apiStats ? [
    { value: (apiStats.partners?.total ?? 1240) + "+", label: "prestataires partenaires" },
    { value: "38", label: "pays couverts" },
    { value: (apiStats.entrepreneurs?.total ?? 1200) + "+", label: "membres communauté" },
    { value: `-${apiStats.avg_savings_pct ?? 23}%`, label: "économie moyenne" },
  ] : STATS;
  const [query, setQuery] = useState("");
  const [activeCategory, setActiveCategory] = useState("");

  return (
    <div className="min-h-screen ts-page"
         style={{ background: P.BG, color: P.TEXT, fontFamily: PARTNER_FONT.sans }}
         data-testid="partenaires-page">
      <Helmet>
        <title>Presta-Partenaire · Le réseau des prestataires chrétiens vérifiés</title>
        <meta name="description" content="1240+ prestataires chrétiens vérifiés. Groupement d'achat, 0 frais ajoutés. Énergie, assurance, comptabilité, juridique, tech, BTP." />
      </Helmet>

      {!embedded && <TheSustainHeader />}

      {/* ── HERO ──────────────────────────────────────────────────── */}
      <section className="max-w-[1280px] mx-auto px-4 md:px-6 pt-16 pb-20 grid lg:grid-cols-[1.1fr_0.9fr] gap-10 items-center">
        <div>
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-[11px] uppercase tracking-[0.25em] mb-6"
               style={{ background: "rgba(212,175,55,0.15)", color: P.NAVY, border: `1px solid ${P.AMBER}55` }}>
            <Sparkles size={11} style={{ color: P.AMBER }} /> Réseau mondial chrétien · by TheSustain
          </div>

          <h1 className="font-display mb-7" style={{  fontSize: "clamp(2.4rem, 5.5vw, 4.6rem)", lineHeight: 1.05, color: P.NAVY }}>
            Le réseau des<br/>
            <em style={{ color: P.AMBER, fontStyle: "italic" }}>prestataires chrétiens</em><br/>
            dans le monde entier
          </h1>

          <p className="text-base md:text-lg max-w-xl mb-8 leading-relaxed" style={{ color: P.TEXT_MUTED }}>
            Trouvez un partenaire de confiance. Grâce au groupement d'achat Zayado,
            vous payez moins cher — <strong style={{ color: P.NAVY }}>sans frais supplémentaires pour vous</strong>.
          </p>

          {/* Badges */}
          <div className="flex flex-wrap gap-x-6 gap-y-2 mb-8 text-sm" style={{ color: P.NAVY }}>
            {[
              "Groupement d'achat",
              "0 commission cachée",
              "Prestataires vérifiés",
            ].map((t) => (
              <span key={t} className="inline-flex items-center gap-2">
                <CheckCircle2 size={14} style={{ color: P.AMBER }} /> {t}
              </span>
            ))}
          </div>

          {/* Search */}
          <div className="rounded-2xl p-2 flex flex-col md:flex-row gap-2 max-w-2xl bg-white"
               style={{ border: `1px solid ${P.BORDER}` }}>
            <div className="flex-1 relative">
              <Search size={15} className="absolute left-4 top-1/2 -translate-y-1/2" style={{ color: P.TEXT_DIM }} />
              <select value={activeCategory} onChange={(e) => setActiveCategory(e.target.value)}
                      className="w-full pl-11 pr-3 py-3.5 text-sm bg-transparent focus:outline-none appearance-none"
                      style={{ color: P.NAVY }}>
                <option value="">Catégorie</option>
                {CATEGORIES.map((c) => <option key={c.key} value={c.key}>{c.label}</option>)}
              </select>
            </div>
            <div className="flex-1 relative">
              <MapPin size={15} className="absolute left-4 top-1/2 -translate-y-1/2" style={{ color: P.TEXT_DIM }} />
              <input type="text" value={query} onChange={(e) => setQuery(e.target.value)}
                     placeholder="Pays ou ville"
                     className="w-full pl-11 pr-3 py-3.5 text-sm bg-transparent focus:outline-none"
                     style={{ color: P.NAVY }}
                     data-testid="partner-search-input" />
            </div>
            <Link to={`/partenaires/recherche?q=${query}&cat=${activeCategory}`}
                  className="inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-xl text-sm font-bold text-white"
                  style={{ background: P.NAVY }}
                  data-testid="partner-search-submit">
              Trouver un prestataire
            </Link>
          </div>
        </div>

        {/* Image collage à droite — entrepreneurs chrétiens divers */}
        <div className="relative hidden lg:block min-h-[480px]">
          <img src="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&w=500&q=80"
               alt="Entrepreneure" className="absolute top-0 right-12 w-[48%] aspect-[3/4] object-cover rounded-2xl shadow-2xl -rotate-3" />
          <img src="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&w=500&q=80"
               alt="Entrepreneur" className="absolute top-8 right-0 w-[48%] aspect-[3/4] object-cover rounded-2xl shadow-2xl rotate-2" />
          <img src="https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?auto=format&w=500&q=80"
               alt="Entrepreneur" className="absolute bottom-0 left-4 w-[48%] aspect-[3/4] object-cover rounded-2xl shadow-2xl rotate-1" />
          <div className="absolute bottom-4 right-4 px-4 py-2 rounded-2xl text-sm shadow-xl bg-white">
            <div className="text-[9px] uppercase tracking-[0.25em] font-bold" style={{ color: P.AMBER }}>Vu par Zayado</div>
            <div className="font-bold" style={{ color: P.NAVY }} data-testid="hero-partners-count">
              {displayStats[0]?.value || "1240+"} prestataires
            </div>
          </div>
        </div>
      </section>

      {/* ── STATS ─────────────────────────────────────────────────── */}
      <section className="border-y" style={{ borderColor: P.BORDER }} data-testid="partner-stats">
        <div className="max-w-[1280px] mx-auto px-4 md:px-6 py-12 grid grid-cols-2 md:grid-cols-4 gap-6">
          {displayStats.map((s, i) => (
            <div key={i} className="text-center" data-testid={`stat-${i}`}>
              <div className="font-bold mb-1" style={{  fontSize: "clamp(2rem, 4vw, 3rem)", color: P.AMBER_LIGHT }}>
                {s.value}
              </div>
              <div className="text-xs uppercase tracking-[0.2em]" style={{ color: P.TEXT_MUTED }}>{s.label}</div>
            </div>
          ))}
        </div>
        {apiStats?.is_floor_data && (
          <div className="max-w-[1280px] mx-auto px-4 md:px-6 pb-5 text-center text-[11px] italic" style={{ color: P.TEXT_MUTED }} data-testid="stats-disclaimer">
            {apiStats.disclaimer || "Réseau en croissance — chiffres mis à jour mensuellement"}
          </div>
        )}
      </section>

      {/* ── CATEGORIES ────────────────────────────────────────────── */}
      <section className="max-w-[1280px] mx-auto px-4 md:px-6 py-20" data-testid="partner-categories">
        <div className="text-[11px] uppercase tracking-[0.3em] mb-3" style={{ color: P.AMBER_LIGHT }}>— Catégories</div>
        <h2 className="font-bold mb-3" style={{  fontSize: "clamp(2rem, 4vw, 3rem)" }}>
          Toutes nos catégories
        </h2>
        <p className="text-sm mb-10 max-w-xl" style={{ color: P.TEXT_MUTED }}>
          Une offre complète pensée pour les fondateurs solos et la communauté Zayado.
        </p>

        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {CATEGORIES.map((c) => {
            const Icon = c.icon;
            return (
              <Link key={c.key} to={`/partenaires/recherche?cat=${c.key}`}
                    className="group p-5 rounded-2xl transition-colors"
                    style={{ background: P.BG_CARD, border: `1px solid ${P.BORDER}` }}
                    data-testid={`partner-cat-${c.key}`}>
                <div className="w-10 h-10 rounded-xl flex items-center justify-center mb-4"
                     style={{ background: "rgba(251,191,36,0.15)" }}>
                  <Icon size={17} style={{ color: P.AMBER }} />
                </div>
                <div className="font-bold text-sm mb-2">{c.label}</div>
                <ArrowRight size={14} className="opacity-50 group-hover:opacity-100 transition" style={{ color: P.AMBER }} />
              </Link>
            );
          })}
        </div>
      </section>

      {/* ── FEATURED PROVIDERS ────────────────────────────────────── */}
      <section className="max-w-[1280px] mx-auto px-4 md:px-6 py-16" data-testid="partner-featured">
        <div className="flex items-end justify-between mb-10 flex-wrap gap-3">
          <div>
            <div className="text-[11px] uppercase tracking-[0.3em] mb-3" style={{ color: P.AMBER_LIGHT }}>
              — Prestataires en vedette
            </div>
            <h2 className="font-bold mb-2" style={{  fontSize: "clamp(2rem, 4vw, 3rem)" }}>
              Prestataires en vedette
            </h2>
            <p className="text-sm" style={{ color: P.TEXT_MUTED }}>
              Sélection éditoriale Zayado — vérifiés et recommandés.
            </p>
          </div>
          <Link to="/partenaires/recherche"
                className="inline-flex items-center gap-2 text-sm font-medium hover:gap-3 transition-all"
                style={{ color: P.AMBER }}>
            Voir tous les prestataires <ArrowRight size={14} />
          </Link>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {FEATURED.map((f, i) => (
            <div key={i} className="rounded-2xl overflow-hidden"
                 style={{ background: P.CARD_BG, color: P.CARD_TEXT }}
                 data-testid={`partner-featured-${i}`}>
              <div className="aspect-[4/3] overflow-hidden relative">
                <img src={f.img} alt={f.name} className="w-full h-full object-cover" />
                <span className="absolute top-3 left-3 px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider flex items-center gap-1"
                      style={{ background: P.AMBER, color: P.BG }}>
                  <CheckCircle2 size={10} /> {f.tag}
                </span>
                <span className="absolute top-3 right-3 px-2.5 py-1 rounded-full text-[10px] font-bold"
                      style={{ background: P.BG, color: P.AMBER_LIGHT }}>
                  {f.saving}
                </span>
              </div>
              <div className="p-4">
                <div className="flex items-start justify-between gap-2 mb-1">
                  <div>
                    <div className="font-bold text-base leading-tight" style={{  color: P.BG }}>
                      {f.name}
                    </div>
                    <div className="text-[11px] mt-0.5" style={{ color: P.CARD_MUTED }}>{f.owner}</div>
                  </div>
                </div>
                <div className="text-xs leading-relaxed mt-2 mb-3 line-clamp-2" style={{ color: P.CARD_MUTED }}>{f.desc}</div>
                <div className="flex items-center justify-between pt-3 border-t" style={{ borderColor: "#e5e7eb" }}>
                  <span className="text-[11px] inline-flex items-center gap-1" style={{ color: P.CARD_MUTED }}>
                    <MapPin size={10} /> {f.city}
                  </span>
                  <span className="text-[11px] inline-flex items-center gap-1 font-bold">
                    <Star size={10} fill={P.AMBER} style={{ color: P.AMBER }} /> {f.rating} <span className="opacity-50">({f.reviews})</span>
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── COMME SELECTRA, EN MIEUX ──────────────────────────────── */}
      <section className="py-20" data-testid="partner-selectra">
        <div className="max-w-[1280px] mx-auto px-4 md:px-6 rounded-3xl p-10 md:p-14 grid lg:grid-cols-2 gap-12 items-center"
             style={{ background: P.BG_CARD, border: `1px solid ${P.BORDER}` }}>
          <div>
            <div className="text-[11px] uppercase tracking-[0.3em] mb-3" style={{ color: P.AMBER_LIGHT }}>
              — Comme Selectra, en mieux
            </div>
            <h2 className="font-bold mb-6" style={{  fontSize: "clamp(1.9rem, 3.5vw, 2.6rem)", lineHeight: 1.1 }}>
              La puissance du groupement, <em style={{ color: P.AMBER_LIGHT }}>sans le moindre frais</em>.
            </h2>
            <ul className="space-y-3 mb-8">
              {[
                "Tarifs négociés en groupe pour toute la communauté",
                "0 frais de mise en relation côté client final",
                "Prestataires choisis main par main par Zayado",
                "Service gratuit, transparent et indépendant",
              ].map((t) => (
                <li key={t} className="flex items-start gap-3 text-sm" style={{ color: "rgba(255,255,255,0.85)" }}>
                  <CheckCircle2 size={15} className="shrink-0 mt-0.5" style={{ color: P.AMBER }} />
                  <span>{t}</span>
                </li>
              ))}
            </ul>
            <Link to="/contact?subject=Demande+devis+gratuit"
                  className="inline-flex items-center gap-2 px-6 py-3.5 rounded-full text-sm font-bold"
                  style={{ background: P.AMBER, color: P.BG }}
                  data-testid="partner-quote-cta">
              Demander un devis gratuit <ArrowRight size={13} />
            </Link>
          </div>

          <div className="grid grid-cols-3 gap-3">
            {[
              { v: "-22%", l: "Économie moyenne pour la communauté" },
              { v: "17,8k", l: "Membres" },
              { v: "100%", l: "Vérifiés Zayado" },
            ].map((s, i) => (
              <div key={i} className="rounded-2xl p-5 text-center"
                   style={{ background: "rgba(255,255,255,0.04)", border: `1px solid ${P.BORDER}` }}>
                <div className="font-bold mb-1" style={{  fontSize: "clamp(1.4rem, 2.5vw, 1.9rem)", color: P.AMBER_LIGHT }}>
                  {s.v}
                </div>
                <div className="text-[10px] uppercase tracking-wider leading-tight" style={{ color: P.TEXT_MUTED }}>{s.l}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── SERVICES PRO ─────────────────────────────────────────── */}
      <section className="max-w-[1280px] mx-auto px-4 md:px-6 py-16" data-testid="partner-services-pro">
        <div className="flex items-end justify-between mb-10 flex-wrap gap-3">
          <div>
            <div className="text-[11px] uppercase tracking-[0.3em] mb-3" style={{ color: P.AMBER_LIGHT }}>
              — Services Pro by Zayado
            </div>
            <h2 className="font-bold mb-2" style={{  fontSize: "clamp(2rem, 4vw, 3rem)" }}>
              3 leviers pour faire grandir votre entreprise
            </h2>
            <p className="text-sm" style={{ color: P.TEXT_MUTED }}>
              Ouverts à toutes et tous, sans condition. Tarifs préférentiels du groupement.
            </p>
          </div>
          <Link to="/services-pro" className="inline-flex items-center gap-2 text-sm font-medium hover:gap-3 transition-all" style={{ color: P.AMBER }}>
            Tout voir <ArrowRight size={14} />
          </Link>
        </div>

        <div className="grid md:grid-cols-3 gap-5">
          {[
            { icon: FileSignature, title: "Création d'entreprise", desc: "Statuts, immat, banque, comptabilité — clé en main.", price: "dès 290 €" },
            { icon: Briefcase, title: "Pilotage d'entreprise", desc: "Tableau de bord, OKR, finances. Votre copilote business mensuel.", price: "dès 190 €/mois" },
            { icon: Sparkles, title: "Extension IA", desc: "Automatisation, agents IA, contenu. app.zayado.net.", price: "essai 3j gratuit" },
          ].map((s, i) => {
            const Icon = s.icon;
            return (
              <Link key={i} to="/services-pro"
                    className="group p-7 rounded-2xl transition-all hover:-translate-y-0.5"
                    style={{ background: P.BG_CARD, border: `1px solid ${P.BORDER}` }}
                    data-testid={`partner-service-${i}`}>
                <div className="w-11 h-11 rounded-xl flex items-center justify-center mb-5"
                     style={{ background: "rgba(251,191,36,0.15)" }}>
                  <Icon size={18} style={{ color: P.AMBER }} />
                </div>
                <h3 className="font-bold text-xl mb-2" style={{ fontFamily: PARTNER_FONT.serif }}>{s.title}</h3>
                <p className="text-sm mb-5 leading-relaxed" style={{ color: P.TEXT_MUTED }}>{s.desc}</p>
                <div className="flex items-center justify-between pt-4 border-t" style={{ borderColor: P.BORDER }}>
                  <span className="text-xs font-bold" style={{ color: P.AMBER_LIGHT }}>{s.price}</span>
                  <ArrowRight size={14} style={{ color: P.AMBER }} />
                </div>
              </Link>
            );
          })}
        </div>
      </section>

      {/* ── TÉMOIGNAGES ───────────────────────────────────────────── */}
      <section className="max-w-[1280px] mx-auto px-4 md:px-6 py-20" data-testid="partner-testimonials">
        <div className="text-[11px] uppercase tracking-[0.3em] mb-3 text-center" style={{ color: P.AMBER_LIGHT }}>— Avis</div>
        <h2 className="font-bold mb-12 text-center" style={{  fontSize: "clamp(2rem, 4vw, 3rem)" }}>
          Trusted by
        </h2>
        <div className="grid md:grid-cols-3 gap-5">
          {TESTIMONIALS.map((t, i) => (
            <div key={i} className="rounded-2xl p-6"
                 style={{ background: P.BG_CARD, border: `1px solid ${P.BORDER}` }}>
              <div className="flex gap-0.5 mb-4">
                {[1,2,3,4,5].map((s) => <Star key={s} size={12} fill={P.AMBER} style={{ color: P.AMBER }} />)}
              </div>
              <p className="text-sm italic leading-relaxed mb-5" style={{ color: "rgba(255,255,255,0.9)" }}>
                "{t.quote}"
              </p>
              <div className="pt-4 border-t" style={{ borderColor: P.BORDER }}>
                <div className="font-bold text-sm">{t.name}</div>
                <div className="text-xs mt-0.5" style={{ color: P.TEXT_MUTED }}>{t.role}</div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── DEVENIR PRESTATAIRE PARTENAIRE ────────────────────────── */}
      <section className="max-w-[1280px] mx-auto px-4 md:px-6 pb-20" data-testid="partner-become">
        <div className="rounded-3xl p-10 md:p-14 grid lg:grid-cols-2 gap-10 items-center"
             style={{ background: P.BG_CARD, border: `1px solid ${P.BORDER}` }}>
          <div>
            <div className="text-[11px] uppercase tracking-[0.3em] mb-3" style={{ color: P.AMBER_LIGHT }}>— Partenariat</div>
            <h2 className="font-bold mb-5" style={{  fontSize: "clamp(2.2rem, 4.5vw, 3.4rem)", lineHeight: 1.1 }}>
              Devenir<br/>prestataire<br/>partenaire
            </h2>
            <p className="text-base mb-7" style={{ color: P.TEXT_MUTED }}>
              Rejoignez le réseau Zayado et bénéficiez du groupement.
            </p>
            <Link to="/devenir-partenaire"
                  className="inline-flex items-center gap-2 px-7 py-3.5 rounded-full text-sm font-bold"
                  style={{ background: P.AMBER, color: P.BG }}
                  data-testid="partner-join-cta">
              Rejoindre l'aventure <ArrowRight size={13} />
            </Link>
          </div>

          <div className="space-y-3">
            {[
              { icon: Globe, label: "Visibilité internationale" },
              { icon: Handshake, label: "Groupement d'achats sur vos services externes" },
              { icon: Heart, label: "Communauté engagée et fidèle" },
            ].map((b, i) => {
              const Icon = b.icon;
              return (
                <div key={i} className="flex items-center gap-3 px-5 py-4 rounded-xl"
                     style={{ background: "rgba(255,255,255,0.04)", border: `1px solid ${P.BORDER}` }}>
                  <div className="w-10 h-10 rounded-full flex items-center justify-center shrink-0"
                       style={{ background: "rgba(251,191,36,0.15)" }}>
                    <Icon size={16} style={{ color: P.AMBER }} />
                  </div>
                  <div className="font-medium text-sm">{b.label}</div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── FOOTER ────────────────────────────────────────────────── */}
      <TheSustainCTA
        title="Prêt à rejoindre le réseau ?"
        description="Rejoignez le réseau chrétien des prestataires de confiance. Visibilité internationale, indépendance garantie, communauté engagée."
        buttonLabel="Devenir partenaire"
        buttonTo="/devenir-partenaire"
      />

      {!embedded && <TheSustainFooter />}
    </div>
  );
}
