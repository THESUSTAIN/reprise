/* CGV — Conditions Générales de Vente Zayado */
import React from "react";
import LegalLayout from "@/components/LegalLayout";

const NAVY = "var(--zayado-navy)";
const GOLD = "var(--zayado-gold)";
const MUTED = "var(--zayado-muted)";

export default function CGV() {
  return (
    <LegalLayout title="Conditions générales de vente" lastUpdate="19 mai 2026" testId="cgv-page" path="/legal/cgv">
      <div className="prose prose-sm max-w-none space-y-6 text-sm leading-relaxed" style={{ color: "var(--zayado-text)" }}>
        <section>
          <h2 className="font-display italic text-xl mb-2" style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)", color: NAVY }}>
            1. Préambule
          </h2>
          <p style={{ color: MUTED }}>
            Les présentes Conditions Générales de Vente (CGV) régissent les ventes effectuées sur le site
            zayado.net entre Zayado SAS (le « Vendeur ») et toute personne physique ou morale (le « Client »)
            souhaitant acquérir les produits proposés.
          </p>
        </section>

        <section>
          <h2 className="font-display italic text-xl mb-2" style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)", color: NAVY }}>
            2. Produits
          </h2>
          <p style={{ color: MUTED }}>
            Les produits proposés sont décrits avec la plus grande précision possible. Les photographies sont
            non contractuelles. Les produits sont soumis à la disponibilité des stocks.
          </p>
        </section>

        <section>
          <h2 className="font-display italic text-xl mb-2" style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)", color: NAVY }}>
            3. Prix
          </h2>
          <p style={{ color: MUTED }}>
            Les prix sont indiqués en euros, TVA française incluse (20%). Le Vendeur se réserve le droit de
            modifier ses prix à tout moment. Les produits seront facturés sur la base des tarifs en vigueur
            au moment de la commande.
          </p>
        </section>

        <section>
          <h2 className="font-display italic text-xl mb-2" style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)", color: NAVY }}>
            4. Commande
          </h2>
          <p style={{ color: MUTED }}>
            Toute commande passée sur zayado.net constitue la formation d'un contrat conclu à distance entre
            le Client et le Vendeur. Le Vendeur se réserve le droit de refuser toute commande pour des motifs
            légitimes (litige antérieur, fraude soupçonnée, etc.).
          </p>
        </section>

        <section>
          <h2 className="font-display italic text-xl mb-2" style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)", color: NAVY }}>
            5. Paiement
          </h2>
          <p style={{ color: MUTED }}>
            Le règlement s'effectue par carte bancaire (Visa, Mastercard, American Express), Apple Pay ou
            PayPal. Les paiements sont sécurisés par notre partenaire Mollie (chiffrement SSL 256-bits).
            Aucune donnée bancaire n'est stockée sur nos serveurs.
          </p>
        </section>

        <section>
          <h2 className="font-display italic text-xl mb-2" style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)", color: NAVY }}>
            6. Livraison
          </h2>
          <p style={{ color: MUTED }}>
            Les produits sont livrés à l'adresse indiquée lors de la commande. Délais moyens :
            France métropolitaine 2-4 jours, Europe 5-7 jours. Livraison offerte dès 50€ d'achat
            (sinon 4.90€ via Colissimo Suivi). En cas de retard exceptionnel, le Client est prévenu par email.
          </p>
        </section>

        <section>
          <h2 className="font-display italic text-xl mb-2" style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)", color: NAVY }}>
            7. Droit de rétractation
          </h2>
          <p style={{ color: MUTED }}>
            Conformément à l'article L221-18 du Code de la consommation, le Client dispose de
            <strong> 30 jours</strong> à compter de la réception pour exercer son droit de rétractation
            (au-delà du minimum légal de 14 jours). Le produit doit être retourné dans son emballage d'origine,
            non utilisé. Étiquette de retour gratuite envoyée sur demande à contact@zayado.net.
          </p>
        </section>

        <section>
          <h2 className="font-display italic text-xl mb-2" style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)", color: NAVY }}>
            8. Garanties
          </h2>
          <p style={{ color: MUTED }}>
            Les produits bénéficient de la garantie légale de conformité (2 ans) et de la garantie contre
            les vices cachés. Une garantie commerciale fabricant peut s'ajouter (variable selon les marques :
            12 à 36 mois).
          </p>
        </section>

        <section>
          <h2 className="font-display italic text-xl mb-2" style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)", color: NAVY }}>
            9. Litiges
          </h2>
          <p style={{ color: MUTED }}>
            Les présentes CGV sont soumises au droit français. En cas de litige, le Client peut saisir
            gratuitement le médiateur de la consommation FEVAD (60 rue La Boétie, 75008 Paris) ou la plateforme
            européenne de règlement en ligne des litiges : ec.europa.eu/consumers/odr.
          </p>
        </section>

        <section>
          <h2 className="font-display italic text-xl mb-2" style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)", color: NAVY }}>
            10. Contact
          </h2>
          <p style={{ color: MUTED }}>
            Zayado SAS · contact@zayado.net · Paris, France<br />
            SIRET : à venir · RCS : à venir · TVA Intracom : à venir
          </p>
        </section>
      </div>
    </LegalLayout>
  );
}
