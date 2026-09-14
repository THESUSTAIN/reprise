/* Livraison & Retours /legal/livraison-retours */
import React from "react";
import { Truck, RotateCcw, Package, Globe, Clock, Shield } from "lucide-react";
import LegalLayout from "@/components/LegalLayout";

const NAVY = "var(--zayado-navy)";
const GOLD = "var(--zayado-gold)";
const MUTED = "var(--zayado-muted)";

export default function LivraisonRetours() {
  return (
    <LegalLayout title="Livraison & retours" lastUpdate="mai 2026" testId="livraison-page" path="/legal/livraison-retours">
      <p className="text-sm md:text-base mb-10 max-w-xl" style={{ color: MUTED }}>
        On veut que vos paquets arrivent vite, bien emballés, et que si vous changez d'avis,
        ce soit simple comme bonjour.
      </p>

      <section className="mb-12">
        <h2 className="font-display italic mb-5 inline-flex items-center gap-3"
            style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)",
                     fontSize: "1.7rem", color: NAVY }}>
          <Truck size={22} /> Livraison
        </h2>
        <div className="grid md:grid-cols-2 gap-4">
          {[
            { icon: Package, title: "France métropolitaine", desc: "4.90€ via Colissimo Suivi · Offerte dès 50€", time: "2-4 jours ouvrés" },
            { icon: Globe, title: "Europe (UE)", desc: "9.90€ via Colissimo International · Offerte dès 100€", time: "5-7 jours ouvrés" },
            { icon: Clock, title: "Expédition", desc: "Préparation et envoi sous 24-48h après commande", time: "Lundi au vendredi" },
            { icon: Shield, title: "Suivi", desc: "Email de confirmation + numéro de suivi La Poste", time: "Mis à jour en temps réel" },
          ].map((s, i) => {
            const I = s.icon;
            return (
              <div key={i} className="p-5 rounded-xl border border-[var(--zayado-border)] bg-white">
                <div className="w-10 h-10 rounded-lg flex items-center justify-center mb-3"
                     style={{ background: "var(--zayado-gold-bg)", color: GOLD }}>
                  <I size={17} />
                </div>
                <div className="font-medium mb-1" style={{ color: "var(--zayado-text)" }}>{s.title}</div>
                <div className="text-sm" style={{ color: MUTED }}>{s.desc}</div>
                <div className="text-xs mt-2 italic" style={{ color: MUTED }}>{s.time}</div>
              </div>
            );
          })}
        </div>
      </section>

      <section>
        <h2 className="font-display italic mb-5 inline-flex items-center gap-3"
            style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)",
                     fontSize: "1.7rem", color: NAVY }}>
          <RotateCcw size={22} /> Retours sous 30 jours
        </h2>
        <div className="p-6 rounded-xl text-white mb-4" style={{ background: NAVY }}>
          <div className="text-[11px] uppercase tracking-[0.25em] mb-2" style={{ color: "var(--zayado-gold-soft)" }}>Notre engagement</div>
          <p className="text-base md:text-lg leading-relaxed">
            <strong>30 jours</strong> pour changer d'avis (au-delà du minimum légal de 14 jours).
            Retour <strong>gratuit en France</strong> via étiquette pré-payée. Remboursement
            sous 5-7 jours ouvrés après réception.
          </p>
        </div>
        <ol className="space-y-3 text-sm" style={{ color: MUTED }}>
          <li className="flex gap-3"><span className="w-6 h-6 rounded-full text-xs font-bold flex items-center justify-center shrink-0" style={{ background: "var(--zayado-gold-bg)", color: GOLD }}>1</span>
            <span>Envoyez-nous un email à <strong>contact@zayado.net</strong> avec votre numéro de commande et le motif.</span></li>
          <li className="flex gap-3"><span className="w-6 h-6 rounded-full text-xs font-bold flex items-center justify-center shrink-0" style={{ background: "var(--zayado-gold-bg)", color: GOLD }}>2</span>
            <span>Vous recevez une <strong>étiquette de retour pré-payée</strong> par email sous 24h.</span></li>
          <li className="flex gap-3"><span className="w-6 h-6 rounded-full text-xs font-bold flex items-center justify-center shrink-0" style={{ background: "var(--zayado-gold-bg)", color: GOLD }}>3</span>
            <span>Vous déposez votre colis dans n'importe quel <strong>bureau de Poste</strong>.</span></li>
          <li className="flex gap-3"><span className="w-6 h-6 rounded-full text-xs font-bold flex items-center justify-center shrink-0" style={{ background: "var(--zayado-gold-bg)", color: GOLD }}>4</span>
            <span>Dès réception et inspection, vous êtes <strong>remboursé·e sous 5-7 jours ouvrés</strong> sur votre moyen de paiement initial.</span></li>
        </ol>
        <p className="text-xs mt-6 italic" style={{ color: MUTED }}>
          ⚠️ Le produit doit être retourné dans son emballage d'origine, non utilisé. Les huiles essentielles
          ouvertes, livres lus et produits personnalisés ne sont pas éligibles au retour.
        </p>
      </section>
    </LegalLayout>
  );
}
