/* Composant partagé : Gate d'accès TheSustain.

   Utilisé par /memoire et /galerie-souvenir pour vérifier qu'un email
   TheSustain a été saisi avant l'accès. L'email est persisté dans
   localStorage.zay_thesustain_email (clé partagée entre les 2 pages).
*/
import React, { useState } from "react";
import { Helmet } from "react-helmet-async";
import { BookOpen } from "lucide-react";
import { PARTNER as P, PARTNER_FONT } from "../pages/partners-theme";
import TheSustainHeader from "./TheSustainHeader";
import TheSustainFooter from "./TheSustainFooter";

export const TS_EMAIL_KEY = "zay_thesustain_email";

export function getTheSustainEmail() {
  if (typeof localStorage === "undefined") return "";
  return localStorage.getItem(TS_EMAIL_KEY) || "";
}

export function setTheSustainEmail(email) {
  if (typeof localStorage === "undefined") return;
  localStorage.setItem(TS_EMAIL_KEY, email);
}

export function clearTheSustainEmail() {
  if (typeof localStorage === "undefined") return;
  localStorage.removeItem(TS_EMAIL_KEY);
}

export default function TheSustainGate({
  title = "Accès via TheSustain.",
  description,
  metaTitle = "Accès TheSustain",
  onConnect,
}) {
  const [email, setEmail] = useState("");
  const [accepted, setAccepted] = useState(false);

  const submit = (e) => {
    e.preventDefault();
    const clean = email.trim().toLowerCase();
    if (!clean || !clean.includes("@") || !accepted) return;
    setTheSustainEmail(clean);
    onConnect?.(clean);
  };

  const defaultDesc = (
    <>
      La fonctionnalité est réservée aux membres de
      <a href="https://thesustain.net" target="_blank" rel="noopener noreferrer"
         className="font-bold underline mx-1" style={{ color: P.NAVY }}>
        thesustain.net
      </a>.
      Saisissez votre email TheSustain pour continuer.
    </>
  );

  return (
    <div className="min-h-screen ts-page flex flex-col"
         style={{ background: P.BG, fontFamily: PARTNER_FONT.sans }}
         data-testid="thesustain-gate">
      <Helmet>
        <title>{metaTitle}</title>
      </Helmet>
      <TheSustainHeader />
      <div className="flex-1 flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-md rounded-3xl bg-white p-8 md:p-10 shadow-sm"
             style={{ border: `1px solid ${P.BORDER}` }}>
          <div className="w-12 h-12 rounded-2xl flex items-center justify-center mb-5 mx-auto"
               style={{ background: "rgba(212,175,55,0.18)" }}>
            <BookOpen size={20} style={{ color: P.AMBER }} />
          </div>
          <h1 className="font-bold text-3xl text-center mb-3"
              style={{ color: P.NAVY }}>
            {title}
          </h1>
          <p className="text-sm text-center mb-7" style={{ color: P.TEXT_MUTED }}>
            {description || defaultDesc}
          </p>
          <form onSubmit={submit} className="space-y-4">
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                   placeholder="vous@email.com" required
                   data-testid="thesustain-email-input"
                   className="w-full px-4 py-3 text-sm rounded-xl border focus:outline-none focus:ring-2"
                   style={{ borderColor: P.BORDER, color: P.NAVY, background: P.BG }} />
            <label className="flex items-start gap-2.5 text-xs cursor-pointer"
                   style={{ color: P.TEXT_MUTED }}>
              <input type="checkbox" checked={accepted}
                     onChange={(e) => setAccepted(e.target.checked)}
                     data-testid="thesustain-accept"
                     className="mt-0.5 shrink-0" />
              <span>
                Je confirme être membre de TheSustain et accepter que cet email
                serve à sauvegarder mes cartes mémoire et souvenirs.
              </span>
            </label>
            <button type="submit" disabled={!email || !accepted}
                    data-testid="thesustain-connect-btn"
                    className="w-full inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xl text-sm font-bold text-white transition disabled:opacity-50"
                    style={{ background: P.NAVY }}>
              Continuer →
            </button>
            <a href="https://thesustain.net" target="_blank" rel="noopener noreferrer"
               className="block text-center text-xs hover:underline" style={{ color: P.AMBER }}>
              Pas encore membre ? Rejoindre TheSustain →
            </a>
          </form>
        </div>
      </div>
      <TheSustainFooter />
    </div>
  );
}
