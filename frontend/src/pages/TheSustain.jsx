import { BookOpen, HeartHandshake } from "lucide-react";

// Page "TheSustain — Foi & vocation", reprise de la maquette de design.
// Aucun backend TheSustain (SSO, contenu) n'existe dans ce projet — cette
// page reste donc volontairement une activation-teaser honnete, pas une
// fonctionnalite simulee comme active.
export default function TheSustain() {
  return (
    <div className="space-y-6" data-testid="page-thesustain">
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-[.14em] text-[#DEC2A3]">TheSustain · Foi & vocation</p>
        <h1 className="font-head text-2xl sm:text-3xl font-semibold text-white mt-1">Travailler avec foi, servir avec cohérence.</h1>
        <p className="text-white/55 text-sm mt-1 max-w-xl">Cet espace est visible uniquement lorsqu'un parcours TheSustain est activé volontairement.</p>
      </div>

      <div className="glass p-6 grid grid-cols-1 lg:grid-cols-[1fr_auto] gap-6 items-center">
        <div>
          <span className="inline-flex items-center gap-1.5 rounded-full bg-white/5 border border-white/15 px-3 py-1 text-[11px] font-semibold text-white/70">
            <span className="w-1.5 h-1.5 rounded-full bg-[#DEC2A3]" /> Parcours foi activable
          </span>
          <h2 className="font-head text-xl font-semibold text-white mt-3">Votre vocation peut relire vos décisions.</h2>
          <p className="text-white/55 text-sm mt-1 max-w-lg leading-relaxed">
            Prière, discernement, service, amour du prochain et intégrité dans les affaires restent proposés librement, sans mesurer votre qualité spirituelle ni imposer la foi au parcours Zayado.
          </p>
          <button disabled
            className="mt-4 inline-flex items-center gap-1.5 rounded-xl border border-white/15 px-4 py-2.5 text-sm font-semibold text-white/40 cursor-not-allowed"
            title="L'activation TheSustain n'est pas encore connectée côté serveur">
            Activer l'espace TheSustain
          </button>
        </div>
        <HeartHandshake size={44} className="text-[#DEC2A3] shrink-0" />
      </div>

      <section className="glass p-6 border border-[#DEC2A3]/30" data-testid="thesustain-discernment">
        <div className="flex items-center gap-2 text-[#DEC2A3] text-[11px] font-semibold uppercase tracking-[.14em]"><BookOpen size={15} /> Temps de discernement</div>
        <blockquote className="font-head text-lg sm:text-xl text-white mt-3 leading-relaxed max-w-3xl">« Tout ce que vous faites, faites-le de tout votre cœur, comme pour le Seigneur. »</blockquote>
        <p className="text-[#F1E2CC] text-sm mt-2 font-medium">Colossiens 3:23</p>
        <p className="text-white/55 text-sm mt-3 max-w-3xl leading-relaxed">Cette référence est proposée ici, dans l’espace TheSustain activé volontairement. Elle peut nourrir votre discernement ; elle ne remplace ni votre responsabilité, ni une décision professionnelle éclairée.</p>
      </section>
    </div>
  );
}
