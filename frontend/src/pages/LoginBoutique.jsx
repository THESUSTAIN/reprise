/* Login Boutique Zayado — design boutique (palette navy/or, sans look SaaS).
   Utilise la même API auth que /login (même DB users) :
   - POST /api/auth/email/request-code
   - POST /api/auth/email/verify-code
   Différences UX vs /login :
   - Pas de Microsoft, pas de Google (boutique = parcours e-commerce léger)
   - Visuel boutique (header logo "Zayado · Boutique", focus mode édito)
   - Après login : redirige vers /compte au lieu de /app */
import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { ArrowRight, Mail, Loader2, ArrowLeft } from "lucide-react";
import { Helmet } from "react-helmet-async";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

const NAVY = "var(--zayado-navy)";
const GOLD = "var(--zayado-gold)";
const MUTED = "var(--zayado-muted)";

export default function LoginBoutique() {
  const navigate = useNavigate();
  const { setUser } = useAuth();

  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [step, setStep] = useState(1);
  const [devCode, setDevCode] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fmtError = (err, fb = "Erreur") => {
    const d = err?.response?.data?.detail;
    if (typeof d === "string") return d;
    if (Array.isArray(d)) return d.map((x) => x?.msg || String(x)).join(", ");
    return fb;
  };

  const requestCode = async (e) => {
    e?.preventDefault();
    setError("");
    if (!email) { setError("Veuillez renseigner votre email."); return; }
    setLoading(true);
    try {
      const r = await api.post("/auth/email/request-code", { email });
      if (r.data?.dev_code) setDevCode(r.data.dev_code);
      setStep(2);
    } catch (err) {
      setError(fmtError(err, "Erreur — vérifiez votre email."));
    } finally { setLoading(false); }
  };

  const verifyCode = async (e) => {
    e?.preventDefault();
    setError("");
    if (!code || code.length < 4) { setError("Code à 6 chiffres requis."); return; }
    setLoading(true);
    try {
      const r = await api.post("/auth/email/verify-code", { email, code });
      // Hydrate le contexte auth puis redirige vers compte boutique
      setUser?.(r.data?.user || { email });
      navigate("/compte", { replace: true });
    } catch (err) {
      setError(fmtError(err, "Code invalide ou expiré."));
    } finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen flex flex-col"
         style={{ background: "var(--zayado-cream)" }}
         data-testid="login-boutique-page">
      <Helmet><title>Connexion Boutique · Zayado</title></Helmet>

      {/* Header minimal */}
      <header className="border-b border-[var(--zayado-border)] bg-white">
        <div className="max-w-[1200px] mx-auto px-4 md:px-6 h-14 flex items-center justify-between">
          <Link to="/boutique" className="font-display italic text-lg"
                style={{ fontFamily: "'DM Serif Display', serif", color: NAVY }}>
            Zayado · <span style={{ color: GOLD }}>Boutique</span>
          </Link>
          <Link to="/connexion" className="text-xs hover:underline inline-flex items-center gap-1" style={{ color: MUTED }}>
            <ArrowLeft size={11} /> Changer d'espace
          </Link>
        </div>
      </header>

      {/* Form centré */}
      <main className="flex-1 flex items-center justify-center px-4 py-10">
        <div className="w-full max-w-[420px]">
          <div className="text-[11px] uppercase tracking-[0.3em] text-center mb-2" style={{ color: GOLD }}>
            Mon compte Boutique
          </div>
          <h1 className="font-display italic text-center mb-2"
              style={{ fontFamily: "'DM Serif Display', serif",
                       fontSize: "clamp(1.8rem, 4vw, 2.6rem)", lineHeight: 1.1, color: NAVY }}>
            Connexion
          </h1>
          <p className="text-sm text-center mb-8" style={{ color: MUTED }}>
            {step === 1
              ? "Recevez votre code de connexion par email."
              : "Saisissez le code reçu par email."}
          </p>

          <div className="bg-white border border-[var(--zayado-border)] rounded-3xl p-7 shadow-sm">
            {step === 1 && (
              <form onSubmit={requestCode} className="space-y-4">
                <label className="block">
                  <span className="text-[11px] uppercase tracking-wider font-medium" style={{ color: NAVY }}>
                    Adresse email
                  </span>
                  <div className="mt-1.5 relative">
                    <Mail size={15} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: MUTED }} />
                    <input type="email" required value={email}
                           onChange={(e) => setEmail(e.target.value)}
                           placeholder="vous@email.fr"
                           className="w-full pl-10 pr-3 py-3 border border-[var(--zayado-border)] rounded-xl text-sm focus:outline-none focus:border-[var(--zayado-navy)]"
                           data-testid="boutique-login-email" />
                  </div>
                </label>

                {error && <div className="text-xs text-red-700">{error}</div>}

                <button type="submit" disabled={loading}
                        className="w-full py-3 rounded-full text-white text-sm font-medium flex items-center justify-center gap-2 disabled:opacity-50"
                        style={{ background: NAVY }}
                        data-testid="boutique-login-submit">
                  {loading ? <Loader2 size={14} className="animate-spin" /> : null}
                  Recevoir mon code <ArrowRight size={13} />
                </button>
              </form>
            )}

            {step === 2 && (
              <form onSubmit={verifyCode} className="space-y-4">
                <div className="text-xs text-center" style={{ color: MUTED }}>
                  Code envoyé à <strong style={{ color: NAVY }}>{email}</strong>
                </div>

                {devCode && (
                  <div className="text-xs px-3 py-2 rounded-lg text-center"
                       style={{ background: "rgba(212,175,55,0.15)", color: NAVY }}>
                    <strong>Mode dev</strong> : code <code>{devCode}</code>
                  </div>
                )}

                <label className="block">
                  <span className="text-[11px] uppercase tracking-wider font-medium" style={{ color: NAVY }}>
                    Code à 6 chiffres
                  </span>
                  <input type="text" required value={code}
                         onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                         placeholder="123456"
                         maxLength={6}
                         autoFocus
                         className="mt-1.5 w-full px-4 py-3 border border-[var(--zayado-border)] rounded-xl text-center tracking-[0.4em] text-lg font-mono focus:outline-none focus:border-[var(--zayado-navy)]"
                         data-testid="boutique-login-code" />
                </label>

                {error && <div className="text-xs text-red-700">{error}</div>}

                <button type="submit" disabled={loading}
                        className="w-full py-3 rounded-full text-white text-sm font-medium flex items-center justify-center gap-2 disabled:opacity-50"
                        style={{ background: NAVY }}
                        data-testid="boutique-login-verify">
                  {loading ? <Loader2 size={14} className="animate-spin" /> : null}
                  Se connecter
                </button>

                <button type="button" onClick={() => { setStep(1); setCode(""); setError(""); }}
                        className="w-full text-xs hover:underline" style={{ color: MUTED }}>
                  ← Modifier mon email
                </button>
              </form>
            )}
          </div>

          <p className="text-[11px] text-center mt-6" style={{ color: MUTED }}>
            En vous connectant, vous acceptez nos{" "}
            <Link to="/legal/cgv" className="underline">CGV</Link> et notre{" "}
            <Link to="/legal/confidentialite" className="underline">politique de confidentialité</Link>.
          </p>
        </div>
      </main>
    </div>
  );
}
