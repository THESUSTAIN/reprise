import React, { useEffect, useState } from "react";
import { Heart, ArrowRight, Users, Shield, Calculator, Phone,
         Monitor, Building, Scale, Loader2, ExternalLink } from "lucide-react";
import { Link } from "react-router-dom";
import api from "@/lib/api";

// Icônes par catégorie de service
const ICON_MAP = {
  assurance:      Shield,
  domiciliation:  Building,
  comptabilite:   Calculator,
  telephonie:     Phone,
  saas:           Monitor,
  coworking:      Users,
  juridique:      Scale,
  default:        Heart,
};

function icon(category) {
  const k = (category || "").toLowerCase();
  for (const [key, Icon] of Object.entries(ICON_MAP)) {
    if (k.includes(key)) return Icon;
  }
  return ICON_MAP.default;
}

// Fallback si l'API ne répond pas
const FALLBACK_SERVICES = [
  { id: "assurance", name: "Assurance pro", description: "Tarif groupement négocié · RC Pro + multirisque", category: "assurance", cta_url: "/app/groupement/assurance" },
  { id: "domiciliation", name: "Domiciliation", description: "Paris et grandes villes · adresse officielle", category: "domiciliation", cta_url: "/app/groupement/domiciliation" },
  { id: "comptabilite", name: "Comptabilité partenaire", description: "Expert-comptable certifié · tarif négocié membres", category: "comptabilite", cta_url: "/app/groupement/comptabilite" },
  { id: "telephonie", name: "Téléphonie pro", description: "Forfait pro avantageux · SIM + appels illimités", category: "telephonie", cta_url: null },
  { id: "saas", name: "Outils SaaS", description: "Crédits et réductions sur logiciels métier", category: "saas", cta_url: null },
  { id: "coworking", name: "Coworking partenaire", description: "Réseau d'espaces à tarif membre", category: "coworking", cta_url: null },
  { id: "juridique", name: "Juridique léger", description: "CGV, contrats type, accompagnement micro", category: "juridique", cta_url: null },
];

export default function Groupement() {
  const [services, setServices] = useState(null);
  const [loading, setLoading]   = useState(true);

  useEffect(() => {
    api.get("/groupement/services")
      .then((r) => setServices(r.data?.services || r.data || FALLBACK_SERVICES))
      .catch(() => setServices(FALLBACK_SERVICES))
      .finally(() => setLoading(false));
  }, []);

  const list = services || FALLBACK_SERVICES;

  return (
    <div className="space-y-6" data-testid="groupement-page">
      <header>
        <div className="chip mb-3"><Heart size={14} /> Groupement Zayado</div>
        <h1 className="font-display text-4xl italic">Vos services négociés.</h1>
        <p className="text-[var(--zayado-muted)] mt-2 max-w-2xl">
          Accédez aux services mutualisés du groupement Zayado — tarifs collectifs
          réservés aux membres. Chaque service est sélectionné et négocié par l'équipe.
        </p>
      </header>

      {/* DAF — mis en avant */}
      <div className="card-soft p-6 border border-[var(--zayado-gold)] bg-[var(--zayado-gold-bg)]"
           data-testid="daf-highlight">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-xl bg-[var(--zayado-navy)] text-white flex items-center justify-center shrink-0">
            <Calculator size={20} />
          </div>
          <div className="flex-1">
            <div className="chip chip-gold text-[10px] mb-2">Service phare</div>
            <div className="font-display text-xl italic mb-1">DAF externalisé IA-augmenté</div>
            <p className="text-sm text-[var(--zayado-muted)] mb-3">
              Un Directeur Administratif & Financier certifié à temps partagé — l'IA prépare,
              l'humain valide. Trésorerie, TVA, URSSAF, alertes proactives.
              <strong className="text-[var(--zayado-navy)]"> 500 à 1 500€/mois</strong> selon mission.
            </p>
            <div className="flex flex-wrap gap-2">
              <Link to="/app/groupement/daf"
                className="btn-navy btn-press inline-flex items-center gap-2 text-sm">
                Demander un devis <ArrowRight size={13} />
              </Link>
              <span className="chip text-xs">Réponse sous 24h</span>
            </div>
          </div>
        </div>
      </div>

      {/* Grille services */}
      {loading ? (
        <div className="flex items-center justify-center py-12 text-[var(--zayado-muted)]">
          <Loader2 size={18} className="animate-spin mr-2" /> Chargement des services…
        </div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="services-grid">
          {list.map((s) => {
            const Icon = icon(s.category || s.name);
            return (
              <div key={s.id || s.name}
                   className="card-soft p-5 flex items-start gap-4 hover:shadow-md transition-shadow"
                   data-testid={`service-${s.id || s.name}`}>
                <div className="w-10 h-10 rounded-xl bg-[var(--zayado-navy)]/10 text-[var(--zayado-navy)] flex items-center justify-center shrink-0">
                  <Icon size={18} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-semibold mb-1">{s.name}</div>
                  <div className="text-sm text-[var(--zayado-muted)] mb-3 leading-relaxed">
                    {s.description || s.d}
                  </div>
                  {s.cta_url ? (
                    <Link to={s.cta_url}
                      className="text-sm text-[var(--zayado-navy)] inline-flex items-center gap-1 font-medium hover:gap-2 transition-all">
                      En savoir plus <ArrowRight size={13} />
                    </Link>
                  ) : (
                    <span className="chip text-[10px]">Bientôt disponible</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Lien vers devenir partenaire */}
      <div className="card-soft p-5 flex items-center justify-between gap-4 flex-wrap">
        <div>
          <div className="font-semibold mb-0.5">Vous êtes prestataire de services ?</div>
          <div className="text-sm text-[var(--zayado-muted)]">
            Rejoignez le réseau Zayado et accédez aux membres du groupement.
          </div>
        </div>
        <Link to="/app/partenaires/devenir"
          className="btn-navy btn-press inline-flex items-center gap-2 text-sm shrink-0">
          Devenir partenaire <ExternalLink size={13} />
        </Link>
      </div>
    </div>
  );
}
