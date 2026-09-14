/* CookieBanner — bandeau RGPD conforme CNIL.
   - 3 catégories : essentiels (toujours actifs), analytics, marketing
   - Choix sauvegardé dans localStorage `zay_cookie_consent` (v1)
   - Réaffiché si version du consentement obsolète (changement de politique)
   - Lien vers /legal/confidentialite
*/
import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { X, Cookie, Settings2, Check } from "lucide-react";

const STORAGE_KEY = "zay_cookie_consent";
const POLICY_VERSION = 1;

const DEFAULT_CONSENT = {
  v: POLICY_VERSION,
  essential: true,       // toujours actif (non désactivable)
  analytics: false,
  marketing: false,
  ts: null,
};

export function getConsent() {
  try {
    const raw = JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
    if (!raw || raw.v !== POLICY_VERSION) return null;
    return raw;
  } catch { return null; }
}

function saveConsent(c) {
  const data = { ...DEFAULT_CONSENT, ...c, ts: new Date().toISOString() };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  window.dispatchEvent(new CustomEvent("zayado:consent-updated", { detail: data }));
}

export default function CookieBanner() {
  const [show, setShow] = useState(false);
  const [openDetails, setOpenDetails] = useState(false);
  const [analytics, setAnalytics] = useState(false);
  const [marketing, setMarketing] = useState(false);

  useEffect(() => {
    // Petit délai pour éviter flash au premier paint
    const t = setTimeout(() => {
      if (!getConsent()) setShow(true);
    }, 800);
    // Écoute l'event pour rouvrir le bandeau depuis le footer
    const onReopen = () => {
      const c = getConsent() || DEFAULT_CONSENT;
      setAnalytics(!!c.analytics); setMarketing(!!c.marketing);
      setOpenDetails(true); setShow(true);
    };
    window.addEventListener("zayado:cookies-reopen", onReopen);
    return () => {
      clearTimeout(t);
      window.removeEventListener("zayado:cookies-reopen", onReopen);
    };
  }, []);

  if (!show) return <div className="notranslate" translate="no" aria-hidden="true" style={{ display: "none" }} />;

  const acceptAll = () => { saveConsent({ analytics: true, marketing: true }); setShow(false); };
  const refuseAll = () => { saveConsent({ analytics: false, marketing: false }); setShow(false); };
  const acceptCustom = () => { saveConsent({ analytics, marketing }); setShow(false); };

  return (
    <div className="fixed inset-x-0 bottom-0 z-[9999] p-3 sm:p-5 pointer-events-none notranslate" translate="no" data-testid="cookie-banner">
      <div className="max-w-3xl mx-auto pointer-events-auto">
        <div className="bg-white rounded-2xl shadow-2xl border border-[var(--zayado-border)] overflow-hidden">
          {/* Bandeau principal */}
          <div className="p-5 sm:p-6">
            <div className="flex items-start gap-3 mb-3">
              <div className="w-10 h-10 rounded-full flex items-center justify-center shrink-0"
                   style={{ background: "var(--zayado-gold-bg, #faf3df)" }}>
                <Cookie size={18} style={{ color: "var(--zayado-gold)" }} />
              </div>
              <div className="flex-1">
                <div className="text-sm font-bold mb-1" style={{ color: "var(--zayado-navy)" }}>
                  Vos données, votre choix
                </div>
                <p className="text-xs leading-relaxed" style={{ color: "var(--zayado-muted)" }}>
                  On utilise des cookies essentiels (panier, session, sécurité — toujours actifs) et,
                  avec votre accord, des cookies pour mesurer l'audience et personnaliser votre expérience.
                  Aucun cookie ne sert à vous tracer hors de Zayado.
                </p>
              </div>
            </div>

            {/* Détails déroulés */}
            {openDetails && (
              <div className="mt-4 space-y-2 border-t border-[var(--zayado-border)] pt-4" data-testid="cookie-details">
                <CookieRow
                  title="Cookies essentiels"
                  desc="Connexion, panier, sécurité CSRF. Indispensables au fonctionnement du site."
                  checked={true}
                  disabled={true}
                />
                <CookieRow
                  title="Mesure d'audience"
                  desc="Statistiques anonymisées pour améliorer l'expérience (Plausible, sans tracking individuel)."
                  checked={analytics}
                  onChange={setAnalytics}
                  testid="cookie-analytics"
                />
                <CookieRow
                  title="Marketing & personnalisation"
                  desc="Newsletter, recommandations produits adaptées à vos centres d'intérêt."
                  checked={marketing}
                  onChange={setMarketing}
                  testid="cookie-marketing"
                />
              </div>
            )}

            {/* Actions */}
            <div className="flex flex-wrap items-center gap-2 mt-4">
              {!openDetails ? (
                <>
                  <button onClick={refuseAll}
                          className="px-4 py-2 rounded-full text-xs font-medium border border-[var(--zayado-border)] hover:bg-[var(--zayado-cream)]"
                          style={{ color: "var(--zayado-text)" }}
                          data-testid="cookie-refuse">
                    Refuser
                  </button>
                  <button onClick={() => setOpenDetails(true)}
                          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full text-xs font-medium border border-[var(--zayado-border)] hover:bg-[var(--zayado-cream)]"
                          style={{ color: "var(--zayado-text)" }}
                          data-testid="cookie-customize">
                    <Settings2 size={12} /> Personnaliser
                  </button>
                  <button onClick={acceptAll}
                          className="ml-auto px-5 py-2 rounded-full text-xs font-medium text-white btn-press"
                          style={{ background: "var(--zayado-navy)" }}
                          data-testid="cookie-accept-all">
                    Tout accepter
                  </button>
                </>
              ) : (
                <>
                  <button onClick={refuseAll}
                          className="px-4 py-2 rounded-full text-xs font-medium border border-[var(--zayado-border)] hover:bg-[var(--zayado-cream)]"
                          style={{ color: "var(--zayado-text)" }}
                          data-testid="cookie-refuse-all">
                    Tout refuser
                  </button>
                  <button onClick={acceptCustom}
                          className="ml-auto inline-flex items-center gap-1.5 px-5 py-2 rounded-full text-xs font-medium text-white btn-press"
                          style={{ background: "var(--zayado-navy)" }}
                          data-testid="cookie-save">
                    <Check size={12} /> Enregistrer mes choix
                  </button>
                </>
              )}
            </div>

            <div className="mt-3 text-[10px] text-center" style={{ color: "var(--zayado-muted)" }}>
              <Link to="/legal/confidentialite" className="hover:underline">
                Politique de confidentialité
              </Link>
              {" · "}
              <Link to="/legal/mentions-legales" className="hover:underline">
                Mentions légales
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function CookieRow({ title, desc, checked, onChange, disabled, testid }) {
  return (
    <label className={"flex items-start gap-3 p-3 rounded-lg cursor-pointer " + (disabled ? "opacity-70" : "hover:bg-[var(--zayado-cream)]")}>
      <input type="checkbox" checked={checked} disabled={disabled}
             onChange={(e) => onChange && onChange(e.target.checked)}
             className="mt-0.5 accent-[var(--zayado-navy)]" data-testid={testid} />
      <div>
        <div className="text-xs font-medium" style={{ color: "var(--zayado-text)" }}>{title}{disabled && " (requis)"}</div>
        <div className="text-[10px] leading-relaxed" style={{ color: "var(--zayado-muted)" }}>{desc}</div>
      </div>
    </label>
  );
}
