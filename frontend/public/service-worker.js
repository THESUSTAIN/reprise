/* MyExtension AI — Service Worker (PWA)
   - Cache "app shell" pour un démarrage rapide et un fallback hors-ligne.
   - Gestion des notifications push (Web Push / VAPID) déjà branchées côté backend.
*/
const CACHE = "zayado-pwa-v2";
const SHELL = ["/", "/index.html", "/manifest.json", "/logo-icon.png"];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).catch(() => {}));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
  );
  self.clients.claim();
});

// Network-first pour la navigation (toujours du frais quand en ligne, shell si hors-ligne).
// On ne touche jamais aux appels /api (toujours réseau).
self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;
  const url = new URL(request.url);
  // Ne jamais intercepter des requêtes hors http(s) — ex: chrome-extension://...
  // venant d'une extension tierce installée dans le navigateur (Google Drive,
  // gestionnaire de mots de passe, etc.). On tentait de les fetch/cacher comme
  // les nôtres, et le fallback caches.match() ne trouvait jamais rien pour ces
  // URLs jamais mises en cache → respondWith(undefined) → "Failed to convert
  // value to 'Response'" dans la console, sans rapport avec notre app.
  if (url.protocol !== "http:" && url.protocol !== "https:") return;
  if (url.origin !== self.location.origin) return;
  if (url.pathname.startsWith("/api")) return;
  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request).catch(() => caches.match("/index.html"))
    );
    return;
  }
  // Network-first pour les assets (JS/CSS/images) : on récupère TOUJOURS la version
  // fraîche quand on est en ligne (évite de resservir un ancien bundle en cache après
  // une mise à jour), et on ne retombe sur le cache que hors-ligne.
  event.respondWith(
    fetch(request).then((res) => {
      const copy = res.clone();
      caches.open(CACHE).then((c) => c.put(request, copy)).catch(() => {});
      return res;
    }).catch(() => caches.match(request))
  );
});

// Notifications push
self.addEventListener("push", (event) => {
  let data = {};
  try { data = event.data ? event.data.json() : {}; } catch (e) { data = { body: event.data && event.data.text() }; }
  const title = data.title || "MyExtension AI";
  const options = {
    body: data.body || "",
    icon: "/logo-icon.png",
    badge: "/logo-icon.png",
    data: { url: data.url || "/" },
    tag: data.tag || undefined,
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const target = (event.notification.data && event.notification.data.url) || "/";
  const targetPath = new URL(target, self.location.origin).pathname + new URL(target, self.location.origin).search;
  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then(async (list) => {
      for (const client of list) {
        if ("focus" in client) {
          // Un onglet est déjà ouvert : il faut le NAVIGUER vers la cible avant de le
          // focus, sinon il reste bloqué sur la page déjà affichée (ex: Cockpit "/").
          const clientPath = new URL(client.url).pathname;
          if (clientPath !== targetPath.split("?")[0] && "navigate" in client) {
            try { await client.navigate(target); } catch (e) { /* cross-origin ou non supporté */ }
          }
          return client.focus();
        }
      }
      if (self.clients.openWindow) return self.clients.openWindow(target);
    })
  );
});
