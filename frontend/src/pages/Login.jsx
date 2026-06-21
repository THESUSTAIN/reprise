import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Mail, ArrowRight, Loader2 } from 'lucide-react';
import Logo from '../components/Logo';
import { authApi } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import { toast } from 'sonner';

const TOKEN_KEY = 'zayado_token';

/**
 * /login — connexion passwordless (fidèle à final-main) :
 *  - Lien magique (email)
 *  - OAuth Google / Microsoft
 *  - Mode invité (preview)
 *  - Handler de callback : ?token=... (magic-link) et ?code=&state=... (OAuth)
 * Aucune inscription / mot de passe.
 */
export default function Login() {
  const navigate = useNavigate();
  const { user, refresh } = useAuth();
  const [sp] = useSearchParams();
  const [email, setEmail] = useState('');
  const [busy, setBusy] = useState(false);
  const [callbackStatus, setCallbackStatus] = useState(null);

  const finishSession = async (token) => {
    localStorage.setItem(TOKEN_KEY, token);
    await refresh();
    navigate('/', { replace: true });
  };

  // Callbacks (magic-link / OAuth)
  useEffect(() => {
    const token = sp.get('token');
    const code = sp.get('code');
    const state = sp.get('state');

    if (token) {
      setCallbackStatus('Vérification du lien…');
      (async () => {
        try {
          const res = await authApi.verifyMagicLink(token);
          await finishSession(res.access_token || res.token);
        } catch (e) {
          setCallbackStatus(null);
          toast.error('Lien invalide ou expiré.');
        }
      })();
      return;
    }
    if (code && state) {
      const provider = state.startsWith('ms_') ? 'microsoft' : 'google';
      setCallbackStatus(`Connexion ${provider}…`);
      (async () => {
        try {
          const redirectUri = `${window.location.origin}/login`;
          const res = await authApi.oauthExchange(provider, { code, redirect_uri: redirectUri, state });
          await finishSession(res.access_token || res.token);
        } catch (e) {
          setCallbackStatus(null);
          toast.error(`Connexion ${provider} impossible.`);
        }
      })();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Déjà connecté → dashboard
  useEffect(() => { if (user) navigate('/', { replace: true }); }, [user, navigate]);

  const onMagicLink = async (e) => {
    e.preventDefault();
    if (!email || !email.includes('@')) { toast.error('Email invalide'); return; }
    setBusy(true);
    try {
      const data = await authApi.requestMagicLink(email);
      if (data?.delivered_via_email) {
        toast.success(`Lien envoyé à ${data.sent_to} — vérifiez votre boîte (expire dans ${data.expires_in_minutes || 15} min).`);
      } else if (data?.dev_link) {
        toast.success('Lien généré — redirection…');
        const url = data.dev_link.startsWith('http') ? data.dev_link : `${window.location.origin}${data.dev_link}`;
        window.location.href = url;
      } else {
        toast.success('Lien magique envoyé.');
      }
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Impossible d'envoyer le lien.");
    } finally { setBusy(false); }
  };

  const startOAuth = async (provider) => {
    setBusy(true);
    try {
      const redirectUri = `${window.location.origin}/login`;
      const data = await authApi.oauthStart(provider, redirectUri);
      if (data?.authorization_url) window.location.href = data.authorization_url;
      else toast.error(`Connexion ${provider} non configurée.`);
    } catch (e) {
      toast.error(`Connexion ${provider} indisponible.`);
    } finally { setBusy(false); }
  };

  const onGuest = async () => {
    setBusy(true);
    try {
      const res = await authApi.guestLogin();
      toast.success('Bienvenue en mode aperçu !');
      await finishSession(res.access_token || res.token);
    } catch (e) {
      toast.error("Mode invité indisponible.");
      setBusy(false);
    }
  };

  if (callbackStatus) {
    return (
      <div className="min-h-screen grid place-items-center" style={{ background: '#0a1a35', color: '#f6f3ee' }}>
        <div className="text-center">
          <Loader2 className="animate-spin mx-auto mb-4" size={28} style={{ color: '#d4b982' }} />
          <p className="text-sm">{callbackStatus}</p>
        </div>
      </div>
    );
  }

  return (
    <div
      data-testid="login-page"
      className="min-h-screen flex items-center justify-center px-4 py-10"
      style={{ background: 'linear-gradient(135deg,#142b45 0%,#1B3A5B 55%,#0c1d31 100%)' }}
    >
      <div className="relative w-full max-w-md">
        <div className="mb-5 flex justify-center" data-testid="login-brand">
          <Logo variant="onDark" size="lg" />
        </div>
        <p className="text-[#f6f3ee]/85 text-[15px] leading-relaxed text-center mb-1">
          Entreprendre avec clarté et sérénité.
        </p>

        <div className="mt-7 w-full bg-[#f6f3ee] rounded-3xl shadow-2xl p-7" data-testid="login-card">
          <div className="text-center mb-5">
            <h2 className="text-[#142b45] text-[20px] font-bold">Se connecter</h2>
            <p className="text-[11px] text-[#6b6358] mt-1">
              Pas de compte ? Il sera créé automatiquement à votre première connexion.
            </p>
          </div>

          <button onClick={() => startOAuth('google')} disabled={busy} data-testid="btn-google"
            className="w-full flex items-center justify-center gap-3 py-3 mb-2.5 rounded-full border border-[#e0d9cb] bg-white hover:border-[#142b45]/40 transition disabled:opacity-50">
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84A10.99 10.99 0 0 0 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18A10.99 10.99 0 0 0 1 12c0 1.77.42 3.45 1.18 4.93l3.66-2.84z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1A10.99 10.99 0 0 0 2.18 7.07l3.66 2.84C6.71 7.31 9.14 5.38 12 5.38z"/>
            </svg>
            <span className="text-[#1a1815] text-[14px] font-medium">Continuer avec Google</span>
          </button>

          <button onClick={() => startOAuth('microsoft')} disabled={busy} data-testid="btn-microsoft"
            className="w-full flex items-center justify-center gap-3 py-3 mb-2.5 rounded-full border border-[#e0d9cb] bg-white hover:border-[#142b45]/40 transition disabled:opacity-50">
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <rect x="1" y="1" width="10" height="10" fill="#F25022" />
              <rect x="13" y="1" width="10" height="10" fill="#7FBA00" />
              <rect x="1" y="13" width="10" height="10" fill="#00A4EF" />
              <rect x="13" y="13" width="10" height="10" fill="#FFB900" />
            </svg>
            <span className="text-[#1a1815] text-[14px] font-medium">Continuer avec Microsoft</span>
          </button>

          <div className="flex items-center gap-3 my-4">
            <div className="flex-1 h-px bg-[#e0d9cb]" />
            <span className="text-[11px] uppercase tracking-wider text-[#6b6358]">ou</span>
            <div className="flex-1 h-px bg-[#e0d9cb]" />
          </div>

          <form onSubmit={onMagicLink} className="space-y-2" data-testid="email-form">
            <div className="relative">
              <Mail className="w-4 h-4 text-[#6b6358] absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                placeholder="adresse@email.com" data-testid="login-email"
                className="w-full pl-10 pr-4 py-3 bg-white border border-[#e0d9cb] rounded-full text-[14px] text-[#1a1815] outline-none focus:border-[#142b45]/40 transition" />
            </div>
            <button type="submit" disabled={busy} data-testid="btn-magic-link"
              className="w-full py-3 rounded-full text-[14px] font-medium inline-flex items-center justify-center gap-2 text-white disabled:opacity-50"
              style={{ background: 'linear-gradient(135deg,#1f4377,#142b45)' }}>
              {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <ArrowRight className="w-4 h-4" />}
              Envoyer le lien magique
            </button>
          </form>

          <p className="text-center text-[10.5px] text-[#6b6358]/80 mt-4 leading-snug">
            En vous connectant, vous acceptez nos CGU et notre Politique de confidentialité.
          </p>
          <p className="text-center text-[11.5px] text-[#6b6358]/80 mt-3">Aucun mot de passe à retenir.</p>

          <div className="mt-5 pt-4 border-t border-[#e7e0d2]" data-testid="guest-access-section">
            <p className="text-center text-[11px] uppercase tracking-wider text-[#6b6358] font-semibold mb-2">Aperçu</p>
            <button type="button" onClick={onGuest} disabled={busy} data-testid="guest-login-btn"
              className="w-full h-10 rounded-full border border-[#e0d9cb] text-[#142b45] text-[13px] font-semibold hover:bg-white transition disabled:opacity-40">
              Continuer en mode invité (sans compte)
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
