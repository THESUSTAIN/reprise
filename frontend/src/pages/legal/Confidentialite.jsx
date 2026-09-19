/* Page Politique de confidentialité Zayado — /legal/confidentialite
   Conforme RGPD : objet du traitement, base légale, durée conservation,
   destinataires, droits utilisateurs, contact DPO. */
import React from "react";
import { Link } from "react-router-dom";
import { ShieldCheck, Mail } from "lucide-react";
import LegalLayout from "@/components/LegalLayout";

const NAVY = "var(--zayado-navy)";
const GOLD = "var(--zayado-gold)";

export default function Confidentialite() {
  return (
    <LegalLayout title="Politique de confidentialité" lastUpdate="mai 2026" testId="page-confidentialite" path="/legal/confidentialite">
      <div className="bg-white rounded-2xl p-6 mb-6 border border-[var(--zayado-border)]">
        <ShieldCheck size={20} className="mb-2" style={{ color: GOLD }} />
        <h2 className="font-bold text-base mb-2" style={{ color: NAVY }}>L'essentiel en 30 secondes</h2>
        <ul className="text-sm space-y-1.5" style={{ color: "var(--zayado-text)" }}>
          <li>✅ Vos données restent en Europe (serveurs Hostinger France + Brevo France)</li>
          <li>✅ On ne revend rien à personne, jamais</li>
          <li>✅ Vous pouvez supprimer votre compte et toutes vos données en 1 clic</li>
          <li>✅ Pas de tracking publicitaire tiers (pas de Facebook Pixel, pas de Google Ads tracking)</li>
        </ul>
      </div>

      <section className="prose prose-sm max-w-none">
        <Block title="1. Qui sommes-nous ?">
          Zayado est un service édité par <strong>Zayado SAS</strong>, immatriculée au RCS de Paris,
          domiciliée à [adresse à compléter]. Délégué à la protection des données (DPO) :
          <a href="mailto:dpo@zayado.net" className="ml-1 hover:underline" style={{ color: NAVY }}>dpo@zayado.net</a>.
        </Block>

        <Block title="2. Quelles données collectons-nous ?">
          <ul className="list-disc pl-5 space-y-1">
            <li><strong>Compte</strong> : email, nom, photo (si Google/Microsoft), mot de passe haché (bcrypt)</li>
            <li><strong>Activité</strong> : projets, idées, analyses, conversations IA, commandes boutique</li>
            <li><strong>Technique</strong> : adresse IP (anonymisée 24h), navigateur, langue, pays</li>
            <li><strong>Marketing</strong> : préférences de communication (newsletter, push)</li>
          </ul>
        </Block>

        <Block title="3. Pourquoi traitons-nous ces données ?">
          <ul className="list-disc pl-5 space-y-1">
            <li><strong>Exécution du service</strong> (base légale : contrat) — vous fournir l'application, votre compte, l'IA</li>
            <li><strong>Sécurité</strong> (base légale : obligation légale) — détecter les abus, anti-spam, RGPD</li>
            <li><strong>Amélioration</strong> (base légale : intérêt légitime) — statistiques anonymisées, agrégées</li>
            <li><strong>Marketing</strong> (base légale : consentement) — newsletter, recommandations personnalisées</li>
          </ul>
        </Block>

        <Block title="4. Combien de temps ?">
          <ul className="list-disc pl-5 space-y-1">
            <li><strong>Compte actif</strong> : tant que vous utilisez Zayado</li>
            <li><strong>Compte inactif depuis 12 mois</strong> : avertissement RGPD à 11 mois, suppression auto à 12 mois</li>
            <li><strong>Commandes & factures</strong> : 10 ans (obligation comptable française)</li>
            <li><strong>Logs techniques</strong> : 13 mois max (anonymisés au-delà)</li>
            <li><strong>Cookies analytics</strong> : 13 mois max</li>
          </ul>
        </Block>

        <Block title="5. Avec qui partageons-nous ?">
          Uniquement avec nos sous-traitants RGPD-compliants, sous contrat DPA :
          <ul className="list-disc pl-5 space-y-1 mt-2">
            <li><strong>Hostinger</strong> (France) — hébergement WordPress + MySQL</li>
            <li><strong>Railway</strong> (UE) — hébergement application SaaS</li>
            <li><strong>Anthropic Claude</strong> (Emergent Universal Key) — IA texte (USA, conditions OpenAI-like)</li>
            <li><strong>Google Gemini</strong> — IA image (USA, idem)</li>
            <li><strong>Brevo</strong> (France) — emails transactionnels et newsletter</li>
            <li><strong>Mollie</strong> (UE) — paiements abonnements</li>
            <li><strong>WooCommerce</strong> (auto-hébergé sur Hostinger) — boutique</li>
          </ul>
        </Block>

        <Block title="6. Vos droits">
          Conformément au RGPD, vous pouvez à tout moment :
          <ul className="list-disc pl-5 space-y-1 mt-2">
            <li>Accéder à toutes vos données (export JSON sur demande)</li>
            <li>Rectifier vos infos personnelles dans Paramètres</li>
            <li>Supprimer votre compte (1 clic dans <Link to="/app/settings" className="hover:underline" style={{ color: NAVY }}>/app/settings</Link>) — effacement définitif sous 30 jours</li>
            <li>Retirer votre consentement marketing en 1 clic dans chaque email</li>
            <li>Vous opposer au traitement (intérêt légitime)</li>
            <li>Demander la portabilité de vos données</li>
            <li>Définir des directives post-mortem</li>
            <li>Saisir la CNIL (cnil.fr) si vous estimez vos droits non respectés</li>
          </ul>
          <p className="mt-3">
            Pour exercer ces droits :
            <a href="mailto:dpo@zayado.net" className="ml-1 hover:underline" style={{ color: NAVY }}>dpo@zayado.net</a>.
            Réponse sous 30 jours max.
          </p>
        </Block>

        <Block title="7. Cookies">
          Voir le détail dans la fenêtre "Vos données, votre choix" (premier accès au site). Vous pouvez
          modifier vos préférences à tout moment en cliquant sur "Cookies" en bas de page.
          <ul className="list-disc pl-5 space-y-1 mt-2">
            <li><strong>Essentiels</strong> (toujours actifs) : session, panier, anti-CSRF</li>
            <li><strong>Mesure d'audience</strong> (optionnel) : Plausible Analytics, sans cookie tiers</li>
            <li><strong>Marketing</strong> (optionnel) : recommandations personnalisées</li>
          </ul>
        </Block>

        <Block title="8. Transferts hors UE">
          Les IA (Claude, Gemini) traitent les prompts sur des serveurs aux USA. Aucune donnée
          identifiante n'est envoyée (pas de nom, pas d'email, pas d'ID utilisateur). Les prompts
          sont anonymisés côté Zayado avant transmission.
        </Block>

        <Block title="9. Mises à jour de cette politique">
          Nous notifions tout changement majeur par email 30 jours avant entrée en vigueur. Les
          modifications mineures (typos, clarifications) sont publiées sans préavis.
        </Block>
      </section>

      <div className="mt-10 p-5 rounded-xl border border-[var(--zayado-border)]" style={{ background: "var(--zayado-cream)" }}>
        <Mail size={16} className="mb-2" style={{ color: GOLD }} />
        <div className="text-sm font-bold mb-1" style={{ color: NAVY }}>Une question sur vos données ?</div>
        <p className="text-xs mb-3" style={{ color: "var(--zayado-muted)" }}>
          Écrivez à notre DPO. On répond toujours, et toujours sans baratin.
        </p>
        <a href="mailto:dpo@zayado.net" className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full text-xs font-medium text-white"
           style={{ background: NAVY }} data-testid="dpo-contact">
          dpo@zayado.net
        </a>
      </div>
    </LegalLayout>
  );
}

function Block({ title, children }) {
  return (
    <div className="mb-6">
      <h2 className="text-base font-bold mb-2" style={{ color: "var(--zayado-navy)" }}>{title}</h2>
      <div className="text-sm leading-relaxed" style={{ color: "var(--zayado-text)" }}>{children}</div>
    </div>
  );
}
