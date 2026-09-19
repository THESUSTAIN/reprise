import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, ArrowRight, Loader2, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { authOnboarding } from "../lib/api";

const STEPS = [
  { id: 1, label: "Vous" },
  { id: 2, label: "Votre activité" },
  { id: 3, label: "Votre cap" },
];

const INSPIRATIONS = [
  { id: "universelle", label: "Inspiration universelle", description: "Un espace neutre, centré sur votre activité." },
  { id: "foi", label: "Foi & vocation", description: "Ajouter cette dimension à votre accompagnement, librement." },
];
const WORKSPACES = ["Solo", "Petite équipe", "Agence / Cabinet"];
const PROJECT_TYPES = [
  { id: "NET", label: "En ligne / digital" },
  { id: "TERRAIN", label: "Terrain / local" },
  { id: "MIXTE", label: "Les deux" },
];
const PRIORITIES = ["Trésorerie", "Ventes", "Organisation", "Énergie", "Croissance"];

export default function Onboarding() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [firstName, setFirstName] = useState("");
  const [company, setCompany] = useState("");
  const [status, setStatus] = useState("");
  const [sector, setSector] = useState("");
  const [inspiration, setInspiration] = useState("universelle");
  const [workspace, setWorkspace] = useState("");
  const [projectType, setProjectType] = useState("NET");
  const [objective, setObjective] = useState("");
  const [priorities, setPriorities] = useState([]);
  const [saving, setSaving] = useState(false);

  const progress = useMemo(() => `${Math.round((step / STEPS.length) * 100)}%`, [step]);
  const togglePriority = (item) => setPriorities((current) => current.includes(item) ? current.filter((x) => x !== item) : [...current, item].slice(0, 3));

  const next = () => {
    if (step === 1 && !firstName.trim()) {
      toast.error("Indiquez au moins votre prénom pour continuer.");
      return;
    }
    setStep((current) => Math.min(3, current + 1));
  };

  const previous = () => setStep((current) => Math.max(1, current - 1));

  const submit = async () => {
    if (!firstName.trim()) {
      toast.error("Indiquez au moins votre prénom pour terminer.");
      return;
    }
    setSaving(true);
    try {
      await authOnboarding({
        first_name: firstName.trim(),
        entreprise: company.trim(),
        statut: status.trim(),
        secteur: sector.trim(),
        inspiration,
        workspace_type: workspace,
        project_type: projectType,
        objectif_90j: objective.trim(),
        priorites: priorities,
      });
      navigate("/");
    } catch (error) {
      toast.error(error?.message || "Échec de l'enregistrement. Réessayez.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="onboarding-page" data-testid="page-onboarding">
      <div className="onboarding-glow onboarding-glow-a" aria-hidden="true" />
      <div className="onboarding-glow onboarding-glow-b" aria-hidden="true" />
      <main className="onboarding-shell">
        <div className="onboarding-brand">
          <div className="onboarding-logo">Z</div>
          <div>
            <div className="onboarding-brand-name">ZAYADO</div>
            <div className="onboarding-brand-sub">MyExtension AI</div>
          </div>
        </div>

        <div className="onboarding-card">
          <div className="onboarding-topline">
            <span className="onboarding-kicker"><Sparkles size={14} /> Configuration personnalisée</span>
            <span className="onboarding-step-count">Étape {step} / 3</span>
          </div>
          <div className="onboarding-progress"><span style={{ width: progress }} /></div>

          {step === 1 && (
            <section className="onboarding-step" data-testid="onboarding-step-1">
              <h1>Commençons par vous.</h1>
              <p>Quelques repères suffisent pour que votre cockpit parle de votre réalité, pas d'un profil générique.</p>
              <div className="onboarding-grid-2">
                <label className="onboarding-field">
                  <span>Prénom <b>*</b></span>
                  <input value={firstName} onChange={(e) => setFirstName(e.target.value)} placeholder="Ex. Marie" autoFocus />
                </label>
                <label className="onboarding-field">
                  <span>Nom de votre activité</span>
                  <input value={company} onChange={(e) => setCompany(e.target.value)} placeholder="Ex. Studio Marie" />
                </label>
              </div>
              <label className="onboarding-field">
                <span>Votre statut</span>
                <input value={status} onChange={(e) => setStatus(e.target.value)} placeholder="Ex. freelance, micro-entreprise, dirigeant…" />
              </label>
              <div className="onboarding-section-label">Votre manière d'être accompagné</div>
              <div className="onboarding-option-grid onboarding-option-grid-2">
                {INSPIRATIONS.map((item) => (
                  <button key={item.id} type="button" onClick={() => setInspiration(item.id)} className={`onboarding-option ${inspiration === item.id ? "is-selected" : ""}`} data-testid={`inspiration-${item.id}`}>
                    <span className="onboarding-option-title">{item.label}</span>
                    <span className="onboarding-option-description">{item.description}</span>
                  </button>
                ))}
              </div>
            </section>
          )}

          {step === 2 && (
            <section className="onboarding-step" data-testid="onboarding-step-2">
              <h1>Parlons de votre activité.</h1>
              <p>Ces informations servent à contextualiser les recommandations, les écrans et votre accompagnement.</p>
              <label className="onboarding-field">
                <span>Secteur d'activité</span>
                <input value={sector} onChange={(e) => setSector(e.target.value)} placeholder="Ex. conseil, artisanat, finance, création…" autoFocus />
              </label>
              <div className="onboarding-section-label">Votre environnement de travail</div>
              <div className="onboarding-option-grid onboarding-option-grid-3">
                {WORKSPACES.map((item) => (
                  <button key={item} type="button" onClick={() => setWorkspace(item)} className={`onboarding-option compact ${workspace === item ? "is-selected" : ""}`}>
                    <span className="onboarding-option-title">{item}</span>
                  </button>
                ))}
              </div>
              <div className="onboarding-section-label">Votre type d'activité principal</div>
              <div className="onboarding-option-grid onboarding-option-grid-3">
                {PROJECT_TYPES.map((item) => (
                  <button key={item.id} type="button" onClick={() => setProjectType(item.id)} className={`onboarding-option compact ${projectType === item.id ? "is-selected" : ""}`}>
                    <span className="onboarding-option-title">{item.label}</span>
                  </button>
                ))}
              </div>
            </section>
          )}

          {step === 3 && (
            <section className="onboarding-step" data-testid="onboarding-step-3">
              <h1>Quel cap voulez-vous donner aux 90 prochains jours ?</h1>
              <p>Votre réponse sert de fil conducteur au cockpit. Vous pourrez la modifier à tout moment.</p>
              <label className="onboarding-field">
                <span>Votre priorité n°1</span>
                <textarea value={objective} onChange={(e) => setObjective(e.target.value)} placeholder="Ex. Stabiliser ma trésorerie, signer 3 nouveaux clients et mieux organiser mes semaines…" autoFocus />
              </label>
              <div className="onboarding-section-label">Choisissez jusqu'à 3 priorités</div>
              <div className="onboarding-chip-row">
                {PRIORITIES.map((item) => (
                  <button key={item} type="button" onClick={() => togglePriority(item)} className={`onboarding-chip ${priorities.includes(item) ? "is-selected" : ""}`}>{item}</button>
                ))}
              </div>
              <div className="onboarding-summary">
                <div><span>Profil</span><strong>{firstName || "Votre prénom"}{company ? ` · ${company}` : ""}</strong></div>
                <div><span>Activité</span><strong>{sector || "À préciser"} · {projectType === "TERRAIN" ? "Terrain" : projectType === "MIXTE" ? "Mixte" : "En ligne"}</strong></div>
                <div><span>Priorités</span><strong>{priorities.length ? priorities.join(" · ") : "À définir ensuite"}</strong></div>
              </div>
            </section>
          )}

          <div className="onboarding-actions">
            {step > 1 ? (
              <button type="button" onClick={previous} className="onboarding-back"><ArrowLeft size={15} /> Retour</button>
            ) : <span />}
            {step < 3 ? (
              <button type="button" onClick={next} className="onboarding-primary">Continuer <ArrowRight size={15} /></button>
            ) : (
              <button type="button" onClick={submit} disabled={saving} className="onboarding-primary" data-testid="onboarding-submit">
                {saving ? <Loader2 size={15} className="animate-spin" /> : <>Entrer dans mon cockpit <ArrowRight size={15} /></>}
              </button>
            )}
          </div>
        </div>
        <p className="onboarding-note">Vos informations restent modifiables dans Paramètres. Aucune décision n'est prise à votre place.</p>
      </main>
    </div>
  );
}
