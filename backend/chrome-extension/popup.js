// Popup — capture rapide d'un prospect vers MyExtension AI (app.zayado.net).
const APP_URL = "https://app.zayado.net";

async function currentTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

// Pré-remplit avec le titre + l'URL + la sélection de la page courante.
(async function init() {
  const tab = await currentTab();
  document.getElementById("url").value = (tab && tab.url) || "";
  document.getElementById("name").value = (tab && tab.title) || "";
  try {
    const [{ result }] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => (window.getSelection ? String(window.getSelection()) : ""),
    });
    if (result) document.getElementById("note").value = result.slice(0, 500);
  } catch (e) { /* page protégée : on ignore */ }
})();

// "Ouvrir l'app" : ouvre la page Croissance avec les champs pré-remplis en query.
document.getElementById("open").addEventListener("click", async () => {
  const name = encodeURIComponent(document.getElementById("name").value || "");
  const url = encodeURIComponent(document.getElementById("url").value || "");
  chrome.tabs.create({ url: `${APP_URL}/croissance?capture_name=${name}&capture_url=${url}` });
});

// "Ajouter au CRM" : stocke localement la capture (file d'attente) puis ouvre l'app
// sur Croissance pour la valider. (L'app lit la file au chargement.)
document.getElementById("send").addEventListener("click", async () => {
  const lead = {
    name: document.getElementById("name").value || "",
    note: document.getElementById("note").value || "",
    url: document.getElementById("url").value || "",
    captured_at: new Date().toISOString(),
  };
  const { zayado_captures = [] } = await chrome.storage.local.get("zayado_captures");
  zayado_captures.push(lead);
  await chrome.storage.local.set({ zayado_captures });
  const name = encodeURIComponent(lead.name);
  const url = encodeURIComponent(lead.url);
  const note = encodeURIComponent(lead.note);
  chrome.tabs.create({ url: `${APP_URL}/croissance?capture_name=${name}&capture_url=${url}&capture_note=${note}` });
  window.close();
});
