/* Cart Drawer — drawer slide-in droite qui s'ouvre automatiquement quand un
   produit est ajouté au panier. Écoute l'event global `zayado:cart-add`.
   - Progress bar "Livraison offerte dès 50€" + montant restant
   - 2 CTAs : "Continuer mes achats" (ferme le drawer) vs "Passer commande"
   - Persistance via `zay_cart` localStorage
   - Auto-close après 5s d'inactivité (option) */
import React, { useEffect, useState, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import { X, ShoppingBag, Plus, Minus, Trash2, ArrowRight, Truck, Check } from "lucide-react";

const NAVY = "var(--zayado-navy)";
const GOLD = "var(--zayado-gold)";
const MUTED = "var(--zayado-muted)";
const FREE_SHIP_THRESHOLD = 50;

function readCart() {
  try { return JSON.parse(localStorage.getItem("zay_cart") || "[]"); } catch { return []; }
}
function writeCart(c) {
  localStorage.setItem("zay_cart", JSON.stringify(c));
  window.dispatchEvent(new CustomEvent("zayado:cart-updated", { detail: { count: c.reduce((s, it) => s + it.quantity, 0) } }));
}

export default function CartDrawer() {
  const [open, setOpen] = useState(false);
  const [cart, setCart] = useState(readCart);
  const [justAdded, setJustAdded] = useState(null); // slug du dernier ajouté pour mini-toast
  const navigate = useNavigate();

  const refresh = useCallback(() => setCart(readCart()), []);

  useEffect(() => {
    const onAdd = (e) => {
      // event detail: { product: {slug,name,price,image}, quantity }
      const { product, quantity = 1 } = e.detail || {};
      if (!product || !product.slug) return;
      const next = readCart();
      const ex = next.find((it) => it.slug === product.slug);
      if (ex) ex.quantity += quantity;
      else next.push({ slug: product.slug, name: product.name, price: product.price, image: product.image, quantity });
      writeCart(next);
      setCart(next);
      setJustAdded(product.slug);
      setOpen(true);
      setTimeout(() => setJustAdded(null), 2500);
    };
    const onOpen = () => setOpen(true);
    const onClose = () => setOpen(false);
    window.addEventListener("zayado:cart-add", onAdd);
    window.addEventListener("zayado:cart-open", onOpen);
    window.addEventListener("zayado:cart-close", onClose);
    window.addEventListener("zayado:cart-updated", refresh);
    return () => {
      window.removeEventListener("zayado:cart-add", onAdd);
      window.removeEventListener("zayado:cart-open", onOpen);
      window.removeEventListener("zayado:cart-close", onClose);
      window.removeEventListener("zayado:cart-updated", refresh);
    };
  }, [refresh]);

  // Bloque le scroll body quand ouvert
  useEffect(() => {
    if (open) {
      const prev = document.body.style.overflow;
      document.body.style.overflow = "hidden";
      return () => { document.body.style.overflow = prev; };
    }
  }, [open]);

  const update = (slug, delta) => {
    const next = cart
      .map((it) => it.slug === slug ? { ...it, quantity: Math.max(0, it.quantity + delta) } : it)
      .filter((it) => it.quantity > 0);
    setCart(next); writeCart(next);
  };
  const remove = (slug) => {
    const next = cart.filter((it) => it.slug !== slug);
    setCart(next); writeCart(next);
  };

  const subtotal = cart.reduce((s, it) => s + parseFloat(it.price) * it.quantity, 0);
  const remaining = Math.max(0, FREE_SHIP_THRESHOLD - subtotal);
  const progress = Math.min(100, (subtotal / FREE_SHIP_THRESHOLD) * 100);
  const shipFree = subtotal >= FREE_SHIP_THRESHOLD;
  const totalCount = cart.reduce((s, it) => s + it.quantity, 0);

  return (
    <>
      {/* Overlay */}
      <div
        className={
          "fixed inset-0 bg-black/40 z-[90] transition-opacity duration-300 " +
          (open ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none")
        }
        onClick={() => setOpen(false)}
        data-testid="cart-drawer-overlay"
      />

      {/* Drawer */}
      <aside
        className={
          "fixed top-0 right-0 h-full w-full sm:w-[440px] max-w-full bg-white z-[100] shadow-2xl flex flex-col transition-transform duration-300 " +
          (open ? "translate-x-0" : "translate-x-full")
        }
        role="dialog"
        aria-label="Panier"
        data-testid="cart-drawer"
      >
        {/* Header */}
        <header className="px-5 py-4 border-b border-[var(--zayado-border)] flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2.5">
            <ShoppingBag size={18} style={{ color: NAVY }} />
            <div>
              <div className="font-display italic text-lg leading-none" style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)", color: NAVY }}>
                Votre panier
              </div>
              <div className="text-[11px] mt-0.5" style={{ color: MUTED }}>
                {totalCount === 0 ? "0 article" : `${totalCount} article${totalCount > 1 ? "s" : ""}`}
              </div>
            </div>
          </div>
          <button onClick={() => setOpen(false)} className="p-2 rounded-full hover:bg-[var(--zayado-cream)]" data-testid="cart-drawer-close" aria-label="Fermer">
            <X size={18} />
          </button>
        </header>

        {/* Toast "Ajouté" */}
        {justAdded && (
          <div className="mx-5 mt-3 px-3 py-2.5 rounded-lg flex items-center gap-2 text-sm animate-in slide-in-from-top duration-300"
               style={{ background: "var(--zayado-gold-bg)", color: NAVY }}
               data-testid="cart-drawer-toast">
            <Check size={14} style={{ color: GOLD }} /> Article ajouté à votre panier !
          </div>
        )}

        {/* Progress bar livraison */}
        {cart.length > 0 && (
          <div className="px-5 pt-3 pb-2 shrink-0">
            <div className="flex items-center gap-2 text-xs mb-1.5" style={{ color: MUTED }}>
              <Truck size={13} style={{ color: GOLD }} />
              {shipFree ? (
                <span className="font-medium" style={{ color: "#2d6a2d" }}>Livraison offerte ! 🎉</span>
              ) : (
                <span>
                  Il vous manque <strong style={{ color: NAVY }}>{remaining.toFixed(2)}€</strong> pour la livraison offerte
                </span>
              )}
            </div>
            <div className="h-1.5 rounded-full overflow-hidden" style={{ background: "var(--zayado-cream-dark)" }}>
              <div className="h-full transition-all duration-500"
                   style={{ width: `${progress}%`, background: shipFree ? "#2d6a2d" : `linear-gradient(90deg, ${GOLD} 0%, var(--zayado-gold-soft) 100%)` }} />
            </div>
          </div>
        )}

        {/* Items */}
        <div className="flex-1 overflow-y-auto px-5 py-3">
          {cart.length === 0 ? (
            <div className="text-center py-16">
              <ShoppingBag size={32} className="mx-auto mb-3 opacity-30" />
              <div className="text-sm mb-5" style={{ color: MUTED }}>Votre panier est vide.</div>
              <button onClick={() => setOpen(false)}
                      className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-full text-white text-sm font-medium btn-press"
                      style={{ background: NAVY }}>
                Découvrir la boutique <ArrowRight size={13} />
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {cart.map((it) => (
                <div key={it.slug} className="flex gap-3 py-2" data-testid={`cart-drawer-line-${it.slug}`}>
                  <Link to={`/boutique/${it.slug}`} onClick={() => setOpen(false)} className="shrink-0">
                    <img src={it.image} alt={it.name} className="w-16 h-16 object-cover rounded" />
                  </Link>
                  <div className="flex-1 min-w-0">
                    <Link to={`/boutique/${it.slug}`} onClick={() => setOpen(false)}
                          className="text-sm font-medium hover:underline line-clamp-2 leading-snug"
                          style={{ color: "var(--zayado-text)" }}>
                      {it.name}
                    </Link>
                    <div className="text-xs mt-0.5" style={{ color: MUTED }}>{parseFloat(it.price).toFixed(2)}€</div>
                    <div className="flex items-center justify-between mt-1.5">
                      <div className="flex items-center border border-[var(--zayado-border)] rounded-full">
                        <button onClick={() => update(it.slug, -1)} className="w-6 h-6 flex items-center justify-center hover:bg-[var(--zayado-cream-dark)] rounded-l-full"><Minus size={11} /></button>
                        <span className="px-2.5 text-xs font-medium">{it.quantity}</span>
                        <button onClick={() => update(it.slug, 1)} className="w-6 h-6 flex items-center justify-center hover:bg-[var(--zayado-cream-dark)] rounded-r-full"><Plus size={11} /></button>
                      </div>
                      <button onClick={() => remove(it.slug)} className="p-1 hover:text-[var(--zayado-red)]" aria-label="Retirer" data-testid={`cart-drawer-remove-${it.slug}`}>
                        <Trash2 size={13} />
                      </button>
                    </div>
                  </div>
                  <div className="text-sm font-bold whitespace-nowrap">{(parseFloat(it.price) * it.quantity).toFixed(2)}€</div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer CTAs */}
        {cart.length > 0 && (
          <footer className="border-t border-[var(--zayado-border)] px-5 py-4 shrink-0" style={{ background: "var(--zayado-cream)" }}>
            <div className="flex items-center justify-between text-base font-bold mb-3" style={{ color: "var(--zayado-text)" }}>
              <span>Sous-total</span>
              <span>{subtotal.toFixed(2)}€</span>
            </div>
            <div className="text-[11px] text-center mb-3" style={{ color: MUTED }}>
              Taxes incluses · Livraison calculée au checkout
            </div>
            <button onClick={() => { setOpen(false); navigate("/checkout"); }}
                    className="w-full py-3 rounded-full text-white font-medium text-sm btn-press inline-flex items-center justify-center gap-1.5"
                    style={{ background: NAVY }}
                    data-testid="cart-drawer-checkout">
              Passer commande <ArrowRight size={14} />
            </button>
            <button onClick={() => setOpen(false)}
                    className="w-full mt-2 py-2.5 rounded-full text-sm font-medium border border-[var(--zayado-border)] hover:bg-white"
                    style={{ color: NAVY }}
                    data-testid="cart-drawer-continue">
              Continuer mes achats
            </button>
          </footer>
        )}
      </aside>
    </>
  );
}

// Helper exporté pour permettre aux composants d'ajouter au panier sans
// dupliquer la logique. Émet l'event que CartDrawer écoute.
export function addToCart(product, quantity = 1) {
  window.dispatchEvent(new CustomEvent("zayado:cart-add", { detail: { product, quantity } }));
}
