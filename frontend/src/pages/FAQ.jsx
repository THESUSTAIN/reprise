/* Page FAQ /faq */
import React, { useState } from "react";
import { Helmet } from "react-helmet-async";
import { ChevronDown, Search } from "lucide-react";
import { useWPPage, parseWPContent } from "@/lib/wpContent";

const NAVY = "var(--zayado-navy)";
const GOLD = "var(--zayado-gold)";
const MUTED = "var(--zayado-muted)";

const FAQS = [
  {
    cat: "Commandes",
    items: [
      { q: "Quels sont les délais de livraison ?", a: "Expédition sous 24-48h ouvrées. Livraison France métropolitaine : 2-4 jours via Colissimo. Europe : 5-7 jours. Suivi par email automatique." },
      { q: "La livraison est-elle offerte ?", a: "Oui, dès 50€ d'achat en France métropolitaine. En-dessous, 4.90€ via Colissimo Suivi." },
      { q: "Comment suivre ma commande ?", a: "Un email de confirmation est envoyé à la commande, puis un email avec le numéro de suivi La Poste dès l'expédition." },
      { q: "Puis-je modifier ou annuler ma commande ?", a: "Oui, dans les 2h suivant la commande, contactez-nous à contact@zayado.net. Au-delà, le colis est généralement préparé." },
    ],
  },
  {
    cat: "Retours & remboursements",
    items: [
      { q: "Quelle est votre politique de retour ?", a: "30 jours pour changer d'avis, sans justification. Retour gratuit en France métropolitaine via étiquette pré-payée envoyée sur simple demande." },
      { q: "Quand suis-je remboursé·e ?", a: "Sous 5-7 jours ouvrés après réception et inspection du colis retourné, sur le moyen de paiement utilisé." },
      { q: "Que faire si mon produit est défectueux ?", a: "Contactez-nous sous 14 jours avec une photo : remplacement ou remboursement immédiat, sans frais." },
    ],
  },
  {
    cat: "Produits",
    items: [
      { q: "Vos produits sont-ils éco-conçus ?", a: "Oui, 100% de notre catalogue est sélectionné selon des critères stricts : production locale (France/Europe), matériaux durables, marques familiales engagées." },
      { q: "Y a-t-il une garantie sur les produits ?", a: "Garantie légale de conformité 2 ans + garantie commerciale fabricant variable (12 à 36 mois selon les marques)." },
      { q: "Vendez-vous des cartes cadeaux ?", a: "Bientôt — cartes cadeaux digitales en cours de mise en place. Inscrivez-vous à la newsletter pour être prévenu·e." },
    ],
  },
  {
    cat: "Compte & confidentialité",
    items: [
      { q: "Comment supprimer mon compte ?", a: "Depuis vos paramètres → 'Supprimer mon compte'. Vos données sont effacées sous 30 jours. Vous pouvez aussi nous écrire à contact@zayado.net." },
      { q: "Mes données sont-elles partagées ?", a: "Non, jamais. Vos données restent en France (RGPD strict) et ne sont jamais revendues. Voir notre politique de confidentialité." },
      { q: "Comment me désinscrire de la newsletter ?", a: "1 clic en bas de chaque email reçu. Vous pouvez aussi nous écrire." },
    ],
  },
];

export default function FAQ() {
  const [search, setSearch] = useState("");
  const [open, setOpen] = useState({});
  const { page: wpPage } = useWPPage("faq");
  const wp = wpPage ? parseWPContent(wpPage.content?.rendered || "") : null;
  const heroTitle = wp?.title || "On vous répond.";
  const heroSubtitle = wp?.subtitle || "Une question qui n'est pas dans cette liste ? <a href=\"#/contact\" class=\"underline\">Écrivez-nous</a>, on répond sous 3h.";

  const filtered = FAQS.map((cat) => ({
    ...cat,
    items: cat.items.filter(
      (i) => !search || i.q.toLowerCase().includes(search.toLowerCase()) || i.a.toLowerCase().includes(search.toLowerCase())
    ),
  })).filter((c) => c.items.length > 0);

  return (
    <>
    <Helmet>
      <title>FAQ — Questions fréquentes sur Zayado</title>
      <meta name="description" content="Livraison, commandes, abonnement MyExtension AI, retours : toutes les réponses aux questions fréquentes sur Zayado." />
      <link rel="canonical" href="https://zayado.net/faq" />
    </Helmet>
    <div className="max-w-[900px] mx-auto px-4 md:px-6 py-10" data-testid="faq-page">
      <div className="text-[11px] uppercase tracking-[0.25em] mb-2" style={{ color: GOLD }}>Questions fréquentes</div>
      <h1 className="font-display italic mb-3"
          style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)",
                   fontSize: "clamp(2rem, 4.5vw, 3rem)", color: "var(--zayado-text)" }}
          data-testid="faq-title"
          dangerouslySetInnerHTML={{ __html: heroTitle }} />
      <p className="text-sm md:text-base mb-8" style={{ color: MUTED }}
         data-testid="faq-subtitle"
         dangerouslySetInnerHTML={{ __html: heroSubtitle }} />

      <div className="relative mb-8">
        <Search size={15} className="absolute left-4 top-1/2 -translate-y-1/2 text-[var(--zayado-muted)]" />
        <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Rechercher une question…"
               className="w-full pl-11 pr-4 py-3 text-sm rounded-full border border-[var(--zayado-border)] bg-white focus:outline-none focus:border-[var(--zayado-navy)]"
               data-testid="faq-search" />
      </div>

      {filtered.length === 0 ? (
        <div className="text-center py-12 text-sm" style={{ color: MUTED }}>
          Aucun résultat. Essayez d'autres mots-clés ou <a href="/contact" className="underline">contactez-nous</a>.
        </div>
      ) : filtered.map((cat) => (
        <section key={cat.cat} className="mb-8" data-testid={`faq-cat-${cat.cat.toLowerCase()}`}>
          <h2 className="font-display italic mb-3"
              style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)",
                       fontSize: "1.5rem", color: NAVY }}>
            {cat.cat}
          </h2>
          <div className="space-y-1 border border-[var(--zayado-border)] rounded-lg bg-white overflow-hidden">
            {cat.items.map((it, i) => {
              const k = `${cat.cat}_${i}`;
              const isOpen = open[k];
              return (
                <div key={i} className="border-b border-[var(--zayado-border)] last:border-b-0">
                  <button onClick={() => setOpen({ ...open, [k]: !isOpen })}
                          className="w-full flex items-center justify-between gap-3 px-4 py-3.5 text-left hover:bg-[var(--zayado-cream)] transition-colors"
                          data-testid={`faq-q-${k}`}>
                    <span className="text-sm font-medium" style={{ color: "var(--zayado-text)" }}>{it.q}</span>
                    <ChevronDown size={15} className="shrink-0 transition-transform" style={{ transform: isOpen ? "rotate(180deg)" : "rotate(0)" }} />
                  </button>
                  {isOpen && (
                    <div className="px-4 pb-4 text-sm leading-relaxed" style={{ color: MUTED }}>
                      {it.a}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      ))}
    </div>
    </>
  );
}
