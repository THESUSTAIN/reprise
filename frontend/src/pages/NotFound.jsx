import React from "react";
import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-[60vh] grid place-items-center px-6 text-center" data-testid="pub-404">
      <div>
        <p className="font-display text-7xl text-gold-deep mb-2">404</p>
        <h1 className="font-display text-3xl text-navy mb-3">Cette page s&apos;est égarée.</h1>
        <p className="text-ink-soft mb-6">Pas de souci, on vous ramène au cockpit.</p>
        <Link to="/" className="inline-flex items-center gap-2 px-5 h-11 rounded-full bg-navy text-cream font-medium">
          <ArrowLeft size={14} /> Retour à l&apos;accueil
        </Link>
      </div>
    </div>
  );
}
