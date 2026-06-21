import React, { useEffect, useState } from "react";
import { toast, Toaster } from "sonner";
import { useI18n } from "@fm/context/I18nContext";

const KEY = "mxai_lang_announced";
const LABELS = { fr: "Français", en: "English", es: "Español", de: "Deutsch", it: "Italiano", pt: "Português" };

/**
 * Subtle one-time notice when the app first detects the user's language.
 * Tells them how to change it via the "Mon espace" menu.
 */
export default function LangAutoToast() {
  const { lang, t } = useI18n();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  useEffect(() => {
    if (!mounted) return;
    try {
      if (localStorage.getItem(KEY)) return;
      localStorage.setItem(KEY, lang);
    } catch { return; }
    const msg = {
      fr: `Application affichée en Français · vous pouvez changer la langue depuis "${t("nav.monEspace")}".`,
      en: `App displayed in English · you can change the language from "${t("nav.monEspace")}".`,
      es: `Aplicación en Español · puede cambiar el idioma desde "${t("nav.monEspace")}".`,
      de: `App auf Deutsch · Sprache änderbar im Menü "${t("nav.monEspace")}".`,
      it: `App in Italiano · puoi cambiare la lingua in "${t("nav.monEspace")}".`,
      pt: `App em Português · pode mudar o idioma em "${t("nav.monEspace")}".`,
    }[lang] || `Language set to ${LABELS[lang] || lang}.`;
    const id = setTimeout(() => toast(msg, { duration: 6000 }), 900);
    return () => clearTimeout(id);
  }, [mounted, lang, t]);

  return <Toaster richColors position="top-center" closeButton />;
}
