// Content script — miroir dynamique (fix E1, audit).
//
// Avant : coquille vide (`window.__zayadoExtension = {version}`), ne lisait
// jamais rien de la page. Le manifest chargeait ça sur <all_urls> (E10),
// ce qui est à la fois inutile (rien n'était lu nulle part) et risqué pour
// la review Chrome Web Store (permission large sans justification claire).
//
// Maintenant : le script n'est injecté QUE sur Gmail / Google Calendar /
// Outlook (voir manifest.json → content_scripts.matches), et lit UNIQUEMENT
// ce qui est déjà affiché à l'écran dans l'onglet actif de l'utilisateur
// (lecture DOM locale — aucune requête réseau, aucun accès à un compte tiers,
// aucune donnée qui ne soit pas déjà sous les yeux de l'utilisateur).
//
// ⚠️ Limite honnête : les sélecteurs CSS ci-dessous ciblent la structure DOM
// actuelle de Gmail/Calendar/Outlook (interfaces non documentées, changent
// sans préavis côté Google/Microsoft). Ce n'est PAS une API officielle — un
// changement de mise en page côté Google/Microsoft peut casser l'extraction
// silencieusement (chaque tentative est dans un try/catch qui échoue en
// douceur plutôt que de planter la page de l'utilisateur).

(function () {
  window.__zayadoExtension = { version: "2.1.0" };

  function safeText(el) {
    return el && el.textContent ? el.textContent.trim() : "";
  }

  function extractGmail() {
    try {
      // Ligne d'objet du fil de discussion ouvert (h2 avec le rôle Gmail dédié).
      const subjectEl = document.querySelector("h2.hP, div[role='main'] h2");
      // Dernier expéditeur visible dans le fil ouvert.
      const senderEl = document.querySelector("span.gD, span[email]");
      if (!subjectEl && !senderEl) return null;
      return {
        module: "gmail",
        subject: safeText(subjectEl),
        sender: senderEl ? (senderEl.getAttribute("email") || safeText(senderEl)) : "",
      };
    } catch (e) {
      return null;
    }
  }

  function extractCalendar() {
    try {
      // Panneau de détail d'un événement Google Calendar ouvert.
      const titleEl = document.querySelector("[data-eventid] .I0UMhf, div[role='dialog'] h2");
      const timeEl = document.querySelector("div[role='dialog'] [data-text]");
      if (!titleEl) return null;
      return {
        module: "gcal",
        title: safeText(titleEl),
        time: safeText(timeEl),
      };
    } catch (e) {
      return null;
    }
  }

  function extractOutlook() {
    try {
      const subjectEl = document.querySelector("[aria-label='Ligne d’objet'], [role='heading'][aria-level='2']");
      const senderEl = document.querySelector("[aria-label*='De :'], span.OZZZK");
      if (!subjectEl && !senderEl) return null;
      return {
        module: "outlook",
        subject: safeText(subjectEl),
        sender: safeText(senderEl),
      };
    } catch (e) {
      return null;
    }
  }

  function extractContext() {
    const host = window.location.hostname;
    let data = null;
    if (host.includes("mail.google.com")) data = extractGmail();
    else if (host.includes("calendar.google.com")) data = extractCalendar();
    else if (host.includes("outlook.")) data = extractOutlook();
    return data;
  }

  function sendMirror() {
    const data = extractContext();
    if (!data) return; // rien de pertinent à l'écran → on n'envoie rien (pas de valeur inventée)
    try {
      chrome.runtime.sendMessage({
        type: "zayado_page_mirror",
        payload: { ...data, url: window.location.href, capturedAt: new Date().toISOString() },
      });
    } catch (e) {
      // Le service worker de fond peut être inactif (MV3) — pas bloquant,
      // la prochaine navigation/mutation retentera.
    }
  }

  // Gmail/Calendar/Outlook sont des SPA : le contenu change sans rechargement
  // de page. On observe les mutations du corps de page (avec un léger debounce)
  // plutôt que de ne lire qu'au chargement initial (ce qui aurait raté 100%
  // des changements de fil/événement une fois la page ouverte).
  let debounceTimer = null;
  const observer = new MutationObserver(() => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(sendMirror, 800);
  });
  observer.observe(document.body, { childList: true, subtree: true });

  sendMirror();
})();
