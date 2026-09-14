import React from "react";
import LegalLayout from "@/components/LegalLayout";

export default function MentionsLegales() {
  return (
    <LegalLayout title="Mentions légales" lastUpdate="18 février 2026" testId="page-legal" path="/legal/mentions-legales">
      <h2 className="font-display text-2xl mt-8 mb-3">Éditeur du site</h2>
      <p>
        <strong>Extension IA by Zayado</strong> est édité par la société Zayado.<br />
        Forme juridique : SAS (Société par Actions Simplifiée) au capital social de 1&nbsp;000&nbsp;&euro;.<br />
        Siège social : 10 rue de la Paix, 75002 Paris, France.<br />
        SIREN : 989 876 826 — RCS Paris (immatriculation du 06/08/2025).<br />
        Directeur de la publication : Wilson Alphonse.<br />
        Email : <a href="mailto:contact@zayado.net" className="text-[var(--zayado-navy)] underline">contact@zayado.net</a>
      </p>

      <h2 className="font-display text-2xl mt-8 mb-3">Hébergement</h2>
      <p>
        Application : <strong>Railway Corporation</strong> — 548 Market St #36947, San Francisco, CA 94104, États-Unis.<br />
        Base de données : <strong>Hostinger International Ltd</strong> — 61 Lordou Vironos Street, 6023 Larnaca, Chypre.<br />
        Authentification email : <strong>Brevo</strong> (Sendinblue SAS) — 7 rue de Madrid, 75008 Paris, France.
      </p>

      <h2 className="font-display text-2xl mt-8 mb-3">Propriété intellectuelle</h2>
      <p>
        L'ensemble des éléments du site (textes, graphismes, logo, code source) est la propriété exclusive de Zayado,
        ou utilisé sous licence. Toute reproduction, représentation, modification ou exploitation, totale ou partielle,
        est strictement interdite sans autorisation écrite préalable.
      </p>

      <h2 className="font-display text-2xl mt-8 mb-3">Crédits</h2>
      <p>
        Conception et développement : Zayado.<br />
        Modèle IA : Claude Sonnet 4.5 (Anthropic, PBC).<br />
        Iconographie : Lucide Icons (ISC License).<br />
        Photos d'illustration : Unsplash (licence libre).
      </p>

      <h2 className="font-display text-2xl mt-8 mb-3">Signaler un contenu</h2>
      <p>
        Conformément à la LCEN (loi n°2004-575), tout signalement de contenu illicite peut être adressé à&nbsp;
        <a href="mailto:contact@zayado.net" className="text-[var(--zayado-navy)] underline">contact@zayado.net</a>.
      </p>

      <h2 className="font-display text-2xl mt-8 mb-3">Liens utiles</h2>
      <p>
        <a href="/legal/politique-confidentialite" className="text-[var(--zayado-navy)] underline">Règles de confidentialité</a> ·{" "}
        <a href="/legal/conditions-utilisation" className="text-[var(--zayado-navy)] underline">Conditions d'utilisation</a>
      </p>
    </LegalLayout>
  );
}
