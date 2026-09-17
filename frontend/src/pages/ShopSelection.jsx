/* /shop/selection — Toute la sélection (design d'origine demandé par l'utilisateur)
   Réutilise <AllProductsGrid /> exporté depuis Boutique.jsx : sidebar filtres
   (Prix, Marques, Note minimum, En stock uniquement) + grille produits avec
   badges (BEST-SELLER, ÉCO, BIO, %, etc.), notes étoiles, coloris.
*/
import React, { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { ArrowLeft, Loader2, Search, X } from "lucide-react";
import api from "@/lib/api";
import { AllProductsGrid } from "@/pages/Boutique";

const NAVY = "var(--zayado-navy)";
const MUTED = "var(--zayado-muted)";
const GOLD = "var(--zayado-gold)";

const CART_KEY = "zay_cart";

function getCart() {
  try { return JSON.parse(localStorage.getItem(CART_KEY) || "[]"); } catch { return []; }
}
function saveCart(items) {
  localStorage.setItem(CART_KEY, JSON.stringify(items));
  try { window.dispatchEvent(new CustomEvent("zay-cart-updated")); } catch {}
}

export default function ShopSelection() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [cart, setCart] = useState(getCart());
  const navigate = useNavigate();
  const loc = useLocation();
  // Initial query depuis ?q=
  const initialQ = new URLSearchParams(loc.search).get("q") || "";
  const [query, setQuery] = useState(initialQ);

  useEffect(() => {
    api.get("/shop/products?limit=100&preview=1")
      .then((r) => {
        const data = r.data || {};
        const raw = Array.isArray(data) ? data : (data.products || []);
        setProducts(raw);
      })
      .finally(() => setLoading(false));
  }, []);

  // Filtre instantané sur nom + marque + description + catégorie
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return products;
    return products.filter((p) => {
      const haystack = [
        p.name, p.title, p.brand, p.short_description,
        ...(p.categories || []).map((c) => c.name || c.slug || ""),
      ].filter(Boolean).join(" ").toLowerCase();
      return haystack.includes(q);
    });
  }, [products, query]);

  // Submit → met à jour l'URL avec ?q=...
  const onSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      navigate(`/shop/selection?q=${encodeURIComponent(query.trim())}`, { replace: true });
    } else {
      navigate("/shop/selection", { replace: true });
    }
  };
  const clearQuery = () => {
    setQuery("");
    navigate("/shop/selection", { replace: true });
  };

  const addToCart = (p) => {
    const next = [...cart];
    const idx = next.findIndex((x) => x.slug === p.slug);
    if (idx >= 0) next[idx].qty += 1;
    else next.push({ slug: p.slug, title: p.title || p.name, price_eur: p.price_eur || p.price, image_url: p.image_url || (p.images && p.images[0]?.src), qty: 1 });
    setCart(next);
    saveCart(next);
  };

  return (
    <div className="min-h-screen bg-[var(--zayado-cream)]" data-testid="shop-selection-page">
      <Helmet>
        <title>Toute la sélection · Zayado Shop</title>
        <meta name="description" content="Toute la sélection Zayado : filtrez par prix, marque, note et disponibilité." />
      </Helmet>

      <div className="max-w-[1280px] mx-auto px-4 md:px-6 pt-8 pb-4">
        <Link to="/boutique" className="text-xs inline-flex items-center gap-1.5 hover:underline mb-4"
              style={{ color: MUTED }}>
          <ArrowLeft size={12} /> Retour à la boutique
        </Link>

        {/* Barre de recherche — filtre instantané sur nom, marque, catégorie */}
        <form onSubmit={onSubmit} className="mb-2" data-testid="shop-selection-search-form">
          <div className="relative max-w-2xl">
            <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none"
                    style={{ color: MUTED }} />
            <input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Rechercher un produit, une marque, une catégorie…"
              data-testid="shop-selection-search-input"
              className="w-full pl-11 pr-12 py-3 text-sm rounded-full border focus:outline-none focus:ring-2 focus:ring-[var(--zayado-gold)] bg-white"
              style={{ borderColor: "var(--zayado-border)", color: "var(--zayado-text)" }}
            />
            {query && (
              <button type="button" onClick={clearQuery}
                      aria-label="Effacer la recherche"
                      data-testid="shop-selection-search-clear"
                      className="absolute right-3 top-1/2 -translate-y-1/2 w-7 h-7 rounded-full inline-flex items-center justify-center hover:bg-[var(--zayado-cream-dark)]"
                      style={{ color: MUTED }}>
                <X size={13} />
              </button>
            )}
          </div>
          {query && !loading && (
            <p className="text-xs mt-2" style={{ color: MUTED }} data-testid="shop-selection-search-count">
              {filtered.length} résultat{filtered.length > 1 ? "s" : ""} pour
              <span style={{ color: GOLD, fontWeight: 600 }}> « {query} »</span>
            </p>
          )}
        </form>
      </div>

      <div className="max-w-[1280px] mx-auto px-4 md:px-6 pb-20">
        {loading ? (
          <div className="py-20 flex items-center justify-center">
            <Loader2 size={28} className="animate-spin" style={{ color: NAVY }} />
          </div>
        ) : filtered.length === 0 ? (
          <div className="py-20 text-center" data-testid="shop-selection-empty">
            <p className="text-sm mb-4" style={{ color: MUTED }}>
              Aucun produit ne correspond à <span style={{ color: GOLD }}>« {query} »</span>.
            </p>
            <button onClick={clearQuery}
                    className="text-xs font-semibold px-4 py-2 rounded-full border hover:bg-white"
                    style={{ borderColor: NAVY, color: NAVY }}>
              Voir tous les produits
            </button>
          </div>
        ) : (
          <AllProductsGrid products={filtered} onAdd={addToCart} />
        )}
      </div>
    </div>
  );
}
