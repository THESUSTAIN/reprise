import React from 'react';
import './fm.css';
import { AuthProvider } from '@fm/context/AuthContext';
import { I18nProvider } from '@fm/context/I18nContext';
import { ThemeProvider } from '@fm/context/ThemeContext';
import { AppProvider } from '@fm/context/AppContext';

/**
 * Coquille des pages portées FIDÈLEMENT depuis final-main (Pilotage, Bien-être, Espace).
 * Fournit les providers final-main (auth/i18n/thème/app) et la classe .fm-page (design tokens).
 * Le token JWT est partagé avec l'app (clé localStorage "zayado_token").
 */
export default function FmShell({ children }) {
  return (
    <I18nProvider>
      <ThemeProvider>
        <AuthProvider>
          <AppProvider>
            <div className="fm-page">{children}</div>
          </AppProvider>
        </AuthProvider>
      </ThemeProvider>
    </I18nProvider>
  );
}
