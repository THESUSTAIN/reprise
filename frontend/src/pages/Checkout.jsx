/* Page checkout simulation /checkout — formulaire adresse + récap + bouton "Payer (simulation)" */
import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { ShieldCheck, ArrowRight, CreditCard, Lock, Check } from "lucide-react";
import api from "@/lib/api";

const NAVY = "var(--zayado-navy)";
const GOLD = "var(--zayado-gold)";
const MUTED = "var(--zayado-muted)";

export default function Checkout() {
  const navigate = useNavigate();
  const [cart, setCart] = useState([]);
  const [step, setStep] = useState("form"); // form | success
  const [orderId, setOrderId] = useState(null);
  const [form, setForm] = useState({
    email: "", first_name: "", last_name: "", address: "", zip: "", city: "", country: "France",
  });

  useEffect(() => {
    try { setCart(JSON.parse(localStorage.getItem("zay_cart") || "[]")); } catch {}
  }, []);

  const subtotal = cart.reduce((s, it) => s + parseFloat(it.price) * it.quantity, 0);
  const shipping = subtotal >= 50 ? 0 : 4.9;
  const total = subtotal + shipping;

  const [submitError, setSubmitError] = useState("");
  // `setBusy` était appelé sans jamais avoir été déclaré : le clic sur
  // « Payer » levait un ReferenceError et la commande ne partait jamais.
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setSubmitError("");
    setBusy(true);

    try {
      // Créer la commande WooCommerce via le backend
      const r = await (
        api.post("/shop/checkout", {
          email: form.email,
          first_name: form.first_name,
          last_name: form.last_name,
          address: form.address,
          zip: form.zip,
          city: form.city,
          country: form.country,
          items: cart.map((it) => ({ slug: it.slug, quantity: it.quantity })),
        })
      );

      if (r.data?.payment_url) {
        // Rediriger vers Mollie/Stripe pour le paiement
        window.location.href = r.data.payment_url;
        return;
      }

      if (r.data?.order_id) {
        setOrderId(r.data.order_id);
        setStep("success");
        localStorage.removeItem("zay_cart");
        return;
      }

      throw new Error("Réponse inattendue du serveur.");
    } catch (err) {
      const msg = err?.response?.data?.detail || err?.message || "Erreur lors de la commande.";
      setSubmitError(msg);
    } finally {
      // Sans ce finally, un échec réseau laissait le bouton bloqué en
      // « Traitement… » sans jamais permettre de réessayer.
      setBusy(false);
    }
  };

  if (step === "success") {
    return (
      <div className="max-w-[700px] mx-auto px-4 py-16 text-center" data-testid="checkout-success">
        <div className="w-20 h-20 mx-auto mb-6 rounded-full flex items-center justify-center"
             style={{ background: "var(--zayado-gold-bg)" }}>
          <Check size={36} style={{ color: GOLD }} />
        </div>
        <div className="text-[11px] uppercase tracking-[0.25em] mb-2" style={{ color: GOLD }}>Commande confirmée</div>
        <h1 className="font-display italic mb-3"
            style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)",
                     fontSize: "clamp(1.8rem, 4vw, 2.6rem)", color: "var(--zayado-text)" }}>
          Merci pour votre confiance.
        </h1>
        <p className="text-sm md:text-base mb-2" style={{ color: MUTED }}>
          Votre numéro de commande : <strong style={{ color: "var(--zayado-text)" }}>{orderId}</strong>
        </p>
        <p className="text-sm mb-8" style={{ color: MUTED }}>
          Un email de confirmation a été envoyé à <strong>{form.email}</strong>.
        </p>

        <div className="flex gap-2 justify-center">
          <Link to="/boutique" className="px-5 py-2.5 rounded-full text-white text-sm font-medium" style={{ background: NAVY }}>
            Retour à la boutique
          </Link>
        </div>
      </div>
    );
  }

  return (
    <>
    <Helmet>
      <title>Paiement — Zayado</title>
      <meta name="robots" content="noindex, follow" />
    </Helmet>
    <div className="max-w-[1100px] mx-auto px-4 md:px-6 py-8" data-testid="checkout-page">
      <div className="text-[11px] uppercase tracking-[0.25em] mb-2" style={{ color: GOLD }}>Paiement</div>
      <h1 className="font-display italic mb-7"
          style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)",
                   fontSize: "clamp(1.8rem, 4vw, 2.6rem)", color: "var(--zayado-text)" }}>
        Finaliser ma commande
      </h1>

      <div className="grid lg:grid-cols-[1fr_360px] gap-6">
        <form onSubmit={submit} className="space-y-5">
          <section className="p-5 rounded-xl border border-[var(--zayado-border)] bg-white">
            <h2 className="font-medium text-base mb-4">Contact</h2>
            <input type="email" required placeholder="Email" value={form.email}
                   onChange={(e) => setForm({ ...form, email: e.target.value })}
                   className="w-full px-3 py-2.5 text-sm rounded-md border border-[var(--zayado-border)] focus:outline-none focus:border-[var(--zayado-navy)]"
                   data-testid="checkout-email" />
          </section>

          <section className="p-5 rounded-xl border border-[var(--zayado-border)] bg-white">
            <h2 className="font-medium text-base mb-4">Adresse de livraison</h2>
            <div className="grid grid-cols-2 gap-3 mb-3">
              <input required placeholder="Prénom" value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} className="px-3 py-2.5 text-sm rounded-md border border-[var(--zayado-border)] focus:outline-none focus:border-[var(--zayado-navy)]" />
              <input required placeholder="Nom" value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} className="px-3 py-2.5 text-sm rounded-md border border-[var(--zayado-border)] focus:outline-none focus:border-[var(--zayado-navy)]" />
            </div>
            <input required placeholder="Adresse" value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} className="w-full px-3 py-2.5 text-sm rounded-md border border-[var(--zayado-border)] focus:outline-none focus:border-[var(--zayado-navy)] mb-3" />
            <div className="grid grid-cols-3 gap-3">
              <input required placeholder="Code postal" value={form.zip} onChange={(e) => setForm({ ...form, zip: e.target.value })} className="px-3 py-2.5 text-sm rounded-md border border-[var(--zayado-border)] focus:outline-none focus:border-[var(--zayado-navy)]" />
              <input required placeholder="Ville" value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} className="col-span-2 px-3 py-2.5 text-sm rounded-md border border-[var(--zayado-border)] focus:outline-none focus:border-[var(--zayado-navy)]" />
            </div>
          </section>

          <section className="p-5 rounded-xl border border-[var(--zayado-border)] bg-white">
            <h2 className="font-medium text-base mb-4">Mode de paiement</h2>

            <div className="flex items-center gap-3 p-3 rounded-md border-2 border-[var(--zayado-navy)]">
              <CreditCard size={18} style={{ color: NAVY }} />
              <span className="text-sm font-medium">Carte bancaire (simulation)</span>
              <span className="ml-auto text-[10px] px-2 py-0.5 rounded-full" style={{ background: NAVY, color: "white" }}>Sélectionné</span>
            </div>
          </section>

          {submitError && (
            <div className="text-sm text-red-700 bg-red-50 px-4 py-3 rounded-xl" data-testid="checkout-error">
              ❌ {submitError}
            </div>
          )}
          <button type="submit" disabled={busy || cart.length === 0}
                  className="w-full py-3.5 rounded-full text-white font-medium btn-press disabled:opacity-60 disabled:cursor-not-allowed"
                  style={{ background: NAVY }} data-testid="checkout-submit">
            <Lock size={14} className="inline mr-2" />
            {busy ? "Traitement en cours…" : cart.length === 0 ? "Votre panier est vide" : `Payer ${total.toFixed(2)}€`}
          </button>
        </form>

        <aside>
          <div className="p-5 rounded-xl border border-[var(--zayado-border)] bg-white sticky top-4">
            <h3 className="font-display italic text-lg mb-4" style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)", color: "var(--zayado-text)" }}>
              Votre commande
            </h3>
            <ul className="space-y-3 mb-4 max-h-[280px] overflow-y-auto">
              {cart.map((it) => (
                <li key={it.slug} className="flex gap-3">
                  <img src={it.image} alt="" className="w-12 h-12 rounded object-cover shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm line-clamp-2">{it.name}</div>
                    <div className="text-xs" style={{ color: MUTED }}>×{it.quantity}</div>
                  </div>
                  <div className="text-sm font-medium whitespace-nowrap">{(parseFloat(it.price) * it.quantity).toFixed(2)}€</div>
                </li>
              ))}
            </ul>
            <div className="space-y-1.5 text-sm pt-4 border-t border-[var(--zayado-border)]" style={{ color: MUTED }}>
              <div className="flex justify-between"><span>Sous-total</span><span>{subtotal.toFixed(2)}€</span></div>
              <div className="flex justify-between"><span>Livraison</span><span>{shipping === 0 ? "Gratuit" : `${shipping.toFixed(2)}€`}</span></div>
              <div className="flex justify-between font-bold text-base pt-2 mt-2 border-t border-[var(--zayado-border)]" style={{ color: "var(--zayado-text)" }}>
                <span>Total</span><span>{total.toFixed(2)}€</span>
              </div>
            </div>
            <div className="mt-3 flex items-center gap-1.5 text-[11px]" style={{ color: MUTED }}>
              <ShieldCheck size={12} /> Paiement sécurisé · SSL 256-bits
            </div>
          </div>
        </aside>
      </div>
    </div>
    </>
  );
}
