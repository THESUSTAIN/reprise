/* Page Favoris /favoris — liste des produits favoris stockés en localStorage
   Hydrate les produits depuis le catalogue Boutique (Woo / mock).
   Permet de retirer un favori et d'ajouter au panier en un clic. */
import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { Heart, HeartOff, ShoppingBag, Trash2, ArrowRight } from "lucide-react";
import api from "@/lib/api";
import { getFavorites, removeFavorite, clearFavorites } from "@/lib/favorites";
import { addToCart } from "@/components/CartDrawer";

const NAVY = "var(--zayado-navy)";
const GOLD = "var(--zayado-gold)";
const MUTED = "var(--zayado-muted)";

export default function Favorites() {
  const [slugs, setSlugs] = useState(getFavorites());
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const onUpdate = () => setSlugs(getFavorites());
    window.addEventListener("zayado:favorites-updated", onUpdate);
    return () => window.removeEventListener("zayado:favorites-updated", onUpdate);
  }, []);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    api.get("/shop/products?preview=1&limit=100").then((r) => {
      if (!alive) return;
      const all = r.data.products || [];
      setProducts(all.filter((p) => slugs.includes(p.slug)));
    }).catch(() => {}).finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, [slugs]);

  return (
    <>
    <Helmet>
      <title>Mes favoris — Zayado</title>
      <meta name="robots" content="noindex, follow" />
    </Helmet>
    <div className="max-w-[1280px] mx-auto px-4 md:px-6 py-8" data-testid="favorites-page">
      <div className="flex items-center justify-between mb-7 gap-4 flex-wrap">
        <div>
          <div className="text-[11px] uppercase tracking-[0.25em] mb-1" style={{ color: GOLD }}>Vos coups de cœur</div>
          <h1 className="font-display italic"
              style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)",
                       fontSize: "clamp(1.8rem, 4vw, 2.6rem)", color: "var(--zayado-text)" }}>
            Favoris <span style={{ color: MUTED, fontStyle: "normal", fontSize: "0.6em" }}>· {slugs.length}</span>
          </h1>
        </div>
        {slugs.length > 0 && (
          <button onClick={() => { if (window.confirm("Vider tous vos favoris ?")) clearFavorites(); }}
                  className="inline-flex items-center gap-1.5 text-xs hover:underline"
                  style={{ color: MUTED }} data-testid="favorites-clear">
            <Trash2 size={12} /> Tout retirer
          </button>
        )}
      </div>

      {loading ? (
        <div className="py-20 text-center text-sm italic" style={{ color: MUTED }}>Chargement…</div>
      ) : slugs.length === 0 ? (
        <div className="text-center py-20 rounded-xl border-2 border-dashed border-[var(--zayado-border)]" data-testid="favorites-empty">
          <Heart size={36} className="mx-auto mb-3 opacity-30" />
          <div className="font-display italic text-xl mb-2" style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)" }}>
            Aucun favori pour l'instant
          </div>
          <div className="text-sm mb-6 max-w-md mx-auto" style={{ color: MUTED }}>
            Cliquez sur le ♡ d'un produit pour le retrouver ici. Vos favoris sont sauvegardés localement, même si vous fermez le navigateur.
          </div>
          <Link to="/boutique" className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full text-white font-medium text-sm btn-press"
                style={{ background: NAVY }}>
            Explorer la boutique <ArrowRight size={13} />
          </Link>
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-5">
          {products.map((p) => (
            <article key={p.slug} className="group bg-white rounded-xl overflow-hidden border border-[var(--zayado-border)] hover:shadow-md transition-shadow"
                     data-testid={`favorite-card-${p.slug}`}>
              <div className="relative aspect-square overflow-hidden bg-[var(--zayado-cream-dark)]">
                <Link to={`/boutique/${p.slug}`}>
                  <img src={p.images?.[0]?.src} alt={p.name} loading="lazy"
                       className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                </Link>
                <button onClick={() => removeFavorite(p.slug)}
                        className="absolute top-2.5 right-2.5 w-8 h-8 rounded-full bg-white shadow flex items-center justify-center hover:bg-[var(--zayado-cream)]"
                        aria-label="Retirer des favoris"
                        data-testid={`favorite-remove-${p.slug}`}>
                  <HeartOff size={14} style={{ color: "var(--zayado-red)" }} />
                </button>
              </div>
              <div className="p-4">
                {p.brand && <div className="text-[10px] uppercase tracking-wider mb-1" style={{ color: GOLD }}>{p.brand}</div>}
                <Link to={`/boutique/${p.slug}`} className="text-sm font-medium hover:underline line-clamp-2 leading-snug"
                      style={{ color: "var(--zayado-text)" }}>
                  {p.name}
                </Link>
                <div className="flex items-baseline gap-2 mt-2 mb-3">
                  <span className="text-base font-bold" style={{ color: p.on_sale ? "var(--zayado-red)" : "var(--zayado-text)" }}>
                    {parseFloat(p.price).toFixed(2)}€
                  </span>
                  {p.on_sale && parseFloat(p.regular_price) > parseFloat(p.price) && (
                    <span className="text-xs line-through" style={{ color: MUTED }}>
                      {parseFloat(p.regular_price).toFixed(2)}€
                    </span>
                  )}
                </div>
                <button onClick={() => addToCart({ slug: p.slug, name: p.name, price: p.price, image: p.images?.[0]?.src }, 1)}
                        className="w-full inline-flex items-center justify-center gap-1.5 py-2 rounded-full text-xs font-medium border hover:text-white transition-colors"
                        style={{ borderColor: NAVY, color: NAVY }}
                        onMouseEnter={(e) => { e.currentTarget.style.background = NAVY; e.currentTarget.style.color = "#fff"; }}
                        onMouseLeave={(e) => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.color = NAVY; }}
                        data-testid={`favorite-add-cart-${p.slug}`}>
                  <ShoppingBag size={12} /> Ajouter au panier
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
    </>
  );
}
