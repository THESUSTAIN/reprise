import React from 'react';
import { Link } from 'react-router-dom';
import { Lock, LogIn } from 'lucide-react';

export default function AuthGate({ title }) {
  return (
    <div data-testid="auth-gate" className="zy-card rounded-2xl p-10 text-center max-w-md mx-auto mt-10">
      <div className="w-14 h-14 rounded-2xl zy-tile-gold flex items-center justify-center mx-auto mb-4">
        <Lock className="w-6 h-6" />
      </div>
      <h2 className="zy-heading text-xl font-bold text-foreground mb-2">Connexion requise</h2>
      <p className="text-sm text-muted-foreground mb-6">
        Connectez-vous pour accéder à {title}.
      </p>
      <Link
        to="/login"
        data-testid="auth-gate-login-link"
        className="zy-btn-primary inline-flex items-center gap-2 h-10 px-5 rounded-lg text-sm font-medium"
      >
        <LogIn className="w-4 h-4" /> Se connecter
      </Link>
    </div>
  );
}
