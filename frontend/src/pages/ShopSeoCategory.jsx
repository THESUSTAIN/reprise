/* Page catégorie SEO Boutique — /shop/:seoSlug

   6 catégories supportées :
   - concentration-bien-etre
   - ergonomie
   - pause-spirituelle
   - amenagement
   - mobilite-nomade
   - coffrets-thematiques

   Sections :
   1. Hero éditorial (titre + tagline + breadcrumb)
   2. "Pourquoi je crois que c'est important" (édito Zayado)
   3. Grille produits filtrée
   4. CTA retour boutique
*/
import React, { useEffect, useState } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { ChevronLeft, Heart, ShoppingBag, ArrowRight, Star, Sparkles } from "lucide-react";
import api from "@/lib/api";
import { isFavorite, toggleFavorite } from "@/lib/favorites";
import { addToCart as addToCartEvt } from "@/components/CartDrawer";
import BundleDiscountHint from "@/components/BundleDiscountHint";

const NAVY = "var(--zayado-navy)";
const GOLD = "var(--zayado-gold)";
const MUTED = "var(--zayado-muted)";

// Contenu éditorial "Pourquoi je crois que c'est important" par catégorie
// (visible sous le hero — pierre angulaire SEO + voix de marque)
const EDITORIALS = {
  "concentration-bien-etre": {
    title: "Pourquoi la concentration est devenue un luxe.",
    body: [
      "Aujourd'hui, chaque entrepreneur est interrompu en moyenne toutes les 11 minutes. Et il faut 23 minutes pour revenir dans son flux. Faites le calcul : sur 8 heures de travail, on perd presque 5h à juste essayer de se reconcentrer.",
      "Ce n'est pas vous le problème. C'est votre environnement. Les lunettes anti-lumière bleue protègent vos yeux après 6h d'écran. Le casque anti-bruit isole physiquement du chaos open-space ou café. Les huiles essentielles agissent sur le système limbique en moins de 30 secondes. Les sons binauraux entraînent vos ondes cérébrales en mode flow.",
      "Ce sont des outils. Pas des gadgets. Et ils changent vraiment la donne quand on les utilise ensemble, en rituel.",
    ],
  },
  "ergonomie": {
    title: "Votre corps, c'est votre outil de travail n°1.",
    body: [
      "Aucun entrepreneur ne risquerait son laptop. Mais tous abîment leur dos, leurs poignets, leurs cervicales — sans même s'en rendre compte. Jusqu'au jour où ça craque.",
      "L'ergonomie, ce n'est pas du confort. C'est de la prévention. Un support PC qui élève l'écran à la bonne hauteur évite 15 ans de tension cervicale. Une souris verticale soulage le canal carpien. Un repose-pieds stabilise les lombaires.",
      "Investir dans ces outils, c'est investir dans ses 30 prochaines années de travail. Et ça coûte 100 fois moins cher qu'un kiné mensuel à vie.",
    ],
  },
  "pause-spirituelle": {
    title: "Le burn-out commence quand on arrête de respirer.",
    body: [
      "L'entrepreneur moyen ne prend pas de vraie pause. Il prend des « micro-pauses Instagram » de 90 secondes qui n'apaisent rien. Le cerveau ne se régénère qu'en mode parasympathique — et ce mode-là ne s'active jamais devant un écran.",
      "Un coussin de méditation, ce n'est pas pour faire le moine. C'est une assise stable qui vous oblige à respirer profondément 10 minutes. Une bougie soja qui crépite, c'est un point d'ancrage sensoriel. Un encens palo santo, c'est un signal olfactif qui dit à votre corps « on coupe ».",
      "Les rituels sont les soft skills cachés de la productivité longue durée.",
    ],
  },
  "amenagement": {
    title: "Vous passez 2400 heures par an dans cet espace.",
    body: [
      "C'est plus que dans votre chambre. Plus que dans votre voiture. Plus qu'avec vos enfants, parfois. Et pourtant 80% des entrepreneurs n'ont jamais conscientisé l'aménagement de leur bureau.",
      "Un tapis en laine absorbe le son et fait baisser la fatigue auditive. Une plante dépolluante filtre le CO₂ et améliore la qualité du sommeil. Une horloge sans tic-tac réduit l'anxiété de fond. Une étagère en chêne ajoute du beau, et le beau apaise.",
      "Aménager son espace, c'est aménager sa journée mentale.",
    ],
  },
  "mobilite-nomade": {
    title: "Penser dans un café, c'est une compétence.",
    body: [
      "Plus d'1 entrepreneur sur 2 travaille au moins 2 jours par semaine hors de chez lui : café, coworking, train, terrasse. Le « bureau », c'est devenu un état d'esprit, plus un lieu.",
      "Mais travailler nomade demande un autre arsenal : un sac qui protège le laptop sans peser une tonne, un support pliable qui rentre dedans, une powerbank pour les longues sessions, une gourde isotherme pour ne pas vivre au café noir.",
      "Bien équipé, on devient mobile et performant. Mal équipé, on devient juste mobile et épuisé.",
    ],
  },
  "coffrets-thematiques": {
    title: "Un rituel, pas une accumulation d'objets.",
    body: [
      "On peut acheter 35 produits séparément. Ou on peut acheter un coffret qui forme un rituel complet, pensé pour fonctionner ensemble.",
      "Le Coffret Deep Work n'est pas une boîte avec 4 trucs dedans. C'est une procédure : tu mets les lunettes, tu enfiles le casque, tu lances les sons binauraux, tu te sers une tasse de matcha, et tu rentres en flow en 90 secondes. Chaque fois.",
      "Les coffrets, c'est l'antidote à la dispersion. Et c'est aussi la meilleure idée cadeau pour un proche entrepreneur.",
    ],
  },
};

function ProductCard({ p }) {
  const navigate = useNavigate();
  const [fav, setFav] = useState(isFavorite(p.id));
  const img = p.images?.[0]?.src || "";
  const onSale = p.on_sale && parseFloat(p.regular_price) > parseFloat(p.price);

  const onAdd = (e) => {
    e.stopPropagation();
    addToCartEvt({
      id: p.id, name: p.name, price: parseFloat(p.price),
      image: img, slug: p.slug, brand: p.brand,
    });
  };
  const onFav = (e) => {
    e.stopPropagation();
    toggleFavorite(p.id);
    setFav(!fav);
  };

  return (
    <article className="group relative cursor-pointer" data-testid={`seo-product-${p.slug}`}
             onClick={() => navigate(`/boutique/${p.slug}`)}>
      <div className="aspect-square rounded-xl overflow-hidden bg-[var(--zayado-cream-dark)] mb-3 relative">
        {p.badge && (
          <span className="absolute top-3 left-3 text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded text-white"
                style={{ background: p.badge.startsWith("-") ? "var(--zayado-red)" : NAVY }}>
            {p.badge}
          </span>
        )}
        <button onClick={onFav} aria-label="Favori"
                className="absolute top-3 right-3 w-9 h-9 rounded-full bg-white/90 flex items-center justify-center hover:bg-white transition">
          <Heart size={15} style={{ color: fav ? "var(--zayado-red)" : "var(--zayado-text)", fill: fav ? "var(--zayado-red)" : "none" }} />
        </button>
        {img && <img src={img} alt={p.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />}
      </div>
      {p.brand && (
        <div className="text-[10px] uppercase tracking-[0.2em] mb-1" style={{ color: GOLD }}>{p.brand}</div>
      )}
      <h3 className="text-sm font-medium mb-1 line-clamp-2 leading-snug" style={{ color: "var(--zayado-text)" }}>{p.name}</h3>
      <div className="flex items-baseline gap-2 mb-2">
        <span className="text-base font-bold" style={{ color: onSale ? "var(--zayado-red)" : "var(--zayado-text)" }}>
          {parseFloat(p.price).toFixed(2)}€
        </span>
        {onSale && (
          <span className="text-xs line-through" style={{ color: MUTED }}>
            {parseFloat(p.regular_price).toFixed(2)}€
          </span>
        )}
      </div>
      {parseFloat(p.average_rating) > 0 && (
        <div className="flex items-center gap-1 text-[11px]" style={{ color: MUTED }}>
          <Star size={11} className="fill-[var(--zayado-gold-soft)] text-[var(--zayado-gold-soft)]" />
          {p.average_rating} ({p.rating_count})
        </div>
      )}
      <button onClick={onAdd}
              className="mt-3 w-full text-xs font-semibold py-2 rounded-full border hover:bg-[var(--zayado-cream-dark)] inline-flex items-center justify-center gap-1.5 transition"
              style={{ borderColor: "var(--zayado-border)", color: "var(--zayado-text)" }}>
        <ShoppingBag size={12} /> Ajouter
      </button>
    </article>
  );
}

export default function ShopSeoCategory({ seoSlug: propSlug }) {
  const params = useParams();
  const seoSlug = propSlug || params.seoSlug || params.slug;
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const editorial = EDITORIALS[seoSlug];

  useEffect(() => {
    setLoading(true);
    api.get(`/shop/seo-categories/${seoSlug}`)
      .then((r) => setData(r.data))
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [seoSlug]);

  if (loading) {
    return (
      <div className="max-w-[1280px] mx-auto px-4 md:px-6 py-12">
        <div className="animate-pulse space-y-4">
          <div className="h-8 w-1/3 bg-[var(--zayado-cream-dark)] rounded" />
          <div className="h-32 bg-[var(--zayado-cream-dark)] rounded" />
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="max-w-[1280px] mx-auto px-4 md:px-6 py-16 text-center">
        <h1 className="text-2xl font-bold mb-3" style={{ color: NAVY }}>Catégorie introuvable</h1>
        <Link to="/boutique" className="text-sm underline" style={{ color: GOLD }}>← Retour à la boutique</Link>
      </div>
    );
  }

  return (
    <div className="max-w-[1280px] mx-auto px-4 md:px-6 py-6" data-testid={`shop-seo-${seoSlug}`}>
      <Helmet>
        <title>{`${data.name} — Boutique Zayado`}</title>
        <meta name="description" content={data.tagline} />
      </Helmet>

      {/* Breadcrumb */}
      <nav className="text-xs mb-6 flex items-center gap-1.5" style={{ color: MUTED }}>
        <Link to="/boutique" className="hover:underline inline-flex items-center gap-1">
          <ChevronLeft size={12} /> Boutique
        </Link>
        <span>/</span>
        <span style={{ color: "var(--zayado-text)" }}>{data.name}</span>
      </nav>

      {/* Hero */}
      <header className="mb-12 max-w-3xl">
        <div className="text-[11px] uppercase tracking-[0.3em] mb-3" style={{ color: GOLD }}>
          — Sélection éditoriale
        </div>
        <h1 className="font-display italic mb-4 leading-tight"
            style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)",
                     fontSize: "clamp(2rem, 5vw, 3.5rem)", color: "var(--zayado-text)" }}>
          {data.name}<span style={{ color: GOLD }}>.</span>
        </h1>
        <p className="text-base md:text-lg leading-relaxed" style={{ color: MUTED }}>
          {data.tagline}
        </p>
        <div className="mt-4 text-xs" style={{ color: MUTED }}>
          {data.count} produit{data.count > 1 ? "s" : ""} dans cette sélection
        </div>
      </header>

      {/* Édito "Pourquoi je crois que c'est important" */}
      {editorial && (
        <section className="mb-14 grid md:grid-cols-[1fr_2fr] gap-8 md:gap-12 items-start"
                 data-testid="shop-seo-editorial">
          <div>
            <div className="inline-flex items-center gap-1.5 text-[11px] uppercase tracking-[0.25em] mb-3"
                 style={{ color: GOLD }}>
              <Sparkles size={11} />
              Pourquoi j'y crois
            </div>
            <h2 className="font-display italic leading-tight"
                style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)",
                         fontSize: "clamp(1.4rem, 2.8vw, 2rem)", color: "var(--zayado-text)" }}>
              {editorial.title}
            </h2>
          </div>
          <div className="space-y-4 text-[15px] leading-relaxed" style={{ color: "var(--zayado-text)" }}>
            {editorial.body.map((p, i) => (
              <p key={i}>{p}</p>
            ))}
          </div>
        </section>
      )}

      {/* Grille produits */}
      <section className="mb-12">
        <div className="border-t border-[var(--zayado-border)] pt-8 mb-8 flex items-baseline justify-between gap-4 flex-wrap">
          <h2 className="font-display italic text-2xl"
              style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)", color: "var(--zayado-text)" }}>
            La sélection
          </h2>
          <Link to="/shop/selection" className="text-xs hover:underline inline-flex items-center gap-1"
                style={{ color: GOLD }}>
            Voir toute la boutique <ArrowRight size={11} />
          </Link>
        </div>

        {/* Bandeau "économisez sur le coffret" : on affiche un hint pour chaque
            coffret pertinent (uniquement si l'utilisateur a déjà ≥2 produits
            du bundle au panier). Le composant BundleDiscountHint se masque
            tout seul sinon. */}
        {data.products
          .filter((p) => Array.isArray(p.bundle_components) && p.bundle_components.length >= 2)
          .map((bundle) => (
            <BundleDiscountHint key={`hint-${bundle.id}`} bundle={bundle} variant="card" />
          ))}

        {data.products.length === 0 ? (
          <p className="text-sm py-8 text-center" style={{ color: MUTED }}>
            Cette catégorie sera bientôt remplie de nouveaux produits.
          </p>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5 md:gap-7">
            {data.products.map((p) => (
              <ProductCard key={p.id} p={p} />
            ))}
          </div>
        )}
      </section>

      {/* CTA retour */}
      <footer className="text-center py-10 border-t border-[var(--zayado-border)]">
        <Link to="/boutique"
              className="inline-flex items-center gap-2 text-sm font-semibold py-3 px-6 rounded-full border hover:bg-[var(--zayado-cream-dark)] transition"
              style={{ borderColor: NAVY, color: NAVY }}
              data-testid="shop-seo-back-boutique">
          <ChevronLeft size={14} /> Retour à la boutique
        </Link>
      </footer>
    </div>
  );
}
