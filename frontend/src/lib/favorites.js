/* Helpers favoris (wishlist) — stockage localStorage `zay_favorites` (array de slugs)
   + synchronisation API pour persistance multi-appareil.
   Émet l'event `zayado:favorites-updated` pour mise à jour réactive des badges. */
// Import statique — api.js est déjà chargé statiquement par 40+ autres modules
// (App.jsx, AuthContext.jsx, etc.), donc le charger dynamiquement ici n'évitait
// aucun poids réel et créait un mélange statique/dynamique instable pour Rollup.
import api from "@/lib/api";

const KEY = "zay_favorites";

export function getFavorites() {
  try { return JSON.parse(localStorage.getItem(KEY) || "[]"); } catch { return []; }
}

export function isFavorite(slug) {
  return getFavorites().includes(slug);
}

// Synchroniser les favoris depuis l'API au démarrage
export async function syncFavoritesFromAPI() {
  try {
    const r = await api.get("/account/favorites");
    if (r.data && Array.isArray(r.data)) {
      localStorage.setItem(KEY, JSON.stringify(r.data));
      window.dispatchEvent(new CustomEvent("zayado:favorites-updated", { detail: { count: r.data.length } }));
    }
  } catch {
    // Pas connecté ou API indisponible — garder localStorage
  }
}

export function toggleFavorite(slug) {
  const list = getFavorites();
  const idx = list.indexOf(slug);
  if (idx >= 0) list.splice(idx, 1); else list.push(slug);
  localStorage.setItem(KEY, JSON.stringify(list));
  window.dispatchEvent(new CustomEvent("zayado:favorites-updated", { detail: { count: list.length, slug, added: idx < 0 } }));

  // Persister côté API (best-effort)
  if (idx < 0) {
    api.post("/account/favorites", { slug }).catch(() => {});
  } else {
    api.delete(`/account/favorites/${slug}`).catch(() => {});
  }

  return idx < 0; // true si ajouté
}

export function removeFavorite(slug) {
  const list = getFavorites().filter((s) => s !== slug);
  localStorage.setItem(KEY, JSON.stringify(list));
  window.dispatchEvent(new CustomEvent("zayado:favorites-updated", { detail: { count: list.length, slug, added: false } }));
  api.delete(`/account/favorites/${slug}`).catch(() => {});
}

export function clearFavorites() {
  localStorage.setItem(KEY, "[]");
  window.dispatchEvent(new CustomEvent("zayado:favorites-updated", { detail: { count: 0 } }));
  api.delete("/account/favorites").catch(() => {});
}
