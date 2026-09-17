import React from "react";
import { Helmet } from "react-helmet-async";
import { Link } from "react-router-dom";
import { ArrowUpRight, ArrowRight, Instagram, Linkedin, Youtube, Sparkles } from "lucide-react";

const NAVY = "#102945";
const CREAM = "#F6F1E8";
const SAND = "#D8B979";
const TERRACOTTA = "#A84A2A";
const INK = "#1A2028";

export function PublicHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-[#e9e2d6] bg-[#fffdfa]/95 backdrop-blur" data-testid="public-header">
      <div className="max-w-7xl mx-auto px-4 md:px-8 h-16 flex items-center justify-between gap-5">
        <Link to="/" className="flex items-center gap-3" aria-label="Zayado">
          <span className="text-3xl font-serif font-semibold" style={{ color: NAVY }}>Z</span>
          <span>
            <span className="block font-semibold tracking-[0.12em]" style={{ color: NAVY }}>ZAYADO</span>
            <span className="block text-[9px] uppercase tracking-[0.19em]" style={{ color: SAND }}>Entreprendre avec sens</span>
          </span>
        </Link>
        <nav className="hidden md:flex items-center gap-7 text-sm" style={{ color: NAVY }}>
          <Link to="/boutique">Boutique</Link>
          <Link to="/avantages">Avantages</Link>
          <Link to="/nos-services">Services</Link>
          <Link to="/myextension-ai">MyExtension AI</Link>
        </nav>
        <Link to="/contact" className="hidden sm:inline-flex items-center gap-2 rounded-full bg-[#102945] text-white px-4 py-2 text-sm font-semibold">
          Parler à Zayado <ArrowUpRight size={15} />
        </Link>
      </div>
    </header>
  );
}

export function UnifiedFooter() {
  return (
    <footer className="bg-[#102945] text-white">
      <div className="max-w-7xl mx-auto px-4 md:px-8 py-10 grid md:grid-cols-4 gap-8">
        <div>
          <div className="text-xl font-serif">ZAYADO</div>
          <p className="mt-2 text-sm text-white/60 max-w-xs">Entreprendre avec sens, clarté et équilibre.</p>
        </div>
        <div><div className="text-xs uppercase tracking-widest text-white/40">Explorer</div><div className="mt-3 space-y-2 text-sm"><Link to="/boutique" className="block text-white/75">Boutique</Link><Link to="/avantages" className="block text-white/75">Avantages</Link><Link to="/nos-services" className="block text-white/75">Services</Link></div></div>
        <div><div className="text-xs uppercase tracking-widest text-white/40">Logiciel</div><div className="mt-3 space-y-2 text-sm"><Link to="/myextension-ai" className="block text-white/75">MyExtension AI</Link><Link to="/tarifs" className="block text-white/75">Tarifs</Link><Link to="/faq" className="block text-white/75">FAQ</Link></div></div>
        <div><div className="text-xs uppercase tracking-widest text-white/40">Contact</div><div className="mt-3 space-y-2 text-sm"><Link to="/contact" className="block text-white/75">Nous contacter</Link><Link to="/a-propos" className="block text-white/75">À propos</Link><Link to="/legal/confidentialite" className="block text-white/75">Confidentialité</Link></div></div>
      </div>
      <div className="border-t border-white/10"><div className="max-w-7xl mx-auto px-4 md:px-8 py-4 text-xs text-white/45 flex flex-wrap items-center justify-between gap-3"><span>© 2026 Zayado. Tous droits réservés.</span><span>Réconcilier sens, travail et bien-être.</span></div></div>
    </footer>
  );
}

const journeys = [
  {title:"Boutique", text:"Des outils sélectionnés pour votre confort, votre concentration et votre quotidien.", href:"/boutique", accent:"#173652"},
  {title:"Avantages", text:"Des offres négociées et des opportunités utiles pour entreprendre, bouger et économiser.", href:"/avantages", accent:"#E7D8C2"},
  {title:"Services", text:"Une équipe et des spécialistes pour vous aider à piloter, structurer et développer votre activité.", href:"/nos-services", accent:"#A84A2A"},
];

export default function Landing() {
  return (
    <div className="min-h-screen overflow-x-hidden" style={{ background: `linear-gradient(180deg, ${CREAM} 0%, #fffdfa 100%)`, color: INK }}>
      <Helmet>
        <title>Zayado | Entreprendre avec sens, clarté et équilibre</title>
        <meta name="description" content="Zayado réunit boutique, avantages et services pour aider les indépendants et petites structures à entreprendre avec sens, clarté et équilibre." />
        <link rel="canonical" href="https://zayado.net/" />
        <meta name="robots" content="index,follow" />
      </Helmet>

      <div className="min-h-[100svh] relative overflow-hidden" style={{ background: "radial-gradient(circle at 20% 20%, rgba(216,185,121,.32), transparent 30%), linear-gradient(135deg,#f6efe3,#e9eef5 48%,#ffffff)" }}>
        <div className="absolute inset-0 opacity-30" style={{backgroundImage:"linear-gradient(rgba(16,41,69,.12) 1px, transparent 1px), linear-gradient(90deg, rgba(16,41,69,.12) 1px, transparent 1px)",backgroundSize:"60px 60px",maskImage:"linear-gradient(90deg,transparent,black 16%,black 86%,transparent)"}}/>
        <div className="relative max-w-[1500px] mx-auto px-5 md:px-10 pt-6 pb-10">
          <div className="flex items-start justify-between gap-5">
            <div className="max-w-[58%] md:max-w-[45%]">
              <div className="text-[clamp(60px,11vw,150px)] leading-[.79] font-serif font-semibold tracking-[-.06em]" style={{color:NAVY}}>Zayado</div>
              <p className="mt-5 text-lg md:text-2xl font-medium max-w-xl" style={{color:NAVY}}>Entreprendre avec sens, clarté et équilibre.</p>
              <div className="mt-8 flex flex-wrap gap-3">
                <Link to="/boutique" className="rounded-full bg-[#102945] text-white px-5 py-3 text-sm font-semibold inline-flex items-center gap-2">Découvrir la marketplace <ArrowUpRight size={15}/></Link>
                <Link to="/myextension-ai" className="rounded-full border border-[#102945]/20 bg-white/60 px-5 py-3 text-sm font-semibold" style={{color:NAVY}}>Découvrir MyExtension AI</Link>
              </div>
            </div>
            <div className="hidden md:flex items-center gap-5 pt-2 text-sm font-semibold" style={{color:NAVY}}>
              <Link to="/boutique">Boutique</Link>
              <Link to="/avantages">Avantages</Link>
              <Link to="/nos-services">Services</Link>
              <Link to="/tarifs">Tarifs</Link>
            </div>
          </div>

          <div className="grid lg:grid-cols-12 gap-5 mt-10 items-end">
            <div className="lg:col-span-7 rounded-[34px] overflow-hidden min-h-[620px] relative bg-[#183247]">
              <img className="absolute inset-0 w-full h-full object-cover" src="https://images.unsplash.com/photo-1497366754035-f200968a6e72?auto=format&fit=crop&w=1800&q=85" alt="Espace de travail élégant" />
              <div className="absolute inset-0 bg-gradient-to-t from-[#091a2b] via-transparent to-transparent"/>
              <div className="absolute left-6 bottom-6 right-6 text-white">
                <div className="text-xs uppercase tracking-[.23em] text-white/60">L'écosystème Zayado</div>
                <h1 className="mt-2 text-4xl md:text-6xl font-serif max-w-xl leading-[.95]">Une marketplace qui accompagne aussi votre activité.</h1>
              </div>
            </div>

            <div className="lg:col-span-5 grid gap-5">
              <Link to="/boutique" className="group rounded-[30px] p-7 min-h-[270px] text-white flex flex-col justify-between" style={{background:NAVY}}>
                <div><div className="text-xs uppercase tracking-[.23em] text-white/50">01 · Boutique</div><h2 className="mt-3 text-3xl font-serif">Les outils qui prolongent votre performance.</h2></div>
                <div className="flex items-center justify-between text-sm"><span>Sélection Corps · Âme · Rituel</span><ArrowRight className="group-hover:translate-x-1 transition"/></div>
              </Link>
              <div className="grid grid-cols-2 gap-5">
                <Link to="/avantages" className="rounded-[28px] p-6 min-h-[220px] flex flex-col justify-between" style={{background:"#E7D8C2",color:NAVY}}><div><div className="text-xs uppercase tracking-[.2em] opacity-60">02 · Avantages</div><h3 className="mt-3 text-2xl font-serif">Négocié pour vous.</h3></div><ArrowUpRight/></Link>
                <Link to="/nos-services" className="rounded-[28px] p-6 min-h-[220px] text-white flex flex-col justify-between" style={{background:TERRACOTTA}}><div><div className="text-xs uppercase tracking-[.2em] text-white/60">03 · Services</div><h3 className="mt-3 text-2xl font-serif">Une équipe derrière votre activité.</h3></div><ArrowUpRight/></Link>
              </div>
            </div>
          </div>

          <div className="mt-8 grid md:grid-cols-4 gap-4">
            {[['Sélection rigoureuse','Produits et offres vérifiés'],['Business Travel','Des offres utiles quand vous bougez'],['Services pro','Finance, gestion, structuration'],['MyExtension AI','Votre cockpit pour tout relier']].map(([a,b])=><div key={a} className="rounded-2xl bg-white/75 backdrop-blur p-4 border border-white"><div className="text-sm font-semibold" style={{color:NAVY}}>{a}</div><div className="text-xs mt-1 text-black/55">{b}</div></div>)}
          </div>
        </div>
      </div>

      <section className="max-w-7xl mx-auto px-4 md:px-8 py-16 md:py-24">
        <div className="text-center max-w-3xl mx-auto"><div className="text-xs uppercase tracking-[.23em]" style={{color:SAND}}>Par où commencer ?</div><h2 className="mt-3 text-4xl md:text-5xl font-serif" style={{color:NAVY}}>Choisissez ce dont votre activité a besoin maintenant.</h2></div>
        <div className="grid md:grid-cols-3 gap-5 mt-10">
          {journeys.map((j)=><Link key={j.title} to={j.href} className="rounded-[28px] p-7 border border-[#e7dfd2] bg-white hover:-translate-y-1 transition shadow-sm"><div className="w-9 h-9 rounded-full" style={{background:j.accent}}/><h3 className="mt-6 text-2xl font-serif" style={{color:NAVY}}>{j.title}</h3><p className="mt-3 text-sm leading-relaxed text-black/55">{j.text}</p><div className="mt-7 inline-flex items-center gap-2 text-sm font-semibold" style={{color:NAVY}}>Explorer <ArrowRight size={16}/></div></Link>)}
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-4 md:px-8 pb-24">
        <div className="rounded-[34px] bg-[#102945] text-white p-8 md:p-12 grid md:grid-cols-2 gap-10 items-center">
          <div><div className="text-xs uppercase tracking-[.22em] text-white/45">Le cockpit</div><h2 className="mt-3 text-4xl md:text-5xl font-serif">MyExtension AI relie tout ce que vous faites.</h2><p className="mt-5 text-white/65 max-w-xl">Vision, pilotage financier, travail, CRM, croissance et énergie réunis dans une même expérience.</p><Link to="/myextension-ai" className="mt-7 inline-flex items-center gap-2 rounded-full bg-white text-[#102945] px-5 py-3 text-sm font-semibold">Voir MyExtension AI <ArrowRight size={16}/></Link></div>
          <div className="grid grid-cols-2 gap-4">{[['Vision','Votre trajectoire'],['Finance','Vos chiffres'],['Travail','Vos missions'],['Growth','Vos actions'],['CRM','Vos relations'],['Énergie','Votre rythme']].map(([a,b])=><div key={a} className="rounded-2xl border border-white/10 bg-white/5 p-4"><div className="font-semibold">{a}</div><div className="text-xs text-white/50 mt-1">{b}</div></div>)}</div>
        </div>
      </section>

      <UnifiedFooter />
    </div>
  );
}
