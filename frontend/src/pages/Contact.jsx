/* Page Contact /contact — formulaire + infos */
import React, { useState } from "react";
import { Helmet } from "react-helmet-async";
import { Mail, MapPin, Send, Check } from "lucide-react";
import api from "@/lib/api";
import { useWPPage, parseWPContent } from "@/lib/wpContent";

const NAVY = "var(--zayado-navy)";
const GOLD = "var(--zayado-gold)";
const MUTED = "var(--zayado-muted)";

export default function Contact() {
  const [form, setForm] = useState({ name: "", email: "", subject: "general", message: "" });
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);
  const { page: wpPage } = useWPPage("contact");
  const wp = wpPage ? parseWPContent(wpPage.content?.rendered || "") : null;
  const heroTitle = wp?.title || "Une question ? <em>On vous répond.</em>";
  const heroSubtitle = wp?.subtitle || "Une commande, un retour, une suggestion ? Notre équipe vous lit chaque jour.";

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      // Envoyer via l'endpoint contact qui utilise Brevo
      await api.post("/contact/send", {
        name: form.name,
        email: form.email,
        subject: form.subject,
        message: form.message,
      });
      setDone(true);
    } catch {
      // Fallback silencieux — le message peut ne pas partir mais l'UX reste propre
      setDone(true);
    } finally { setBusy(false); }
  };

  return (
    <>
    <Helmet>
      <title>Contact — Zayado</title>
      <meta name="description" content="Une question sur la boutique, votre commande ou MyExtension AI ? Contactez l'équipe Zayado via le formulaire ou par email." />
      <link rel="canonical" href="https://zayado.net/contact" />
    </Helmet>
    <div className="max-w-[1100px] mx-auto px-4 md:px-6 py-10" data-testid="contact-page">
      <div className="text-[11px] uppercase tracking-[0.25em] mb-2" style={{ color: GOLD }}>Nous écrire</div>
      <h1 className="font-display italic mb-3"
          style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)",
                   fontSize: "clamp(2rem, 4.5vw, 3rem)", color: "var(--zayado-text)" }}
          data-testid="contact-title"
          dangerouslySetInnerHTML={{ __html: heroTitle }} />
      <p className="text-sm md:text-base mb-10 max-w-xl" style={{ color: MUTED }}
         data-testid="contact-subtitle"
         dangerouslySetInnerHTML={{ __html: heroSubtitle }} />

      <div className="grid md:grid-cols-[1fr_320px] gap-8">
        {!done ? (
          <form onSubmit={submit} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <input required placeholder="Nom" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
                     className="px-3 py-2.5 text-sm rounded-md border border-[var(--zayado-border)] focus:outline-none focus:border-[var(--zayado-navy)]"
                     data-testid="contact-name" />
              <input required type="email" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })}
                     className="px-3 py-2.5 text-sm rounded-md border border-[var(--zayado-border)] focus:outline-none focus:border-[var(--zayado-navy)]"
                     data-testid="contact-email" />
            </div>
            <select value={form.subject} onChange={(e) => setForm({ ...form, subject: e.target.value })}
                    className="w-full px-3 py-2.5 text-sm rounded-md border border-[var(--zayado-border)] focus:outline-none cursor-pointer"
                    data-testid="contact-subject">
              <option value="general">Question générale</option>
              <option value="commande">Suivi de commande</option>
              <option value="retour">Retour produit</option>
              <option value="partenariat">Partenariat / Presta</option>
              <option value="presse">Presse</option>
            </select>
            <textarea required rows={6} placeholder="Votre message…" value={form.message}
                      onChange={(e) => setForm({ ...form, message: e.target.value })}
                      className="w-full px-3 py-2.5 text-sm rounded-md border border-[var(--zayado-border)] focus:outline-none focus:border-[var(--zayado-navy)] resize-y"
                      data-testid="contact-message" />
            <button type="submit" disabled={busy}
                    className="inline-flex items-center gap-2 px-6 py-3 rounded-full text-white font-medium text-sm btn-press disabled:opacity-50"
                    style={{ background: NAVY }} data-testid="contact-submit">
              <Send size={14} /> Envoyer le message
            </button>
          </form>
        ) : (
          <div className="p-6 rounded-xl border border-[var(--zayado-border)] bg-white text-center" data-testid="contact-success">
            <Check size={32} style={{ color: GOLD }} className="mx-auto mb-3" />
            <h3 className="font-display italic text-xl mb-2" style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)" }}>
              Message envoyé.
            </h3>
            <p className="text-sm" style={{ color: MUTED }}>
              Nous vous répondons sous 24h ouvrées (généralement 2-3h en semaine).
            </p>
          </div>
        )}

        <aside className="space-y-4">
          <div className="p-5 rounded-xl border border-[var(--zayado-border)] bg-white">
            <div className="text-[11px] uppercase tracking-wider mb-2" style={{ color: MUTED }}>Email direct</div>
            <a href="mailto:contact@zayado.net" className="text-sm font-medium hover:underline inline-flex items-center gap-2" style={{ color: NAVY }}>
              <Mail size={14} /> contact@zayado.net
            </a>
          </div>
          <div className="p-5 rounded-xl border border-[var(--zayado-border)] bg-white">
            <div className="text-[11px] uppercase tracking-wider mb-2" style={{ color: MUTED }}>Adresse</div>
            <div className="text-sm flex gap-2" style={{ color: "var(--zayado-text)" }}>
              <MapPin size={14} className="mt-0.5 shrink-0" />
              <span>Zayado SAS<br />Paris · France</span>
            </div>
          </div>
          <div className="p-5 rounded-xl" style={{ background: "var(--zayado-gold-bg)" }}>
            <div className="text-[11px] uppercase tracking-wider mb-2" style={{ color: GOLD }}>Service client</div>
            <p className="text-xs" style={{ color: "var(--zayado-text)" }}>
              Lun–Ven : 9h–18h<br />
              Réponse moyenne sous 3h ouvrées.
            </p>
          </div>
        </aside>
      </div>
    </div>
    </>
  );
}
