import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Loader2, ArrowRight } from "lucide-react";
import { toast } from "sonner";
import { authOnboarding } from "../lib/api";

const INSPIRATIONS = [
  { id: "universelle", label: "Inspiration universelle" },
  { id: "foi", label: "Foi" },
];
const WORKSPACES = ["Solo", "Petite équipe", "Agence / Cabinet"];
const PROJECT_TYPES = ["Service", "Produit", "Les deux"];

export default function Onboarding() {
  const navigate = useNavigate();
  const [firstName, setFirstName] = useState("");
  const [inspiration, setInspiration] = useState("");
  const [workspace, setWorkspace] = useState("");
  const [projectType, setProjectType] = useState("");
  const [saving, setSaving] = useState(false);

  const submit = async () => {
    setSaving(true);
    try {
      await authOnboarding({ first_name: firstName.trim(), inspiration, workspace_type: workspace, project_type: projectType });
      navigate("/");
    } catch { toast.error("Échec de l'enregistrement"); }
    finally { setSaving(false); }
  };

  return (
    <div className="min-h-screen bg-[#0A1128] p-4" data-testid="page-onboarding">
      <div className="mx-auto max-w-lg py-10">
        <h1 className="font-head text-2xl font-semibold text-white">Bienvenue</h1>
        <p className="mt-1 text-sm text-white/55">Quelques informations pour personnaliser votre espace — rien n'est imposé, tout est modifiable ensuite dans les Paramètres.</p>

        <div className="mt-6 glass space-y-5 rounded-2xl p-5">
          <div>
            <label className="mb-1.5 block text-[12px] font-medium text-white/70">Votre prénom</label>
            <input value={firstName} onChange={(e) => setFirstName(e.target.value)} placeholder="Prénom"
              className="w-full rounded-xl border border-white/15 bg-white/5 px-3.5 py-2.5 text-sm text-white placeholder:text-white/35 focus:outline-none focus:border-[#DEC2A3]/50" />
          </div>

          <div>
            <label className="mb-1.5 block text-[12px] font-medium text-white/70">Style d'inspiration — au choix, jamais imposé</label>
            <div className="grid grid-cols-2 gap-2">
              {INSPIRATIONS.map((i) => (
                <button key={i.id} onClick={() => setInspiration(i.id)} data-testid={`inspiration-${i.id}`}
                  className={`rounded-xl border px-3.5 py-2.5 text-sm font-medium ${inspiration === i.id ? "border-[#DEC2A3] bg-[#DEC2A3]/15 text-[#F0DCA5]" : "border-white/15 bg-white/5 text-white/70"}`}>
                  {i.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="mb-1.5 block text-[12px] font-medium text-white/70">Votre espace de travail</label>
            <div className="grid grid-cols-3 gap-2">
              {WORKSPACES.map((w) => (
                <button key={w} onClick={() => setWorkspace(w)}
                  className={`rounded-xl border px-2 py-2.5 text-xs font-medium ${workspace === w ? "border-[#DEC2A3] bg-[#DEC2A3]/15 text-[#F0DCA5]" : "border-white/15 bg-white/5 text-white/70"}`}>
                  {w}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="mb-1.5 block text-[12px] font-medium text-white/70">Type de projet</label>
            <div className="grid grid-cols-3 gap-2">
              {PROJECT_TYPES.map((t) => (
                <button key={t} onClick={() => setProjectType(t)}
                  className={`rounded-xl border px-2 py-2.5 text-xs font-medium ${projectType === t ? "border-[#DEC2A3] bg-[#DEC2A3]/15 text-[#F0DCA5]" : "border-white/15 bg-white/5 text-white/70"}`}>
                  {t}
                </button>
              ))}
            </div>
          </div>
        </div>

        <button onClick={submit} disabled={saving} data-testid="onboarding-submit"
          className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-[#DEC2A3] py-3 text-sm font-semibold text-[#0A1128] hover:opacity-90 disabled:opacity-60">
          {saving ? <Loader2 size={15} className="animate-spin" /> : <>Continuer <ArrowRight size={15} /></>}
        </button>
      </div>
    </div>
  );
}
