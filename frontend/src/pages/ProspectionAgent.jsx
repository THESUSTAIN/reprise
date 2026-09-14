/* Agent Prospection — écran de pilotage.
 *
 * Trois moments, dans cet ordre, parce que c'est l'ordre dans lequel on
 * réfléchit : QUI je cherche (le profil client idéal), OÙ je cherche (les
 * sources et ce qui leur manque), puis CE QUE j'ai trouvé.
 *
 * Deux partis pris assumés :
 *  — Une source non configurée le dit AVANT le scan. Rien n'est plus décourageant
 *    qu'un scan qui rend zéro résultat sans expliquer pourquoi.
 *  — Le score est toujours accompagné de ses raisons. Un chiffre seul produit
 *    soit une confiance aveugle, soit un rejet en bloc — jamais un arbitrage.
 */
import { useEffect, useState, useCallback } from "react";
import {
  Radar, Search, Loader2, Building2, MapPin, MessageSquare, Sparkles,
  ChevronDown, ChevronRight, Copy, Check, ShieldAlert, ExternalLink,
  Info, RefreshCw, Save,
} from "lucide-react";
import { toast } from "sonner";
import {
  getIcp, saveIcp, getProspectionSources, runProspectionScan,
  getProspectionRuns, draftApproach, getGdprNotice,
} from "../lib/api";

const ICONE_SOURCE = { entreprises: Building2, commerces: MapPin, intentions: MessageSquare };

function Champ({ label, aide, children }) {
  return (
    <label className="block">
      <span className="text-xs font-semibold text-white/70">{label}</span>
      {aide && <span className="mt-0.5 block text-[11px] leading-snug text-white/40">{aide}</span>}
      <div className="mt-1.5">{children}</div>
    </label>
  );
}

const styleSaisie =
  "w-full rounded-xl border border-white/15 bg-white/5 px-3 py-2 text-sm text-white " +
  "placeholder:text-white/30 focus:border-[#DEC2A3]/60 focus:outline-none";

function couleurScore(score) {
  if (score >= 70) return "#5DCAA5";
  if (score >= 45) return "#DEC2A3";
  return "#8A94A6";
}

/* ── Fiche d'un prospect ─────────────────────────────────────── */
function CarteProspect({ lead, onBrouillon, brouillon, redactionEnCours }) {
  const [ouvert, setOuvert] = useState(false);
  const [copie, setCopie] = useState(false);
  const fiche = lead.fiche || {};
  const signaux = Array.isArray(fiche.signaux) ? fiche.signaux : [];

  const copier = async () => {
    const texte = [brouillon?.objet ? `Objet : ${brouillon.objet}` : "", brouillon?.message || ""]
      .filter(Boolean).join("\n\n");
    try {
      await navigator.clipboard.writeText(texte);
      setCopie(true);
      setTimeout(() => setCopie(false), 2000);
    } catch {
      toast.error("Copie impossible depuis ce navigateur.");
    }
  };

  return (
    <article className="glass overflow-hidden" data-testid={`prospect-${lead.id}`}>
      <button type="button" onClick={() => setOuvert((v) => !v)}
        className="flex w-full items-start gap-3 p-4 text-left hover:bg-white/[0.03]">
        <span className="flex h-11 w-11 shrink-0 flex-col items-center justify-center rounded-xl border"
          style={{ borderColor: `${couleurScore(lead.score)}55`, background: `${couleurScore(lead.score)}18`, color: couleurScore(lead.score) }}>
          <span className="font-head text-sm font-bold leading-none">{lead.score}</span>
          <span className="mt-0.5 text-[8px] uppercase tracking-wide opacity-70">score</span>
        </span>

        <div className="min-w-0 flex-1">
          <p className="m-0 truncate text-sm font-semibold text-white">{lead.name}</p>
          <p className="m-0 mt-0.5 line-clamp-2 text-[12px] leading-relaxed text-white/50">{lead.snippet}</p>
          <div className="mt-2 flex flex-wrap items-center gap-1.5">
            <span className="rounded-full bg-white/8 px-2 py-0.5 text-[10px] font-medium text-white/60">{lead.source}</span>
            {lead.email && (
              <span className="rounded-full bg-white/8 px-2 py-0.5 text-[10px] font-medium text-white/60">{lead.email}</span>
            )}
            {lead.telephone && (
              <span className="rounded-full bg-white/8 px-2 py-0.5 text-[10px] font-medium text-white/60">{lead.telephone}</span>
            )}
            {lead.email_nominatif && (
              <span className="inline-flex items-center gap-1 rounded-full bg-amber-400/15 px-2 py-0.5 text-[10px] font-semibold text-amber-200">
                <ShieldAlert size={10} /> adresse nominative
              </span>
            )}
          </div>
        </div>
        <span className="mt-1 shrink-0 text-white/30">{ouvert ? <ChevronDown size={16} /> : <ChevronRight size={16} />}</span>
      </button>

      {ouvert && (
        <div className="border-t border-white/10 px-4 pb-4 pt-3 space-y-3">
          <div>
            <p className="m-0 text-[11px] font-semibold uppercase tracking-wide text-white/45">Pourquoi ce score</p>
            <ul className="mt-1.5 space-y-1 pl-0 list-none">
              {(lead.score_raisons || []).map((raison) => (
                <li key={raison} className="flex gap-2 text-[12.5px] leading-relaxed text-white/65">
                  <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-[#DEC2A3]" />{raison}
                </li>
              ))}
              {!(lead.score_raisons || []).length && (
                <li className="text-[12.5px] text-white/40">Aucun élément différenciant relevé.</li>
              )}
            </ul>
          </div>

          {(fiche.activite || signaux.length > 0) && (
            <div className="rounded-xl border border-white/10 bg-white/[0.03] p-3">
              <p className="m-0 text-[11px] font-semibold uppercase tracking-wide text-white/45">Lu sur son site</p>
              {fiche.activite && <p className="m-0 mt-1.5 text-[12.5px] leading-relaxed text-white/70">{fiche.activite}</p>}
              {signaux.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {signaux.map((s) => (
                    <span key={String(s)} className="rounded-full bg-[#DEC2A3]/12 px-2 py-0.5 text-[10.5px] text-[#F0DCA5]">{String(s)}</span>
                  ))}
                </div>
              )}
              {fiche._url_lue && (
                <a href={fiche._url_lue} target="_blank" rel="noreferrer noopener"
                  className="mt-2.5 inline-flex items-center gap-1 text-[11.5px] font-semibold text-[#DEC2A3] hover:text-[#FFD700]">
                  Voir la page lue <ExternalLink size={11} />
                </a>
              )}
            </div>
          )}

          {!fiche.activite && (
            <p className="m-0 rounded-xl border border-dashed border-white/12 px-3 py-2.5 text-[12px] leading-relaxed text-white/45">
              Pas de fiche enrichie : aucun site connu, site inaccessible, ou lecture refusée par le
              robots.txt du domaine. Le prospect reste utilisable, avec moins de contexte.
            </p>
          )}

          <div className="flex flex-wrap gap-2">
            {["email", "linkedin", "telephone"].map((canal) => (
              <button key={canal} onClick={() => onBrouillon(lead, canal)} disabled={redactionEnCours}
                data-testid={`brouillon-${canal}-${lead.id}`}
                className="inline-flex items-center gap-1.5 rounded-xl border border-[#DEC2A3]/35 bg-[#DEC2A3]/12 px-3 py-1.5 text-xs font-semibold text-[#F0DCA5] hover:bg-[#DEC2A3]/22 disabled:opacity-50">
                {redactionEnCours ? <Loader2 size={12} className="animate-spin" /> : <Sparkles size={12} />}
                Rédiger un {canal === "telephone" ? "script téléphone" : canal === "linkedin" ? "message LinkedIn" : "email"}
              </button>
            ))}
          </div>

          {brouillon && (
            <div className="rounded-xl border border-[#DEC2A3]/25 bg-[#0A1128]/50 p-3" data-testid={`brouillon-resultat-${lead.id}`}>
              <div className="mb-2 flex items-center justify-between gap-2">
                <span className="text-[10px] font-bold uppercase tracking-wide text-[#E8C96A]">Brouillon — non envoyé</span>
                <button onClick={copier} className="inline-flex items-center gap-1 text-[11px] font-semibold text-[#E8C96A] hover:text-white">
                  {copie ? <Check size={11} /> : <Copy size={11} />} {copie ? "Copié" : "Copier"}
                </button>
              </div>
              {brouillon.objet && <p className="m-0 mb-1.5 text-[12.5px] font-semibold text-white">Objet : {brouillon.objet}</p>}
              <p className="m-0 whitespace-pre-wrap text-[12.5px] leading-relaxed text-white/85">{brouillon.message}</p>
              {brouillon.pourquoi && (
                <p className="m-0 mt-2 text-[11.5px] italic text-white/45">{brouillon.pourquoi}</p>
              )}
              <p className="m-0 mt-2.5 flex gap-1.5 text-[11px] leading-relaxed text-amber-200/80">
                <Info size={12} className="mt-0.5 shrink-0" />{brouillon.avertissement}
              </p>
              {brouillon.rappel_rgpd && (
                <p className="m-0 mt-1.5 flex gap-1.5 text-[11px] leading-relaxed text-amber-200/80">
                  <ShieldAlert size={12} className="mt-0.5 shrink-0" />{brouillon.rappel_rgpd}
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </article>
  );
}

/* ── Écran ───────────────────────────────────────────────────── */
export default function ProspectionAgent() {
  const [icp, setIcp] = useState(null);
  const [sources, setSources] = useState(null);
  const [selection, setSelection] = useState(["entreprises"]);
  const [scanEnCours, setScanEnCours] = useState(false);
  const [resultat, setResultat] = useState(null);
  const [enregistrement, setEnregistrement] = useState(false);
  const [brouillons, setBrouillons] = useState({});
  const [redactionPour, setRedactionPour] = useState(null);
  const [mention, setMention] = useState(null);
  const [runs, setRuns] = useState([]);
  const [erreur, setErreur] = useState("");

  const charger = useCallback(async () => {
    setErreur("");
    try {
      const [profil, etat, historique] = await Promise.all([
        getIcp(),
        getProspectionSources(),
        getProspectionRuns().catch(() => ({ entrees: [] })),
      ]);
      setIcp(profil);
      setSources(etat);
      setRuns(historique?.entrees || []);
    } catch {
      setErreur("Impossible de charger l'agent. Vérifiez votre connexion, puis réessayez.");
    }
  }, []);

  useEffect(() => { charger(); }, [charger]);

  const majIcp = (cle, valeur) => setIcp((precedent) => ({ ...precedent, [cle]: valeur }));

  const enregistrerIcp = async () => {
    setEnregistrement(true);
    try {
      const enregistre = await saveIcp(icp);
      setIcp(enregistre);
      setSources(await getProspectionSources());
      toast.success("Profil enregistré.");
    } catch {
      toast.error("Enregistrement impossible pour l'instant.");
    } finally {
      setEnregistrement(false);
    }
  };

  const lancerScan = async () => {
    if (!selection.length) {
      toast.error("Sélectionnez au moins une source.");
      return;
    }
    setScanEnCours(true);
    setResultat(null);
    try {
      // Le profil est enregistré avant le scan : sinon l'agent chercherait
      // avec l'ancien profil pendant que l'écran affiche le nouveau.
      await saveIcp(icp);
      const reponse = await runProspectionScan({ sources: selection, limite: 15, enrichir: true });
      setResultat(reponse);
      setRuns((await getProspectionRuns().catch(() => ({ entrees: [] })))?.entrees || []);
      if (reponse.nouveaux) toast.success(`${reponse.nouveaux} nouveau(x) prospect(s) ajouté(s) au pipeline.`);
    } catch (e) {
      const detail = e?.response?.data?.detail;
      toast.error(detail || "Le scan n'a pas abouti. Réessayez dans un instant.");
    } finally {
      setScanEnCours(false);
    }
  };

  const rediger = async (lead, canal) => {
    setRedactionPour(lead.id);
    try {
      const texte = await draftApproach({ lead_id: lead.id, canal });
      setBrouillons((precedent) => ({ ...precedent, [lead.id]: texte }));
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Rédaction impossible pour l'instant.");
    } finally {
      setRedactionPour(null);
    }
  };

  const afficherMention = async () => {
    try {
      setMention(await getGdprNotice());
    } catch {
      toast.error("Texte indisponible pour l'instant.");
    }
  };

  if (erreur) {
    return (
      <section className="glass p-6" data-testid="prospection-erreur">
        <p className="m-0 text-sm text-white/75">{erreur}</p>
        <button onClick={charger} className="mt-3 inline-flex items-center gap-1.5 rounded-xl border border-white/20 px-3 py-1.5 text-xs font-semibold text-white/80 hover:bg-white/5">
          <RefreshCw size={13} /> Réessayer
        </button>
      </section>
    );
  }

  if (!icp || !sources) {
    return (
      <section className="glass flex items-center justify-center gap-2 p-10 text-sm text-white/50" data-testid="prospection-chargement">
        <Loader2 size={16} className="animate-spin" /> Chargement de l'agent…
      </section>
    );
  }

  const listeSources = sources.sources || [];
  const aucunePrete = listeSources.every((s) => !s.pret);

  return (
    <section className="space-y-5" data-testid="page-prospection">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[.14em] text-[#DEC2A3]">Agent Prospection</p>
          <h1 className="mt-1 font-head text-2xl font-semibold text-white">Il cherche, lit et prépare. Vous décidez.</h1>
          <p className="mt-1 max-w-2xl text-sm leading-relaxed text-white/55">
            L'agent interroge des sources publiques, lit le site de chaque prospect et vous rend une
            fiche avec un score justifié. Aucun message n'est envoyé sans votre relecture.
          </p>
        </div>
        <span className="rounded-full border border-white/15 bg-white/5 px-3 py-1.5 text-[11px] text-white/55">
          Enrichissement : {sources.enrichissement?.moteur}
        </span>
      </header>

      {/* ── 1. QUI ─────────────────────────────────────────────── */}
      <div className="glass p-5">
        <h2 className="font-head text-base font-semibold text-white">1 · Qui cherchez-vous ?</h2>
        <p className="mt-1 text-[12.5px] leading-relaxed text-white/50">
          Plus ce profil est précis, moins l'agent vous rapporte de bruit. C'est le seul réglage
          qui change vraiment la qualité des résultats.
        </p>

        <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
          <Champ label="Ce que vous vendez" aide="Une phrase, comme vous le diriez à quelqu'un.">
            <input className={styleSaisie} data-testid="icp-offre" value={icp.offre || ""}
              onChange={(e) => majIcp("offre", e.target.value)}
              placeholder="Ex : je refais les sites vitrines des artisans" />
          </Champ>
          <Champ label="Le problème que ça règle" aide="Ce qui coince chez le client avant vous.">
            <input className={styleSaisie} data-testid="icp-probleme" value={icp.probleme_resolu || ""}
              onChange={(e) => majIcp("probleme_resolu", e.target.value)}
              placeholder="Ex : ils sont invisibles sur Google" />
          </Champ>
          <Champ label="Secteur visé">
            <input className={styleSaisie} data-testid="icp-secteur" value={icp.secteur || ""}
              onChange={(e) => majIcp("secteur", e.target.value)} placeholder="Ex : plomberie, cabinet comptable" />
          </Champ>
          <Champ label="Code NAF (facultatif)" aide="Affine la recherche dans le registre des entreprises.">
            <input className={styleSaisie} data-testid="icp-naf" value={icp.code_naf || ""}
              onChange={(e) => majIcp("code_naf", e.target.value)} placeholder="Ex : 43.22A" />
          </Champ>
          <Champ label="Département" aide="Deux chiffres.">
            <input className={styleSaisie} data-testid="icp-departement" value={icp.departement || ""}
              onChange={(e) => majIcp("departement", e.target.value)} placeholder="Ex : 44" />
          </Champ>
          <Champ label="Ville" aide="Nécessaire pour les commerces locaux.">
            <input className={styleSaisie} data-testid="icp-ville" value={icp.ville || ""}
              onChange={(e) => majIcp("ville", e.target.value)} placeholder="Ex : Nantes" />
          </Champ>
          <Champ label="Type de commerce" aide="Ce que vous taperiez dans une carte.">
            <input className={styleSaisie} data-testid="icp-commerce" value={icp.type_commerce || ""}
              onChange={(e) => majIcp("type_commerce", e.target.value)} placeholder="Ex : boulangerie" />
          </Champ>
          <Champ label="Mots-clés d'intention" aide="Séparés par des virgules. Ce que quelqu'un écrirait en cherchant votre service.">
            <input className={styleSaisie} data-testid="icp-intentions"
              value={Array.isArray(icp.mots_cles_intention) ? icp.mots_cles_intention.join(", ") : (icp.mots_cles_intention || "")}
              onChange={(e) => majIcp("mots_cles_intention", e.target.value.split(",").map((v) => v.trim()).filter(Boolean))}
              placeholder="Ex : cherche un site web, besoin d'un comptable" />
          </Champ>
          <Champ label="Signaux qui vous intéressent" aide="Séparés par des virgules.">
            <input className={styleSaisie} data-testid="icp-signaux"
              value={Array.isArray(icp.signaux_positifs) ? icp.signaux_positifs.join(", ") : (icp.signaux_positifs || "")}
              onChange={(e) => majIcp("signaux_positifs", e.target.value.split(",").map((v) => v.trim()).filter(Boolean))}
              placeholder="Ex : recrute, vient d'ouvrir" />
          </Champ>
          <Champ label="Signaux qui vous font passer votre chemin" aide="Séparés par des virgules.">
            <input className={styleSaisie} data-testid="icp-exclusions"
              value={Array.isArray(icp.signaux_redhibitoires) ? icp.signaux_redhibitoires.join(", ") : (icp.signaux_redhibitoires || "")}
              onChange={(e) => majIcp("signaux_redhibitoires", e.target.value.split(",").map((v) => v.trim()).filter(Boolean))}
              placeholder="Ex : franchise, fermé définitivement" />
          </Champ>
        </div>

        <button onClick={enregistrerIcp} disabled={enregistrement} data-testid="icp-enregistrer"
          className="mt-4 inline-flex items-center gap-1.5 rounded-xl border border-white/20 px-3.5 py-2 text-xs font-semibold text-white/80 hover:bg-white/5 disabled:opacity-50">
          {enregistrement ? <Loader2 size={13} className="animate-spin" /> : <Save size={13} />} Enregistrer le profil
        </button>
      </div>

      {/* ── 2. OÙ ──────────────────────────────────────────────── */}
      <div className="glass p-5">
        <h2 className="font-head text-base font-semibold text-white">2 · Où doit-il chercher ?</h2>
        <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-3">
          {listeSources.map((source) => {
            const Icone = ICONE_SOURCE[source.id] || Radar;
            const active = selection.includes(source.id);
            return (
              <button key={source.id} type="button" data-testid={`source-${source.id}`}
                onClick={() => setSelection((liste) => liste.includes(source.id)
                  ? liste.filter((s) => s !== source.id) : [...liste, source.id])}
                className={`rounded-xl border p-4 text-left transition-colors ${
                  active ? "border-[#DEC2A3]/50 bg-[#DEC2A3]/10" : "border-white/12 bg-white/[0.03] hover:border-white/25"}`}>
                <div className="flex items-center gap-2">
                  <Icone size={15} className={active ? "text-[#DEC2A3]" : "text-white/45"} />
                  <span className="text-sm font-semibold text-white">{source.label}</span>
                </div>
                <p className="m-0 mt-1.5 text-[12px] leading-relaxed text-white/50">{source.detail}</p>
                {source.pret ? (
                  <p className="m-0 mt-2 text-[11px] font-semibold text-emerald-300">Prête</p>
                ) : (
                  <p className="m-0 mt-2 text-[11px] leading-relaxed text-amber-200/85">{source.manque}</p>
                )}
              </button>
            );
          })}
        </div>

        {aucunePrete && (
          <p className="m-0 mt-3 rounded-xl border border-amber-400/30 bg-amber-400/10 px-3 py-2.5 text-[12.5px] leading-relaxed text-amber-100">
            Aucune source n'est prête. Complétez au minimum un secteur ou un code NAF ci-dessus,
            puis enregistrez le profil.
          </p>
        )}

        <div className="mt-4 flex flex-wrap items-center gap-3">
          <button onClick={lancerScan} disabled={scanEnCours || !selection.length} data-testid="lancer-scan"
            className="inline-flex items-center gap-2 rounded-xl bg-[#DEC2A3] px-4 py-2.5 text-sm font-bold text-[#0A1128] disabled:opacity-50">
            {scanEnCours ? <Loader2 size={15} className="animate-spin" /> : <Search size={15} />}
            {scanEnCours ? "Recherche en cours…" : "Lancer un scan"}
          </button>
          {scanEnCours && (
            <span className="text-[12px] text-white/45">
              L'agent lit de vrais sites : comptez une à deux minutes.
            </span>
          )}
        </div>
      </div>

      {/* ── 3. RÉSULTATS ───────────────────────────────────────── */}
      {resultat && (
        <div className="space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h2 className="m-0 font-head text-base font-semibold text-white">
              3 · {resultat.nouveaux} nouveau(x) prospect(s)
              <span className="ml-2 text-[12px] font-normal text-white/45">
                sur {resultat.examines} examiné(s) · les doublons sont écartés
              </span>
            </h2>
            <button onClick={afficherMention} className="text-[11.5px] font-semibold text-[#DEC2A3] hover:text-[#FFD700]">
              Texte d'information RGPD à joindre
            </button>
          </div>

          {resultat.journal?.length > 0 && (
            <p className="m-0 text-[11.5px] text-white/40">{resultat.journal.join(" · ")}</p>
          )}

          {mention && (
            <div className="rounded-xl border border-white/15 bg-white/[0.04] p-4" data-testid="mention-rgpd">
              <p className="m-0 text-[12.5px] leading-relaxed text-white/75">{mention.texte}</p>
              <p className="m-0 mt-2 text-[11.5px] text-white/45">{mention.rappel}</p>
            </div>
          )}

          {resultat.leads?.length > 0 ? (
            <div className="space-y-2.5">
              {resultat.leads.map((lead) => (
                <CarteProspect key={lead.id} lead={lead} onBrouillon={rediger}
                  brouillon={brouillons[lead.id]} redactionEnCours={redactionPour === lead.id} />
              ))}
            </div>
          ) : (
            <div className="glass p-6" data-testid="prospection-vide">
              <p className="m-0 text-sm font-semibold text-white/75">Aucun nouveau prospect cette fois.</p>
              <p className="m-0 mt-1.5 text-[12.5px] leading-relaxed text-white/50">
                {resultat.message || "Les résultats trouvés étaient déjà dans votre pipeline. Élargissez le secteur, changez de département, ou activez une autre source."}
              </p>
            </div>
          )}
        </div>
      )}

      {runs.length > 0 && !resultat && (
        <div className="glass p-5">
          <p className="m-0 text-[11px] font-semibold uppercase tracking-wide text-white/45">Scans précédents</p>
          <ul className="mt-2 space-y-1.5 list-none p-0">
            {runs.slice(0, 5).map((run) => (
              <li key={run.date} className="flex flex-wrap justify-between gap-2 text-[12.5px] text-white/60">
                <span>{new Date(run.date).toLocaleString("fr-FR", { dateStyle: "medium", timeStyle: "short" })}</span>
                <span className="text-white/40">{run.nouveaux} retenu(s) sur {run.examines} · {(run.sources || []).join(", ")}</span>
              </li>
            ))}
          </ul>
          <p className="m-0 mt-3 text-[11.5px] leading-relaxed text-white/40">
            Les prospects détectés rejoignent votre pipeline dans l'onglet Croissance.
          </p>
        </div>
      )}
    </section>
  );
}
