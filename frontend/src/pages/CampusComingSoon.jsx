import { GraduationCap, LockKeyhole, ShieldCheck } from "lucide-react";
import { useNavigate } from "react-router-dom";

const TABS = [
  ["/campus", "Aujourd’hui"],
  ["/campus/entreprise", "Mon entreprise"],
  ["/campus/missions", "Missions"],
  ["/campus/coach", "Coach IA"],
  ["/campus/progression", "Progression"],
  ["/campus/portfolio", "Portfolio"],
  ["/campus/alternance", "Alternance"],
];

export default function CampusComingSoon() {
  const navigate = useNavigate();
  const isProjectAdmin = process.env.REACT_APP_PREVIEW_ADMIN === "true" && localStorage.getItem("zayado_preview_admin") === "1";
  return (
    <div className="space-y-6" data-testid="campus-coming-soon">
      <header>
        <p className="text-[11px] font-semibold uppercase tracking-[.16em] text-[#DEC2A3]">MyExtension Campus</p>
        <h1 className="font-head mt-1 text-2xl font-semibold text-white sm:text-3xl">Pratique & progrès</h1>
        <p className="mt-1 max-w-2xl text-sm text-white/55">Un espace d’apprentissage professionnel sera bientôt intégré à votre environnement Business.</p>
      </header>
      <nav className="flex gap-2 overflow-x-auto pb-1" aria-label="Navigation Campus">
        {TABS.map(([path, label], index) => <button key={path} type="button" onClick={() => navigate(path)} className={`whitespace-nowrap rounded-full border px-3.5 py-2 text-sm font-semibold ${index === 0 ? "border-[#DEC2A3]/40 bg-[#DEC2A3] text-[#0A1128]" : "border-white/15 bg-white/[.04] text-white/55"}`}>{label}</button>)}
      </nav>
      <section className="glass flex min-h-[390px] items-center justify-center p-8 text-center sm:p-12">
        <div className="max-w-xl">
          <span className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl border border-[#DEC2A3]/30 bg-[#DEC2A3]/10 text-[#F1E2CC]"><GraduationCap size={30} /></span>
          <p className="mt-6 text-[11px] font-semibold uppercase tracking-[.18em] text-[#DEC2A3]">Campus</p>
          <h2 className="font-head mt-3 text-3xl font-semibold text-white sm:text-4xl">Bientôt disponible</h2>
          <p className="mx-auto mt-4 max-w-lg text-sm leading-7 text-white/60">Cet espace est actuellement en préparation. Les missions, le Coach IA et la progression ne sont pas encore ouverts aux utilisateurs.</p>
          <div className="mx-auto mt-6 flex max-w-md items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/[.04] px-4 py-3 text-xs text-white/50"><LockKeyhole size={15} className="text-[#F1E2CC]" /> Accès désactivé jusqu’à la prochaine version.</div>
          <button type="button" disabled={!isProjectAdmin} onClick={() => isProjectAdmin && navigate("/campus/missions")} className="mt-5 inline-flex items-center gap-2 rounded-xl border border-[#DEC2A3]/25 px-4 py-2.5 text-sm font-semibold text-[#F1E2CC] disabled:cursor-not-allowed disabled:opacity-45" title="Réservé à l’administrateur du projet"><ShieldCheck size={15} /> Ouvrir — admin du projet uniquement</button>
        </div>
      </section>
    </div>
  );
}

export { CampusComingSoon };
