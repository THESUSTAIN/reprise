import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Sparkles, ArrowRight, X } from "lucide-react";

/**
 * Bannière sticky affichée sur le Dashboard si l'utilisateur a passé l'onboarding.
 *
 * - Visible si localStorage["zayado_onboarding_skipped"] === "1"
 * - Masquable (croix) → localStorage["zayado_onboarding_banner_dismissed"] = "1"
 * - CTA → /onboarding
 */
export default function OnboardingBanner() {
  const [show, setShow] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    try {
      const skipped = localStorage.getItem("zayado_onboarding_skipped") === "1";
      const dismissed = localStorage.getItem("zayado_onboarding_banner_dismissed") === "1";
      const onboarded = localStorage.getItem("zayado_onboarded") === "1";
      setShow(skipped && !dismissed && !onboarded);
    } catch (e) { /* noop */ }
  }, []);

  const dismiss = () => {
    try { localStorage.setItem("zayado_onboarding_banner_dismissed", "1"); } catch (e) { /* noop */ }
    setShow(false);
  };

  if (!show) return null;

  return (
    <div
      className="mb-5 rounded-2xl p-4 sm:p-5 flex items-center gap-3 shadow-md"
      style={{ background: "linear-gradient(135deg, #1a3a6e 0%, #2c4d85 100%)", color: "#f6f3ee" }}
      data-testid="onboarding-banner"
    >
      <div className="w-11 h-11 rounded-2xl grid place-items-center shrink-0"
           style={{ background: "#f3e9d0", color: "#b89855" }}>
        <Sparkles size={20} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="font-semibold text-[14.5px] mb-0.5">Finalise ton onboarding</div>
        <div className="text-[12.5px] opacity-85 leading-snug">
          3 questions courtes pour que le cockpit s&apos;aligne sur ton profil et tes priorités.
        </div>
      </div>
      <button
        onClick={() => navigate("/onboarding")}
        className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full text-[12.5px] font-semibold transition shrink-0 shadow-sm"
        style={{ background: "#f6f3ee", color: "#1a3a6e" }}
        data-testid="onboarding-banner-cta"
      >
        Compléter <ArrowRight size={13} />
      </button>
      <button
        onClick={dismiss}
        className="w-8 h-8 rounded-full grid place-items-center hover:bg-white/15 transition shrink-0"
        style={{ color: "#f6f3ee" }}
        aria-label="Fermer"
        data-testid="onboarding-banner-close"
      >
        <X size={15} />
      </button>
    </div>
  );
}
