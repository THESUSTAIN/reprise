import React from "react";
import LegalLayout from "@/components/LegalLayout";

export default function ConditionsUtilisation() {
  return (
    <LegalLayout title="Conditions d'utilisation" lastUpdate="18 février 2026" testId="page-terms" path="/legal/conditions-utilisation">
      <h2 className="font-display text-2xl mt-8 mb-3">1. Objet</h2>
      <p>
        Les présentes Conditions Générales d'Utilisation (CGU) régissent l'accès et l'utilisation de la plateforme
        <strong> Extension IA by Zayado</strong> (« le Service »), accessible à l'adresse <a href="https://app.zayado.net" className="text-[var(--zayado-navy)] underline">app.zayado.net</a>.
      </p>

      <h2 className="font-display text-2xl mt-8 mb-3">2. Acceptation</h2>
      <p>
        En créant un compte, vous acceptez sans réserve les présentes CGU et notre <a href="/legal/politique-confidentialite" className="text-[var(--zayado-navy)] underline">politique de confidentialité</a>.
        Si vous n'acceptez pas ces conditions, n'utilisez pas le Service.
      </p>

      <h2 className="font-display text-2xl mt-8 mb-3">3. Description du Service</h2>
      <p>
        Extension IA by Zayado est une plateforme SaaS destinée aux entrepreneurs, artisans et indépendants, qui propose :
      </p>
      <ul className="list-disc pl-6 my-3 space-y-1">
        <li>Validation de projet par méthodologie Mom Test et Lean Startup.</li>
        <li>Feuille de route 30/60/90 jours et pilotage d'objectifs.</li>
        <li>Capture et analyse d'idées (texte, lien, audio, screenshot, PDF) via IA.</li>
        <li>CRM superfans (suivi de contacts, leads, clients).</li>
        <li>Pilotage financier simplifié.</li>
        <li>Suivi quotidien de l'énergie et bilan burnout.</li>
        <li>Collaborateur IA via Claude Sonnet 4.5.</li>
        <li>Groupement et collaboration (offre Business).</li>
      </ul>

      <h2 className="font-display text-2xl mt-8 mb-3">4. Compte utilisateur</h2>
      <p>
        Vous devez fournir des informations exactes. Vous êtes responsable de la confidentialité de vos identifiants
        et de toute activité sur votre compte. Toute utilisation frauduleuse doit être signalée immédiatement à contact@zayado.net.
      </p>

      <h2 className="font-display text-2xl mt-8 mb-3">5. Offres et paiement</h2>
      <ul className="list-disc pl-6 my-3 space-y-1">
        <li><strong>Offre Découverte</strong> : gratuite (limitations sur le nombre de projets, capacité IA, intégrations).</li>
        <li><strong>Offre Pro</strong> : 19€/mois — toutes les fonctionnalités personnelles.</li>
        <li><strong>Offre Business</strong> : 99€/mois — équipe, permissions, Microsoft Teams, intégrations avancées.</li>
      </ul>
      <p>
        Les paiements sont traités par <strong>Mollie</strong> (sous-traitant agréé). Renouvellement automatique, résiliable à tout moment
        depuis Paramètres &gt; Abonnement. Aucun remboursement au prorata pour les mois entamés.
      </p>

      <h2 className="font-display text-2xl mt-8 mb-3">6. Utilisation de l'IA</h2>
      <p>
        Les réponses générées par l'IA (Claude Sonnet 4.5 d'Anthropic) sont des suggestions à valeur informative. Elles ne remplacent
        ni un conseil professionnel (juridique, fiscal, médical), ni votre propre jugement. Vous restez seul responsable de vos décisions.
      </p>

      <h2 className="font-display text-2xl mt-8 mb-3">7. Comportements interdits</h2>
      <ul className="list-disc pl-6 my-3 space-y-1">
        <li>Usurpation d'identité ou utilisation de fausses informations.</li>
        <li>Tentatives d'accès non autorisé aux systèmes, scraping massif, attaque par déni de service.</li>
        <li>Publication ou stockage de contenu illégal, haineux, diffamatoire, ou portant atteinte aux droits de tiers.</li>
        <li>Revente ou redistribution du Service sans accord écrit.</li>
      </ul>

      <h2 className="font-display text-2xl mt-8 mb-3">8. Propriété intellectuelle</h2>
      <p>
        La plateforme, son design, son code et ses contenus sont la propriété exclusive de Zayado. Vous conservez la propriété
        intégrale des contenus que vous y publiez (idées, projets, fiches). Vous nous accordez une licence non-exclusive d'usage
        à des fins d'exécution du Service uniquement.
      </p>

      <h2 className="font-display text-2xl mt-8 mb-3">9. Limitation de responsabilité</h2>
      <p>
        Le Service est fourni "en l'état". Zayado ne saurait être tenue responsable des pertes indirectes (manque à gagner,
        perte de données causée par une force majeure ou un sous-traitant tiers). Nous mettons tout en œuvre pour assurer
        la disponibilité du Service mais ne garantissons pas une disponibilité de 100%.
      </p>

      <h2 className="font-display text-2xl mt-8 mb-3">10. Résiliation</h2>
      <p>
        Vous pouvez supprimer votre compte à tout moment. Nous nous réservons le droit de suspendre ou résilier un compte
        en cas de violation des CGU, après notification.
      </p>

      <h2 className="font-display text-2xl mt-8 mb-3">11. Droit applicable</h2>
      <p>
        Les CGU sont soumises au droit français. Tout litige sera porté devant les tribunaux compétents du ressort
        du siège social de Zayado, après tentative de résolution amiable.
      </p>

      <h2 className="font-display text-2xl mt-8 mb-3">12. Contact</h2>
      <p>
        <a href="mailto:contact@zayado.net" className="text-[var(--zayado-navy)] underline">contact@zayado.net</a>
      </p>
    </LegalLayout>
  );
}
