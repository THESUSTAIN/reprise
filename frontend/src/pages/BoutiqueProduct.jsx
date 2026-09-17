/* Page détail produit /boutique/:slug — galerie + description + variantes + ajout panier + cross-sell + favoris */
import React, { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import {
  ChevronLeft, ShoppingBag, Heart, Star, Truck, ShieldCheck,
  RotateCcw, Leaf, ChevronDown, Check, Share,
} from "lucide-react";
import api from "@/lib/api";
import { isFavorite, toggleFavorite } from "@/lib/favorites";
import { addToCart as addToCartEvt } from "@/components/CartDrawer";
import VirtualTryOn from "@/components/VirtualTryOn";
import Product3DViewer from "@/components/Product3DViewer";
import BundleDiscountHint from "@/components/BundleDiscountHint";

const NAVY = "var(--zayado-navy)";
const GOLD = "var(--zayado-gold)";
const MUTED = "var(--zayado-muted)";

export default function BoutiqueProduct() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const [p, setP] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeImg, setActiveImg] = useState(0);
  const [qty, setQty] = useState(1);
  const [openSection, setOpenSection] = useState("desc");
  const [added, setAdded] = useState(false);
  const [fav, setFav] = useState(false);
  const [crossSell, setCrossSell] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [matchingBundles, setMatchingBundles] = useState([]);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setActiveImg(0);
    api.get(`/shop/products/${slug}?preview=1`).then((r) => {
      if (alive) setP(r.data);
    }).catch(() => {
      api.get(`/shop/products?preview=1`).then((r) => {
        if (alive) setP((r.data.products || []).find((x) => x.slug === slug) || null);
      });
    }).finally(() => { if (alive) setLoading(false); });
    // Charge les autres produits pour cross-sell
    api.get(`/shop/products?preview=1&limit=24`).then((r) => {
      if (alive) setCrossSell((r.data.products || []).filter((x) => x.slug !== slug));
    }).catch(() => {});
    // Reviews WooCommerce (optionnel, échoue silencieusement en mock)
    api.get(`/shop/products/${slug}/reviews?preview=1`).then((r) => {
      if (alive) setReviews(r.data.reviews || []);
    }).catch(() => { if (alive) setReviews([]); });
    // Coffrets contenant ce produit (pour suggestion bundle discount)
    api.get(`/shop/seo-categories/coffrets-thematiques`).then((r) => {
      if (!alive) return;
      const bundles = (r.data?.products || []).filter((b) =>
        Array.isArray(b.bundle_components) &&
        // matching par id : le produit courant doit être dans bundle_components
        // (on attend que setP soit fait, donc on relit via la prochaine maj)
        true
      );
      setMatchingBundles(bundles);
    }).catch(() => {});
    return () => { alive = false; };
  }, [slug]);

  useEffect(() => { setFav(isFavorite(slug)); }, [slug]);
  useEffect(() => {
    const onUpdate = () => setFav(isFavorite(slug));
    window.addEventListener("zayado:favorites-updated", onUpdate);
    return () => window.removeEventListener("zayado:favorites-updated", onUpdate);
  }, [slug]);

  if (loading) return <div className="min-h-[60vh] flex items-center justify-center text-sm italic" style={{ color: MUTED }} data-testid="product-loading">Chargement…</div>;
  if (!p) return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center" data-testid="product-404">
      <div className="text-sm mb-3" style={{ color: MUTED }}>Produit introuvable.</div>
      <Link to="/boutique" className="px-4 py-2 rounded-full text-white text-sm" style={{ background: NAVY }}>Retour à la boutique</Link>
    </div>
  );

  const img = p.images?.[activeImg]?.src || p.images?.[0]?.src;
  const onSale = p.on_sale && parseFloat(p.regular_price) > parseFloat(p.price);
  const stock = p.stock_quantity || 0;

  const addToCart = () => {
    addToCartEvt({ slug: p.slug, name: p.name, price: p.price, image: p.images?.[0]?.src }, qty);
    setAdded(true);
    setTimeout(() => setAdded(false), 2000);
  };

  const onShare = async () => {
    const url = window.location.href;
    if (navigator.share) {
      try { await navigator.share({ title: p.name, url }); } catch {}
    } else {
      try { await navigator.clipboard.writeText(url); } catch {}
    }
  };

  // Sélection cross-sell : 4 produits du même univers, slug différent
  const suggestions = crossSell
    .filter((x) => x.universe === p.universe)
    .slice(0, 4);
  // Si pas assez dans même univers, compléter avec n'importe quoi
  if (suggestions.length < 4) {
    const fill = crossSell.filter((x) => !suggestions.find((s) => s.slug === x.slug)).slice(0, 4 - suggestions.length);
    suggestions.push(...fill);
  }

  // Détection auto features visuelles selon le produit
  const prodSlug = (p.slug || "").toLowerCase();
  const name = (p.name || "").toLowerCase();
  const isEyewear = /lunette|lunettes|vue|glasses|verre|optique/.test(prodSlug + " " + name);
  // model3d_url peut venir des meta data WooCommerce ; pour l'instant on
  // permet l'override via une convention de chemin local /models3d/{slug}.glb
  const model3dUrl = p.model_3d_url || p.model3d || (p.has_3d ? `/models3d/${prodSlug}.glb` : null);
  const has3D = Boolean(model3dUrl);

  // Si la galerie réelle a < 2 images, on génère 3 vues à partir de la même
  // image pour conserver le pattern visuel d'une galerie (la prod WP gère vraiment plusieurs images).
  const gallery = (p.images && p.images.length > 1)
    ? p.images
    : (p.images && p.images.length === 1 ? [p.images[0], p.images[0], p.images[0]] : []);

  return (
    <div className="max-w-[1280px] mx-auto px-4 md:px-6 py-6" data-testid="boutique-product">
      {/* Breadcrumb */}
      <nav className="text-xs mb-6 flex items-center gap-1.5" style={{ color: MUTED }}>
        <Link to="/boutique" className="hover:underline inline-flex items-center gap-1">
          <ChevronLeft size={12} /> Boutique
        </Link>
        <span>/</span>
        <Link to={`/boutique?u=${p.universe}`} className="hover:underline capitalize">{p.universe === "ame" ? "Âme" : "Corps"}</Link>
        <span>/</span>
        <span className="line-clamp-1" style={{ color: "var(--zayado-text)" }}>{p.name}</span>
      </nav>

      <div className="grid md:grid-cols-2 gap-8 md:gap-12">
        {/* Galerie ou viewer 3D si modèle disponible */}
        <div data-testid="product-gallery">
          {has3D ? (
            <Product3DViewer modelUrl={model3dUrl} productName={p.name} fallbackImages={gallery} />
          ) : (
            <>
              <div className="aspect-square rounded-xl overflow-hidden bg-[var(--zayado-cream-dark)] mb-3">
                <img src={img} alt={p.name} className="w-full h-full object-cover" />
              </div>
              {gallery.length > 1 && (
                <div className="flex gap-2 overflow-x-auto no-scrollbar">
                  {gallery.map((i, idx) => (
                    <button key={idx} onClick={() => setActiveImg(idx)}
                            className="w-16 h-16 rounded overflow-hidden border-2 shrink-0 transition-all"
                            style={{ borderColor: idx === activeImg ? NAVY : "var(--zayado-border)" }}
                            data-testid={`product-thumb-${idx}`}>
                      <img src={i.src} alt="" className="w-full h-full object-cover" />
                    </button>
                  ))}
                </div>
              )}
            </>
          )}
        </div>

        {/* Infos */}
        <div data-testid="product-info">
          {p.brand && (
            <div className="text-xs uppercase tracking-[0.25em] mb-2" style={{ color: GOLD }}>{p.brand}</div>
          )}
          <h1 className="font-display italic mb-3 leading-tight"
              style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)",
                       fontSize: "clamp(1.7rem, 3.5vw, 2.6rem)", color: "var(--zayado-text)" }}>
            {p.name}
          </h1>

          {/* Rating */}
          {parseFloat(p.average_rating) > 0 && (
            <div className="flex items-center gap-2 mb-4">
              <div className="flex">
                {[1,2,3,4,5].map((n) => (
                  <Star key={n} size={14} className="fill-[var(--zayado-gold-soft)] text-[var(--zayado-gold-soft)]" />
                ))}
              </div>
              <span className="text-sm font-medium">{p.average_rating}</span>
              <span className="text-xs" style={{ color: MUTED }}>({p.rating_count} avis vérifiés)</span>
            </div>
          )}

          {/* Prix */}
          <div className="flex items-baseline gap-3 mb-2">
            <span className="text-3xl font-bold" style={{ color: onSale ? "var(--zayado-red)" : "var(--zayado-text)" }}>
              {parseFloat(p.price).toFixed(2)}€
            </span>
            {onSale && (
              <span className="text-lg line-through" style={{ color: MUTED }}>
                {parseFloat(p.regular_price).toFixed(2)}€
              </span>
            )}
            {onSale && (
              <span className="text-xs px-2 py-0.5 rounded font-bold text-white" style={{ background: "var(--zayado-red)" }}>
                −{Math.round((1 - parseFloat(p.price) / parseFloat(p.regular_price)) * 100)}%
              </span>
            )}
          </div>
          <div className="text-xs mb-5" style={{ color: MUTED }}>
            TVA incluse · Livraison calculée au checkout
          </div>

          {/* Short desc */}
          {p.short_description && (
            <p className="text-sm md:text-base mb-5 leading-relaxed" style={{ color: "var(--zayado-text)" }}>
              {p.short_description}
            </p>
          )}

          {/* Variantes (swatches) */}
          <div className="mb-5">
            <div className="text-xs font-medium mb-2" style={{ color: MUTED }}>Coloris · 3 disponibles</div>
            <div className="flex gap-2">
              {["#1f3a5f", "#c2a96a", "#d4d0c4"].map((c, i) => (
                <button key={i}
                        className="w-9 h-9 rounded-full border-2 hover:scale-110 transition-transform"
                        style={{ background: c, borderColor: i === 0 ? NAVY : "var(--zayado-border)" }}
                        aria-label={`Coloris ${i+1}`} />
              ))}
            </div>
          </div>

          {/* Stock + Quantité */}
          <div className="flex items-center gap-3 mb-5">
            <div className="text-xs font-medium" style={{ color: MUTED }}>Quantité</div>
            <div className="flex items-center border border-[var(--zayado-border)] rounded-full">
              <button onClick={() => setQty(Math.max(1, qty - 1))} className="px-3 py-1.5 hover:bg-[var(--zayado-cream-dark)] rounded-l-full">−</button>
              <span className="px-4 text-sm font-medium">{qty}</span>
              <button onClick={() => setQty(qty + 1)} className="px-3 py-1.5 hover:bg-[var(--zayado-cream-dark)] rounded-r-full">+</button>
            </div>
            <div className="text-xs" style={{ color: stock > 10 ? "#2d6a2d" : "var(--zayado-red)" }}>
              {stock > 10 ? `En stock (${stock})` : `Plus que ${stock} en stock`}
            </div>
          </div>

          {/* CTAs */}
          <div className="flex gap-2 mb-5">
            <button onClick={addToCart}
                    className="flex-1 inline-flex items-center justify-center gap-2 py-3.5 rounded-full text-white font-medium btn-press"
                    style={{ background: NAVY }} data-testid="product-add-cart">
              {added ? <><Check size={16} /> Ajouté au panier !</> : <><ShoppingBag size={16} /> Ajouter au panier</>}
            </button>
            <button onClick={() => toggleFavorite(p.slug)}
                    className="w-12 h-12 rounded-full border flex items-center justify-center transition-colors"
                    style={{ borderColor: fav ? "var(--zayado-red)" : "var(--zayado-border)",
                             background: fav ? "var(--zayado-gold-bg)" : "transparent" }}
                    aria-label={fav ? "Retirer des favoris" : "Ajouter aux favoris"}
                    data-testid="product-fav">
              <Heart size={18} style={{ color: fav ? "var(--zayado-red)" : "var(--zayado-text)", fill: fav ? "var(--zayado-red)" : "none" }} />
            </button>
            <button onClick={onShare}
                    className="w-12 h-12 rounded-full border border-[var(--zayado-border)] flex items-center justify-center hover:bg-[var(--zayado-cream-dark)]"
                    aria-label="Partager"
                    data-testid="product-share">
              <Share size={16} />
            </button>
          </div>

          {/* Trust signals */}
          <div className="grid grid-cols-2 gap-2 mb-5 text-xs">
            <div className="flex items-center gap-1.5" style={{ color: MUTED }}><Truck size={14} style={{ color: GOLD }} /> Livraison offerte dès 50€</div>
            <div className="flex items-center gap-1.5" style={{ color: MUTED }}><RotateCcw size={14} style={{ color: GOLD }} /> Retours gratuits 30j</div>
            <div className="flex items-center gap-1.5" style={{ color: MUTED }}><ShieldCheck size={14} style={{ color: GOLD }} /> Paiement sécurisé</div>
            <div className="flex items-center gap-1.5" style={{ color: MUTED }}><Leaf size={14} style={{ color: GOLD }} /> Production locale</div>
          </div>

          {/* Bundle hints — affichés uniquement si ce produit fait partie
              d'un coffret ET que ≥2 produits du coffret sont au panier */}
          {matchingBundles
            .filter((b) => (b.bundle_components || []).map(String).includes(String(p.id)))
            .map((b) => (
              <BundleDiscountHint key={`bh-${b.id}`} bundle={b} variant="card" />
            ))}

          {/* Essai virtuel — affiché uniquement sur les lunettes */}
          {isEyewear && (
            <div className="mb-5" data-testid="product-tryon">
              <VirtualTryOn productName={p.name} productSlug={p.slug} />
            </div>
          )}

          {/* Sections déroulantes */}
          <div className="border-t border-[var(--zayado-border)]">
            {[
              { k: "desc", label: "Description", content: p.short_description || "Description complète à venir." },
              { k: "compo", label: "Composition & origine", content: "Production française · Matériaux durables · Petite série." },
              { k: "livr", label: "Livraison & retours", content: "Expédition 24-48h · Livraison France 4.90€ (offerte dès 50€) · Retours 30 jours gratuits." },
              { k: "avis", label: `Avis (${reviews.length || p.rating_count || 0})`, content: "Voir tous les avis vérifiés ci-dessous." },
            ].map((s) => (
              <div key={s.k} className="border-b border-[var(--zayado-border)]">
                <button onClick={() => setOpenSection(openSection === s.k ? null : s.k)}
                        className="w-full flex items-center justify-between py-3.5 text-sm font-medium"
                        style={{ color: "var(--zayado-text)" }}
                        data-testid={`product-section-${s.k}`}>
                  {s.label}
                  <ChevronDown size={16} className="transition-transform" style={{ transform: openSection === s.k ? "rotate(180deg)" : "rotate(0)" }} />
                </button>
                {openSection === s.k && (
                  <div className="pb-4 text-sm leading-relaxed" style={{ color: MUTED }}>
                    {s.content}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Avis clients réels (WooCommerce reviews) */}
      {reviews.length > 0 && (
        <section className="mt-14 pt-10 border-t border-[var(--zayado-border)]" data-testid="product-reviews">
          <div className="flex items-baseline justify-between mb-6 gap-4 flex-wrap">
            <div>
              <div className="text-[11px] uppercase tracking-[0.25em] mb-1" style={{ color: GOLD }}>Avis clients vérifiés</div>
              <h2 className="font-display italic"
                  style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)",
                           fontSize: "clamp(1.5rem, 3vw, 2rem)", color: "var(--zayado-text)" }}>
                Ce qu'en disent <em>les clients.</em>
              </h2>
            </div>
            {parseFloat(p.average_rating) > 0 && (
              <div className="flex items-center gap-2">
                <div className="flex">
                  {[1,2,3,4,5].map((n) => (
                    <Star key={n} size={16} className="fill-[var(--zayado-gold-soft)] text-[var(--zayado-gold-soft)]" />
                  ))}
                </div>
                <span className="text-sm font-bold">{p.average_rating}/5</span>
                <span className="text-xs" style={{ color: MUTED }}>· {reviews.length} avis</span>
              </div>
            )}
          </div>
          <div className="grid md:grid-cols-2 gap-4">
            {reviews.slice(0, 6).map((rv, i) => (
              <article key={i} className="bg-white rounded-xl p-5 border border-[var(--zayado-border)]" data-testid={`product-review-${i}`}>
                <div className="flex items-center justify-between mb-2.5">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold"
                         style={{ background: "var(--zayado-gold-bg)", color: GOLD }}>
                      {(rv.reviewer || "?")[0].toUpperCase()}
                    </div>
                    <div>
                      <div className="text-sm font-medium" style={{ color: "var(--zayado-text)" }}>{rv.reviewer || "Client"}</div>
                      <div className="text-[10px]" style={{ color: MUTED }}>
                        {rv.date_created ? new Date(rv.date_created).toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" }) : ""}
                      </div>
                    </div>
                  </div>
                  <div className="flex">
                    {[1,2,3,4,5].map((n) => (
                      <Star key={n} size={11} className={n <= (rv.rating || 0) ? "fill-[var(--zayado-gold-soft)] text-[var(--zayado-gold-soft)]" : "text-[var(--zayado-border)]"} />
                    ))}
                  </div>
                </div>
                <div className="text-sm leading-relaxed" style={{ color: "var(--zayado-text)" }}
                     dangerouslySetInnerHTML={{ __html: (rv.review || "").replace(/<\/?(p|br)[^>]*>/gi, " ").trim() }} />
              </article>
            ))}
          </div>
        </section>
      )}

      {/* Cross-sell "On vous suggère" */}
      {suggestions.length > 0 && (
        <section className="mt-14 pt-10 border-t border-[var(--zayado-border)]" data-testid="product-cross-sell">
          <div className="text-[11px] uppercase tracking-[0.25em] mb-1" style={{ color: GOLD }}>Pour compléter votre rituel</div>
          <h2 className="font-display italic mb-6"
              style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)",
                       fontSize: "clamp(1.5rem, 3vw, 2rem)", color: "var(--zayado-text)" }}>
            On vous <em>suggère.</em>
          </h2>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {suggestions.map((s) => (
              <Link key={s.slug} to={`/boutique/${s.slug}`} className="group bg-white rounded-xl overflow-hidden border border-[var(--zayado-border)] hover:shadow-md transition-shadow block"
                    data-testid={`cross-sell-${s.slug}`}>
                <div className="aspect-square overflow-hidden bg-[var(--zayado-cream-dark)]">
                  <img src={s.images?.[0]?.src} alt={s.name} loading="lazy"
                       className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                </div>
                <div className="p-3">
                  {s.brand && <div className="text-[10px] uppercase tracking-wider mb-0.5" style={{ color: GOLD }}>{s.brand}</div>}
                  <div className="text-xs font-medium line-clamp-2 leading-snug" style={{ color: "var(--zayado-text)" }}>{s.name}</div>
                  <div className="text-sm font-bold mt-1.5" style={{ color: s.on_sale ? "var(--zayado-red)" : "var(--zayado-text)" }}>
                    {parseFloat(s.price).toFixed(2)}€
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
