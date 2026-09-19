/* /partenaires/recherche — Annuaire prestataires Zayado filtrable.
   Reprend les codes du modèle TheSustain (économie, vérifié, groupement)
   au design Zayado (palette navy/or, beige cream, DM Serif Display).

   Layout : sidebar filtres (catégorie, pays, note, prix) + grille de cards
   prestataires + barre de tri + pagination front-only.

   MVP : 24 prestataires mockés. Backend annuaire viendra plus tard
   (endpoint /api/partners/search à brancher). */
import React, { useState, useMemo, useEffect } from "react";
import api from "@/lib/api";
import { Link, useLocation } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import {
  Search, MapPin, Star, ShieldCheck, ArrowRight, ArrowLeft,
  X, SlidersHorizontal, Heart, FileSignature, Briefcase, Cpu, Wrench, BookOpen,
} from "lucide-react";
import TheSustainHeader from "@/components/TheSustainHeader";
import TheSustainFooter from "@/components/TheSustainFooter";

const NAVY = "#3B5998";   // bleu TheSustain
const GOLD = "#AF1C1A";   // rouge CTA TheSustain
const MUTED = "#4B5563";
const PAGE_SIZE = 9;

// ── Données mockées (24 prestataires) ─────────────────────────────────
const CATS = [
  { key: "protection", label: "Protection sociale", icon: Heart },
  { key: "creation", label: "Création & juridique", icon: FileSignature },
  { key: "compta", label: "Comptabilité", icon: Briefcase },
  { key: "tech", label: "Tech & IA", icon: Cpu },
  { key: "artisans", label: "Artisans & BTP", icon: Wrench },
  { key: "spirituel", label: "Bien-être & spirituel", icon: BookOpen },
];

const COUNTRIES = ["France", "Belgique", "Suisse", "Canada", "Maroc", "Sénégal"];

const PARTNERS = [
  { id: 1, cat: "protection", name: "Cabinet ORIAS Référencé", city: "Lyon", country: "France", rating: 4.9, saving: "−22%", price: "premium", verified: true, img: "https://images.unsplash.com/photo-1576091160550-2173dba999ef?auto=format&w=600&q=80", desc: "Mutuelle TNS et prévoyance Madelin. Économie moyenne 22% pour la communauté Zayado." },
  { id: 2, cat: "compta", name: "Cabinet Comptable Pro Zayado", city: "Paris", country: "France", rating: 4.8, saving: "−30%", price: "standard", verified: true, img: "https://images.unsplash.com/photo-1554224155-6726b3ff858f?auto=format&w=600&q=80", desc: "Bilan micro à 49€/mois. Suivi mensuel via tableau de bord Pilotage Zayado." },
  { id: 3, cat: "creation", name: "Création SASU / EURL Express", city: "Bordeaux", country: "France", rating: 4.7, saving: "dès 290€", price: "premium", verified: true, img: "https://images.unsplash.com/photo-1450101499163-c8848c66ca85?auto=format&w=600&q=80", desc: "Statuts sur-mesure, immatriculation, accompagnement banque pro. Clé en main." },
  { id: 4, cat: "tech", name: "Studio Web Sustain", city: "Bruxelles", country: "Belgique", rating: 4.9, saving: "−18%", price: "premium", verified: true, img: "https://images.unsplash.com/photo-1551434678-e076c223a692?auto=format&w=600&q=80", desc: "Sites vitrines + e-commerce. Hébergement Cloudflare offert 12 mois pour Zayado." },
  { id: 5, cat: "artisans", name: "Réseau Artisans Verts", city: "Toulouse", country: "France", rating: 4.6, saving: "−15%", price: "standard", verified: true, img: "https://images.unsplash.com/photo-1581094794329-c8112a89af12?auto=format&w=600&q=80", desc: "Plomberie, électricité, menuiserie. Devis sous 24h, garantie 2 ans." },
  { id: 6, cat: "spirituel", name: "Maison de Prière TheSustain", city: "Marseille", country: "France", rating: 5.0, saving: "Gratuit", price: "economique", verified: true, img: "https://images.unsplash.com/photo-1499209974431-9dddcece7f88?auto=format&w=600&q=80", desc: "Versets quotidiens, prière en ligne, méditation guidée. Plateforme TheSustain." },
  { id: 7, cat: "compta", name: "Comptable Solo Genève", city: "Genève", country: "Suisse", rating: 4.8, saving: "−24%", price: "premium", verified: true, img: "https://images.unsplash.com/photo-1450101499163-c8848c66ca85?auto=format&w=600&q=80", desc: "Spécialiste indépendants suisses. Forfait Zayado dès 89 CHF/mois." },
  { id: 8, cat: "tech", name: "Agence IA Zayado Partner", city: "Lyon", country: "France", rating: 4.7, saving: "−20%", price: "standard", verified: true, img: "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&w=600&q=80", desc: "Automatisations n8n + Claude, mise en place agents IA sur-mesure." },
  { id: 9, cat: "creation", name: "Juriste Solo Bordeaux", city: "Bordeaux", country: "France", rating: 4.5, saving: "−15%", price: "standard", verified: true, img: "https://images.unsplash.com/photo-1589829085413-56de8ae18c73?auto=format&w=600&q=80", desc: "CGV, RGPD, contrats commerciaux. Audit juridique offert pour Zayado." },
  { id: 10, cat: "protection", name: "Courtier Madelin Pro", city: "Montréal", country: "Canada", rating: 4.6, saving: "−18%", price: "premium", verified: true, img: "https://images.unsplash.com/photo-1521791136064-7986c2920216?auto=format&w=600&q=80", desc: "Assurance santé indépendants au Canada. Réseau de soins exclusif." },
  { id: 11, cat: "artisans", name: "Menuiserie Bruno T.", city: "Nantes", country: "France", rating: 4.9, saving: "−10%", price: "standard", verified: true, img: "https://images.unsplash.com/photo-1567361808960-dec9cb578182?auto=format&w=600&q=80", desc: "Aménagement intérieur sur-mesure. Témoignage Zayado : 'pas de tracas Excel'." },
  { id: 12, cat: "spirituel", name: "Coach Bien-être Zayado", city: "Lille", country: "France", rating: 4.8, saving: "−25%", price: "standard", verified: true, img: "https://images.unsplash.com/photo-1545389336-cf090694435e?auto=format&w=600&q=80", desc: "Programme anti-burnout 8 semaines. 1 séance offerte avec Zayado." },
  { id: 13, cat: "creation", name: "Notaire Indépendants", city: "Paris", country: "France", rating: 4.4, saving: "−12%", price: "premium", verified: true, img: "https://images.unsplash.com/photo-1589829085413-56de8ae18c73?auto=format&w=600&q=80", desc: "Pacte associés, transmission, dépôt statuts. Premier RDV offert." },
  { id: 14, cat: "tech", name: "Dev React Freelance Pro", city: "Casablanca", country: "Maroc", rating: 4.7, saving: "−30%", price: "economique", verified: true, img: "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&w=600&q=80", desc: "App React + FastAPI sur-mesure. Tarif Zayado : 350€/jour au lieu de 500€." },
  { id: 15, cat: "compta", name: "Expert-Comptable Senior", city: "Lausanne", country: "Suisse", rating: 4.9, saving: "−20%", price: "premium", verified: true, img: "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?auto=format&w=600&q=80", desc: "Cabinet senior pour SASU/EURL >100k€ CA. Offre Zayado : audit gratuit." },
  { id: 16, cat: "protection", name: "Mutuelle Indépendants Dakar", city: "Dakar", country: "Sénégal", rating: 4.6, saving: "−28%", price: "economique", verified: true, img: "https://images.unsplash.com/photo-1505751172876-fa1923c5c528?auto=format&w=600&q=80", desc: "Assurance santé pour entrepreneurs ouest-africains. Adhésion Zayado." },
  { id: 17, cat: "artisans", name: "Plomberie Express", city: "Marseille", country: "France", rating: 4.5, saving: "−12%", price: "economique", verified: true, img: "https://images.unsplash.com/photo-1581244277943-fe4a9c777189?auto=format&w=600&q=80", desc: "Interventions sous 24h. Garantie main d'œuvre 2 ans." },
  { id: 18, cat: "spirituel", name: "Retraites Zayado x TheSustain", city: "Annecy", country: "France", rating: 5.0, saving: "−15%", price: "premium", verified: true, img: "https://images.unsplash.com/photo-1518604666860-9ed391f76460?auto=format&w=600&q=80", desc: "Retraites de fondateurs 3 jours, montagne. Communauté de pairs." },
  { id: 19, cat: "tech", name: "Cybersécurité TPE", city: "Paris", country: "France", rating: 4.8, saving: "−22%", price: "premium", verified: true, img: "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&w=600&q=80", desc: "Audit RGPD + sécurisation. Pack Zayado : 990€ au lieu de 1290€." },
  { id: 20, cat: "creation", name: "Avocat Affaires", city: "Bruxelles", country: "Belgique", rating: 4.7, saving: "−15%", price: "premium", verified: true, img: "https://images.unsplash.com/photo-1505664194779-8beaceb93744?auto=format&w=600&q=80", desc: "Droit commercial belge & européen. 1h de conseil offerte." },
  { id: 21, cat: "compta", name: "Compta Solo Casablanca", city: "Casablanca", country: "Maroc", rating: 4.4, saving: "−35%", price: "economique", verified: true, img: "https://images.unsplash.com/photo-1554224311-beee460c201b?auto=format&w=600&q=80", desc: "Spécialiste TPE marocaines. Tarifs très compétitifs pour Zayado." },
  { id: 22, cat: "artisans", name: "Électricien Certifié Qualifelec", city: "Lyon", country: "France", rating: 4.8, saving: "−10%", price: "standard", verified: true, img: "https://images.unsplash.com/photo-1621905251189-08b45d6a269e?auto=format&w=600&q=80", desc: "Installation, rénovation, mise aux normes. Devis offert." },
  { id: 23, cat: "tech", name: "SEO & Contenu Pro", city: "Toulouse", country: "France", rating: 4.6, saving: "−18%", price: "standard", verified: true, img: "https://images.unsplash.com/photo-1432888622747-4eb9a8efeb07?auto=format&w=600&q=80", desc: "Audit SEO + plan éditorial 6 mois. Génération articles assistée IA." },
  { id: 24, cat: "protection", name: "Prévoyance Famille TNS", city: "Nantes", country: "France", rating: 4.7, saving: "−16%", price: "premium", verified: true, img: "https://images.unsplash.com/photo-1559757148-5c350d0d3c56?auto=format&w=600&q=80", desc: "Prévoyance décès, invalidité, IJ. Optimisation Madelin." },
];

const PRICE_TIERS = [
  { key: "economique", label: "Économique" },
  { key: "standard", label: "Standard" },
  { key: "premium", label: "Premium" },
];

const SORT_OPTIONS = [
  { key: "rating", label: "Note la plus haute" },
  { key: "saving", label: "Plus grosse économie" },
  { key: "az", label: "Ordre alphabétique" },
];

// ── Carte prestataire ─────────────────────────────────────────────────
function PartnerCard({ p }) {
  const cat = CATS.find((c) => c.key === p.cat);
  return (
    <Link to={`/partenaires/${p.id}`}
          className="group bg-white border border-[var(--zayado-border)] rounded-2xl overflow-hidden hover:shadow-lg hover:border-[var(--zayado-navy)] transition-all"
          data-testid={`partner-result-${p.id}`}>
      <div className="aspect-[4/3] overflow-hidden relative">
        <img src={p.img} alt={p.name}
             className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
        <span className="absolute top-3 left-3 px-2.5 py-1 bg-white rounded-full text-[10px] font-bold uppercase tracking-wider"
              style={{ color: NAVY }}>
          {p.saving}
        </span>
        {p.verified && (
          <span className="absolute top-3 right-3 w-7 h-7 rounded-full bg-white flex items-center justify-center" title="Vérifié Zayado">
            <ShieldCheck size={13} style={{ color: GOLD }} />
          </span>
        )}
      </div>
      <div className="p-5">
        <div className="flex items-center justify-between mb-1.5">
          <div className="text-[10px] uppercase tracking-[0.2em]" style={{ color: GOLD }}>
            {cat?.label || p.cat}
          </div>
          <div className="flex items-center gap-1 text-xs" style={{ color: NAVY }}>
            <Star size={11} fill={GOLD} style={{ color: GOLD }} />
            <span className="font-bold">{p.rating.toFixed(1)}</span>
          </div>
        </div>
        <div className="font-bold text-base mb-2 leading-tight" style={{ color: NAVY }}>{p.name}</div>
        <div className="text-xs leading-relaxed mb-3 line-clamp-2" style={{ color: MUTED }}>{p.desc}</div>
        <div className="flex items-center justify-between pt-3 border-t border-[var(--zayado-border)]">
          <span className="inline-flex items-center gap-1 text-[11px]" style={{ color: MUTED }}>
            <MapPin size={11} /> {p.city}, {p.country}
          </span>
          <span className="inline-flex items-center gap-1 text-xs font-medium group-hover:gap-2 transition-all" style={{ color: NAVY }}>
            Voir <ArrowRight size={11} />
          </span>
        </div>
      </div>
    </Link>
  );
}

// ── Page principale ──────────────────────────────────────────────────
export default function PartenairesRecherche({ embedded = false }) {
  const loc = useLocation();
  const [apiPartners, setApiPartners] = React.useState(null);

  useEffect(() => {
    api.get("/partners/search?limit=100")
      .then((r) => { if (r.data && Array.isArray(r.data) && r.data.length > 0) setApiPartners(r.data); })
      .catch(() => {});
  }, []);

  const PARTNERS_DATA = apiPartners || PARTNERS;
  const params = new URLSearchParams(loc.search);
  const initialCat = params.get("cat") || "";
  const initialQ = params.get("q") || "";

  const [query, setQuery] = useState(initialQ);
  const [activeCat, setActiveCat] = useState(initialCat);
  const [activeCountry, setActiveCountry] = useState("");
  const [activePrice, setActivePrice] = useState("");
  const [minRating, setMinRating] = useState(0);
  const [sort, setSort] = useState("rating");
  const [page, setPage] = useState(1);
  const [filtersOpen, setFiltersOpen] = useState(false);

  // Filtrage + tri
  const filtered = useMemo(() => {
    let list = PARTNERS.filter((p) => {
      if (activeCat && p.cat !== activeCat) return false;
      if (activeCountry && p.country !== activeCountry) return false;
      if (activePrice && p.price !== activePrice) return false;
      if (minRating && p.rating < minRating) return false;
      if (query) {
        const q = query.toLowerCase();
        if (!p.name.toLowerCase().includes(q) && !p.desc.toLowerCase().includes(q) && !p.city.toLowerCase().includes(q)) {
          return false;
        }
      }
      return true;
    });
    list.sort((a, b) => {
      if (sort === "rating") return b.rating - a.rating;
      if (sort === "saving") {
        const va = parseInt((a.saving || "").replace(/\D/g, "")) || 0;
        const vb = parseInt((b.saving || "").replace(/\D/g, "")) || 0;
        return vb - va;
      }
      if (sort === "az") return a.name.localeCompare(b.name);
      return 0;
    });
    return list;
  }, [activeCat, activeCountry, activePrice, minRating, query, sort]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const pageItems = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const resetFilters = () => {
    setQuery(""); setActiveCat(""); setActiveCountry("");
    setActivePrice(""); setMinRating(0); setPage(1);
  };

  const activeFiltersCount = [activeCat, activeCountry, activePrice].filter(Boolean).length + (minRating ? 1 : 0) + (query ? 1 : 0);

  return (
    <div className="min-h-screen ts-page" style={{ background: "#FFFFFF" }} data-testid="partner-search-page">
      <Helmet>
        <title>Annuaire des prestataires · Presta-Partenaire TheSustain</title>
        <meta name="description" content="Annuaire des prestataires chrétiens TheSustain : mutuelle, comptabilité, juridique, tech, BTP. Filtrez par catégorie, pays, note." />
      </Helmet>
      {!embedded && <TheSustainHeader />}

      {/* Hero compact */}
      <section className="max-w-[1400px] mx-auto px-4 md:px-6 pt-10 pb-6">
        <Link to="/partenaires" className="text-xs hover:underline inline-flex items-center gap-1 mb-4" style={{ color: MUTED }}>
          <ArrowLeft size={11} /> Retour au réseau Zayado
        </Link>
        <h1 className="font-bold mb-3"
            style={{ fontFamily: "'DM Serif Display', serif",
                     fontSize: "clamp(1.8rem, 4vw, 2.8rem)", lineHeight: 1.1, color: NAVY }}>
          Annuaire des prestataires
        </h1>
        <p className="text-sm max-w-2xl mb-6" style={{ color: MUTED }}>
          {filtered.length} prestataire{filtered.length > 1 ? "s" : ""} vérifié{filtered.length > 1 ? "s" : ""} ·
          {" "}Économie moyenne <strong style={{ color: NAVY }}>−22%</strong> pour la communauté Zayado.
        </p>

        {/* Search principal */}
        <div className="bg-white border border-[var(--zayado-border)] rounded-2xl p-3 flex flex-col md:flex-row gap-3 max-w-3xl shadow-sm">
          <div className="flex-1 relative">
            <Search size={15} className="absolute left-4 top-1/2 -translate-y-1/2" style={{ color: MUTED }} />
            <input type="text" value={query}
                   onChange={(e) => { setQuery(e.target.value); setPage(1); }}
                   placeholder="Rechercher par nom, mot-clé, ville…"
                   className="w-full pl-11 pr-3 py-3 text-sm bg-transparent focus:outline-none"
                   data-testid="search-query" />
          </div>
          <button onClick={() => setFiltersOpen(true)}
                  className="md:hidden inline-flex items-center justify-center gap-2 px-4 py-3 rounded-xl border border-[var(--zayado-border)] text-sm font-medium"
                  data-testid="filters-toggle">
            <SlidersHorizontal size={14} /> Filtres
            {activeFiltersCount > 0 && (
              <span className="ml-1 px-1.5 py-0.5 rounded-full text-[10px] text-white" style={{ background: NAVY }}>
                {activeFiltersCount}
              </span>
            )}
          </button>
        </div>
      </section>

      <div className="max-w-[1400px] mx-auto px-4 md:px-6 pb-16 grid lg:grid-cols-[260px_1fr] gap-8">
        {/* ── Sidebar filtres ──────────────────────────────────── */}
        <aside className={`${filtersOpen ? "fixed inset-0 z-50 bg-white p-6 overflow-y-auto" : "hidden lg:block"}`}
               data-testid="filters-sidebar">
          {filtersOpen && (
            <div className="flex items-center justify-between mb-5 lg:hidden">
              <div className="font-bold text-base" style={{ color: NAVY }}>Filtres</div>
              <button onClick={() => setFiltersOpen(false)} className="p-1">
                <X size={18} />
              </button>
            </div>
          )}

          <div className="space-y-7">
            {/* Catégorie */}
            <div>
              <div className="text-[11px] uppercase tracking-[0.2em] font-bold mb-3" style={{ color: NAVY }}>Catégorie</div>
              <div className="space-y-1.5">
                <button onClick={() => { setActiveCat(""); setPage(1); }}
                        className={`block w-full text-left px-3 py-1.5 rounded-lg text-sm transition-colors ${!activeCat ? "bg-[var(--zayado-navy)] text-white" : "hover:bg-white"}`}
                        style={{ color: !activeCat ? "#fff" : "var(--zayado-text)" }}
                        data-testid="filter-cat-all">
                  Toutes ({PARTNERS.length})
                </button>
                {CATS.map((c) => {
                  const n = PARTNERS.filter((p) => p.cat === c.key).length;
                  const Icon = c.icon;
                  return (
                    <button key={c.key} onClick={() => { setActiveCat(c.key); setPage(1); }}
                            className={`flex items-center justify-between w-full text-left px-3 py-1.5 rounded-lg text-sm transition-colors ${activeCat === c.key ? "bg-[var(--zayado-navy)] text-white" : "hover:bg-white"}`}
                            style={{ color: activeCat === c.key ? "#fff" : "var(--zayado-text)" }}
                            data-testid={`filter-cat-${c.key}`}>
                      <span className="inline-flex items-center gap-2">
                        <Icon size={13} /> {c.label}
                      </span>
                      <span className="text-xs opacity-70">{n}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Pays */}
            <div>
              <div className="text-[11px] uppercase tracking-[0.2em] font-bold mb-3" style={{ color: NAVY }}>Pays</div>
              <select value={activeCountry}
                      onChange={(e) => { setActiveCountry(e.target.value); setPage(1); }}
                      className="w-full px-3 py-2 border border-[var(--zayado-border)] rounded-lg text-sm bg-white focus:outline-none focus:border-[var(--zayado-navy)]"
                      data-testid="filter-country">
                <option value="">Tous les pays</option>
                {COUNTRIES.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>

            {/* Gamme tarifaire */}
            <div>
              <div className="text-[11px] uppercase tracking-[0.2em] font-bold mb-3" style={{ color: NAVY }}>Gamme</div>
              <div className="flex flex-wrap gap-2">
                <button onClick={() => { setActivePrice(""); setPage(1); }}
                        className={`px-3 py-1.5 rounded-full text-xs border ${!activePrice ? "border-[var(--zayado-navy)] bg-[var(--zayado-navy)] text-white" : "border-[var(--zayado-border)] bg-white hover:border-[var(--zayado-navy)]"}`}
                        data-testid="filter-price-all">Toutes</button>
                {PRICE_TIERS.map((t) => (
                  <button key={t.key}
                          onClick={() => { setActivePrice(t.key); setPage(1); }}
                          className={`px-3 py-1.5 rounded-full text-xs border ${activePrice === t.key ? "border-[var(--zayado-navy)] bg-[var(--zayado-navy)] text-white" : "border-[var(--zayado-border)] bg-white hover:border-[var(--zayado-navy)]"}`}
                          data-testid={`filter-price-${t.key}`}>
                    {t.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Note minimum */}
            <div>
              <div className="text-[11px] uppercase tracking-[0.2em] font-bold mb-3" style={{ color: NAVY }}>Note minimum</div>
              <div className="flex gap-1">
                {[0, 4, 4.5, 4.8].map((r) => (
                  <button key={r}
                          onClick={() => { setMinRating(r); setPage(1); }}
                          className={`flex-1 px-2 py-2 rounded-lg text-xs border inline-flex items-center justify-center gap-1 ${minRating === r ? "border-[var(--zayado-navy)] bg-[var(--zayado-navy)] text-white" : "border-[var(--zayado-border)] bg-white hover:border-[var(--zayado-navy)]"}`}
                          data-testid={`filter-rating-${r}`}>
                    {r === 0 ? "Toutes" : <>{r}+ <Star size={10} fill="currentColor" /></>}
                  </button>
                ))}
              </div>
            </div>

            {/* Reset */}
            {activeFiltersCount > 0 && (
              <button onClick={resetFilters}
                      className="w-full text-xs hover:underline text-left"
                      style={{ color: MUTED }}
                      data-testid="filters-reset">
                Réinitialiser les filtres ({activeFiltersCount})
              </button>
            )}

            {filtersOpen && (
              <button onClick={() => setFiltersOpen(false)}
                      className="lg:hidden w-full py-3 rounded-full text-white text-sm font-medium"
                      style={{ background: NAVY }}>
                Voir les {filtered.length} résultats
              </button>
            )}
          </div>
        </aside>

        {/* ── Résultats ─────────────────────────────────────────── */}
        <div>
          {/* Barre tri */}
          <div className="flex items-center justify-between mb-5 flex-wrap gap-3">
            <div className="text-sm" style={{ color: MUTED }}>
              <strong style={{ color: NAVY }}>{filtered.length}</strong> prestataire{filtered.length > 1 ? "s" : ""}
              {activeCat && <> dans <em>{CATS.find((c) => c.key === activeCat)?.label}</em></>}
            </div>
            <div className="flex items-center gap-2">
              <label className="text-xs" style={{ color: MUTED }}>Trier par</label>
              <select value={sort} onChange={(e) => setSort(e.target.value)}
                      className="px-3 py-1.5 border border-[var(--zayado-border)] rounded-lg text-sm bg-white focus:outline-none focus:border-[var(--zayado-navy)]"
                      data-testid="sort-select">
                {SORT_OPTIONS.map((o) => <option key={o.key} value={o.key}>{o.label}</option>)}
              </select>
            </div>
          </div>

          {/* Grid */}
          {pageItems.length > 0 ? (
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5" data-testid="partner-results-grid">
              {pageItems.map((p) => <PartnerCard key={p.id} p={p} />)}
            </div>
          ) : (
            <div className="bg-white border border-[var(--zayado-border)] rounded-2xl p-10 text-center" data-testid="partner-results-empty">
              <div className="text-5xl mb-3" style={{ color: GOLD }}>—</div>
              <h3 className="font-bold mb-2" style={{ color: NAVY }}>Aucun prestataire ne correspond.</h3>
              <p className="text-sm mb-5" style={{ color: MUTED }}>
                Modifiez vos filtres ou contactez-nous pour qu'on cherche pour vous.
              </p>
              <button onClick={resetFilters}
                      className="px-5 py-2.5 rounded-full text-white text-sm font-medium"
                      style={{ background: NAVY }}>
                Réinitialiser les filtres
              </button>
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-10" data-testid="partner-pagination">
              <button onClick={() => setPage(Math.max(1, page - 1))}
                      disabled={page === 1}
                      className="px-3 py-2 rounded-lg text-sm border border-[var(--zayado-border)] bg-white disabled:opacity-40 hover:border-[var(--zayado-navy)]">
                <ArrowLeft size={13} />
              </button>
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((n) => (
                <button key={n} onClick={() => setPage(n)}
                        className={`w-9 h-9 rounded-lg text-sm font-medium ${page === n ? "bg-[var(--zayado-navy)] text-white" : "bg-white border border-[var(--zayado-border)] hover:border-[var(--zayado-navy)]"}`}>
                  {n}
                </button>
              ))}
              <button onClick={() => setPage(Math.min(totalPages, page + 1))}
                      disabled={page === totalPages}
                      className="px-3 py-2 rounded-lg text-sm border border-[var(--zayado-border)] bg-white disabled:opacity-40 hover:border-[var(--zayado-navy)]">
                <ArrowRight size={13} />
              </button>
            </div>
          )}

          {/* CTA Devenir partenaire */}
          <div className="mt-12 bg-white border border-[var(--zayado-border)] rounded-2xl p-7 text-center">
            <div className="text-[11px] uppercase tracking-[0.25em] mb-2" style={{ color: GOLD }}>— Vous êtes prestataire ?</div>
            <h3 className="font-bold mb-2"
                style={{ fontFamily: "'DM Serif Display', serif",
                         fontSize: "clamp(1.4rem, 3vw, 1.9rem)", color: NAVY }}>
              Rejoignez le réseau Zayado
            </h3>
            <p className="text-sm mb-5 max-w-md mx-auto" style={{ color: MUTED }}>
              Sélection à entrée, indépendance garantie, communauté engagée et fidèle.
            </p>
            <Link to="/devenir-partenaire"
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-full text-white text-sm font-medium"
                  style={{ background: GOLD }}>
              Postuler comme partenaire <ArrowRight size={13} />
            </Link>
          </div>
        </div>
      </div>

      {!embedded && <TheSustainFooter />}
    </div>
  );
}
