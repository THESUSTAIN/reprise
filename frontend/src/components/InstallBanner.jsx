import { useEffect, useRef, useState } from "react";
import { X } from "lucide-react";

const INSTALL_DISMISS_KEY = "mx_pwa_prompt_dismissed";

// Bannière d'installation PWA — reprend le modèle natif (carte blanche,
// icône carrée, titre + sous-titre, lien d'action coloré, bouton fermer)
// plutôt qu'un toast générique. Utilisable à la fois sur Login (avant
// connexion) et dans l'app (Layout.jsx) — même composant, même logique.
export function useInstallPromptState() {
  const deferred = useRef(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const onPrompt = (e) => {
      e.preventDefault();
      deferred.current = e;
      try { if (localStorage.getItem(INSTALL_DISMISS_KEY) === "1") return; } catch { /* noop */ }
      setVisible(true);
    };
    const onInstalled = () => setVisible(false);
    window.addEventListener("beforeinstallprompt", onPrompt);
    window.addEventListener("appinstalled", onInstalled);
    return () => {
      window.removeEventListener("beforeinstallprompt", onPrompt);
      window.removeEventListener("appinstalled", onInstalled);
    };
  }, []);

  const install = async () => {
    if (!deferred.current) return;
    deferred.current.prompt();
    await deferred.current.userChoice;
    deferred.current = null;
    setVisible(false);
  };

  const dismiss = () => {
    try { localStorage.setItem(INSTALL_DISMISS_KEY, "1"); } catch { /* noop */ }
    setVisible(false);
  };

  return { visible, install, dismiss };
}

export default function InstallBanner() {
  const { visible, install, dismiss } = useInstallPromptState();
  if (!visible) return null;

  return (
    <div
      className="fixed inset-x-0 bottom-0 z-[200] flex justify-center px-3 pb-3 sm:px-4 sm:pb-4"
      data-testid="pwa-install-banner"
    >
      <div className="flex w-full max-w-md items-center gap-3 rounded-2xl bg-white px-4 py-3.5 shadow-[0_12px_40px_rgba(0,0,0,0.25)]">
        <button
          onClick={dismiss}
          aria-label="Fermer"
          data-testid="pwa-install-dismiss"
          className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[#8A8F98] hover:bg-black/5"
        >
          <X size={16} />
        </button>
        <img
          src="/logo-icon.png"
          alt="Zayado"
          className="h-11 w-11 shrink-0 rounded-xl object-cover"
        />
        <div className="min-w-0 flex-1">
          <p className="text-[15px] font-bold leading-tight text-[#14171A]">Faciliter votre quotidien&nbsp;?</p>
          <p className="mt-0.5 text-[13px] leading-tight text-[#5B6169]">Téléchargez l'application Zayado</p>
        </div>
        <button
          onClick={install}
          data-testid="pwa-install-download"
          className="shrink-0 text-[15px] font-semibold text-[#2E5BFF] hover:underline"
        >
          Télécharger
        </button>
      </div>
    </div>
  );
}
