/**
 * AppContext — fournit les données cockpit aux pages Espace.
 * Chargé depuis GET /api/dashboard/summary au mount.
 * Fallback structurel vide si le backend n'est pas disponible.
 */
import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { getToken } from "@fm/lib/api";

const AppContext = createContext(null);

const BASE = process.env.REACT_APP_BACKEND_URL || "";

// Fallback structurel — aucune donnée hardcodée
const EMPTY_COCKPIT = {
  livrables:  [],
  documents:  [],
  processes:  [],
  summary:    null,
};

export function AppProvider({ children }) {
  const [cockpit,  setCockpit]  = useState(EMPTY_COCKPIT);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState(null);

  const loadCockpit = useCallback(async () => {
    const token = getToken();
    if (!token) { setLoading(false); return; } // non connecté

    try {
      const r = await fetch(`${BASE}/api/dashboard/summary`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!r.ok) throw new Error(`${r.status}`);
      const data = await r.json();

      // Mapper la réponse backend → structure cockpit attendue par les pages
      setCockpit({
        livrables: data.ia_checklist
          ? data.ia_checklist.map((it, i) => ({
              id:       `ia-${i}`,
              title:    it.label,
              status:   it.done ? "done" : "todo",
              type:     "IA",
              duration: data.mission_du_jour?.duration_min || 20,
            }))
          : [],
        documents:  [],   // Documents.jsx utilise documentsApi directement ✅
        processes:  [],   // Processus.jsx utilise son propre API ✅
        summary:    data, // données brutes disponibles pour d'autres composants
      });
      setError(null);
    } catch (e) {
      setError(e.message);
      setCockpit(EMPTY_COCKPIT);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadCockpit(); }, [loadCockpit]);

  const value = { cockpit, setCockpit, loading, error, reload: loadCockpit };
  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) return { cockpit: EMPTY_COCKPIT, setCockpit: () => {}, loading: false, error: null, reload: () => {} };
  return ctx;
}

export default AppContext;
