/* Page panier dédiée /panier — version pleine page (mobile-friendly) */
import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { ShoppingBag, Plus, Minus, Trash2, ArrowRight, ShieldCheck, Truck, RotateCcw } from "lucide-react";

const NAVY = "var(--zayado-navy)";
const GOLD = "var(--zayado-gold)";
const MUTED = "var(--zayado-muted)";

export default function Cart() {
  const navigate = useNavigate();
  const [cart, setCart] = useState([]);

  useEffect(() => {
    try { setCart(JSON.parse(localStorage.getItem("zay_cart") || "[]")); } catch {}
  }, []);

  const update = (slug, delta) => {
    const next = cart.map((it) => it.slug === slug ? { ...it, quantity: Math.max(0, it.quantity + delta) } : it)
      .filter((it) => it.quantity > 0);
    setCart(next);
    localStorage.setItem("zay_cart", JSON.stringify(next));
  };
  const remove = (slug) => {
    const next = cart.filter((it) => it.slug !== slug);
    setCart(next);
    localStorage.setItem("zay_cart", JSON.stringify(next));
  };

  const subtotal = cart.reduce((s, it) => s + parseFloat(it.price) * it.quantity, 0);
  const shipping = subtotal >= 50 || subtotal === 0 ? 0 : 4.9;
  const total = subtotal + shipping;

  return (
    <>
    <Helmet>
      <title>Votre panier — Zayado</title>
      <meta name="robots" content="noindex, follow" />
    </Helmet>
    <div className="max-w-[1100px] mx-auto px-4 md:px-6 py-8" data-testid="cart-page">
      <div className="text-[11px] uppercase tracking-[0.25em] mb-2" style={{ color: GOLD }}>Panier</div>
      <h1 className="font-display italic mb-7"
          style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)",
                   fontSize: "clamp(1.8rem, 4vw, 2.6rem)", color: "var(--zayado-text)" }}>
        Votre sélection{cart.length > 0 && <span style={{ color: MUTED, fontStyle: "normal", fontSize: "0.7em" }}> · {cart.length} article{cart.length > 1 ? "s" : ""}</span>}
      </h1>

      {cart.length === 0 ? (
        <div className="text-center py-20 rounded-xl border-2 border-dashed border-[var(--zayado-border)]" data-testid="cart-empty">
          <ShoppingBag size={36} className="mx-auto mb-3 opacity-40" />
          <div className="text-sm mb-5" style={{ color: MUTED }}>Votre panier est vide.</div>
          <Link to="/boutique" className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full text-white font-medium text-sm btn-press"
                style={{ background: NAVY }}>
            Découvrir la boutique <ArrowRight size={13} />
          </Link>
        </div>
      ) : (
        <div className="grid lg:grid-cols-[1fr_360px] gap-6">
          {/* Items */}
          <div className="space-y-3">
            {cart.map((it) => (
              <div key={it.slug} className="flex gap-4 p-4 rounded-lg border border-[var(--zayado-border)] bg-white" data-testid={`cart-line-${it.slug}`}>
                <img src={it.image} alt={it.name} className="w-20 h-20 md:w-24 md:h-24 object-cover rounded shrink-0" />
                <div className="flex-1 min-w-0">
                  <Link to={`/boutique/${it.slug}`} className="text-sm md:text-base font-medium hover:underline line-clamp-2" style={{ color: "var(--zayado-text)" }}>
                    {it.name}
                  </Link>
                  <div className="text-xs mt-1" style={{ color: MUTED }}>{parseFloat(it.price).toFixed(2)}€ l'unité</div>
                  <div className="flex items-center gap-3 mt-3">
                    <div className="flex items-center border border-[var(--zayado-border)] rounded-full">
                      <button onClick={() => update(it.slug, -1)} className="w-7 h-7 flex items-center justify-center hover:bg-[var(--zayado-cream-dark)] rounded-l-full"><Minus size={12} /></button>
                      <span className="px-3 text-sm font-medium">{it.quantity}</span>
                      <button onClick={() => update(it.slug, 1)} className="w-7 h-7 flex items-center justify-center hover:bg-[var(--zayado-cream-dark)] rounded-r-full"><Plus size={12} /></button>
                    </div>
                    <button onClick={() => remove(it.slug)} className="text-xs hover:underline inline-flex items-center gap-1" style={{ color: "var(--zayado-red)" }}>
                      <Trash2 size={12} /> Retirer
                    </button>
                  </div>
                </div>
                <div className="text-base md:text-lg font-bold whitespace-nowrap self-start">{(parseFloat(it.price) * it.quantity).toFixed(2)}€</div>
              </div>
            ))}
          </div>

          {/* Récap */}
          <aside className="space-y-3">
            <div className="p-5 rounded-xl border border-[var(--zayado-border)] bg-white sticky top-4" data-testid="cart-summary">
              <h3 className="font-display italic text-lg mb-4" style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)", color: "var(--zayado-text)" }}>
                Récapitulatif
              </h3>
              <div className="space-y-2 text-sm" style={{ color: MUTED }}>
                <div className="flex justify-between"><span>Sous-total</span><span>{subtotal.toFixed(2)}€</span></div>
                <div className="flex justify-between"><span>Livraison {shipping === 0 && subtotal > 0 ? "(offerte)" : ""}</span><span>{shipping === 0 ? "Gratuit" : `${shipping.toFixed(2)}€`}</span></div>
              </div>
              <div className="flex justify-between font-bold text-lg pt-3 mt-3 border-t border-[var(--zayado-border)]" style={{ color: "var(--zayado-text)" }}>
                <span>Total</span><span>{total.toFixed(2)}€</span>
              </div>
              {subtotal < 50 && (
                <div className="mt-3 p-2.5 rounded-md text-xs text-center" style={{ background: "var(--zayado-gold-bg)", color: GOLD }}>
                  Encore {(50 - subtotal).toFixed(2)}€ pour la livraison offerte.
                </div>
              )}
              <button onClick={() => navigate("/checkout")}
                      className="w-full mt-4 py-3 rounded-full text-white font-medium text-sm btn-press"
                      style={{ background: NAVY }} data-testid="cart-checkout-btn">
                Passer au paiement <ArrowRight size={13} className="inline ml-1" />
              </button>
              <Link to="/boutique" className="block mt-2 text-center text-xs hover:underline" style={{ color: MUTED }}>
                Continuer mes achats
              </Link>
            </div>
            <div className="text-[11px] space-y-1.5 px-2" style={{ color: MUTED }}>
              <div className="flex items-center gap-1.5"><ShieldCheck size={12} /> Paiement sécurisé SSL 256-bits</div>
              <div className="flex items-center gap-1.5"><Truck size={12} /> Expédition 24-48h ouvrées</div>
              <div className="flex items-center gap-1.5"><RotateCcw size={12} /> Retours gratuits sous 30 jours</div>
            </div>
          </aside>
        </div>
      )}
    </div>
    </>
  );
}
