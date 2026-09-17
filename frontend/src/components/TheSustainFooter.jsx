/* Footer officiel Presta-Partenaire by TheSustain.
   Calqué sur thesustain-app.vercel.app : fond #0F172A (très sombre),
   4 colonnes (logo+tagline + Liens / Support / Suivez-nous),
   strip bas © + "Propulsé par Zayado".
*/
import React from "react";
import { Link } from "react-router-dom";
import { PARTNER as P, TS_LOGOS } from "../pages/partners-theme";

const COLS = [
  {
    title: "Liens rapides",
    links: [
      ["À propos", "/a-propos"],
      ["Devenir partenaire", "/devenir-partenaire"],
      ["Annuaire prestataires", "/partenaires/recherche"],
      ["Services Pro", "/services-pro"],
    ],
  },
  {
    title: "Spiritualité",
    links: [
      ["Mémoire (versets)", "/memoire"],
      ["Galerie souvenir", "/galerie-souvenir"],
      ["Assistant Pasteur", "/assistant-pasteur"],
    ],
  },
  {
    title: "Communauté",
    links: [
      ["TheSustain.net", "https://thesustain.net", true],
      ["Contact", "/contact"],
      ["FAQ", "/faq"],
    ],
  },
];

export default function TheSustainFooter() {
  return (
    <footer className="text-white mt-20"
            style={{ background: P.BG_FOOTER, fontFamily: "'Inter', system-ui, sans-serif" }}
            data-testid="thesustain-footer">
      <div className="max-w-[1280px] mx-auto px-6 md:px-8 py-14 grid grid-cols-1 md:grid-cols-4 gap-10">
        {/* Logo + tagline */}
        <div>
          <img src={TS_LOGOS.HANDS} alt="TheSustain"
               className="w-28 h-auto object-contain mb-4"
               data-testid="thesustain-footer-logo" />
          <h3 className="text-lg font-bold mb-2">TheSustain</h3>
          <p className="text-sm leading-relaxed text-white/60">
            Le réseau chrétien des prestataires et entrepreneurs de confiance.<br/>
            Semer sur la terre pour récolter dans les cieux.
          </p>
        </div>

        {/* Colonnes liens */}
        {COLS.map((col) => (
          <div key={col.title}>
            <h4 className="text-base font-bold mb-4 text-white">
              {col.title}
            </h4>
            <ul className="space-y-2.5">
              {col.links.map(([label, href, external]) => external ? (
                <li key={label}>
                  <a href={href} target="_blank" rel="noopener noreferrer"
                     className="text-sm text-white/70 hover:text-white transition">
                    {label}
                  </a>
                </li>
              ) : (
                <li key={label}>
                  <Link to={href} className="text-sm text-white/70 hover:text-white transition">
                    {label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      {/* Strip bas © + Propulsé par Zayado */}
      <div className="border-t border-white/10">
        <div className="max-w-[1280px] mx-auto px-6 md:px-8 py-5 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="text-white/50">
            © {new Date().getFullYear()} TheSustain — Tous droits réservés
          </div>
          <a href="https://zayado.net" target="_blank" rel="noopener noreferrer"
             className="text-white/50 hover:text-white transition uppercase tracking-wider font-medium"
             data-testid="thesustain-footer-zayado">
            Propulsé par <span className="font-bold text-white">Zayado</span>
          </a>
        </div>
      </div>
    </footer>
  );
}
