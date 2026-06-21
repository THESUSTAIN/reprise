import React, { useEffect, useState, useCallback } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Mail, ArrowRight, ArrowLeft, X, Loader2 } from "lucide-react";
import Logo from "@fm/components/layout/LogoIcon";
import { authApi, setToken, setStoredUser } from "@fm/lib/api";
import { useAuth } from "@fm/context/AuthContext";
import { toast } from "sonner";

/**
 * LoginModal — fenêtre modale globale "MyExtension AI | Zayado".
 *
 * Activation :
 *   - Par URL : ajouter `?login=1` à n'importe quelle URL → modal s'ouvre
 *   - Programmatique : `window.dispatchEvent(new Event("zayado:open-login"))`
 *
 * Fermeture :
 *   - Clic backdrop, bouton X, touche ESC, ou login réussi
 *   - L'URL est nettoyée (?login=1 retiré) à la fermeture
 *
 * Texte fidèle à la page /login historique (avant suppression).
 * Le bouton "Continuer en mode invité" est visible uniquement en environnement
 * de preview (REACT_APP_BACKEND_URL contient "preview" / "emergentagent" /
 * "localhost"). En production, le backend rejette aussi /api/auth/guest.
 */
export default function LoginModal() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, refresh } = useAuth();
  const [open, setOpen] = useState(false);
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);

  // Ouverture par URL ?login=1
  useEffect(() => {
    const sp = new URLSearchParams(location.search);
    if (sp.get("login") === "1" && !user) setOpen(true);
  }, [location.search, user]);

  // Ouverture programmatique
  useEffect(() => {
    const handler = () => { if (!user) setOpen(true); };
    window.addEventListener("zayado:open-login", handler);
    return () => window.removeEventListener("zayado:open-login", handler);
  }, [user]);

  // ESC pour fermer + lock scroll
  useEffect(() => {
    if (!open) return;
    const onKey = (e) => { if (e.key === "Escape") handleClose(); };
    window.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const handleClose = useCallback(() => {
    setOpen(false);
    setEmail("");
    const sp = new URLSearchParams(location.search);
    if (sp.get("login")) {
      sp.delete("login");
      navigate({ pathname: location.pathname, search: sp.toString() ? `?${sp.toString()}` : "" }, { replace: true });
    }
  }, [location, navigate]);

  // Auto-close si connecté
  useEffect(() => { if (user && open) handleClose(); }, [user, open, handleClose]);

  const requireConsent = () => true; // case à cocher retirée — texte CGU/Privacy reste affiché en bas

  // Le backend renvoie { authorization_url } — on doit lui passer redirect_uri (callback frontend)
  // puis suivre l'URL d'autorisation retournée.
  const startOAuth = async (provider) => {
    if (!requireConsent()) return;
    setBusy(true);
    try {
      const base = process.env.REACT_APP_BACKEND_URL || "";
      const redirectUri = `${window.location.origin}/login`; // Login.js gère ?code & ?state
      const r = await fetch(
        `${base}/api/oauth/${provider}/start?redirect_uri=${encodeURIComponent(redirectUri)}`,
        { method: "GET", credentials: "include" }
      );
      const data = await r.json();
      if (!r.ok) {
        throw new Error(data?.detail || `OAuth ${provider} indisponible`);
      }
      if (data?.authorization_url) {
        window.location.href = data.authorization_url;
      } else {
        throw new Error("URL d'autorisation introuvable.");
      }
    } catch (e) {
      toast.error(e?.message || `Connexion ${provider} impossible`);
      setBusy(false);
    }
  };
  const onGoogle = () => startOAuth("google");
  const onMicrosoft = () => startOAuth("microsoft");

  const onMagicLink = async (e) => {
    e?.preventDefault();
    if (!requireConsent()) return;
    if (!email || !email.includes("@")) {
      toast.error("Email invalide");
      return;
    }
    setBusy(true);
    try {
      const data = await authApi.requestMagicLink(email);
      if (data?.delivered_via_email) {
        toast.success(`Lien envoyé à ${data.sent_to} — vérifiez votre boîte (expire dans ${data.expires_in_minutes || 30} min).`);
      } else if (data?.dev_link) {
        toast.success(`Lien généré (Brevo non disponible) — ouvrez : ${data.dev_link}`, { duration: 20000 });
      } else {
        toast.success("Lien magique envoyé.");
      }
      setEmail("");
    } catch (err) {
      toast.error(err?.message || "Impossible d'envoyer le lien.");
    } finally {
      setBusy(false);
    }
  };

  // Preview-only guest access
  const backendUrl = process.env.REACT_APP_BACKEND_URL || "";
  const isPreviewEnv = /preview|emergentagent|localhost/i.test(backendUrl);

  const onGuest = async () => {
    setBusy(true);
    try {
      const { token: jwt, user: u } = await authApi.guestLogin();
      setToken(jwt);
      setStoredUser(u);
      await refresh();
      toast.success("Bienvenue en mode aperçu !");
      handleClose();
      navigate("/", { replace: true });
    } catch (e) {
      toast.error(e?.message || "Mode invité indisponible en production.");
    } finally {
      setBusy(false);
    }
  };

  if (!open) return null;

  const previewSiteHref =
    typeof window !== "undefined" && window.location.hostname.includes("preview.emergentagent")
      ? `${backendUrl}/api/preview-site/myextension-ai`
      : "https://zayado.net/myextension-ai";

  return (
    <div
      className="fixed inset-0 z-[10000] flex items-center justify-center px-4 sm:px-6 py-8 overflow-y-auto"
      data-testid="login-modal"
      role="dialog"
      aria-modal="true"
      aria-label="Connexion MyExtension AI"
    >
      {/* Backdrop navy nuit */}
      <div
        className="absolute inset-0"
        style={{ background: "rgba(10, 28, 58, 0.85)", backdropFilter: "blur(10px)" }}
        onClick={handleClose}
        data-testid="login-modal-backdrop"
      />

      {/* Modal container */}
      <div
        className="relative w-full max-w-md my-auto"
        style={{ animation: "modalIn 0.25s ease-out" }}
      >
        {/* Bouton Retour (top-left, hors carte) */}
        <a
          href={previewSiteHref}
          className="absolute -top-12 left-0 inline-flex items-center gap-1.5 px-3.5 py-2 rounded-full text-cream/85 hover:text-cream bg-white/5 hover:bg-white/10 border border-cream/15 backdrop-blur transition text-[13px]"
          data-testid="login-back-btn"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Retour
        </a>

        {/* Close button */}
        <button
          onClick={handleClose}
          aria-label="Fermer"
          className="absolute -top-12 right-0 w-9 h-9 rounded-full grid place-items-center text-cream/85 hover:text-cream bg-white/5 hover:bg-white/10 border border-cream/15 backdrop-blur transition"
          data-testid="login-modal-close"
        >
          <X size={17} />
        </button>

        {/* Brand / wordmark on dark */}
        <div className="mb-5 flex justify-center" data-testid="login-brand">
          <Logo variant="onDark" size="lg" testid="login-logo" />
        </div>

        <p className="text-cream/85 font-display text-[15px] leading-relaxed text-center mb-1">
          Entreprendre avec clarté et sérénité.
        </p>

        {/* Card */}
        <div
          className="mt-7 w-full max-w-md bg-cream rounded-3xl shadow-[0_30px_80px_-20px_rgba(0,0,0,0.5)] p-7"
          data-testid="login-card"
        >
          <div className="text-center mb-5">
            <h2 className="font-display text-navy text-[20px]">Se connecter</h2>
            <p className="text-[11px] text-ink-muted mt-1">
              Pas de compte ? Il sera créé automatiquement à votre première connexion.
            </p>
          </div>

          <button
            onClick={onGoogle}
            data-testid="btn-google"
            className="w-full flex items-center justify-center gap-3 py-3 mb-2.5 rounded-full border border-sand-300 bg-white hover:border-navy/40 transition"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84A10.99 10.99 0 0 0 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18A10.99 10.99 0 0 0 1 12c0 1.77.42 3.45 1.18 4.93l3.66-2.84z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1A10.99 10.99 0 0 0 2.18 7.07l3.66 2.84C6.71 7.31 9.14 5.38 12 5.38z"/>
            </svg>
            <span className="text-ink text-[14px] font-medium">Continuer avec Google</span>
          </button>

          <button
            onClick={onMicrosoft}
            data-testid="btn-microsoft"
            className="w-full flex items-center justify-center gap-3 py-3 mb-2.5 rounded-full border border-sand-300 bg-white hover:border-navy/40 transition"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <rect x="1" y="1" width="10" height="10" fill="#F25022" />
              <rect x="13" y="1" width="10" height="10" fill="#7FBA00" />
              <rect x="1" y="13" width="10" height="10" fill="#00A4EF" />
              <rect x="13" y="13" width="10" height="10" fill="#FFB900" />
            </svg>
            <span className="text-ink text-[14px] font-medium">Continuer avec Microsoft</span>
          </button>

          <div className="flex items-center gap-3 my-4">
            <div className="flex-1 h-px bg-sand-300" />
            <span className="text-[11px] uppercase tracking-wider text-ink-muted">ou</span>
            <div className="flex-1 h-px bg-sand-300" />
          </div>

          {/* Champ email visible d'emblée (plus de bouton "Continuer avec votre email") */}
          <form onSubmit={onMagicLink} className="space-y-2" data-testid="email-form">
            <div className="relative">
              <Mail className="w-4 h-4 text-ink-muted absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="adresse@email.com"
                data-testid="email-input"
                className="w-full pl-10 pr-4 py-3 bg-white border border-sand-300 rounded-full text-[14px] text-ink placeholder:text-ink-muted/60 outline-none focus:border-navy/40 transition"
              />
            </div>
            <button
              type="submit"
              disabled={busy}
              data-testid="btn-magic-link"
              className="w-full bg-navy text-cream py-3 rounded-full text-[14px] font-medium hover:bg-navy-bright transition inline-flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <ArrowRight className="w-4 h-4" />}
              Envoyer le lien magique
            </button>
          </form>

          <p className="text-center text-[10.5px] text-ink-muted/70 mt-4 leading-snug">
            En vous connectant, vous acceptez nos{" "}
            <a href="/terms" target="_blank" rel="noopener noreferrer" className="text-navy underline hover:text-navy-bright" data-testid="link-terms">CGU</a>
            {" "}et notre{" "}
            <a href="/privacy" target="_blank" rel="noopener noreferrer" className="text-navy underline hover:text-navy-bright" data-testid="link-privacy">Politique de confidentialité</a>.
          </p>

          <p className="text-center text-[11.5px] text-ink-muted/80 mt-4">
            Aucune carte bancaire requise.
          </p>
          <p className="text-center text-[11.5px] text-ink-muted/80 mt-1">
            Aucun mot de passe à retenir.
          </p>

          {isPreviewEnv && (
            <div className="mt-5 pt-4 border-t border-sand-200" data-testid="guest-access-section">
              <p className="text-center text-[11px] uppercase tracking-wider text-ink-muted font-semibold mb-2">Aperçu</p>
              <button
                type="button"
                onClick={onGuest}
                disabled={busy}
                data-testid="guest-login-btn"
                className="w-full h-10 rounded-full border border-sand-300 text-navy text-[13px] font-semibold hover:bg-cream-soft transition-colors disabled:opacity-40"
              >
                Continuer en mode invité (sans compte)
              </button>
              <p className="text-center text-[10.5px] text-ink-muted mt-2 italic">
                Disponible uniquement en environnement de preview.
              </p>
            </div>
          )}
        </div>

        <div
          className="mt-5 max-w-md w-full flex flex-wrap items-center justify-center gap-x-3 gap-y-1.5 text-[11.5px] text-cream/55"
          data-testid="login-trust-row"
        >
          <span>Vos données restent privées — RGPD, hébergement européen.</span>
        </div>
      </div>

      <style>{`
        @keyframes modalIn {
          from { opacity: 0; transform: translateY(20px) scale(0.97); }
          to { opacity: 1; transform: translateY(0) scale(1); }
        }
      `}</style>
    </div>
  );
}
