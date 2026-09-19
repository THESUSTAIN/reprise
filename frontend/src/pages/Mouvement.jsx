import { useEffect, useState } from "react";
import { ArrowRight, Check, Rocket } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { getTaches, updateTacheStatut } from "../lib/api";

// Mouvement — la SEMAINE d'exécution. Volontairement léger (2 cartes) et
// complémentaire d'Aujourd'hui, jamais en doublon :
//   Aujourd'hui = la journée (1 priorité, capture, énergie, impact)
//   Mouvement   = la semaine (tout ce qui est en cours + ce qui a bougé)

const openCopilot = (ask) =>
  window.dispatchEvent(new CustomEvent("cours:open-copilot", { detail: ask ? { ask } : {} }));

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

  const basculer = async (t) => {
    const cible = t.statut === "Terminé" ? "A faire" : "Terminé";
    setTaches((prev) => prev.map((x) => (x.id === t.id ? { ...x, statut: cible } : x)));
    if (cible === "Terminé") toast.success("Bien joué — une action de plus bouclée. L'app la compte pour vous.");
    try { await updateTacheStatut(t.id, cible); }
    catch { setTaches((prev) => prev.map((x) => (x.id === t.id ? t : x))); }
  };

  const enCours = taches.filter((t) => t.statut !== "Terminé");
  const bouclees = taches.filter((t) => t.statut === "Terminé");
  const bouclees7j = bouclees.filter((t) => t.created_at && (Date.now() - new Date(t.created_at).getTime()) < 7 * 86400000).length;

  return (
    <div className="space-y-4" data-testid="page-mouvement">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="eyebrow-chip">Mouvement · Votre semaine</p>
          <h1 className="font-head text-2xl sm:text-3xl font-semibold text-white mt-1">
            Ce qui <em className="gold-text">avance.</em>
          </h1>
          <p className="text-white/55 text-sm mt-1">
            {loading ? "Chargement…" : `${enCours.length} action${enCours.length > 1 ? "s" : ""} en cours · ${bouclees7j} bouclée${bouclees7j > 1 ? "s" : ""} sur 7 jours`}
          </p>
        </div>
        <button onClick={() => openCopilot("Voici ma semaine. Aide-moi à prioriser et à découper ce qui compte.")} data-testid="mouvement-copilote-btn"
          className="inline-flex items-center gap-1.5 rounded-full border border-white/15 bg-white/5 px-4 py-2.5 text-sm font-semibold text-white/85 hover:bg-white/10 transition-colors">
          <Rocket size={15} className="text-[#DEC2A3]" /> Prioriser avec le Copilote
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* En cours */}
        <section className="glass p-6" data-testid="mouvement-en-cours">
          <p className="eyebrow-chip">En cours</p>
          <h2 className="font-head text-lg font-semibold text-white">À faire avancer cette semaine</h2>
          {loading ? (
            <p className="text-[13px] text-white/45 mt-4">Chargement…</p>
          ) : enCours.length > 0 ? (
            <ul className="mt-3 space-y-1.5 list-none p-0">
              {enCours.map((t) => (
                <li key={t.id} className="flex items-center gap-3 rounded-xl border border-white/[.08] bg-white/[.03] px-3.5 py-2.5" data-testid={`mouvement-tache-${t.id}`}>
                  <button onClick={() => basculer(t)} aria-label={`Marquer « ${t.label} » comme terminée`} data-testid={`mouvement-check-${t.id}`}
                    className="w-5 h-5 rounded-full border-[1.5px] border-white/30 grid place-items-center shrink-0 hover:border-[#DEC2A3] transition-colors" />
                  <span className="text-[13.5px] text-white/85">{t.label}</span>
                  {t.priorite === "Haute" && <span className="ml-auto text-[9px] uppercase tracking-[.1em] text-rose-300 font-semibold shrink-0">Prioritaire</span>}
                </li>
              ))}
            </ul>
          ) : (
            <div className="mt-4">
              <p className="text-[13px] text-white/50 leading-relaxed">
                Rien en cours — la semaine est vierge. Les actions se notent depuis Aujourd'hui, en une ligne.
              </p>
              <button onClick={() => navigate("/")} data-testid="mouvement-vers-aujourdhui"
                className="mt-3 inline-flex items-center gap-1.5 rounded-full gold-bg px-4 py-2 text-sm font-semibold">
                Noter une action <ArrowRight size={13} />
              </button>
            </div>
          )}
        </section>

        {/* Ce qui a bougé */}
        <section className="glass p-6" data-testid="mouvement-bouge">
          <p className="eyebrow-chip">Ce qui a bougé</p>
          <h2 className="font-head text-lg font-semibold text-white">La preuve que ça avance</h2>
          {loading ? (
            <p className="text-[13px] text-white/45 mt-4">Chargement…</p>
          ) : bouclees.length > 0 ? (
            <ul className="mt-3 space-y-1.5 list-none p-0">
              {bouclees.slice(0, 8).map((t) => (
                <li key={t.id} className="flex items-center gap-3 rounded-xl border border-white/[.06] bg-white/[.02] px-3.5 py-2.5" data-testid={`mouvement-bouclee-${t.id}`}>
                  <span className="w-5 h-5 rounded-full gold-bg grid place-items-center shrink-0"><Check size={11} /></span>
                  <span className="text-[13.5px] text-white/45 line-through">{t.label}</span>
                  <span className="ml-auto text-[10.5px] text-white/35 shrink-0">
                    {t.created_at ? new Intl.DateTimeFormat("fr-FR", { day: "numeric", month: "short" }).format(new Date(t.created_at)) : ""}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-[13px] text-white/50 leading-relaxed mt-4">
              Rien de bouclé pour l'instant — la première action terminée apparaîtra ici, et elle comptera dans votre impact sur Aujourd'hui.
            </p>
          )}
        </section>
      </div>
    </div>
  );
}
