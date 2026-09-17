// Zayado Copilot — side panel logic.
// Couche IA contextuelle : connexion au compte, capture du contexte de page,
// analyse IA et actions (tâche / opportunité / note / CRM) vers le Business OS.

// Fix E3 (audit) : DEFAULT_API pointait vers l'URL de preview
// (strategy-brain-2.preview.emergentagent.com), retirée de host_permissions
// dans manifest.json — elle aurait cassé silencieusement en prod (host non
// autorisé → tous les fetch() échouent). Pointe maintenant vers le domaine
// prod réel, cohérent avec host_permissions et externally_connectable.
const DEFAULT_API = "https://app.zayado.net";
const $ = (id) => document.getElementById(id);

async function getConfig() {
  const { zayado_api_base, zayado_token, zayado_email } = await chrome.storage.local.get([
    "zayado_api_base", "zayado_token", "zayado_email",
  ]);
  return { apiBase: zayado_api_base || DEFAULT_API, token: zayado_token || "", email: zayado_email || "" };
}

async function api(path, { method = "GET", body, token } = {}) {
  const { apiBase } = await getConfig();
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${apiBase}/api${path}`, {
    method, headers, body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// ── Auth (lien magique) ──────────────────────────────────────────────
// Fix E2 (audit) : en prod, l'API ne renvoie jamais dev_link (comportement
// serveur correct, voir backend/routes/auth.py) — seulement
// `delivered_via_email: true`. Avant, l'UI affichait un message statique
// et ne se remettait JAMAIS à jour automatiquement une fois le lien cliqué
// dans la boîte mail. On écoute désormais chrome.storage : dès que
// background.js reçoit le pont d'auth depuis app.zayado.net (voir
// onMessageExternal), la session apparaît ici sans action supplémentaire.
chrome.storage.onChanged.addListener((changes, area) => {
  if (area === "local" && (changes.zayado_token || changes.zayado_email)) {
    refreshAuthUI();
  }
  if (area === "local" && changes.zayado_pending_context) {
    loadContext();
  }
});

async function refreshAuthUI() {
  const { token, email } = await getConfig();
  if (token) {
    $("authed").classList.remove("hidden");
    $("loginForm").classList.add("hidden");
    $("authedEmail").textContent = email || "Session active";
    connectLiveStream();       // fix E5 : ouvre le flux temps réel dès qu'on est connecté
  } else {
    $("authed").classList.add("hidden");
    $("loginForm").classList.remove("hidden");
    disconnectLiveStream();
  }
}

// ── Cockpit en direct (SSE — fix E5) ─────────────────────────────────
// Le side-panel reflète en direct les changements du cockpit (Business OS)
// via le flux SSE déjà exposé par le backend (/api/vision/events/stream).
// EventSource ne peut pas envoyer de header Authorization → le JWT passe en
// query string (usage standard SSE, cf. backend vision_events.py). À chaque
// event (card_update / tick), on ré-interroge /vision/brain/panel pour
// rafraîchir le score et l'horodatage, avec un petit "flash" visuel.
let _liveSource = null;

function disconnectLiveStream() {
  if (_liveSource) { try { _liveSource.close(); } catch (e) {} _liveSource = null; }
  $("liveCard").classList.add("hidden");
}

async function connectLiveStream() {
  const { apiBase, token } = await getConfig();
  if (!token) return;
  if (_liveSource) return; // déjà connecté
  $("liveCard").classList.remove("hidden");
  await refreshLive(); // premier rendu immédiat
  try {
    const url = `${apiBase}/api/vision/events/stream?token=${encodeURIComponent(token)}`;
    _liveSource = new EventSource(url);
    const onEvt = () => { flashLive(); refreshLive(); };
    _liveSource.addEventListener("card_update", onEvt);
    _liveSource.addEventListener("tick", onEvt);
    _liveSource.onerror = () => {
      // EventSource se reconnecte tout seul ; on signale juste l'état.
      $("liveDot").textContent = "● reconnexion…";
      $("liveDot").style.color = "#fbbf24";
    };
    _liveSource.onopen = () => {
      $("liveDot").textContent = "● live";
      $("liveDot").style.color = "#6ee7b7";
    };
  } catch (e) { /* environnement sans EventSource : silencieux */ }
}

function flashLive() {
  const el = $("liveScore");
  el.style.transition = "none";
  el.style.textShadow = "0 0 14px rgba(201,164,73,.9)";
  setTimeout(() => { el.style.transition = "text-shadow .6s"; el.style.textShadow = "none"; }, 60);
}

async function refreshLive() {
  const { token } = await getConfig();
  if (!token) return;
  try {
    const panel = await api("/vision/brain/panel", { token });
    if (typeof panel.alignment_score === "number") $("liveScore").textContent = panel.alignment_score;
    if (panel.live_analysis && panel.live_analysis.label) $("liveLabel").textContent = panel.live_analysis.label;
    const t = new Date().toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    $("liveUpdated").textContent = "Mis à jour à " + t;
  } catch (e) { /* token expiré / hors-ligne : le prochain tick réessaiera */ }
}

async function login() {
  const email = $("email").value.trim();
  if (!email) return;
  $("authToast").textContent = "Connexion…";
  $("authToast").classList.remove("err");
  try {
    const link = await api("/auth/request-link", { method: "POST", body: { email } });
    if (link.dev_link) {
      // Préproduction uniquement (ALLOW_GUEST_LOGIN=true côté serveur) :
      // on peut consommer le lien directement, pas d'email réel à ouvrir.
      const token = link.dev_link.split("token=")[1];
      const session = await api("/auth/verify-link", { method: "POST", body: { token } });
      const access = session.access_token || session.token;
      if (!access) throw new Error("no token");
      await chrome.storage.local.set({ zayado_token: access, zayado_email: email });
      $("authToast").textContent = "Connecté ✓";
      refreshAuthUI();
    } else {
      // Prod : email réel envoyé. L'utilisateur clique le lien dans sa boîte
      // mail, atterrit sur app.zayado.net, qui transmet la session à
      // l'extension via le pont externally_connectable — refreshAuthUI() se
      // déclenche alors automatiquement via chrome.storage.onChanged.
      $("authToast").textContent = "Lien envoyé par email — cliquez-le, cette fenêtre se mettra à jour automatiquement.";
    }
  } catch (e) {
    $("authToast").textContent = "Échec de connexion. Vérifiez l'email.";
    $("authToast").classList.add("err");
  }
}

async function logout() {
  await chrome.storage.local.remove(["zayado_token"]);
  refreshAuthUI();
}

// ── Contexte de page ────────────────────────────────────────────────
async function loadContext() {
  const pending = (await chrome.storage.local.get("zayado_pending_context")).zayado_pending_context;
  if (pending) {
    await chrome.storage.local.remove("zayado_pending_context");
    applyContext(pending);
    return;
  }
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    let selection = "";
    try {
      const [{ result }] = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: () => (window.getSelection ? String(window.getSelection()) : ""),
      });
      selection = result || "";
    } catch (e) { /* page protégée */ }
    applyContext({ title: tab?.title || "", url: tab?.url || "", selection });
  } catch (e) { /* ignore */ }
}

function applyContext({ title, url, selection, module, subject, sender, time }) {
  // Fix E1/E4 (audit) : content.js envoie désormais un contexte Gmail/Calendar/
  // Outlook ({module, subject, sender, time}) en plus du format historique
  // (capture manuelle par menu contextuel : {title, url, selection}). On
  // normalise les deux formes vers l'affichage existant plutôt que de casser
  // le flux actuel.
  const displayTitle = title || subject || "—";
  const selectionText = selection || (sender ? `De : ${sender}` : "") || (time ? `Horaire : ${time}` : "");
  $("ctxTitle").textContent = displayTitle;
  $("ctxUrl").textContent = url || "";
  $("ctxSelection").value = (selectionText || "").slice(0, 800);
  $("ctxSelection").dataset.url = url || "";
  $("ctxSelection").dataset.title = displayTitle;
  if (module) $("ctxSelection").dataset.module = module;
}

// ── Analyse IA ──────────────────────────────────────────────────────
async function analyze() {
  const { token } = await getConfig();
  if (!token) { $("authToast").textContent = "Connectez-vous d'abord."; return; }
  const el = $("ctxSelection");
  $("analyze").textContent = "Analyse…";
  try {
    const res = await api("/vision/brain/page-context", {
      method: "POST", token,
      body: { title: el.dataset.title || "", url: el.dataset.url || "", selection: el.value || "" },
    });
    $("summary").textContent = res.summary || "";
    $("contact").textContent = res.detected_contact ? `Contact détecté : ${res.detected_contact.email}` : "";
    renderActions(res.actions || []);
    $("result").classList.remove("hidden");
  } catch (e) {
    $("summary").textContent = "Analyse indisponible. Réessayez.";
    $("result").classList.remove("hidden");
  } finally {
    $("analyze").textContent = "✨ Analyser avec l'IA";
  }
}

function renderActions(actions) {
  const box = $("actionBtns");
  box.innerHTML = "";
  const KIND_CAT = { task: "tache", opportunity: "opportunite", note: "idee", lead: "prospect" };
  actions.forEach((a) => {
    const b = document.createElement("button");
    b.className = "btn ghost small";
    b.textContent = a.label;
    b.onclick = () => capture(KIND_CAT[a.kind] || "idee", a.label);
    box.appendChild(b);
  });
}

async function capture(category, label) {
  const { token } = await getConfig();
  const el = $("ctxSelection");
  const content = `[${label}] ${el.dataset.title || ""}\n${el.value || ""}\n${el.dataset.url || ""}`.trim();
  $("captureToast").textContent = "Enregistrement…";
  try {
    await api("/features/captures", { method: "POST", token, body: { content, category, source: "extension" } });
    $("captureToast").textContent = `✓ ${label} créé dans votre cockpit`;
  } catch (e) {
    $("captureToast").textContent = "Échec de l'enregistrement.";
    $("captureToast").classList.add("err");
  }
}

async function openHub() {
  const { apiBase } = await getConfig();
  chrome.tabs.create({ url: `${apiBase}/vision-board` });
}

// ── Init ─────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  $("login").addEventListener("click", login);
  $("logout").addEventListener("click", logout);
  $("analyze").addEventListener("click", analyze);
  $("openHub").addEventListener("click", openHub);
  refreshAuthUI();
  loadContext();
});
