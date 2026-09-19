import { useEffect, useState } from "react";
import { ArrowLeft, ArrowRight, Check, Rocket } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { getTaches, updateTacheStatut } from "../lib/api";

// Mouvement — tableau d'avancement de la semaine (validé le 19/09).
// Rôle distinct d'Aujourd'hui : Aujourd'hui = LE jour (1 priorité, capture,
// énergie) ; Mouvement = faire AVANCER chaque action d'une colonne à l'autre.
// Les statuts sont réels (« A faire » → « En cours » → « Terminé ») et
// persistés via PUT /tasks/{id}/status.

const openCopilot = (ask) =>
  window.dispatchEvent(new CustomEvent("cours:open-copilot", { detail: ask ? { ask } : {} }));

const COLONNES = [
  { id: "afaire", label: "À faire", statut: "A faire", vide: "Rien en attente — capturez depuis Aujourd'hui." },
  { id: "encours", label: "En cours", statut: "En cours", vide: "Rien en cours — faites avancer une action d'un cran." },
  { id: "termine", label: "Terminé", statut: "Terminé", vide: "Rien de bouclé pour l'instant — la première comptera dans votre impact." },
];
const ORDRE = ["A faire", "En cours", "Terminé"];

export default function Mouvement() {
  const navigate = useNavigate();
  const [taches, setTaches] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getTaches()
      .then((t) => setTaches(Array.isArray(t) ? t : []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const deplacer = async (t, sens) => {
    const index = ORDRE.indexOf(t.statut);
    const cible = ORDRE[Math.min(ORDRE.length - 1, Math.max(0, index + sens))];
    if (cible === t.statut) return;
    const avant = t.statut;
    setTaches((prev) => prev.map((x) => (x.id === t.id ? { ...x, statut: cible } : x)));
    if (cible === "Terminé") toast.success("Bien joué — une action de plus bouclée. L'app la compte pour vous.");
    try { await updateTacheStatut(t.id, cible); }
    catch { setTaches((prev) => prev.map((x) => (x.id === t.id ? { ...x, statut: avant } : x))); }
  };

  const total = taches.length;
  const terminees = taches.filter((t) => t.statut === "Terminé").length;
  const progression = total ? Math.round((terminees / total) * 100) : 0;

  return (
    <div className="space-y-4" data-testid="page-mouvement">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="eyebrow-chip">Mouvement · Votre semaine</p>
          <h1 className="font-head text-2xl sm:text-3xl font-semibold text-white mt-1">
            Ce qui <em className="gold-text">avance.</em>
          </h1>
          <p className="text-white/55 text-sm mt-1">
            {loading ? "Chargement…" : total ? `${terminees}/${total} actions bouclées · ${progression}% du tableau` : "Votre tableau est vierge — il se remplit depuis Aujourd'hui."}
          </p>
        </div>
        <button onClick={() => openCopilot("Voici mon tableau d'avancement. Aide-moi à prioriser et à découper ce qui compte.")} data-testid="mouvement-copilote-btn"
          className="inline-flex items-center gap-1.5 rounded-full border border-white/15 bg-white/5 px-4 py-2.5 text-sm font-semibold text-white/85 hover:bg-white/10 transition-colors">
          <Rocket size={15} className="text-[#DEC2A3]" /> Prioriser avec le Copilote
        </button>
      </div>

      {/* Barre de progression du tableau */}
      {total > 0 && (
        <div className="h-1.5 rounded-full bg-white/10 overflow-hidden" data-testid="mouvement-progression">
          <div className="h-full rounded-full bg-gradient-to-r from-[#F1E2CC] to-[#DEC2A3] transition-all duration-500" style={{ width: `${progression}%` }} />
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {COLONNES.map((col, colIndex) => {
          const cartes = taches.filter((t) => t.statut === col.statut);
          return (
            <section key={col.id} className="glass p-5" data-testid={`mouvement-col-${col.id}`}>
              <div className="flex items-baseline justify-between">
                <p className="eyebrow-chip" style={{ marginBottom: 6 }}>{col.label}</p>
                <span className="font-head text-sm font-semibold text-white/50" data-testid={`mouvement-count-${col.id}`}>{cartes.length}</span>
              </div>
              {loading ? (
                <p className="text-[12.5px] text-white/45 mt-3">Chargement…</p>
              ) : cartes.length > 0 ? (
                <ul className="mt-2 space-y-2 list-none p-0">
                  {cartes.map((t) => (
                    <li key={t.id} className="rounded-2xl border border-white/[.10] bg-white/[.04] px-3.5 py-3" data-testid={`mouvement-tache-${t.id}`}>
                      <div className="flex items-start gap-2.5">
                        {col.statut === "Terminé" && <span className="w-5 h-5 rounded-full gold-bg grid place-items-center shrink-0 mt-0.5"><Check size={11} /></span>}
                        <span className={`text-[13.5px] leading-snug ${col.statut === "Terminé" ? "text-white/45 line-through" : "text-white/88"}`}>{t.label}</span>
                      </div>
                      <div className="flex items-center gap-2 mt-2.5">
                        {t.priorite === "Haute" && <span className="text-[9px] uppercase tracking-[.1em] text-rose-300 font-semibold">Prioritaire</span>}
                        <span className="ml-auto flex gap-1.5">
                          {colIndex > 0 && (
                            <button onClick={() => deplacer(t, -1)} aria-label={`Reculer « ${t.label} »`} data-testid={`mouvement-recule-${t.id}`}
                              className="w-7 h-7 rounded-full border border-white/15 bg-white/5 grid place-items-center text-white/60 hover:text-white hover:border-white/30 transition-colors">
                              <ArrowLeft size={13} />
                            </button>
                          )}
                          {colIndex < COLONNES.length - 1 && (
                            <button onClick={() => deplacer(t, 1)} aria-label={`Faire avancer « ${t.label} »`} data-testid={`mouvement-avance-${t.id}`}
                              className="w-7 h-7 rounded-full gold-bg grid place-items-center transition-transform hover:scale-105">
                              <ArrowRight size={13} />
                            </button>
                          )}
                        </span>
                      </div>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-[12.5px] text-white/45 leading-relaxed mt-3">{col.vide}</p>
              )}
              {col.id === "afaire" && !loading && cartes.length === 0 && (
                <button onClick={() => navigate("/")} data-testid="mouvement-vers-aujourdhui"
                  className="mt-3 inline-flex items-center gap-1.5 rounded-full gold-bg px-4 py-2 text-sm font-semibold">
                  Noter une action <ArrowRight size={13} />
                </button>
              )}
            </section>
          );
        })}
      </div>
    </div>
  );
}
