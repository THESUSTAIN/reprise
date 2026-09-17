// Hook autonome pour le module Vision Board Final-main, adapté à Cours-main.
// La langue est lue depuis les préférences locales ; le module reste en français
// par défaut sans dépendre de l’architecture Final-main.
import { useState, useCallback } from "react";

const STR = {
  "board.addNote": { fr: "Idée ajoutée au board", en: "Idea added to board" },
  "board.reset": { fr: "Board réinitialisé", en: "Board reset" },
  "board.promptPlaceholder": { fr: "Décris une idée, l'IA l'ajoute au board…", en: "Describe an idea, AI adds it to the board…" },
  "board.hint": { fr: "Astuce : appuie sur Entrée pour ajouter une note.", en: "Tip: press Enter to add a note." },
  "board.dragHint": { fr: "Glisse les cartes pour les organiser · double-clic pour éditer.", en: "Drag cards to organize · double-click to edit." },
  "board.editImageHint": { fr: "Colle une URL d'image puis Entrée", en: "Paste an image URL then Enter" },
  "board.select": { fr: "Sélection", en: "Select" }, "board.pan": { fr: "Déplacer (main)", en: "Pan (hand)" },
  "board.zoomOut": { fr: "Dézoomer", en: "Zoom out" }, "board.zoomIn": { fr: "Zoomer", en: "Zoom in" },
  "board.fitReset": { fr: "Réinitialiser", en: "Reset" }, "board.fullscreen": { fr: "Plein écran", en: "Fullscreen" },
  "board.exitFullscreen": { fr: "Quitter le plein écran", en: "Exit fullscreen" }, "board.deleted": { fr: "Carte supprimée", en: "Card deleted" },
  "pillars.title": { fr: "Piliers stratégiques", en: "Strategic pillars" }, "pillars.subtitle": { fr: "Les fondations de ta vision et leur avancement.", en: "The foundations of your vision and their progress." },
  "pillars.add": { fr: "Ajouter un pilier", en: "Add a pillar" }, "pillars.objectives": { fr: "Objectifs", en: "Objectives" },
  "book.title": { fr: "Vision Book", en: "Vision Book" }, "book.subtitle": { fr: "Ta vision compilée en un livre inspirant.", en: "Your vision compiled into an inspiring book." },
  "book.exportPdf": { fr: "Exporter en PDF", en: "Export as PDF" }, "templates.title": { fr: "Templates", en: "Templates" },
  "templates.subtitle": { fr: "Des modèles pros à ouvrir directement dans Canva.", en: "Pro templates to open directly in Canva." },
  "notif.title": { fr: "Souvenirs & rappels", en: "Memories & reminders" }, "notif.subtitle": { fr: "Reviens sur tes moments clés et reste motivé.", en: "Revisit your key moments and stay motivated." },
  "notif.highlights": { fr: "À la une", en: "Highlights" }, "notif.settings": { fr: "Paramètres de notification", en: "Notification settings" },
  "common.search": { fr: "Rechercher…", en: "Search…" },
};

export function useApp() {
  let language = "fr";
  try { language = JSON.parse(localStorage.getItem("cours-main-settings-preferences") || "{}").language || "fr"; } catch { /* français par défaut */ }
  const lang = language === "en" ? "en" : "fr";
  const tv = useCallback((obj) => (obj == null ? "" : typeof obj === "string" ? obj : (obj[lang] ?? obj.fr ?? obj.en ?? "")), [lang]);
  const t = useCallback((key) => { const entry = STR[key]; return entry ? (entry[lang] ?? entry.fr) : key; }, [lang]);
  const [extraNotes, setExtraNotes] = useState([]);
  const addNote = useCallback((note) => setExtraNotes((prev) => [...prev, note]), []);
  const removeNote = useCallback((id) => setExtraNotes((prev) => prev.filter((note) => note.id !== id)), []);
  const updateNote = useCallback((id, patch) => setExtraNotes((prev) => prev.map((note) => note.id === id ? { ...note, ...patch } : note)), []);
  const resetNotes = useCallback(() => setExtraNotes([]), []);
  return { t, tv, lang, extraNotes, addNote, removeNote, updateNote, resetNotes };
}
