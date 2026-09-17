/* Footer Zayado officiel — dégradé navy, palette cream/navy/or.
   Partagé entre PublicBoutique et les pages SaaS (/groupement, etc.). */
import React from "react";
import { Link } from "react-router-dom";

const GOLD = "var(--zayado-gold)";

const FOOTER_COLS = [
  { title: "Boutique", links: [["Tout voir","/boutique"],["Corps","/boutique?u=corps"],["Âme","/boutique?u=ame"],["Rituel","/boutique?u=rituel"]] },
  { title: "Groupement", links: [["Mutuelle TNS","/groupement/mutuelle"],["Prévoyance","/groupement/prevoyance"],["Création d'entreprise","/groupement/creation"],["Comptabilité","/groupement/comptabilite"]] },
  { title: "Service", links: [["Contact","/contact"],["FAQ","/faq"],["Livraison & retours","/legal/livraison-retours"],["Suivi de commande","/contact"]] },
  { title: "Légal", links: [["CGU","/legal/conditions-utilisation"],["CGV","/legal/cgv"],["Mentions légales","/legal/mentions-legales"],["Confidentialité","/legal/confidentialite"]] },
];

export default function PublicFooter() {
  return (
    <footer className="mt-16 text-white" style={{ background: "var(--zayado-navy-gradient)" }}
            data-testid="zayado-public-footer">
      <div className="max-w-[1280px] mx-auto px-6 py-12 grid grid-cols-2 md:grid-cols-5 gap-8 md:gap-12">
        <div className="col-span-2">
          <div className="font-display italic text-2xl mb-3"
               style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)" }}>
            zayado.net
          </div>
          <p className="text-xs leading-relaxed max-w-xs mb-4 text-white/70">
            L'essentiel pour les entrepreneurs qui construisent leur trajectoire avec <em style={{ color: GOLD, fontStyle: "italic" }}>calme.</em>
          </p>
          <div className="text-[11px] text-white/50">
            Conçu en France · Petites séries · Production locale
          </div>
        </div>
        {FOOTER_COLS.map((col) => (
          <div key={col.title}>
            <div className="text-xs uppercase tracking-wider font-bold mb-4"
                 style={{ color: GOLD }}>{col.title}</div>
            <ul className="space-y-2">
              {col.links.map(([l, href]) => (
                <li key={l}>
                  <Link to={href} className="text-xs hover:text-white text-white/70">
                    {l}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <div className="max-w-[1280px] mx-auto px-6 pb-6 border-t border-white/10 pt-5 flex flex-wrap items-center justify-between gap-3 text-[11px] text-white/60">
        <div>© {new Date().getFullYear()} zayado.net · SaaS pour entrepreneurs solos</div>
        <div className="flex items-center gap-3">
          <span>Paiement sécurisé</span>
          <span>·</span>
          <span>CB · Apple Pay · PayPal</span>
        </div>
      </div>
    </footer>
  );
}
