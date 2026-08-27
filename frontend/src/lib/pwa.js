// pwa.js — abonnement Web Push (VAPID), porté depuis final-main.
// Le service worker (public/service-worker.js) gère déjà l'affichage des
// notifications reçues — ce fichier ne gère que l'abonnement du navigateur.
import { api } from "./api";

function getSessionId() {
  const key = "mx_copilot_session_id";
  let sessionId = localStorage.getItem(key);
  if (!sessionId) {
    sessionId = window.crypto?.randomUUID?.() || `local-${Date.now()}-${Math.random().toString(16).slice(2)}`;
    localStorage.setItem(key, sessionId);
  }
  return sessionId;
}

function urlBase64ToUint8Array(base64String) {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const raw = window.atob(base64);
  const arr = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) arr[i] = raw.charCodeAt(i);
  return arr;
}

export async function isPushSubscribed() {
  if (!("serviceWorker" in navigator) || !("PushManager" in window)) return false;
  const reg = await navigator.serviceWorker.ready.catch(() => null);
  if (!reg) return false;
  const sub = await reg.pushManager.getSubscription();
  return !!sub;
}

export async function subscribeToPush() {
  if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
    return { ok: false, error: "Notifications non supportées par ce navigateur." };
  }
  const permission = await Notification.requestPermission();
  if (permission !== "granted") return { ok: false, error: "Permission refusée." };

  const reg = await navigator.serviceWorker.ready;
  let key;
  try {
    key = (await api.get("/push/public-key")).data.public_key;
  } catch {
    return { ok: false, error: "Clé VAPID indisponible." };
  }
  if (!key) return { ok: false, error: "Clé VAPID indisponible." };

  const sub = await reg.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array(key),
  });
  await api.post("/push/subscribe", { ...sub.toJSON(), session_id: getSessionId() });
  return { ok: true };
}

export async function unsubscribeFromPush() {
  const reg = await navigator.serviceWorker.ready.catch(() => null);
  const sub = await reg?.pushManager.getSubscription();
  if (sub) await sub.unsubscribe().catch(() => {});
  await api.post(`/push/unsubscribe?session_id=${encodeURIComponent(getSessionId())}`).catch(() => {});
  return { ok: true };
}

export async function sendTestPush() {
  return api.post(`/push/test?session_id=${encodeURIComponent(getSessionId())}`).then((r) => r.data);
}
