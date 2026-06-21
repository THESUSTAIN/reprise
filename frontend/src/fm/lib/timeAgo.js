/** Format a date as relative time in French (il y a X minutes/heures/jours). */
export function timeAgoFR(input) {
  if (!input) return "—";
  const d = new Date(input);
  if (isNaN(d.getTime())) return "—";
  const diff = Math.floor((Date.now() - d.getTime()) / 1000);
  if (diff < 30) return "à l'instant";
  if (diff < 60) return `il y a ${diff}s`;
  if (diff < 3600) {
    const m = Math.floor(diff / 60);
    return `il y a ${m} min`;
  }
  if (diff < 86400) {
    const h = Math.floor(diff / 3600);
    return `il y a ${h} h`;
  }
  if (diff < 86400 * 7) {
    const days = Math.floor(diff / 86400);
    return `il y a ${days} j`;
  }
  if (diff < 86400 * 30) {
    const w = Math.floor(diff / (86400 * 7));
    return `il y a ${w} sem.`;
  }
  if (diff < 86400 * 365) {
    const mo = Math.floor(diff / (86400 * 30));
    return `il y a ${mo} mois`;
  }
  const y = Math.floor(diff / (86400 * 365));
  return `il y a ${y} an${y > 1 ? "s" : ""}`;
}

/** Format full date (DD/MM/YYYY HH:mm). */
export function formatDateTimeFR(input) {
  if (!input) return "—";
  const d = new Date(input);
  if (isNaN(d.getTime())) return "—";
  return d.toLocaleString("fr-FR", {
    day: "2-digit", month: "2-digit", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}
