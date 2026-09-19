import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Mail, ShieldCheck, Loader2, RotateCcw, Server, Lock, Star, X } from "lucide-react";
import { toast } from "sonner";
import {
  sendMagicLink, verifyMagicLink, demoLogin, oauthStart, oauthExchange, setLanguage,
} from "../lib/api";
import "./login.css";
import InstallBanner from "../components/InstallBanner";

// Reprend l'UI de final-main (structure, .login-* CSS), mais rebranchée sur
// les vraies fonctions déjà existantes dans CE repo (lib/api.js /
// routes/auth.py) : sendMagicLink, verifyMagicLink, demoLogin, oauthStart.
// useAuth()/usePrefs()/ssoApi n'existent pas ici (c'étaient des fichiers de
// contexte propres à final-main) — d'où l'échec de build initial
// ("Can't resolve '@/context/PrefsContext'"). Le sous-système SSO par
// domaine d'entreprise (ssoOpen/ssoDomain/ssoApi) a été retiré : dans
// final-main il était déjà mort (défini mais jamais rendu dans le JSX,
// aucun bouton ne l'ouvrait), donc rien n'est perdu.

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 48 48"><path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3c-1.6 4.7-6.1 8-11.3 8-6.6 0-12-5.4-12-12s5.4-12 12-12c3 0 5.8 1.1 7.9 3l5.7-5.7C34.6 6.1 29.6 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.3-.4-3.5z"/><path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.7 16 19 13 24 13c3 0 5.8 1.1 7.9 3l5.7-5.7C34.6 6.1 29.6 4 24 4 16.3 4 9.7 8.3 6.3 14.7z"/><path fill="#4CAF50" d="M24 44c5.5 0 10.4-2.1 14.1-5.5l-6.5-5.5C29.6 34.9 26.9 36 24 36c-5.2 0-9.6-3.3-11.2-8l-6.6 5.1C9.6 39.6 16.2 44 24 44z"/><path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.2-2.2 4.1-4.1 5.5l6.5 5.5C41.4 36.8 44 31 44 24c0-1.3-.1-2.3-.4-3.5z"/></svg>
  );
}
function MicrosoftIcon() {
  return (<svg width="16" height="16" viewBox="0 0 23 23"><path fill="#f35325" d="M1 1h10v10H1z"/><path fill="#81bc06" d="M12 1h10v10H12z"/><path fill="#05a6f0" d="M1 12h10v10H1z"/><path fill="#ffba08" d="M12 12h10v10H12z"/></svg>);
}

const STR = {
  fr: {
    welcome: "Bienvenue sur", subtitle: "Connectez-vous ou créez votre compte en un clic — sans mot de passe à retenir.",
    google: "Google", microsoft: "Microsoft", orEmail: "ou par email", yourEmail: "Votre email",
    getLink: "Recevoir mon lien", emailSent: "Email envoyé", previewMode: "Mode preview",
    clickLink: (e) => <>Cliquez sur le lien reçu à <b>{e}</b> pour vous connecter.</>,
    previewText: "L'email n'est pas envoyé en preview. Cliquez sur ce lien pour vous connecter :",
    connectNow: "→ Se connecter maintenant", resend: "Renvoyer un lien",
    noAccount: "Pas de compte ? Il sera créé automatiquement à votre première connexion.",
    guest: "Aperçu gratuit", testAccount: "Ouvrir le compte test (Thomas)", lastLogin: "Dernière connexion",
    redirecting: (p) => `Redirection vers ${p}…`, cgu: "CGU", privacy: "Confidentialité",
    enterEmail: "Entrez votre adresse email.", linkSent: "Lien de connexion envoyé ! Vérifiez votre boîte mail.",
    previewInfo: "Mode preview : utilisez le lien affiché ci-dessous.",
    sendFail: "Envoi impossible pour le moment. Essayez Google.",
    deliveryFail: "L'envoi de l'email est momentanément indisponible. Réessayez dans quelques instants.",
    errGoogle: "La connexion avec Google a échoué. Réessayez, ou utilisez votre email.",
    errMsft: "La connexion avec Microsoft a échoué. Réessayez, ou utilisez votre email.",
    errLink: "Ce lien de connexion est invalide ou a expiré. Demandez-en un nouveau.",
    trustTitle: "Sécurité & confidentialité",
    trustHosting: "Hébergement Railway",
    trustEncryption: "Connexion chiffrée (HTTPS)",
    thesustain: "Continuer avec thesustain.net",
    landingTitleA: "Votre entreprise,", landingTitleB: "pilotée avec clarté.",
    proofRating: "Avis vérifiés · Trustpilot & Google",
    proofQuote: "« Zayado m'a aidée sur plusieurs plans : création d'entreprise, flyers, structuration des idées. Vraiment professionnels et à l'écoute. »",
    proofAuthor: "Theodora", proofMeta: "Avis Trustpilot · août 2025",
    startCta: "Commencer", haveAccount: "J'ai déjà un compte",
    welcomeBack: "Content de vous revoir !", sheetSub: "Connectez-vous pour retrouver votre cockpit.",
  },
  en: {
    welcome: "Welcome to", subtitle: "Sign in or create your account in one click — no password to remember.",
    google: "Google", microsoft: "Microsoft", orEmail: "or with email", yourEmail: "Your email",
    getLink: "Send me a link", emailSent: "Email sent", previewMode: "Preview mode",
    clickLink: (e) => <>Click the link sent to <b>{e}</b> to sign in.</>,
    previewText: "Email isn't sent in preview. Click this link to sign in:",
    connectNow: "→ Sign in now", resend: "Resend a link",
    noAccount: "No account? It will be created automatically on your first sign-in.",
    guest: "Free preview", testAccount: "Open test account (Thomas)", lastLogin: "Last sign-in",
    redirecting: (p) => `Redirecting to ${p}…`, cgu: "Terms", privacy: "Privacy",
    enterEmail: "Enter your email address.", linkSent: "Sign-in link sent! Check your inbox.",
    previewInfo: "Preview mode: use the link shown below.",
    sendFail: "Couldn't send right now. Try Google.",
    deliveryFail: "Email delivery is temporarily unavailable. Please try again shortly.",
    errGoogle: "Google sign-in failed. Try again, or use your email.",
    errMsft: "Microsoft sign-in failed. Try again, or use your email.",
    errLink: "This sign-in link is invalid or expired. Request a new one.",
    trustTitle: "Security & privacy",
    trustHosting: "Hosted on Railway",
    trustEncryption: "Encrypted connection (HTTPS)",
    thesustain: "Continue with thesustain.net",
    landingTitleA: "Your business,", landingTitleB: "driven with clarity.",
    proofRating: "Verified reviews · Trustpilot & Google",
    proofQuote: "“Zayado helped me on so many levels: company setup, flyers, structuring my ideas. Truly professional and caring.”",
    proofAuthor: "Theodora", proofMeta: "Trustpilot review · Aug 2025",
    startCta: "Get started", haveAccount: "I already have an account",
    welcomeBack: "Great to see you again!", sheetSub: "Sign in to get back to your cockpit.",
  },
};

const PRIVACY_URL = "https://zayado.net/confidentialite";
const CGU_URL = "https://zayado.net/cgu";
const LAST_EMAIL_KEY = "zayado_last_email";
const LAST_METHOD_KEY = "zayado_last_login_method";

export default function Login() {
  const navigate = useNavigate();
  const [lang, setLang] = useState(() => (typeof window !== "undefined" && localStorage.getItem("zayado_lang")) || "fr");
  const t = STR[lang] || STR.fr;

  const [email, setEmail] = useState(() => (typeof window !== "undefined" && localStorage.getItem(LAST_EMAIL_KEY)) || "");
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);
  const [devLink, setDevLink] = useState(null);
  const [oauthProvider, setOauthProvider] = useState(null); // "Google" | "Microsoft" | null
  // Nouveau gabarit : desktop = preuve à gauche + connexion à droite ;
  // mobile = page d'accueil + bottom-sheet de connexion au clic (modèle validé).
  const [isMobile, setIsMobile] = useState(() => typeof window !== "undefined" && window.innerWidth < 900);
  const [sheetOpen, setSheetOpen] = useState(false);
  useEffect(() => {
    const update = () => setIsMobile(window.innerWidth < 900);
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, []);

  // Vérification du lien magique : le backend renvoie vers /login?token=...
  // (voir routes/auth.py, dev_link). Sans cet effet, cliquer sur le lien
  // recharge juste la page de login sans jamais connecter personne.
  useEffect(() => {
    const token = new URLSearchParams(window.location.search).get("token");
    if (!token) return;
    verifyMagicLink(token)
      .then((res) => {
        toast.success("Connexion réussie");
        finishLogin(res);
      })
      .catch(() => toast.error(t.errLink));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Retour Google/Microsoft : le fournisseur redirige vers /login?code=...&state=...
  // (voir routes/oauth.py google_oauth_start/microsoft_oauth_start, state = "google_…"
  // ou "microsoft_…"). Sans cet effet, le code arrive bien mais n'est jamais échangé
  // contre une session — la page reste silencieusement sur /login.
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");
    const state = params.get("state") || "";
    if (!code) return;
    const provider = state.startsWith("microsoft_") ? "microsoft" : "google";
    setOauthProvider(provider === "google" ? "Google" : "Microsoft");
    const redirectUri = `${window.location.origin}/login`;
    oauthExchange(provider, code, redirectUri)
      .then((res) => {
        rememberMethod(provider);
        window.history.replaceState({}, "", "/login");
        finishLogin(res);
      })
      .catch(() => {
        setOauthProvider(null);
        window.history.replaceState({}, "", "/login?error=" + (provider === "google" ? "google_failed" : "microsoft_failed"));
        toast.error(provider === "google" ? t.errGoogle : t.errMsft);
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const changeLang = (l) => {
    setLang(l);
    localStorage.setItem("zayado_lang", l);
    setLanguage(l).catch(() => {});
  };

  const errorParam = new URLSearchParams(window.location.search).get("error");
  const errorMessage =
    errorParam === "google_failed" ? t.errGoogle
    : errorParam === "microsoft_failed" ? t.errMsft
    : errorParam === "link_failed" ? t.errLink
    : null;
  const isLinkError = errorParam === "link_failed";

  const lastMethod = localStorage.getItem(LAST_METHOD_KEY);
  const rememberMethod = (m) => localStorage.setItem(LAST_METHOD_KEY, m);
  const lastMethodLabel = lastMethod === "google" ? "Google" : lastMethod === "microsoft" ? "Microsoft" : lastMethod === "email" ? "Email" : null;

  const finishLogin = (res) => {
    localStorage.setItem("cours_auth_token", res.access_token || res.token);
    if (!res.user?.onboarding_done) {
      navigate("/onboarding");
      return;
    }
    // Après une déconnexion en cours de route, on rouvre la page que
    // l'utilisateur consultait plutôt que de le renvoyer systématiquement à
    // l'accueil — il perdait sinon le fil de ce qu'il était en train de faire.
    let destination = "/";
    try {
      const memorisee = sessionStorage.getItem("zay_redirect_after_login");
      sessionStorage.removeItem("zay_redirect_after_login");
      if (memorisee && memorisee.startsWith("/") && !memorisee.startsWith("//") && !memorisee.startsWith("/login")) {
        destination = memorisee;
      }
    } catch { /* noop */ }
    navigate(destination, { replace: true });
  };

  const doOauthLogin = async (provider, label) => {
    rememberMethod(provider);
    setOauthProvider(label);
    try {
      const redirectUri = `${window.location.origin}/login`;
      const res = await oauthStart(provider, redirectUri);
      window.location.href = res.authorization_url;
    } catch {
      toast.error(provider === "google" ? t.errGoogle : t.errMsft);
      setOauthProvider(null);
    }
  };
  const doLogin = () => doOauthLogin("google", "Google");
  const doLoginMicrosoft = () => doOauthLogin("microsoft", "Microsoft");

  // Compte test (preview/démo uniquement) : demo-login direct, fiable.
  const openTestAccount = async () => {
    try {
      const res = await demoLogin("thomas@zayado.fr");
      rememberMethod("email");
      toast.success("Compte ouvert");
      finishLogin(res);
    } catch { toast.error("Compte test indisponible ici."); }
  };

  // SSO thesustain.net (démo) : compte membre dédié, même mécanisme que le
  // compte test — fiable, pas de dépendance à l'envoi d'email.
  const openThesustain = async () => {
    try {
      localStorage.setItem("zayado_sso", "thesustain");
      localStorage.removeItem("zayado_sso_seeded");
      const res = await demoLogin("membre@thesustain.net");
      rememberMethod("thesustain");
      finishLogin(res);
    } catch { toast.error("SSO thesustain.net indisponible ici."); }
  };

  const _host = (typeof window !== "undefined" && window.location.hostname) || "";
  const IS_PRODUCTION = /(^|\.)zayado\.net$/i.test(_host) || /(^|\.)myextension-ai\.com$/i.test(_host);

  const sendLink = async (addr) => {
    const value = (addr || "").trim();
    if (!value) { toast.error(t.enterEmail); return; }
    setSending(true);
    try {
      const res = await sendMagicLink(value);
      localStorage.setItem(LAST_EMAIL_KEY, value);
      rememberMethod("email");
      setSent(true);
      if (res?.delivered_via_email && !res?.dev_link) {
        toast.success(t.linkSent); setDevLink(null);
      } else if (res?.dev_link) {
        setDevLink(res.dev_link); toast.info(t.previewInfo);
      } else if (res?.delivery_failed) {
        setSent(false); toast.error(t.deliveryFail);
      } else {
        toast.success(t.linkSent); setDevLink(null);
      }
    } catch {
      toast.error(t.sendFail);
    } finally {
      setSending(false);
    }
  };

  const emailContinue = (e) => { e.preventDefault(); sendLink(email); };

  const blocConnexion = (
    <>
      <div className="login-card" data-testid="login-card">

          {errorMessage && (
            <div className="login-error-banner" data-testid="login-error-banner">
              {errorMessage}
              {isLinkError && (
                <div style={{ marginTop: 8 }}>
                  <button className="login-resend" onClick={() => sendLink(email)} disabled={sending} data-testid="login-resend-btn">
                    {sending ? <Loader2 size={14} className="spin" /> : <RotateCcw size={14} />} {t.resend}
                  </button>
                </div>
              )}
            </div>
          )}

          <div className="login-social-row">
            <button className="login-btn login-btn-light login-btn-social" onClick={doLogin} data-testid="login-google-btn">
              <GoogleIcon /> {t.google}
            </button>
            <button className="login-btn login-btn-msft login-btn-social" onClick={doLoginMicrosoft} data-testid="login-microsoft-btn">
              <MicrosoftIcon /> {t.microsoft}
            </button>
          </div>

          <div className="login-sep"><span>{t.orEmail}</span></div>

          {sent ? (
            <div className="login-sent" data-testid="login-email-sent">
              <Mail size={18} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <strong>{devLink ? t.previewMode : t.emailSent}</strong>
                {devLink ? (
                  <>
                    <span>{t.previewText}</span>
                    <a href={devLink} data-testid="login-dev-link"
                      style={{ display: "inline-block", marginTop: 8, padding: "8px 14px", borderRadius: 999,
                        background: "#DEC2A3", color: "#0B1F3A", fontWeight: 700, fontSize: 13, textDecoration: "none", wordBreak: "break-all" }}>
                      {t.connectNow}
                    </a>
                    <div style={{ marginTop: 8 }}>
                      <button className="login-resend" onClick={() => sendLink(email)} disabled={sending} data-testid="login-resend-btn">
                        {sending ? <Loader2 size={14} className="spin" /> : <RotateCcw size={14} />} {t.resend}
                      </button>
                    </div>
                  </>
                ) : (
                  <>
                    <span>{t.clickLink(email)}</span>
                    <div style={{ marginTop: 8 }}>
                      <button className="login-resend" onClick={() => sendLink(email)} disabled={sending} data-testid="login-resend-btn">
                        {sending ? <Loader2 size={14} className="spin" /> : <RotateCcw size={14} />} {t.resend}
                      </button>
                    </div>
                  </>
                )}
              </div>
            </div>
          ) : (
            <form onSubmit={emailContinue}>
              <label className="login-input-label" htmlFor="login-email">{t.yourEmail}</label>
              <input id="login-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                placeholder="vous@exemple.fr" className="login-input" data-testid="login-email-input" />
              <button type="submit" className="login-btn login-btn-dark" disabled={sending} data-testid="login-email-btn">
                {sending ? <Loader2 size={16} className="spin" /> : <Mail size={16} />} {t.getLink}
              </button>
            </form>
          )}

          {lastMethodLabel && (
            <p className="login-last-line" data-testid="login-last-method">{t.lastLogin} : {lastMethodLabel}</p>
          )}

          <p className="login-microcopy">{t.noAccount}</p>

          <div className="login-sep-thin" />

          <button className="login-btn login-btn-social" onClick={openThesustain} data-testid="login-thesustain-btn"
            style={{ marginTop: 4, borderColor: "rgba(222, 194, 163,0.5)", color: "var(--gold-strong, #DEC2A3)" }}>
            {t.thesustain}
          </button>
          {!IS_PRODUCTION && (
            <>
              <div className="login-sep-thin" />
              <button className="login-btn login-btn-teal" onClick={openTestAccount} data-testid="login-guest-btn">
                {t.testAccount}
              </button>
            </>
          )}
      </div>

      <p className="login-foot">
        <ShieldCheck size={13} />{" "}
        <a href={CGU_URL} target="_blank" rel="noopener noreferrer">{t.cgu}</a>
        <span className="login-link-dot">·</span>
        <a href={PRIVACY_URL} target="_blank" rel="noopener noreferrer" data-testid="login-privacy-link">{t.privacy}</a>
      </p>

      <div className="login-trust" data-testid="login-trust-footer"
        style={{ display: "flex", flexWrap: "wrap", gap: 14, justifyContent: "center", marginTop: 14, opacity: 0.7, color: "rgba(255,255,255,0.7)" }}>
        <span style={{ display: "inline-flex", alignItems: "center", gap: 5, fontSize: 11 }} title={t.trustHosting}>
          <Server size={12} /> {t.trustHosting}
        </span>
        <span style={{ display: "inline-flex", alignItems: "center", gap: 5, fontSize: 11 }} title={t.trustEncryption}>
          <Lock size={12} /> {t.trustEncryption}
        </span>
      </div>
    </>
  );

  const etoiles = (
    <span className="login-proof-stars" aria-label="5 sur 5">
      {[...Array(5)].map((_, i) => <Star key={i} size={15} fill="#E8C96A" color="#E8C96A" />)}
    </span>
  );

  return (
    <div className="login-screen" data-testid="login-page">
      <div className="login-sky" />

      {oauthProvider && (
        <div className="login-oauth-overlay" data-testid="login-oauth-overlay">
          <Loader2 size={34} className="spin" style={{ color: "#F1E2CC" }} />
          <p>{t.redirecting(oauthProvider)}</p>
        </div>
      )}

      <motion.div className={`login-inner ${isMobile ? "is-landing" : "is-split"}`}
        initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>

        <div className="login-topbar">
          <div className="login-lang" data-testid="login-lang-switch" role="group" aria-label="Language">
            <button className={lang === "fr" ? "active" : ""} onClick={() => changeLang("fr")} data-testid="login-lang-fr">FR</button>
            <button className={lang === "en" ? "active" : ""} onClick={() => changeLang("en")} data-testid="login-lang-en">EN</button>
          </div>
        </div>

        {!isMobile && (
          <aside className="login-proof" data-testid="login-proof">
            <img src="/logo-icon.png" alt="MyExtension Business" className="login-logo-img" />
            <h1 className="login-proof-headline">
              {t.landingTitleA} <em>{t.landingTitleB}</em>
            </h1>
            <div className="login-proof-rating">{etoiles}<span>{t.proofRating}</span></div>
            <figure className="login-proof-card">
              <blockquote>{t.proofQuote}</blockquote>
              <figcaption>
                <span className="login-proof-avatar">TH</span>
                <span><b>{t.proofAuthor}</b><small>{t.proofMeta}</small></span>
              </figcaption>
            </figure>
          </aside>
        )}

        {isMobile ? (
          <div className="login-landing" data-testid="login-landing">
            <img src="/logo-icon.png" alt="MyExtension Business" className="login-logo-img" data-testid="login-logo" />
            <h1 className="login-proof-headline" data-testid="login-title">
              {t.landingTitleA} <em>{t.landingTitleB}</em>
            </h1>
            <div className="login-proof-rating">{etoiles}<span>{t.proofRating}</span></div>
            <figure className="login-proof-card">
              <blockquote>{t.proofQuote}</blockquote>
              <figcaption>
                <span className="login-proof-avatar">TH</span>
                <span><b>{t.proofAuthor}</b><small>{t.proofMeta}</small></span>
              </figcaption>
            </figure>
            <button className="login-btn login-cta-start" onClick={() => setSheetOpen(true)} data-testid="login-start-btn">
              {t.startCta}
            </button>
            <button className="login-have-account" onClick={() => setSheetOpen(true)} data-testid="login-have-account">
              {t.haveAccount}
            </button>
          </div>
        ) : (
          <>
            <h1 className="login-title-wrap" data-testid="login-title">
              <span className="login-title">
                {t.welcome} MyExtension <span className="login-brand-name-accent">Business</span>
                <span className="login-title-by" data-testid="login-title-by"><em>by</em> Zayado</span>
              </span>
            </h1>
            <p className="login-subtitle login-subtitle-plain">{t.subtitle}</p>
            {blocConnexion}
          </>
        )}
      </motion.div>

      {isMobile && sheetOpen && (
        <div className="login-sheet-backdrop" data-testid="login-sheet-backdrop" onClick={(e) => { if (e.target === e.currentTarget) setSheetOpen(false); }}>
          <section className="login-sheet" role="dialog" aria-modal="true" data-testid="login-sheet">
            <button className="login-sheet-close" onClick={() => setSheetOpen(false)} aria-label="Fermer" data-testid="login-sheet-close"><X size={17} /></button>
            <h2 className="login-sheet-title">{t.welcomeBack}</h2>
            <p className="login-sheet-sub">{t.sheetSub}</p>
            {blocConnexion}
          </section>
        </div>
      )}

      <InstallBanner />
    </div>
  );
}
