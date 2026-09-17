/* BundleDiscountHint — picto "Économisez X% en prenant le coffret"

   Logique : on lit le panier (zay_cart). Si l'utilisateur a déjà 2 produits
   ou plus de la liste `bundleComponents` du coffret, on affiche un badge
   coloré incitant à remplacer ses produits individuels par le coffret.

   Calcul :
   - On somme le prix des produits individuels au panier qui font partie
     du bundle.
   - On compare au prix du coffret.
   - On affiche le % d'économie + un CTA "Remplacer par le coffret".

   Plug : utilisé sur la fiche produit coffret + sur la carte coffret
   de la page /shop/coffrets-thematiques.
*/
import React, { useEffect, useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { Sparkles, ArrowRight } from "lucide-react";
import { addToCart as addToCartEvt } from "@/components/CartDrawer";

const NAVY = "var(--zayado-navy)";
const GOLD = "var(--zayado-gold)";

function readCart() {
  try { return JSON.parse(localStorage.getItem("zay_cart") || "[]"); }
  catch { return []; }
}

export default function BundleDiscountHint({ bundle, variant = "card" }) {
  const navigate = useNavigate();
  const [cart, setCart] = useState(readCart);

  useEffect(() => {
    const refresh = () => setCart(readCart());
    window.addEventListener("zayado:cart-updated", refresh);
    return () => window.removeEventListener("zayado:cart-updated", refresh);
  }, []);

  const stats = useMemo(() => {
    const ids = new Set((bundle?.bundle_components || []).map(String));
    if (ids.size === 0) return { matched: 0, savedPct: 0, savedAmount: 0 };
    // Le panier stocke id en number ou string selon l'origine → on normalise
    const matched = cart.filter((it) => ids.has(String(it.id))).length;
    if (matched < 2) return { matched, savedPct: 0, savedAmount: 0 };

    const regular = parseFloat(bundle.regular_price || bundle.price);
    const price = parseFloat(bundle.price);
    const savedAmount = Math.max(0, regular - price);
    const savedPct = regular > 0 ? Math.round((savedAmount / regular) * 100) : 0;
    return { matched, savedPct, savedAmount };
  }, [cart, bundle]);

  if (stats.matched < 2 || stats.savedPct === 0) return null;

  const goToBundle = () => {
    navigate(`/boutique/${bundle.slug}`);
  };

  const addBundle = (e) => {
    e.stopPropagation();
    addToCartEvt({
      id: bundle.id, name: bundle.name, price: parseFloat(bundle.price),
      image: bundle.images?.[0]?.src, slug: bundle.slug, brand: bundle.brand,
    });
  };

  if (variant === "compact") {
    return (
      <button onClick={goToBundle}
              data-testid={`bundle-hint-compact-${bundle.slug}`}
              className="inline-flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full text-white"
              style={{ background: GOLD }}>
        <Sparkles size={9} />
        -{stats.savedPct}% avec le coffret
      </button>
    );
  }

  // variant === "card" — bandeau riche
  return (
    <div className="rounded-xl p-4 md:p-5 mb-4 relative overflow-hidden"
         data-testid={`bundle-hint-card-${bundle.slug}`}
         style={{ background: "linear-gradient(135deg, #1a3a6e 0%, #2d5391 100%)", color: "#fff" }}>
      <div className="flex items-start gap-3 md:gap-4">
        <div className="shrink-0 w-10 h-10 rounded-full flex items-center justify-center"
             style={{ background: "rgba(212,175,55,0.25)" }}>
          <Sparkles size={18} style={{ color: "#f0d488" }} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-[10px] uppercase tracking-[0.2em] mb-1" style={{ color: "#f0d488" }}>
            Vous économisez gros
          </div>
          <p className="text-sm md:text-[15px] leading-snug mb-3">
            Vous avez déjà <strong>{stats.matched} produit{stats.matched > 1 ? "s" : ""}</strong> de ce coffret au panier.
            <br />Prenez le coffret entier et économisez <strong>{stats.savedAmount.toFixed(0)}€ (-{stats.savedPct}%)</strong>.
          </p>
          <div className="flex flex-wrap gap-2">
            <button onClick={addBundle}
                    data-testid={`bundle-hint-cta-${bundle.slug}`}
                    className="inline-flex items-center gap-1.5 text-xs font-bold px-4 py-2 rounded-full transition"
                    style={{ background: "#f0d488", color: "#1a3a6e" }}>
              Ajouter le coffret au panier <ArrowRight size={11} />
            </button>
            <button onClick={goToBundle}
                    className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-2 rounded-full hover:bg-white/10 transition"
                    style={{ color: "rgba(255,255,255,0.85)" }}>
              Voir le coffret
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
