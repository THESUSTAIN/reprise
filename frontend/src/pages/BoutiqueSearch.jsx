/* Page Recherche /boutique/recherche?q=... — filtre les produits par query
   string sur titre/brand/description.
   Comme Kiabi : la barre de recherche reste dans le header sticky en haut.
   Cette page n'a PAS de barre de recherche dédiée pour éviter le doublon. */
import React, { useEffect, useState, useMemo } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Search, ArrowRight, Heart, ShoppingBag } from "lucide-react";
import api from "@/lib/api";
import { isFavorite, toggleFavorite } from "@/lib/favorites";
import { addToCart } from "@/components/CartDrawer";

const NAVY = "var(--zayado-navy)";
const GOLD = "var(--zayado-gold)";
const MUTED = "var(--zayado-muted)";

export default function BoutiqueSearch() {
  const [sp] = useSearchParams();
  const q = (sp.get("q") || "").trim();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [, setFavTick] = useState(0);

  useEffect(() => {
    const onUpdate = () => setFavTick((t) => t + 1);
    window.addEventListener("zayado:favorites-updated", onUpdate);
    return () => window.removeEventListener("zayado:favorites-updated", onUpdate);
  }, []);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    api.get("/shop/products?preview=1&limit=100").then((r) => {
      if (alive) setProducts(r.data.products || []);
    }).catch(() => {}).finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, []);

  const results = useMemo(() => {
    if (!q) return [];
    const query = q.toLowerCase();
    return products.filter((p) => {
      const hay = `${p.name || ""} ${p.brand || ""} ${p.short_description || ""} ${(p.categories || []).map((c) => c.name).join(" ")}`.toLowerCase();
      return hay.includes(query);
    });
  }, [q, products]);

  return (
    <div className="max-w-[1280px] mx-auto px-4 md:px-6 py-8" data-testid="boutique-search">
      <div className="text-[11px] uppercase tracking-[0.25em] mb-1" style={{ color: GOLD }}>Recherche</div>
      <h1 className="font-display italic mb-2"
          style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)",
                   fontSize: "clamp(1.6rem, 3.5vw, 2.4rem)", color: "var(--zayado-text)" }}>
        {q ? <>Résultats pour <em>« {q} »</em></> : "Que cherchez-vous ?"}
      </h1>

      {loading ? (
        <div className="py-20 text-center text-sm italic" style={{ color: MUTED }}>Chargement du catalogue…</div>
      ) : !q ? (
        <div className="py-8">
          <div className="text-sm mb-4" style={{ color: MUTED }}>
            Utilisez la barre de recherche en haut de page ou explorez nos suggestions populaires :
          </div>
          <div className="flex flex-wrap gap-2">
            {["lunettes", "huile essentielle", "bougie", "méditation", "ergonomie", "encens", "lavande"].map((s) => (
              <Link key={s} to={`/boutique/recherche?q=${encodeURIComponent(s)}`}
                    className="px-3.5 py-1.5 rounded-full text-xs border border-[var(--zayado-border)] hover:bg-[var(--zayado-cream)]"
                    style={{ color: "var(--zayado-text)" }}
                    data-testid={`search-suggest-${s.replace(/\s+/g, "-")}`}>
                {s}
              </Link>
            ))}
          </div>
        </div>
      ) : results.length === 0 ? (
        <div className="text-center py-16 rounded-xl border-2 border-dashed border-[var(--zayado-border)] mt-6">
          <Search size={32} className="mx-auto mb-3 opacity-30" />
          <div className="font-display italic text-xl mb-2" style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)" }}>
            Aucun résultat pour « {q} »
          </div>
          <div className="text-sm mb-5" style={{ color: MUTED }}>
            Essayez un terme plus large depuis la barre du haut, ou explorez nos univers.
          </div>
          <Link to="/boutique" className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-full text-white text-sm font-medium btn-press"
                style={{ background: NAVY }}>
            Voir tous les produits <ArrowRight size={13} />
          </Link>
        </div>
      ) : (
        <>
          <div className="text-xs mb-6 mt-2" style={{ color: MUTED }} data-testid="search-count">
            {results.length} résultat{results.length > 1 ? "s" : ""}
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-5">
            {results.map((p) => {
              const fav = isFavorite(p.slug);
              return (
                <article key={p.slug} className="group bg-white rounded-xl overflow-hidden border border-[var(--zayado-border)] hover:shadow-md transition-shadow"
                         data-testid={`search-result-${p.slug}`}>
                  <div className="relative aspect-square overflow-hidden bg-[var(--zayado-cream-dark)]">
                    <Link to={`/boutique/${p.slug}`}>
                      <img src={p.images?.[0]?.src} alt={p.name} loading="lazy"
                           className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                    </Link>
                    <button onClick={() => toggleFavorite(p.slug)}
                            className="absolute top-2.5 right-2.5 w-8 h-8 rounded-full bg-white shadow flex items-center justify-center hover:bg-[var(--zayado-cream)]"
                            aria-label={fav ? "Retirer des favoris" : "Ajouter aux favoris"}
                            data-testid={`search-fav-${p.slug}`}>
                      <Heart size={14} style={{ color: fav ? "var(--zayado-red)" : "var(--zayado-text)", fill: fav ? "var(--zayado-red)" : "none" }} />
                    </button>
                  </div>
                  <div className="p-4">
                    {p.brand && <div className="text-[10px] uppercase tracking-wider mb-1" style={{ color: GOLD }}>{p.brand}</div>}
                    <Link to={`/boutique/${p.slug}`} className="text-sm font-medium hover:underline line-clamp-2 leading-snug" style={{ color: "var(--zayado-text)" }}>
                      {p.name}
                    </Link>
                    <div className="flex items-baseline gap-2 mt-2 mb-3">
                      <span className="text-base font-bold" style={{ color: p.on_sale ? "var(--zayado-red)" : "var(--zayado-text)" }}>
                        {parseFloat(p.price).toFixed(2)}€
                      </span>
                      {p.on_sale && parseFloat(p.regular_price) > parseFloat(p.price) && (
                        <span className="text-xs line-through" style={{ color: MUTED }}>{parseFloat(p.regular_price).toFixed(2)}€</span>
                      )}
                    </div>
                    <button onClick={() => addToCart({ slug: p.slug, name: p.name, price: p.price, image: p.images?.[0]?.src }, 1)}
                            className="w-full inline-flex items-center justify-center gap-1.5 py-2 rounded-full text-xs font-medium text-white btn-press"
                            style={{ background: NAVY }}>
                      <ShoppingBag size={12} /> Ajouter
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
