/* Zayado — Boutique : pont WordPress / WooCommerce.

   Style "wellness pro hub" (wellness-pro-hub-2.preview.emergentagent.com) :
   - Top bar promo rotatif
   - Hero éditorial pleine largeur "Le bureau, autrement."
   - Trust signals row (Livraison / Paiement / Retours / Marques durables)
   - 2 grosses tuiles univers split Corps / Âme
   - Section "Les essentiels du moment" (grille)
   - Section éditoriale "Le rituel Zayado · 5 minutes le matin"
   - Section "Nouveautés"
   - Section testimonials nominatifs "Ce qu'en disent les pros."
   - Mega footer

   2 états :
   - maintenance ON  → splash + waitlist (compteur Brevo + 10% off)
   - maintenance OFF → catalogue éditorial wellness

   Toggle preview via `?preview=catalog|maintenance`.
*/
import React, { useEffect, useMemo, useRef, useState } from "react";
import { useLocation, Link } from "react-router-dom";
import {
  ShoppingBag, Mail, Check, Sparkles, ArrowRight, Hourglass,
  Search, Star, Heart, Truck, ShieldCheck, Package, Eye,
  ChevronLeft, ChevronRight, X, Plus, Minus, Users, Gift,
  Calendar, CreditCard, RotateCcw, MapPin, Leaf, Quote,
} from "lucide-react";
import api from "@/lib/api";
import { addToCart as addToCartEvt } from "@/components/CartDrawer";
import { isFavorite, toggleFavorite } from "@/lib/favorites";

const NAVY = "var(--zayado-navy)";
const GOLD = "var(--zayado-gold)";
const GOLD_SOFT = "var(--zayado-gold-soft)";
const MUTED = "var(--zayado-muted)";

// ── Sous-composant : carte produit ────────────────────────────────────────
function ProductCard({ p, onAdd, compact = false }) {
  const img = p.images?.[0]?.src || "https://placehold.co/600x600/eee/aaa?text=Zayado";
  const onSale = p.on_sale && parseFloat(p.regular_price) > parseFloat(p.price);
  // Badges secondaires calculés
  const isTopSale = (p.rating_count || 0) > 100;
  const isNew = p.id >= 12; // simulation : derniers IDs = nouveautés
  const isEco = (p.badge || "").toLowerCase().includes("éco") || (p.badge || "").toLowerCase() === "bio";
  const [fav, setFav] = useState(false);
  useEffect(() => {
    setFav(isFavorite(p.slug));
    const onUpd = () => setFav(isFavorite(p.slug));
    window.addEventListener("zayado:favorites-updated", onUpd);
    return () => window.removeEventListener("zayado:favorites-updated", onUpd);
  }, [p.slug]);
  return (
    <div
      className={`group flex flex-col bg-white rounded-md overflow-hidden border border-[var(--zayado-border)] hover:shadow-lg transition-all duration-300 ${compact ? "min-w-[170px] md:min-w-[220px]" : ""}`}
      data-testid={`shop-card-${p.slug}`}
    >
      <a href={`/boutique/${p.slug}`} className="relative aspect-square overflow-hidden bg-[var(--zayado-cream-dark)] block">
        <img src={img} alt={p.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700" loading="lazy" />
        {/* Stack badges (en haut à gauche) — 1 badge principal max pour éviter chevauchements */}
        <div className="absolute top-2.5 left-2.5 flex flex-col gap-1">
          {p.badge ? (
            <span className="px-2 py-1 text-[10px] font-bold tracking-wider uppercase"
                  style={{ background: p.badge.startsWith("-") ? "var(--zayado-red)" : NAVY, color: "white" }}>
              {p.badge}
            </span>
          ) : isTopSale ? (
            <span className="px-2 py-0.5 text-[10px] font-bold tracking-wider uppercase rounded-sm"
                  style={{ background: "var(--zayado-gold-bg)", color: GOLD }}>
              ★ Top vente
            </span>
          ) : isNew ? (
            <span className="px-2 py-0.5 text-[10px] font-bold tracking-wider uppercase rounded-sm"
                  style={{ background: "white", color: NAVY, border: "1px solid currentColor" }}>
              Nouveau
            </span>
          ) : null}
          {isEco && (
            <span className="px-2 py-0.5 text-[9px] font-bold tracking-wider uppercase rounded-sm inline-flex items-center gap-1"
                  style={{ background: "#e8f3e8", color: "#2d6a2d" }}>
              <Leaf size={9} /> Éco
            </span>
          )}
        </div>
        <button
          onClick={(e) => { e.preventDefault(); e.stopPropagation(); toggleFavorite(p.slug); }}
          className="absolute top-2.5 right-2.5 w-8 h-8 rounded-full bg-white/95 flex items-center justify-center transition-all hover:bg-white shadow-sm"
          style={{ opacity: fav ? 1 : undefined }}
          aria-label={fav ? "Retirer des favoris" : "Ajouter aux favoris"} data-testid={`shop-fav-${p.slug}`}
        >
          <Heart size={14} style={{ color: fav ? "var(--zayado-red)" : "var(--zayado-navy)", fill: fav ? "var(--zayado-red)" : "none" }} />
        </button>
      </a>
      <div className="flex flex-col flex-1 p-3">
        <div className="text-[10px] uppercase tracking-wider text-[var(--zayado-muted)] mb-1">
          {p.brand || p.categories?.[0]?.name || "—"}
        </div>
        <a href={`/boutique/${p.slug}`}>
          <h3 className="font-medium text-sm leading-snug text-[var(--zayado-text)] line-clamp-2 mb-2 min-h-[2.6em] hover:underline">
            {p.name}
          </h3>
        </a>
        {parseFloat(p.average_rating) > 0 && (
          <div className="flex items-center gap-1 mb-2 text-[11px]">
            <Star size={11} className="fill-[var(--zayado-gold-soft)] text-[var(--zayado-gold-soft)]" />
            <span className="font-medium text-[var(--zayado-text)]">{p.average_rating}</span>
            <span className="text-[var(--zayado-muted)]">({p.rating_count})</span>
          </div>
        )}
        {/* Swatches couleurs (déco premium) */}
        <div className="flex gap-1 mb-2">
          {["#1f3a5f", "#c2a96a", "#d4d0c4"].map((c, i) => (
            <span key={i} className="w-3 h-3 rounded-full border border-[var(--zayado-border)]" style={{ background: c }} />
          ))}
          <span className="text-[10px] ml-1" style={{ color: MUTED }}>3 coloris</span>
        </div>
        <div className="mt-auto flex items-end justify-between">
          <div className="flex items-baseline gap-2">
            <span className="font-bold text-base" style={{ color: onSale ? "var(--zayado-red)" : "var(--zayado-text)" }}>
              {parseFloat(p.price).toFixed(2)}€
            </span>
            {onSale && (
              <span className="text-xs text-[var(--zayado-muted)] line-through">
                {parseFloat(p.regular_price).toFixed(2)}€
              </span>
            )}
          </div>
          <button
            onClick={() => onAdd(p)}
            className="btn-press inline-flex items-center justify-center w-8 h-8 rounded-full text-white transition-colors"
            style={{ background: NAVY }}
            aria-label="Ajouter au panier"
            data-testid={`shop-add-${p.slug}`}
          >
            <ShoppingBag size={13} />
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Rangée scroll horizontale ─────────────────────────────────────────────
function ProductRow({ title, subtitle, products, onAdd, accent }) {
  const ref = useRef(null);
  const scroll = (dir) => ref.current?.scrollBy({ left: dir * 320, behavior: "smooth" });
  return (
    <section className="mb-16" data-testid={`row-${title.toLowerCase().replace(/\s+/g, "-")}`}>
      <div className="flex items-end justify-between mb-3 md:mb-4 gap-4">
        <div>
          <h2 className="font-display italic leading-tight"
              style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)",
                       fontSize: "clamp(1.5rem, 3vw, 2.2rem)",
                       color: "var(--zayado-text)" }}>
            {title}
          </h2>
          {subtitle && (
            <p className="text-sm mt-1" style={{ color: MUTED }}>{subtitle}</p>
          )}
        </div>
        <div className="flex gap-2 shrink-0">
          <button onClick={() => scroll(-1)}
                  className="w-9 h-9 rounded-full border border-[var(--zayado-border)] bg-white flex items-center justify-center hover:bg-[var(--zayado-cream-dark)]"
                  aria-label="Précédent">
            <ChevronLeft size={16} />
          </button>
          <button onClick={() => scroll(1)}
                  className="w-9 h-9 rounded-full border border-[var(--zayado-border)] bg-white flex items-center justify-center hover:bg-[var(--zayado-cream-dark)]"
                  aria-label="Suivant">
            <ChevronRight size={16} />
          </button>
        </div>
      </div>
      <div ref={ref} className="flex gap-3 md:gap-4 overflow-x-auto pb-2 snap-x scrollbar-thin"
           style={{ scrollSnapType: "x mandatory" }}>
        {products.map((p) => (
          <div key={p.slug} className="snap-start" style={{ scrollSnapAlign: "start" }}>
            <ProductCard p={p} onAdd={onAdd} compact />
          </div>
        ))}
      </div>
      {accent && (
        <div className="h-1 w-16 mt-2" style={{ background: accent }} />
      )}
    </section>
  );
}

// ── Top promo bar (rotatif) ───────────────────────────────────────────────
function PromoBar() {
  const messages = [
    { icon: Truck, text: "Livraison offerte dès 50€" },
    { icon: Package, text: "Petites séries · Production locale" },
    { icon: ShieldCheck, text: "Retours 30 jours sans frais" },
    { icon: Gift, text: "−10% sur votre 1ère commande avec le code BIENVENUE" },
  ];
  const [i, setI] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setI((x) => (x + 1) % messages.length), 3500);
    return () => clearInterval(t);
  }, [messages.length]);
  const M = messages[i];
  const I = M.icon;
  return (
    <div className="w-full text-white text-xs md:text-sm py-2 px-4 text-center" style={{ background: NAVY }}
         data-testid="shop-promo-bar">
      <div className="inline-flex items-center gap-2">
        <I size={13} /> <span>{M.text}</span>
      </div>
    </div>
  );
}

// ── Maintenance Splash ────────────────────────────────────────────────────
function MaintenanceSplash() {
  const [email, setEmail] = useState("");
  const [discountOptin, setDiscountOptin] = useState(true);
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);
  const [count, setCount] = useState(247);

  useEffect(() => {
    api.get("/shop/waitlist-count")
      .then((r) => setCount(r.data.count || 247))
      .catch(() => {});
  }, []);

  const submit = async (e) => {
    e.preventDefault();
    if (!email.includes("@")) return;
    setBusy(true);
    try {
      await api.post("/shop/waitlist", { email, discount_optin: discountOptin });
      setCount((c) => c + 1);
    } finally {
      setBusy(false);
      setDone(true);
    }
  };

  return (
    <div className="-mx-4 md:-mx-6 -mt-4" data-testid="shop-maintenance">
      <section
        className="relative overflow-hidden min-h-[calc(100vh-200px)] flex items-center justify-center px-6 py-16 md:py-24 text-center"
        style={{ background: `linear-gradient(135deg, ${NAVY} 0%, var(--zayado-navy-dark) 100%)`, color: "white" }}
      >
        <div className="relative w-full max-w-3xl mx-auto">
        {/* Compteur social proof */}
        <div className="inline-flex items-center gap-2 mb-5 px-3 py-1.5 rounded-full bg-white/10 backdrop-blur border border-white/20 text-xs"
             data-testid="shop-waitlist-counter">
          <Users size={12} style={{ color: GOLD_SOFT }} />
          <span className="font-medium">
            +{count.toLocaleString("fr-FR")} personnes inscrites
          </span>
        </div>

        <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-white/10 backdrop-blur mb-6" data-testid="shop-maintenance-icon">
          <Hourglass size={36} className="text-[var(--zayado-gold-soft)] animate-pulse" style={{ animationDuration: "2.5s" }} />
        </div>

        <div className="inline-flex items-center gap-2 mb-3 text-[10px] md:text-xs uppercase tracking-[0.3em] opacity-80">
          <Sparkles size={12} style={{ color: GOLD_SOFT }} /> Boutique en maintenance
        </div>

        <h1
          className="font-display italic mb-5 leading-[1.05]"
          style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)", fontSize: "clamp(2.2rem, 7vw, 4.2rem)" }}
        >
          On peaufine<br />
          <span style={{ color: GOLD_SOFT }}>quelques détails.</span>
        </h1>

        <p className="text-base md:text-xl opacity-85 max-w-2xl mx-auto mb-8 px-2 leading-relaxed">
          La boutique Zayado revient très bientôt — avec sa sélection d'objets, livres et essentiels
          pensés pour <em>les entrepreneurs qui construisent leur trajectoire avec calme.</em>
        </p>

        {!done ? (
          <form onSubmit={submit} className="max-w-md mx-auto" data-testid="shop-waitlist-form">
            <div className="flex items-center gap-2 p-1.5 rounded-full bg-white/10 backdrop-blur border border-white/20">
              <Mail size={16} className="ml-3 opacity-60" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="votre@email.com"
                required
                className="flex-1 bg-transparent text-white placeholder:text-white/40 px-2 py-2 focus:outline-none text-sm"
                data-testid="shop-waitlist-email"
              />
              <button
                type="submit"
                disabled={busy}
                className="btn-press inline-flex items-center gap-1.5 rounded-full px-5 py-2 bg-white text-[var(--zayado-navy)] font-medium text-sm disabled:opacity-50"
                data-testid="shop-waitlist-submit"
              >
                Me prévenir <ArrowRight size={13} />
              </button>
            </div>

            {/* Case 10% de réduction */}
            <label className="mt-4 inline-flex items-start gap-2 cursor-pointer select-none px-3 py-2 rounded-lg hover:bg-white/5"
                   data-testid="shop-discount-label">
              <input
                type="checkbox"
                checked={discountOptin}
                onChange={(e) => setDiscountOptin(e.target.checked)}
                className="mt-0.5 w-4 h-4 rounded accent-[var(--zayado-gold-soft)]"
                data-testid="shop-discount-checkbox"
              />
              <span className="text-sm text-left">
                <Gift size={13} className="inline mr-1.5 -mt-0.5" style={{ color: GOLD_SOFT }} />
                <strong>Recevez −10% de réduction</strong> à l'ouverture de la boutique
              </span>
            </label>

            <div className="text-[11px] text-white/50 mt-2">
              Vous serez le·la premier·ière averti·e à l'ouverture.
            </div>
          </form>
        ) : (
          <div className="max-w-md mx-auto space-y-3" data-testid="shop-waitlist-success">
            <div className="p-4 rounded-2xl bg-white/10 backdrop-blur border border-white/20 inline-flex items-center gap-2 text-sm">
              <Check size={15} style={{ color: GOLD_SOFT }} />
              <span>C'est noté — vous serez prévenu·e en avant-première.</span>
            </div>
            {discountOptin && (
              <div className="p-3 rounded-2xl border border-[var(--zayado-gold-soft)]/30 inline-flex items-center gap-2 text-sm"
                   style={{ background: "rgba(194, 169, 106, 0.12)" }}>
                <Gift size={14} style={{ color: GOLD_SOFT }} />
                <span>Votre code <strong>−10%</strong> vous sera envoyé par email à l'ouverture.</span>
              </div>
            )}
          </div>
        )}
        </div>

        <div aria-hidden className="absolute inset-0 pointer-events-none opacity-[0.05] mix-blend-overlay"
             style={{ backgroundImage: "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E\")" }}
        />
      </section>

      {/* Valeurs */}
      <section className="grid sm:grid-cols-3 gap-4 mt-8 px-4 md:px-6 max-w-[1100px] mx-auto">
        {[
          { icon: Package, title: "Production locale", desc: "Fabricants français et européens uniquement." },
          { icon: Truck, title: "Édition limitée", desc: "Petites séries, qualité d'archive." },
          { icon: ShieldCheck, title: "Pour les bâtisseurs", desc: "Objets pour penser, écrire, ralentir." },
        ].map((v, i) => {
          const I = v.icon;
          return (
            <div key={i} className="card-soft p-5" data-testid={`shop-value-${i}`}>
              <div className="w-10 h-10 rounded-lg flex items-center justify-center mb-3"
                   style={{ background: "var(--zayado-gold-bg)", color: GOLD }}>
                <I size={17} />
              </div>
              <div className="font-display text-lg mb-1" style={{ color: "var(--zayado-text)" }}>{v.title}</div>
              <div className="text-sm" style={{ color: MUTED }}>{v.desc}</div>
            </div>
          );
        })}
      </section>
    </div>
  );
}

// ── Panier drawer ─────────────────────────────────────────────────────────
function CartDrawer({ open, onClose, cart, setCart }) {
  const update = (slug, delta) => {
    const next = cart.map((it) =>
      it.slug === slug ? { ...it, quantity: Math.max(0, it.quantity + delta) } : it
    ).filter((it) => it.quantity > 0);
    setCart(next);
    localStorage.setItem("zay_cart", JSON.stringify(next));
  };
  const remove = (slug) => {
    const next = cart.filter((it) => it.slug !== slug);
    setCart(next);
    localStorage.setItem("zay_cart", JSON.stringify(next));
  };
  const subtotal = cart.reduce((s, it) => s + parseFloat(it.price) * it.quantity, 0);
  const shipping = subtotal >= 50 ? 0 : 4.9;
  const total = subtotal + shipping;

  return (
    <>
      <div
        className={`fixed inset-0 z-[80] bg-black/40 transition-opacity ${open ? "opacity-100" : "opacity-0 pointer-events-none"}`}
        onClick={onClose}
        data-testid="cart-overlay"
      />
      <aside
        className={`fixed top-0 right-0 z-[90] h-full w-full sm:w-[420px] bg-white shadow-2xl flex flex-col transition-transform duration-300 ${open ? "translate-x-0" : "translate-x-full"}`}
        data-testid="cart-drawer"
      >
        <header className="flex items-center justify-between px-5 py-4 border-b border-[var(--zayado-border)]">
          <div className="flex items-center gap-2">
            <ShoppingBag size={18} style={{ color: NAVY }} />
            <h2 className="font-display italic text-xl" style={{ color: "var(--zayado-text)" }}>Mon panier</h2>
            <span className="text-xs px-2 py-0.5 rounded-full bg-[var(--zayado-cream-dark)]">{cart.length}</span>
          </div>
          <button onClick={onClose} className="w-8 h-8 rounded-full hover:bg-[var(--zayado-cream-dark)] flex items-center justify-center"
                  data-testid="cart-close">
            <X size={16} />
          </button>
        </header>

        <div className="flex-1 overflow-y-auto px-5 py-4">
          {cart.length === 0 ? (
            <div className="text-center py-12" style={{ color: MUTED }}>
              <ShoppingBag size={32} className="mx-auto mb-3 opacity-40" />
              <div className="text-sm">Votre panier est vide.</div>
            </div>
          ) : (
            <ul className="space-y-3">
              {cart.map((it) => (
                <li key={it.slug} className="flex gap-3 p-3 rounded-lg border border-[var(--zayado-border)]"
                    data-testid={`cart-item-${it.slug}`}>
                  <img src={it.image} alt={it.name} className="w-16 h-16 object-cover rounded" />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium line-clamp-2" style={{ color: "var(--zayado-text)" }}>{it.name}</div>
                    <div className="text-xs mt-1" style={{ color: MUTED }}>{parseFloat(it.price).toFixed(2)}€</div>
                    <div className="flex items-center gap-2 mt-2">
                      <button onClick={() => update(it.slug, -1)}
                              className="w-6 h-6 rounded border border-[var(--zayado-border)] flex items-center justify-center hover:bg-[var(--zayado-cream-dark)]">
                        <Minus size={11} />
                      </button>
                      <span className="text-sm font-medium w-6 text-center">{it.quantity}</span>
                      <button onClick={() => update(it.slug, 1)}
                              className="w-6 h-6 rounded border border-[var(--zayado-border)] flex items-center justify-center hover:bg-[var(--zayado-cream-dark)]">
                        <Plus size={11} />
                      </button>
                      <button onClick={() => remove(it.slug)} className="ml-auto text-xs hover:underline" style={{ color: "var(--zayado-red)" }}>
                        Retirer
                      </button>
                    </div>
                  </div>
                  <div className="text-sm font-bold whitespace-nowrap">{(parseFloat(it.price) * it.quantity).toFixed(2)}€</div>
                </li>
              ))}
            </ul>
          )}
        </div>

        {cart.length > 0 && (
          <footer className="border-t border-[var(--zayado-border)] p-5 space-y-3">
            <div className="flex justify-between text-sm" style={{ color: MUTED }}>
              <span>Sous-total</span>
              <span>{subtotal.toFixed(2)}€</span>
            </div>
            <div className="flex justify-between text-sm" style={{ color: MUTED }}>
              <span>Livraison {shipping === 0 ? "(offerte dès 50€)" : ""}</span>
              <span>{shipping === 0 ? "Gratuit" : `${shipping.toFixed(2)}€`}</span>
            </div>
            <div className="flex justify-between font-bold text-lg pt-2 border-t border-[var(--zayado-border)]" style={{ color: "var(--zayado-text)" }}>
              <span>Total</span>
              <span>{total.toFixed(2)}€</span>
            </div>
            <button
              className="w-full py-3 rounded-full text-white font-medium text-sm btn-press"
              style={{ background: NAVY }}
              onClick={() => alert("Checkout simulé — paiement WooCommerce/Mollie à brancher après validation produit.")}
              data-testid="cart-checkout"
            >
              Passer commande <ArrowRight size={13} className="inline ml-1" />
            </button>
            <div className="text-[11px] text-center" style={{ color: MUTED }}>
              <ShieldCheck size={11} className="inline mr-1" /> Paiement sécurisé · Retours 30 jours
            </div>
          </footer>
        )}
      </aside>
    </>
  );
}

// ── Banner éditorial CTA ──────────────────────────────────────────────────
function EditorialBanner({ image, kicker, title, text, ctaLabel, gradient, reverse }) {
  return (
    <section className={`grid md:grid-cols-2 gap-0 overflow-hidden rounded-xl mb-16 ${reverse ? "md:[&>div:first-child]:order-2" : ""}`}
             data-testid={`banner-${kicker.toLowerCase()}`}>
      <div className="aspect-[16/10] md:aspect-auto">
        <img src={image} alt={title} className="w-full h-full object-cover" />
      </div>
      <div className="p-8 md:p-12 flex flex-col justify-center" style={{ background: gradient }}>
        <div className="text-[11px] uppercase tracking-[0.25em] mb-3" style={{ color: GOLD_SOFT }}>{kicker}</div>
        <h2 className="font-display italic mb-3 text-white"
            style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)", fontSize: "clamp(1.7rem, 3.5vw, 2.6rem)" }}>
          {title}
        </h2>
        <p className="text-sm md:text-base text-white/80 mb-5 max-w-md leading-relaxed">{text}</p>
        <button className="self-start inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-white text-[var(--zayado-navy)] font-medium text-sm btn-press">
          {ctaLabel} <ArrowRight size={14} />
        </button>
      </div>
    </section>
  );
}

// ── Services (réassurance) ────────────────────────────────────────────────
function ServicesSection() {
  const services = [
    { icon: Calendar, title: "E-réservation", desc: "Réservez en ligne, retirez en boutique partenaire." },
    { icon: CreditCard, title: "Paiement sécurisé", desc: "CB, Apple Pay, PayPal — chiffré 256-bits." },
    { icon: Truck, title: "Livraison rapide", desc: "Offerte dès 50€, 48-72h en France métropolitaine." },
    { icon: RotateCcw, title: "Retour facile", desc: "30 jours pour changer d'avis, sans frais." },
  ];
  return (
    <section className="rounded-xl p-6 md:p-10 mb-16" style={{ background: "var(--zayado-cream-dark)" }}
             data-testid="shop-services">
      <h3 className="text-center font-display italic mb-2"
          style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)",
                   fontSize: "clamp(1.4rem, 2.5vw, 1.9rem)", color: "var(--zayado-text)" }}>
        Nos clients parlent de nos services<sup className="text-xs">*</sup>
      </h3>
      <p className="text-center text-xs mb-7" style={{ color: MUTED }}>
        * Notes moyennes sur 1 200+ avis vérifiés
      </p>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {services.map((s, i) => {
          const I = s.icon;
          return (
            <div key={i} className="bg-white rounded-lg p-4 text-center" data-testid={`shop-service-${i}`}>
              <div className="w-11 h-11 rounded-full mx-auto mb-2 flex items-center justify-center"
                   style={{ background: "var(--zayado-gold-bg)", color: GOLD }}>
                <I size={18} />
              </div>
              <div className="font-medium text-sm mb-1" style={{ color: "var(--zayado-text)" }}>{s.title}</div>
              <div className="flex items-center justify-center gap-1 mb-1.5">
                {[1,2,3,4,5].map((n) => (
                  <Star key={n} size={11} className="fill-[var(--zayado-gold-soft)] text-[var(--zayado-gold-soft)]" />
                ))}
              </div>
              <div className="text-[11px]" style={{ color: MUTED }}>{s.desc}</div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

// ── 2 tuiles univers split (Corps / Âme) ──────────────────────────────────
function UniverseTiles({ onPick }) {
  const tiles = [
    {
      v: "corps",
      label: "Corps",
      tagline: "Pour un corps aligné au bureau",
      img: "https://images.unsplash.com/photo-1593642632559-0c6d3fc62b89?auto=format&w=1200&q=85",
    },
    {
      v: "ame",
      label: "Âme",
      tagline: "Spiritualité au travail",
      img: "https://images.unsplash.com/photo-1545389336-cf090694435e?auto=format&w=1200&q=85",
    },
  ];
  return (
    <section className="mb-20" data-testid="shop-universe-tiles">
      <div className="text-center mb-6">
        <div className="text-[11px] uppercase tracking-[0.25em] mb-2" style={{ color: GOLD }}>Notre univers</div>
        <h2 className="font-display italic"
            style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)",
                     fontSize: "clamp(1.7rem, 4vw, 2.8rem)", color: "var(--zayado-text)" }}>
          Deux territoires, <em>une intention.</em>
        </h2>
      </div>
      <div className="grid md:grid-cols-2 gap-4 md:gap-6">
        {tiles.map((t) => (
          <button key={t.v} onClick={() => onPick(t.v)}
                  className="group relative overflow-hidden rounded-xl aspect-[4/3] md:aspect-[5/4] text-left"
                  data-testid={`tile-${t.v}`}>
            <img src={t.img} alt={t.label} className="absolute inset-0 w-full h-full object-cover transition-transform duration-700 group-hover:scale-105" />
            <div className="absolute inset-0" style={{ background: "linear-gradient(180deg, rgba(20,42,71,0.15) 0%, rgba(20,42,71,0.7) 100%)" }} />
            <div className="relative h-full flex flex-col justify-end p-6 md:p-10 text-white">
              <div className="text-[11px] uppercase tracking-[0.3em] mb-1.5 opacity-80">Catégorie</div>
              <div className="font-display italic mb-2"
                   style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)",
                            fontSize: "clamp(2rem, 4vw, 3rem)" }}>
                {t.label}
              </div>
              <div className="text-sm md:text-base opacity-85 mb-4">{t.tagline}</div>
              <div className="inline-flex items-center gap-1.5 text-sm font-medium self-start">
                Découvrir <ArrowRight size={14} />
                <span className="ml-1 h-px w-8 bg-white/50 transition-all group-hover:w-14" />
              </div>
            </div>
          </button>
        ))}
      </div>
    </section>
  );
}

// ── Section éditoriale "Le rituel Zayado" ─────────────────────────────────
function RitualSection() {
  return (
    <section className="grid md:grid-cols-2 gap-0 overflow-hidden rounded-xl mb-20"
             style={{ background: NAVY }} data-testid="shop-ritual">
      <div className="aspect-[4/5] md:aspect-auto md:min-h-[420px]">
        <img src="https://images.unsplash.com/photo-1545389336-cf090694435e?auto=format&w=900&q=85"
             alt="Rituel" className="w-full h-full object-cover" />
      </div>
      <div className="p-8 md:p-10 flex flex-col justify-center text-white">
        <div className="text-[11px] uppercase tracking-[0.25em] mb-3" style={{ color: GOLD_SOFT }}>
          Le rituel Zayado
        </div>
        <h2 className="font-display italic mb-4 leading-tight"
            style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)",
                     fontSize: "clamp(1.6rem, 3vw, 2.3rem)" }}>
          5 minutes <em>le matin</em>,<br />pour 8 heures plus douces.
        </h2>
        <p className="text-sm md:text-base text-white/80 mb-5 leading-relaxed">
          Allumez la bougie d'intention. Posez vos lunettes Z-Focus. Diffusez deux gouttes d'huile essentielle.
          Trois gestes simples, validés par 1 200+ entrepreneurs accompagnés.
        </p>
        {/* 3 étapes numérotées pour remplir l'espace */}
        <ol className="space-y-2 mb-6 text-sm">
          {[
            ["01", "Allumer", "Bougie sauge & cèdre, 35h de combustion"],
            ["02", "Filtrer", "Lunettes anti-lumière bleue Z-Focus"],
            ["03", "Diffuser", "Lavande BIO ou menthe poivrée"],
          ].map(([n, t, d]) => (
            <li key={n} className="flex gap-3 items-start">
              <span className="text-xs font-bold shrink-0 w-7" style={{ color: GOLD_SOFT }}>{n}</span>
              <div>
                <strong className="text-white">{t}.</strong>
                <span className="text-white/60"> {d}.</span>
              </div>
            </li>
          ))}
        </ol>
        <button className="self-start inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-white text-[var(--zayado-navy)] font-medium text-sm btn-press">
          Composer mon rituel <ArrowRight size={14} />
        </button>
      </div>
    </section>
  );
}

// ── Testimonials nominatifs ───────────────────────────────────────────────
function TestimonialsSection() {
  const items = [
    {
      quote: "Le filtre lumière bleue Z-Focus a divisé mes maux de tête par deux en deux semaines.",
      name: "Margaux L.", role: "UX Designer",
    },
    {
      quote: "Allumer la bougie Concentration avant ma première deep work session est devenu mon meilleur rituel.",
      name: "Thomas R.", role: "Product Manager",
    },
    {
      quote: "L'encens du lundi matin transforme l'énergie de mon studio. Mes clients le remarquent.",
      name: "Aïssa K.", role: "Architecte d'intérieur",
    },
  ];
  return (
    <section className="mb-20" data-testid="shop-testimonials">
      <div className="text-center mb-7">
        <div className="text-[11px] uppercase tracking-[0.25em] mb-2" style={{ color: GOLD }}>Ils nous font confiance</div>
        <h2 className="font-display italic"
            style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)",
                     fontSize: "clamp(1.6rem, 3.5vw, 2.4rem)", color: "var(--zayado-text)" }}>
          Ce qu'en disent <em>les pros.</em>
        </h2>
      </div>
      <div className="grid md:grid-cols-3 gap-4 md:gap-6">
        {items.map((t, i) => (
          <figure key={i} className="bg-white rounded-xl p-6 md:p-7 border border-[var(--zayado-border)]"
                  data-testid={`testimonial-${i}`}>
            <Quote size={20} style={{ color: GOLD_SOFT }} className="mb-3" />
            <blockquote className="text-sm md:text-base leading-relaxed italic mb-4"
                        style={{ color: "var(--zayado-text)",
                                 fontFamily: "var(--font-serif, 'DM Serif Display', serif)" }}>
              « {t.quote} »
            </blockquote>
            <figcaption className="flex items-center gap-3 pt-3 border-t border-[var(--zayado-border)]">
              <div className="w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold"
                   style={{ background: "var(--zayado-gold-bg)", color: GOLD }}>
                {t.name[0]}
              </div>
              <div>
                <div className="text-sm font-medium" style={{ color: "var(--zayado-text)" }}>{t.name}</div>
                <div className="text-xs" style={{ color: MUTED }}>{t.role}</div>
              </div>
            </figcaption>
          </figure>
        ))}
      </div>
    </section>
  );
}

// ── Newsletter band (entre rangées) ───────────────────────────────────────
function NewsletterBand() {
  const [email, setEmail] = useState("");
  const [done, setDone] = useState(false);
  const submit = async (e) => {
    e.preventDefault();
    if (!email.includes("@")) return;
    try { await api.post("/shop/waitlist", { email, discount_optin: true }); } catch {}
    setDone(true);
  };
  return (
    <section className="relative overflow-hidden rounded-2xl p-6 md:p-12 mb-20 grid md:grid-cols-2 gap-6 items-center text-white"
             style={{ background: "var(--zayado-navy-gradient)" }} data-testid="shop-newsletter-band">
      <div>
        <div className="text-[11px] uppercase tracking-[0.25em] mb-2"
             style={{ color: "var(--zayado-gold)" }}>Newsletter</div>
        <h3 className="font-display italic mb-3 leading-tight"
            style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)",
                     fontSize: "clamp(1.5rem, 3vw, 2.2rem)", color: "#ffffff" }}>
          Recevez nos pépites <em style={{ color: "var(--zayado-gold)" }}>en avant-première.</em>
        </h3>
        <p className="text-sm md:text-base mb-2 text-white/80">
          1 email tous les 15 jours · Rituels d'entrepreneur, ventes privées, nouveautés.
          <strong className="text-white"> −10% sur votre 1ère commande.</strong>
        </p>
      </div>
      {!done ? (
        <form onSubmit={submit} className="flex items-center gap-2 p-1.5 rounded-full bg-white">
          <Mail size={16} className="ml-3 text-[var(--zayado-muted)]" />
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                 placeholder="votre@email.com" required
                 className="flex-1 bg-transparent px-2 py-2 focus:outline-none text-sm text-[var(--zayado-text)]"
                 data-testid="newsletter-email" />
          <button type="submit"
                  className="btn-press inline-flex items-center gap-1.5 rounded-full px-5 py-2 text-white font-medium text-sm"
                  style={{ background: "var(--zayado-gold)" }} data-testid="newsletter-submit">
            S'inscrire <ArrowRight size={13} />
          </button>
        </form>
      ) : (
        <div className="p-4 rounded-full bg-white inline-flex items-center gap-2 text-sm text-[var(--zayado-text)]"
             data-testid="newsletter-done">
          <Check size={15} style={{ color: "var(--zayado-gold)" }} /> Merci ! Votre code −10% arrive par email.
        </div>
      )}
    </section>
  );
}

// ── Édito conseils ────────────────────────────────────────────────────────
function EditoConseils() {
  const articles = [
    {
      img: "https://images.unsplash.com/photo-1499209974431-9dddcece7f88?auto=format&w=800&q=80",
      kicker: "Ergonomie",
      title: "5 réglages essentiels pour un poste sain",
      excerpt: "Hauteur d'écran, posture, éclairage… les détails qui sauvent vos cervicales.",
    },
    {
      img: "https://images.unsplash.com/photo-1545389336-cf090694435e?auto=format&w=800&q=80",
      kicker: "Rituel",
      title: "Construire son rituel matinal d'entrepreneur",
      excerpt: "3 étapes en 7 minutes pour rentrer dans la journée avec clarté.",
    },
    {
      img: "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&w=800&q=80",
      kicker: "Lecture",
      title: "Les 6 livres qui ont changé notre rapport au travail",
      excerpt: "Sélection de la rédaction Zayado : essentialisme, deep work, ikigai.",
    },
  ];
  return (
    <section className="mb-20" data-testid="shop-edito">
      <div className="flex items-end justify-between mb-6">
        <div>
          <div className="text-[11px] uppercase tracking-[0.25em] mb-1" style={{ color: GOLD }}>Conseils</div>
          <h2 className="font-display italic"
              style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)",
                       fontSize: "clamp(1.6rem, 3.5vw, 2.4rem)", color: "var(--zayado-text)" }}>
            Le journal Zayado.
          </h2>
        </div>
        <a href="/articles" className="text-sm font-medium hover:underline" style={{ color: NAVY }}>
          Tous les articles →
        </a>
      </div>
      <div className="grid md:grid-cols-3 gap-4 md:gap-6">
        {articles.map((a, i) => (
          <article key={i} className="group cursor-pointer" data-testid={`edito-${i}`}>
            <div className="aspect-[4/3] overflow-hidden rounded-lg mb-3">
              <img src={a.img} alt={a.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700" />
            </div>
            <div className="text-[10px] uppercase tracking-wider mb-1" style={{ color: GOLD }}>{a.kicker}</div>
            <h3 className="font-display text-lg leading-tight mb-2 group-hover:underline"
                style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)",
                         color: "var(--zayado-text)" }}>
              {a.title}
            </h3>
            <p className="text-sm" style={{ color: MUTED }}>{a.excerpt}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

// ── Catalogue wellness-style (mode actif) ─────────────────────────────────
function Catalog({ openCart, cart, setCart, source }) {
  const loc = useLocation();
  const urlUniverse = new URLSearchParams(loc.search).get("u");
  const [universe, setUniverse] = useState(urlUniverse === "corps" || urlUniverse === "ame" ? urlUniverse : "all");
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("featured");
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  // Sync universe ← URL param ?u= (depuis le mega-menu du header)
  useEffect(() => {
    if (urlUniverse === "corps" || urlUniverse === "ame") setUniverse(urlUniverse);
    else if (urlUniverse === null) setUniverse("all");
  }, [urlUniverse]);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    const params = new URLSearchParams();
    if (universe !== "all") params.set("universe", universe);
    if (search) params.set("search", search);
    params.set("sort", sort);
    params.set("preview", "1");
    api.get(`/shop/products?${params.toString()}`)
      .then((r) => { if (alive) setProducts(r.data.products || []); })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, [universe, search, sort]);

  const addToCart = (p) => {
    addToCartEvt({ slug: p.slug, name: p.name, price: p.price, image: p.images?.[0]?.src }, 1);
  };

  // Découpages thématiques pour les rangées — produits distincts entre sections
  const coupsDeCoeur = useMemo(() => products.filter(p => p.featured).slice(0, 6), [products]);
  const nouveautes = useMemo(() => [...products].sort((a, b) => (b.id || 0) - (a.id || 0)).slice(0, 6), [products]);
  const petitsPrix = useMemo(() => [...products].filter(p => parseFloat(p.price) < 30).slice(0, 6), [products]);
  const topVentes = useMemo(
    () => [...products].sort((a, b) => (b.rating_count || 0) - (a.rating_count || 0)).slice(0, 6),
    [products]
  );
  const ecoConcus = useMemo(() => [...products].filter(p => {
    const b = (p.badge || "").toLowerCase();
    return b.includes("éco") || b === "bio" || b === "soja" || b === "artisanal";
  }).slice(0, 6), [products]);
  const all = products;

  const showSourceBanner = source !== "woocommerce";

  return (
    <div className="max-w-[1320px] mx-auto" data-testid="shop-catalog">
      {/* Bandeau preview mock */}
      {showSourceBanner && (
        <div className="mb-4 px-4 py-2 rounded-md text-xs flex items-center gap-2"
             style={{ background: "var(--zayado-gold-bg)", color: GOLD }}
             data-testid="shop-source-banner">
          <Eye size={13} />
          <span><strong>Aperçu mockup</strong> — les produits affichés sont fictifs. Ils seront remplacés par WooCommerce dès connexion des clés API.</span>
        </div>
      )}

      {/* La nav catégories Corps/Âme vit dans le header Kiabi du wrapper public.
          Le filtre `universe` est synchronisé via les URL params ?u=corps|ame. */}

      {/* Hero éditorial — wellness style */}
      <section className="relative rounded-2xl overflow-hidden mb-6 md:mb-8 aspect-[21/9] md:aspect-[24/9]"
               data-testid="shop-hero">
        <img src="https://images.unsplash.com/photo-1499209974431-9dddcece7f88?auto=format&w=1600&q=80"
             alt="Hero" className="absolute inset-0 w-full h-full object-cover" />
        <div className="absolute inset-0" style={{ background: "linear-gradient(90deg, rgba(20,42,71,0.85) 0%, rgba(20,42,71,0.45) 60%, transparent 100%)" }} />
        <div className="relative h-full flex flex-col justify-center px-6 md:px-14 max-w-[640px]">
          <div className="text-[11px] uppercase tracking-[0.3em] mb-3 text-white/80">
            La boutique des entrepreneurs apaisés
          </div>
          <h1 className="font-display italic leading-[1.02] mb-4 text-white"
              style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)",
                       fontSize: "clamp(2rem, 5.5vw, 3.8rem)" }}>
            Le bureau, <em style={{ color: GOLD_SOFT, fontStyle: "italic" }}>autrement.</em>
          </h1>
          <p className="text-sm md:text-base text-white/85 mb-6 max-w-md leading-relaxed">
            La première boutique dédiée au bien-être des entrepreneurs — pour le corps qui travaille, et l'âme qui respire.
          </p>
          <div className="flex flex-wrap gap-2">
            <button onClick={() => setUniverse("corps")}
                    className="px-5 py-2.5 rounded-full bg-white text-[var(--zayado-navy)] font-medium text-sm btn-press"
                    data-testid="hero-cta-corps">
              Explorer le Corps <ArrowRight size={13} className="inline ml-1" />
            </button>
            <button onClick={() => setUniverse("ame")}
                    className="px-5 py-2.5 rounded-full border border-white/40 text-white font-medium text-sm btn-press hover:bg-white/10"
                    data-testid="hero-cta-ame">
              Explorer l'Âme <ArrowRight size={13} className="inline ml-1" />
            </button>
          </div>
        </div>
      </section>

      {/* Trust signals row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-6 py-4 mb-8 border-y border-[var(--zayado-border)]"
           data-testid="shop-trust-row">
        {[
          { icon: Truck, text: "Livraison offerte dès 50€" },
          { icon: ShieldCheck, text: "Paiement sécurisé" },
          { icon: RotateCcw, text: "Retours gratuits 30j" },
          { icon: Leaf, text: "Marques durables sélectionnées" },
        ].map((t, i) => {
          const I = t.icon;
          return (
            <div key={i} className="flex items-center gap-2 text-xs md:text-sm" style={{ color: "var(--zayado-text)" }}>
              <I size={15} style={{ color: GOLD }} />
              <span className="font-medium">{t.text}</span>
            </div>
          );
        })}
      </div>

      {/* Recherche + tri (sticky léger) — la nav Corps/Âme et la search globale vivent dans le header Kiabi du wrapper public. */}
      <div className="flex flex-wrap items-center justify-between gap-2 mb-8" data-testid="shop-toolbar">
        <div className="text-xs" style={{ color: MUTED }}>
          {universe === "all" ? "Tous les produits" : universe === "corps" ? "Univers Corps" : "Univers Âme"} · {products.length} article{products.length > 1 ? "s" : ""}
        </div>
        <select value={sort} onChange={(e) => setSort(e.target.value)}
                className="px-4 py-2.5 text-sm rounded-full border border-[var(--zayado-border)] bg-white focus:outline-none cursor-pointer"
                data-testid="shop-sort">
          <option value="featured">★ Mis en avant</option>
          <option value="price_asc">Prix croissant</option>
          <option value="price_desc">Prix décroissant</option>
          <option value="rating">Meilleures notes</option>
          <option value="new">Nouveautés</option>
        </select>
      </div>

      {loading ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 md:gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="aspect-[3/4] rounded-lg bg-[var(--zayado-cream-dark)] animate-pulse" />
          ))}
        </div>
      ) : products.length === 0 ? (
        <div className="text-center py-16" style={{ color: MUTED }} data-testid="shop-empty">
          <Search size={32} className="mx-auto mb-3 opacity-50" />
          Aucun produit ne correspond à votre recherche.
        </div>
      ) : (
        <>
          {/* 2 tuiles univers split */}
          <UniverseTiles onPick={setUniverse} />

          {/* Section : Les essentiels du moment */}
          {coupsDeCoeur.length > 0 && (
            <ProductRow
              title="Les essentiels du moment"
              subtitle="Sélection"
              products={coupsDeCoeur}
              onAdd={addToCart}
              accent={GOLD_SOFT}
            />
          )}

          {/* Section éditoriale — Le rituel Zayado */}
          <RitualSection />

          {/* Section : Les pépites du moment */}
          {nouveautes.length > 0 && (
            <ProductRow
              title="Nos nouveautés"
              subtitle="Tout juste arrivés"
              products={nouveautes}
              onAdd={addToCart}
            />
          )}

          {/* Section : Petits prix */}
          {petitsPrix.length > 0 && (
            <ProductRow
              title="Petits prix, grands effets"
              subtitle="Tout à moins de 30€"
              products={petitsPrix}
              onAdd={addToCart}
            />
          )}

          {/* Top ventes */}
          {topVentes.length > 0 && (
            <ProductRow
              title="Vos top ventes"
              subtitle="Les chouchous de la communauté"
              products={topVentes}
              onAdd={addToCart}
              accent={GOLD}
            />
          )}

          {/* Éco-conçus */}
          {ecoConcus.length > 0 && (
            <ProductRow
              title="Éco-conçus"
              subtitle="Matériaux durables, production locale"
              products={ecoConcus}
              onAdd={addToCart}
            />
          )}

          {/* Encart Newsletter */}
          <NewsletterBand />

          {/* Édito Conseils */}
          <EditoConseils />

          {/* CTA vers la sélection complète (page dédiée) */}
          <section className="mb-16 text-center" data-testid="shop-cta-selection">
            <Link to="/shop/selection"
                  className="inline-flex items-center gap-2 px-7 py-3.5 rounded-full text-sm font-bold text-white hover:opacity-90 transition"
                  style={{ background: "var(--zayado-navy)" }}>
              Voir toute la sélection <ArrowRight size={14} />
            </Link>
            <p className="text-xs mt-3" style={{ color: MUTED }}>
              Toute la sélection sur une page dédiée, organisée par univers et catégorie.
            </p>
          </section>

          {/* Testimonials nominatifs */}
          <TestimonialsSection />

          {/* Services / réassurance */}
          <ServicesSection />
        </>
      )}
    </div>
  );
}

// ── Mega Footer ───────────────────────────────────────────────────────────
function ShopFooter() {
  return (
    <footer className="mt-12 pt-10 pb-6 border-t border-[var(--zayado-border)]"
            style={{ background: "var(--zayado-cream-dark)" }} data-testid="shop-footer">
      <div className="max-w-[1280px] mx-auto px-6 grid grid-cols-2 md:grid-cols-5 gap-8 mb-8">
        <div className="col-span-2">
          <div className="font-display italic text-2xl mb-2" style={{ color: NAVY, fontFamily: "var(--font-serif, 'DM Serif Display', serif)" }}>
            Zayado
          </div>
          <p className="text-xs leading-relaxed mb-3 max-w-xs" style={{ color: MUTED }}>
            L'essentiel pour les entrepreneurs qui construisent leur trajectoire avec calme. Petites séries, production locale.
          </p>
          <div className="flex items-center gap-1 text-xs" style={{ color: MUTED }}>
            <MapPin size={12} /> Conçu en France
          </div>
        </div>
        {[
          { title: "Corps", links: ["Lunettes", "Ergonomie", "Posture", "Huiles essentielles"] },
          { title: "Âme", links: ["Méditation", "Encens", "Cristaux", "Bougies", "Livres", "Audio"] },
          { title: "Services", links: ["E-réservation", "Livraison", "Retours 30j", "FAQ", "Contact"] },
        ].map((col) => (
          <div key={col.title}>
            <div className="text-xs uppercase tracking-wider font-bold mb-3" style={{ color: "var(--zayado-text)" }}>{col.title}</div>
            <ul className="space-y-1.5">
              {col.links.map((l) => (
                <li key={l}><Link to="#" className="text-xs hover:underline" style={{ color: MUTED }}>{l}</Link></li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <div className="max-w-[1280px] mx-auto px-6 pt-6 border-t border-[var(--zayado-border)] flex flex-wrap items-center justify-between gap-3 text-[11px]"
           style={{ color: MUTED }}>
        <div>© {new Date().getFullYear()} Zayado · Boutique propulsée par WooCommerce</div>
        <div className="flex gap-4">
          <Link to="/legal/mentions-legales">Mentions légales</Link>
          <Link to="/legal/conditions-utilisation">CGU</Link>
          <Link to="/legal/politique-confidentialite">Confidentialité</Link>
        </div>
        <div className="flex items-center gap-2">
          <CreditCard size={12} /> CB · Apple Pay · PayPal
        </div>
      </div>
    </footer>
  );
}

// ── Grille "Toute la sélection" avec filtres avancés ────────────────────────
export function AllProductsGrid({ products, onAdd }) {
  const catalogMaxPrice = useMemo(() => Math.ceil(Math.max(100, ...products.map((p) => parseFloat(p.price) || 0))), [products]);
  const [priceMax, setPriceMax] = useState(catalogMaxPrice);
  const [brands, setBrands] = useState([]);
  const [ratingMin, setRatingMin] = useState(0);
  const [inStockOnly, setInStockOnly] = useState(false);
  const [showFilters, setShowFilters] = useState(false);

  // Marques disponibles (avec compteur)
  const brandList = useMemo(() => {
    const counts = {};
    products.forEach((p) => {
      const b = p.brand || "Autres";
      counts[b] = (counts[b] || 0) + 1;
    });
    return Object.entries(counts).map(([name, count]) => ({ name, count })).sort((a, b) => b.count - a.count);
  }, [products]);

  // Reset priceMax quand le catalogue change (changement d'univers)
  useEffect(() => { setPriceMax(catalogMaxPrice); }, [catalogMaxPrice]);

  const filtered = useMemo(() => {
    return products.filter((p) => {
      if (parseFloat(p.price) > priceMax) return false;
      if (brands.length > 0 && !brands.includes(p.brand || "Autres")) return false;
      if (ratingMin > 0 && parseFloat(p.average_rating || 0) < ratingMin) return false;
      if (inStockOnly && (p.stock_quantity || 0) <= 0) return false;
      return true;
    });
  }, [products, priceMax, brands, ratingMin, inStockOnly]);

  const toggleBrand = (b) => setBrands((prev) => prev.includes(b) ? prev.filter((x) => x !== b) : [...prev, b]);
  const resetFilters = () => { setPriceMax(catalogMaxPrice); setBrands([]); setRatingMin(0); setInStockOnly(false); };
  const activeCount = (priceMax < catalogMaxPrice ? 1 : 0) + brands.length + (ratingMin > 0 ? 1 : 0) + (inStockOnly ? 1 : 0);

  return (
    <section className="mb-20" data-testid="shop-all-grid">
      <div className="flex items-end justify-between mb-4 gap-3 flex-wrap">
        <h2 className="font-display italic"
            style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)",
                     fontSize: "clamp(1.5rem, 3vw, 2.2rem)", color: "var(--zayado-text)" }}>
          Toute la sélection
        </h2>
        <div className="flex items-center gap-2">
          <button onClick={() => setShowFilters(!showFilters)}
                  className="lg:hidden inline-flex items-center gap-1.5 px-3 py-2 rounded-full text-xs font-medium border border-[var(--zayado-border)] bg-white"
                  data-testid="filters-toggle-mobile">
            Filtres {activeCount > 0 && <span className="px-1.5 py-0.5 rounded-full text-white text-[10px]" style={{ background: NAVY }}>{activeCount}</span>}
          </button>
          <div className="text-xs" style={{ color: MUTED }}>{filtered.length} / {products.length} produit{products.length > 1 ? "s" : ""}</div>
        </div>
      </div>

      <div className="grid lg:grid-cols-[240px_1fr] gap-6">
        <aside className={`${showFilters ? "block" : "hidden"} lg:block`} data-testid="shop-filters">
          <div className="bg-white rounded-xl border border-[var(--zayado-border)] p-5 lg:sticky lg:top-32 space-y-5">
            <div className="flex items-center justify-between">
              <div className="text-sm font-bold" style={{ color: NAVY }}>Filtres</div>
              {activeCount > 0 && (
                <button onClick={resetFilters} className="text-[11px] hover:underline" style={{ color: MUTED }} data-testid="filters-reset">
                  Tout effacer
                </button>
              )}
            </div>

            <div>
              <div className="text-xs font-medium mb-2" style={{ color: "var(--zayado-text)" }}>
                Prix : jusqu'à <strong>{priceMax}€</strong>
              </div>
              <input type="range" min="5" max={catalogMaxPrice} step="5" value={priceMax}
                     onChange={(e) => setPriceMax(parseInt(e.target.value, 10))}
                     className="w-full accent-[var(--zayado-navy)]"
                     data-testid="filter-price" />
              <div className="flex justify-between text-[10px] mt-1" style={{ color: MUTED }}>
                <span>5€</span><span>{catalogMaxPrice}€</span>
              </div>
            </div>

            {brandList.length > 0 && (
              <div>
                <div className="text-xs font-medium mb-2" style={{ color: "var(--zayado-text)" }}>Marques</div>
                <div className="max-h-44 overflow-y-auto space-y-1.5 pr-1">
                  {brandList.slice(0, 12).map((b) => (
                    <label key={b.name} className="flex items-center gap-2 text-xs cursor-pointer hover:underline">
                      <input type="checkbox" checked={brands.includes(b.name)} onChange={() => toggleBrand(b.name)}
                             className="accent-[var(--zayado-navy)]"
                             data-testid={`filter-brand-${b.name.replace(/\s+/g, "-").toLowerCase()}`} />
                      <span className="flex-1 truncate">{b.name}</span>
                      <span style={{ color: MUTED }}>({b.count})</span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            <div>
              <div className="text-xs font-medium mb-2" style={{ color: "var(--zayado-text)" }}>Note minimum</div>
              <div className="flex gap-1">
                {[0, 3, 4, 4.5].map((r) => (
                  <button key={r} onClick={() => setRatingMin(r)}
                          className="flex-1 py-1.5 rounded text-[11px] font-medium border transition-colors"
                          style={{ borderColor: ratingMin === r ? NAVY : "var(--zayado-border)",
                                   background: ratingMin === r ? NAVY : "transparent",
                                   color: ratingMin === r ? "#fff" : "var(--zayado-text)" }}
                          data-testid={`filter-rating-${r}`}>
                    {r === 0 ? "Tous" : `${r}★+`}
                  </button>
                ))}
              </div>
            </div>

            <label className="flex items-center gap-2 text-xs cursor-pointer">
              <input type="checkbox" checked={inStockOnly} onChange={(e) => setInStockOnly(e.target.checked)}
                     className="accent-[var(--zayado-navy)]" data-testid="filter-stock" />
              <span>En stock uniquement</span>
            </label>
          </div>
        </aside>

        <div>
          {filtered.length === 0 ? (
            <div className="text-center py-16 rounded-xl border-2 border-dashed border-[var(--zayado-border)]">
              <Search size={28} className="mx-auto mb-2 opacity-40" />
              <div className="text-sm mb-3" style={{ color: MUTED }}>Aucun produit ne correspond à vos filtres.</div>
              <button onClick={resetFilters} className="text-xs px-4 py-2 rounded-full bg-white border border-[var(--zayado-border)] hover:bg-[var(--zayado-cream)]">
                Réinitialiser les filtres
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-3 xl:grid-cols-4 gap-3 md:gap-4">
              {filtered.map((p) => <ProductCard key={p.slug} p={p} onAdd={onAdd} />)}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

// ── Page principale ───────────────────────────────────────────────────────
export default function Boutique() {
  const [status, setStatus] = useState(null);
  const [cart, setCart] = useState(() => {
    try { return JSON.parse(localStorage.getItem("zay_cart") || "[]"); } catch { return []; }
  });
  const [cartOpen, setCartOpen] = useState(false);
  const location = useLocation();
  const preview = new URLSearchParams(location.search).get("preview");

  useEffect(() => {
    api.get("/shop/status")
      .then((r) => setStatus(r.data))
      .catch(() => setStatus({ maintenance: true, source: "mock" }));
  }, []);

  const showMaintenance = useMemo(() => {
    if (preview === "catalog") return false;
    if (preview === "maintenance") return true;
    return status?.maintenance ?? true;
  }, [status, preview]);

  const cartCount = cart.reduce((s, it) => s + it.quantity, 0);

  if (!status) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center" data-testid="shop-loading">
        <div className="text-sm italic" style={{ color: MUTED }}>Chargement de la boutique…</div>
      </div>
    );
  }

  return (
    <div className="pb-0" data-testid="boutique-page">
      {/* Toggle preview admin — caché en production. Pour debug uniquement,
          ajouter `?preview=catalog` ou `?preview=maintenance&debug=1` dans l'URL.
          L'état réel de maintenance est piloté par WordPress (plugin Maintenance). */}
      {preview && new URLSearchParams(location.search).get("debug") === "1" && (
        <div className="max-w-[1280px] mx-auto px-4 pt-3 flex items-center justify-end gap-2 text-xs">
          <span style={{ color: MUTED }}>Aperçu :</span>
          <Link to="?preview=maintenance&debug=1" className="px-2 py-1 rounded border border-[var(--zayado-border)]"
                style={{ background: showMaintenance ? NAVY : "transparent", color: showMaintenance ? "white" : "var(--zayado-text)" }}>
            Maintenance
          </Link>
          <Link to="?preview=catalog&debug=1" className="px-2 py-1 rounded border border-[var(--zayado-border)]"
                style={{ background: !showMaintenance ? NAVY : "transparent", color: !showMaintenance ? "white" : "var(--zayado-text)" }}>
            Catalogue
          </Link>
        </div>
      )}

      <div className="px-4 md:px-6 pt-4">
        {showMaintenance ? (
          <MaintenanceSplash />
        ) : (
          <Catalog
            cart={cart}
            setCart={setCart}
            openCart={() => setCartOpen(true)}
            source={status.source}
          />
        )}
      </div>

      {!showMaintenance && (
        <button
          onClick={() => setCartOpen(true)}
          className="fixed bottom-6 right-6 z-[60] px-4 py-3 rounded-full shadow-lg flex items-center gap-2 text-white hover:scale-105 transition-transform"
          style={{ background: NAVY }}
          data-testid="shop-cart-fab"
        >
          <ShoppingBag size={16} />
          {cartCount > 0 ? (
            <>
              <span className="text-sm font-medium">{cartCount}</span>
              <span className="text-xs opacity-70">·</span>
              <span className="text-sm font-bold">
                {cart.reduce((s, it) => s + parseFloat(it.price) * it.quantity, 0).toFixed(2)}€
              </span>
            </>
          ) : (
            <span className="text-sm font-medium">Panier</span>
          )}
        </button>
      )}

      <CartDrawer open={cartOpen} onClose={() => setCartOpen(false)} cart={cart} setCart={setCart} />
    </div>
  );
}
