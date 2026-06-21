import { useCallback, useEffect, useState } from "react";
import { api } from "@fm/lib/api";

const VAPID_PUBLIC_KEY = process.env.REACT_APP_VAPID_PUBLIC_KEY || "";

function urlBase64ToUint8Array(base64String) {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = atob(base64);
  const out = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; i++) out[i] = rawData.charCodeAt(i);
  return out;
}

/**
 * Hook usePush()
 * ─────────────
 * Gère la souscription Web Push avec VAPID.
 *
 * Retour :
 *   { supported, permission, subscribed, loading, subscribe, unsubscribe, test, prefs, updatePrefs }
 *
 * Usage :
 *   const { subscribed, subscribe, test } = usePush();
 *   <button onClick={subscribe}>Activer</button>
 */
export default function usePush() {
  const [supported, setSupported] = useState(false);
  const [permission, setPermission] = useState("default");
  const [subscribed, setSubscribed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [prefs, setPrefs] = useState({
    wellbeing: true,
    business: true,
    ai_tasks: true,
    reminders: true,
  });

  useEffect(() => {
    const ok =
      "serviceWorker" in navigator &&
      "PushManager" in window &&
      "Notification" in window;
    setSupported(ok);
    if (ok) setPermission(Notification.permission);
  }, []);

  // Récupère l'état de souscription côté serveur
  const refresh = useCallback(async () => {
    try {
      const data = await api.get("/api/push/preferences");
      setSubscribed(!!data.subscribed);
      if (data.preferences) setPrefs(data.preferences);
    } catch {}
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const subscribe = useCallback(async () => {
    if (!supported) throw new Error("Notifications non supportées sur ce navigateur");
    if (!VAPID_PUBLIC_KEY) throw new Error("Clé publique VAPID manquante");
    setLoading(true);
    try {
      const perm = await Notification.requestPermission();
      setPermission(perm);
      if (perm !== "granted") {
        throw new Error("Permission refusée");
      }
      // Service worker doit être enregistré (App.js s'en charge)
      const reg = await navigator.serviceWorker.ready;
      let sub = await reg.pushManager.getSubscription();
      if (!sub) {
        sub = await reg.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY),
        });
      }
      await api.post("/api/push/subscribe", {
        subscription: sub.toJSON(),
        user_agent: navigator.userAgent,
      });
      setSubscribed(true);
      return sub;
    } finally {
      setLoading(false);
    }
  }, [supported]);

  const unsubscribe = useCallback(async () => {
    setLoading(true);
    try {
      if ("serviceWorker" in navigator) {
        const reg = await navigator.serviceWorker.ready;
        const sub = await reg.pushManager.getSubscription();
        if (sub) await sub.unsubscribe();
      }
      await api.post("/api/push/unsubscribe", {});
      setSubscribed(false);
    } finally {
      setLoading(false);
    }
  }, []);

  const test = useCallback(async () => {
    return api.post("/api/push/test", {
      title: "🔔 MyExtension AI",
      body: "Vos notifications fonctionnent — bienvenue !",
      url: "/",
    });
  }, []);

  const updatePrefs = useCallback(async (next) => {
    const data = await api.put("/api/push/preferences", next);
    if (data?.preferences) setPrefs(data.preferences);
    return data;
  }, []);

  return {
    supported,
    permission,
    subscribed,
    loading,
    prefs,
    subscribe,
    unsubscribe,
    test,
    updatePrefs,
    refresh,
  };
}
