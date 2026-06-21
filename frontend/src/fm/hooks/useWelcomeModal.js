import { useState, useEffect } from "react";
import { WELCOME_CONTENT } from "@fm/content/welcomeContent";

const STORAGE_PREFIX = "zay_welcome_seen_";

/**
 * useWelcomeModal(pageKey)
 * ───────────────────────────────────────────────────────────────────────
 * Affiche le popup de bienvenue de `pageKey` la première fois que
 * l'utilisateur visite la page. Persisté en localStorage — ne réapparaît
 * plus une fois fermé.
 *
 * Exemple :
 *   const { content, show, close } = useWelcomeModal("dashboard");
 *   <WelcomeModal open={show} onClose={close} {...content} />
 */
export default function useWelcomeModal(pageKey) {
  const content = WELCOME_CONTENT[pageKey] || null;
  const storageKey = STORAGE_PREFIX + pageKey;

  const [show, setShow] = useState(false);

  useEffect(() => {
    if (!content) return;
    try {
      const seen = localStorage.getItem(storageKey);
      if (!seen) setShow(true);
    } catch {
      setShow(true); // si localStorage indisponible, on affiche quand même
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pageKey]);

  const close = () => {
    setShow(false);
    try { localStorage.setItem(storageKey, "1"); } catch {}
  };

  // Permet de relancer le tutoriel manuellement (ex: bouton "Aide")
  const replay = () => setShow(true);

  return { content, show: show && !!content, close, replay };
}
