import React from "react";
import { Helmet } from "react-helmet-async";
import { Link } from "react-router-dom";
import { ArrowRight, Calculator, Building2, FileText, TrendingUp } from "lucide-react";
import { PublicHeader, UnifiedFooter } from "./LandingHub";

const SERVICES=[
 {title:"Vous ne savez pas vraiment ce que votre activité vous rapporte", href:"/services/finance-pilotage", icon:Calculator, label:"Finance & pilotage", text:"Quand le chiffre d'affaires ne suffit plus à savoir si vous gagnez vraiment, Zayado vous aide à remettre les chiffres au service de vos décisions."},
 {title:"Votre agenda se remplit de tâches qui ne font pas avancer votre activité", href:"/services/gestion-administrative", icon:FileText, label:"Gestion & délégation", text:"Facturation, relances, documents et suivi vous prennent trop de place ? Identifions ce qui peut sortir de votre quotidien sans vous faire perdre la main."},
 {title:"Vous avez une idée ou une activité, mais pas encore une base claire pour avancer", href:"/services/creation-structuration", icon:Building2, label:"Création & structuration", text:"Statut, offre, organisation, priorités : on commence par le point qui bloque vraiment, puis on construit le bon parcours."},
 {title:"Vous envisagez une cession ou une reprise, mais vous ne savez pas encore par où commencer", href:"/services/cession-reprise", icon:TrendingUp, label:"Cession & reprise", text:"Avant de négocier, il faut savoir ce qui est prêt, ce qui manque et quels diagnostics doivent être priorisés."}
];

export default function NosServices(){
 return <div className="min-h-screen bg-[#f7f2e9] text-[#1d242d]">
  <Helmet>
   <title>Services Zayado | Finance, gestion, création, cession & reprise</title>
   <meta name="description" content="Un problème de trésorerie, trop d'administratif, une activité à structurer ou une cession à préparer ? Zayado commence par votre situation et vous oriente vers le bon parcours."/>
   <link rel="canonical" href="https://zayado.net/nos-services"/>
   <meta name="robots" content="index,follow"/>
  </Helmet>
  <PublicHeader/>
  <main>
   <section className="relative overflow-hidden text-white" style={{background:"linear-gradient(135deg,#071b3a 0%,#173d68 60%,#496c8c 100%)"}}>
    <div className="absolute inset-0" style={{background:"radial-gradient(circle at 82% 16%,rgba(242,220,176,.35),transparent 28%),radial-gradient(circle at 12% 82%,rgba(255,255,255,.12),transparent 28%)"}}/>
    <div className="relative max-w-6xl mx-auto px-5 md:px-8 py-16 md:py-24">
      <div className="text-xs uppercase tracking-[.25em] text-[#f0d9a8]">ZAYADO SERVICES</div>
      <h1 className="mt-5 max-w-5xl text-4xl md:text-6xl xl:text-7xl font-serif leading-[.98]">Commencez par ce qui vous pèse aujourd'hui. Nous verrons ensuite ce qu'il faut faire.</h1>
      <p className="mt-6 max-w-3xl text-lg md:text-xl leading-relaxed text-white/75">Pas de catalogue de prestations à parcourir. Décrivez votre situation, votre blocage ou la décision qui vous attend ; le parcours s'adapte ensuite à votre besoin.</p>
      <a href="#parcours" className="mt-8 inline-flex items-center gap-2 rounded-full px-6 py-3.5 font-semibold text-[#102945] bg-gradient-to-r from-[#f3e4c1] to-[#c99c52]">Trouver mon parcours <ArrowRight size={16}/></a>
    </div>
   </section>

   <section id="parcours" className="max-w-6xl mx-auto px-5 md:px-8 py-16 md:py-20 scroll-mt-20">
    <div className="max-w-3xl"><div className="text-xs uppercase tracking-[.22em] text-[#9d7a43]">Quel problème cherchez-vous à résoudre ?</div><h2 className="mt-3 text-3xl md:text-5xl font-serif text-[#102945]">Vous n'avez pas besoin de connaître le nom du service. Vous devez simplement reconnaître votre situation.</h2></div>
    <div className="grid md:grid-cols-2 gap-5 mt-10">
      {SERVICES.map(({title,href,icon:Icon,label,text})=><Link key={href} to={href} className="group rounded-[30px] bg-white border border-[#e2d9c9] p-7 md:p-8 shadow-sm hover:-translate-y-1 transition hover:shadow-lg">
        <div className="flex items-center justify-between gap-4"><div className="w-12 h-12 rounded-2xl grid place-items-center bg-[#edf2f7] text-[#173d68]"><Icon size={22}/></div><span className="text-[10px] uppercase tracking-[.18em] text-[#9d7a43]">{label}</span></div>
        <h3 className="mt-6 text-2xl md:text-3xl font-serif text-[#102945] leading-tight">{title}</h3>
        <p className="mt-4 text-[#63665f] leading-relaxed">{text}</p>
        <div className="mt-7 inline-flex items-center gap-2 text-sm font-semibold text-[#173d68]">Voir le parcours <ArrowRight size={16} className="group-hover:translate-x-1 transition"/></div>
      </Link>)}
    </div>
   </section>

   <section className="border-y border-[#e5ddcf] bg-white"><div className="max-w-6xl mx-auto px-5 md:px-8 py-12 grid md:grid-cols-3 gap-7"><div><div className="text-xs uppercase tracking-[.2em] text-[#9d7a43]">01 · Votre situation</div><h3 className="mt-2 text-xl font-semibold text-[#183654]">On part du problème, pas du produit.</h3><p className="mt-2 text-sm text-[#686d68]">Vous expliquez ce qui vous bloque aujourd'hui, avec vos mots.</p></div><div><div className="text-xs uppercase tracking-[.2em] text-[#9d7a43]">02 · Votre cadrage</div><h3 className="mt-2 text-xl font-semibold text-[#183654]">Quelques questions pour éviter le mauvais parcours.</h3><p className="mt-2 text-sm text-[#686d68]">Le diagnostic sert à identifier ce qu'il faut réellement traiter en premier.</p></div><div><div className="text-xs uppercase tracking-[.2em] text-[#9d7a43]">03 · La bonne réponse</div><h3 className="mt-2 text-xl font-semibold text-[#183654]">Zayado ou le bon spécialiste.</h3><p className="mt-2 text-sm text-[#686d68]">Quand le service est opéré par Zayado, l'équipe le prend en charge ; sinon, nous mobilisons la bonne expertise.</p></div></div></section>

   <section className="max-w-6xl mx-auto px-5 md:px-8 py-16"><div className="rounded-[30px] bg-gradient-to-br from-[#102945] to-[#214f77] p-8 md:p-12 text-white flex flex-col lg:flex-row items-start lg:items-center justify-between gap-8"><div><div className="text-xs uppercase tracking-[.22em] text-[#efdbb2]">Sans formulaire générique</div><h2 className="mt-3 text-3xl md:text-4xl font-serif">Votre situation mérite mieux qu'un simple « contactez-nous ».</h2><p className="mt-3 max-w-2xl text-white/70">Choisissez la douleur qui vous ressemble le plus ; le tunnel prend ensuite le relais.</p></div><a href="#parcours" className="shrink-0 inline-flex items-center gap-2 rounded-full px-6 py-3.5 font-semibold text-[#102945] bg-gradient-to-r from-[#f3e4c1] to-[#c99c52]">Commencer <ArrowRight size={16}/></a></div></section>
  </main>
  <UnifiedFooter/>
 </div>
}
