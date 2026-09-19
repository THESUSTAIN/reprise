// Background service worker.
//
// Fix E1 (audit) : reçoit maintenant le contexte remonté par content.js
// (Gmail/Calendar/Outlook) et le stocke pour que le side panel l'affiche
// automatiquement, comme il le fait déjà pour la capture manuelle par menu
// contextuel.
//
// Fix E2 (audit) : pont d'authentification prod. Avant, sidepanel.js ne
// savait consommer QUE le `dev_link` (auto-consommé) renvoyé par l'API en
// préproduction — en prod, l'API renvoie `delivered_via_email: true` sans
// lien direct (par design, côté serveur c'est déjà correct — voir
// backend/routes/auth.py), et rien côté extension ne détectait jamais que
// l'utilisateur s'était connecté ailleurs après avoir cliqué le lien reçu
// par email. Ce listener permet à la page web (app.zayado.net, après que
// l'utilisateur a cliqué son lien magique) d'transmettre la session à
// l'extension via chrome.runtime.sendMessage — voir externally_connectable
// dans manifest.json.
chrome.runtime.onInstalled.addListener(() => {
  try {
    chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true });
  } catch (e) { /* older Chrome */ }
  chrome.contextMenus.create({
    id: "zayado-capture",
    title: "Envoyer la sélection à Zayado Copilot",
    contexts: ["selection", "link", "page"],
  });
});

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  const payload = {
    title: (tab && tab.title) || "",
    url: info.linkUrl || (tab && tab.url) || "",
    selection: info.selectionText || "",
  };
  await chrome.storage.local.set({ zayado_pending_context: payload });
  try { await chrome.sidePanel.open({ tabId: tab.id }); } catch (e) { /* ignore */ }
});

// Contexte remonté par content.js (Gmail/Calendar/Outlook) — fix E1.
chrome.runtime.onMessage.addListener((message) => {
  if (message && message.type === "zayado_page_mirror") {
    chrome.storage.local.set({ zayado_pending_context: message.payload });
  }
});

// Pont d'auth prod — fix E2. Uniquement depuis les domaines listés dans
// `externally_connectable` (manifest.json) ; `sender.origin` est vérifié en
// plus pour ne jamais accepter un message d'une origine non attendue, même
// si le manifest venait à changer sans que ce fichier soit relu.
const ALLOWED_ORIGINS = ["https://app.zayado.net", "https://zayado.net"];
chrome.runtime.onMessageExternal.addListener((message, sender, sendResponse) => {
  if (!sender || !ALLOWED_ORIGINS.includes(sender.origin)) {
    sendResponse && sendResponse({ ok: false, error: "origin_not_allowed" });
    return;
  }
  if (message && message.type === "zayado_session" && message.token) {
    chrome.storage.local.set({
      zayado_token: message.token,
      zayado_email: message.email || "",
    }).then(() => {
      sendResponse && sendResponse({ ok: true });
    });
    return true; // réponse asynchrone
  }
  if (message && message.type === "zayado_logout") {
    chrome.storage.local.remove(["zayado_token", "zayado_email"]).then(() => {
      sendResponse && sendResponse({ ok: true });
    });
    return true;
  }
  sendResponse && sendResponse({ ok: false, error: "unknown_message" });
});
