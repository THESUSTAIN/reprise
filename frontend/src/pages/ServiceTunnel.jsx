import React, { useMemo, useState } from "react";
import { Helmet } from "react-helmet-async";
import { Link, useLocation } from "react-router-dom";
import { ArrowRight, Check, ChevronLeft, ShieldCheck, Clock3, MessageCircle, Calculator, FileText, Building2, TrendingUp } from "lucide-react";
import { PublicHeader, UnifiedFooter } from "./LandingHub";

const CONFIG = {
  "/services/finance-pilotage": {
    key: "finance",
    title: "Votre activité avance, mais vos chiffres ne vous donnent pas encore une vraie direction.",
    intro: "Quand le chiffre d'affaires monte mais que la trésorerie reste tendue, quand vous travaillez beaucoup sans savoir ce qui est vraiment rentable, le problème n'est pas forcément de travailler plus : il faut voir clair.",
    tag: "Finance & pilotage",
    icon: Calculator,
    gradient: "linear-gradient(135deg,#071b3a 0%,#173d68 55%,#345f86 100%)",
    pain: [
      "Vous ne savez pas précisément ce qui vous rapporte le plus.",
      "Votre trésorerie vous préoccupe mais vous manquez d'un point de vue régulier.",
      "Vous prenez des décisions au feeling faute d'indicateurs lisibles.",
      "Vos chiffres existent, mais ils ne vous aident pas encore à décider."
    ],
    promise: "Passer de chiffres dispersés à un pilotage financier compréhensible.",
    bullets: [
      "Lecture de marge, rentabilité et trésorerie",
      "Repérage des points de vigilance et des leviers",
      "Tableau de pilotage adapté à votre activité",
      "Préparation des décisions financières prioritaires"
    ],
    questions: [
      { k:"pain", q:"Qu'est-ce qui vous préoccupe le plus aujourd'hui ?", opts:["Je ne vois pas assez clair dans mes chiffres","Ma trésorerie me préoccupe","Je veux savoir ce qui est vraiment rentable","Je prépare une décision importante"] },
      { k:"stage", q:"Votre activité en est où ?", opts:["Je démarre","Je suis lancé mais seul","Je suis en croissance","Je dois remettre de l'ordre"] },
      { k:"horizon", q:"À quel moment avez-vous besoin d'y voir plus clair ?", opts:["Très rapidement","Ce mois-ci","Dans les 3 mois","Je suis encore en réflexion"] }
    ],
    result: "Votre premier échange peut se concentrer sur vos chiffres, votre priorité du moment et le niveau de pilotage dont vous avez réellement besoin.",
    cta: "Demander mon cadrage financier"
  },
  "/services/gestion-administrative": {
    key: "gestion",
    title: "Votre journée est pleine… mais trop souvent de tâches qui ne font pas avancer votre activité.",
    intro: "Factures, relances, documents, suivi, échéances : quand l'administratif grignote les heures que vous devriez consacrer à vos clients, le vrai coût se mesure aussi en énergie et en opportunités perdues.",
    tag: "Gestion & délégation",
    icon: FileText,
    gradient: "linear-gradient(135deg,#0b2343 0%,#244e74 58%,#7f6a50 100%)",
    pain: [
      "Vous repoussez encore des tâches administratives importantes.",
      "Votre facturation ou vos relances prennent trop de place.",
      "Vous avez du mal à garder une vision propre des échéances et documents.",
      "Vous voudriez déléguer, mais sans perdre le contrôle."
    ],
    promise: "Récupérer du temps sans perdre la visibilité sur votre activité.",
    bullets: [
      "Facturation, suivi administratif et relances",
      "Organisation des flux, documents et échéances",
      "Préparation d'éléments utiles au pilotage",
      "Délégation progressive selon votre niveau de besoin"
    ],
    questions: [
      { k:"pain", q:"Quelle tâche vous prend le plus de temps ?", opts:["Facturation et relances","Documents et administratif","Suivi des échéances","Un peu de tout"] },
      { k:"control", q:"Que voulez-vous déléguer ?", opts:["Une tâche précise","Un bloc récurrent","Une grande partie du back-office","Je ne sais pas encore"] },
      { k:"horizon", q:"À quel rythme voulez-vous retrouver de l'air ?", opts:["Dès maintenant","Ce mois-ci","Dans les 3 mois","Je veux d'abord évaluer"] }
    ],
    result: "Votre cadrage permet d'identifier ce qui doit réellement sortir de votre agenda, ce qui doit rester sous votre contrôle et la meilleure façon d'organiser la délégation.",
    cta: "Identifier ce que je peux déléguer"
  },
  "/services/creation-structuration": {
    key: "creation",
    title: "Vous avez une idée ou une activité, mais pas encore la structure qui vous permet d'avancer sereinement.",
    intro: "Statut, offre, organisation, premières priorités : au début, tout arrive en même temps. Une mauvaise décision prise trop tôt peut vous coûter du temps, de l'argent et de l'énergie.",
    tag: "Création & structuration",
    icon: Building2,
    gradient: "linear-gradient(135deg,#102945 0%,#2e587b 58%,#b98d5a 100%)",
    pain: [
      "Vous ne savez pas par quoi commencer concrètement.",
      "Vous hésitez entre plusieurs statuts ou façons de structurer votre activité.",
      "Votre offre existe, mais son modèle économique reste flou.",
      "Vous avez lancé l'activité et sentez déjà que la base manque de structure."
    ],
    promise: "Clarifier votre point de départ et les décisions à prendre avant d'accélérer.",
    bullets: [
      "Clarification de l'offre et du modèle économique",
      "Cadrage des priorités de lancement ou de remise à plat",
      "Préparation des éléments utiles à la création",
      "Orientation vers les expertises réglementées nécessaires"
    ],
    questions: [
      { k:"stage", q:"Où en êtes-vous ?", opts:["J'ai une idée","Je prépare le lancement","Je suis déjà lancé","Je veux remettre mon activité à plat"] },
      { k:"block", q:"Qu'est-ce qui vous bloque le plus ?", opts:["Le statut / cadre","L'offre et le modèle","L'organisation","Je manque de visibilité"] },
      { k:"horizon", q:"Quel est votre prochain objectif ?", opts:["Lancer","Structurer","Développer","Décider avant d'agir"] }
    ],
    result: "Vous repartez avec un point de départ mieux défini et un parcours adapté aux décisions qui comptent vraiment à ce stade.",
    cta: "Clarifier mon projet"
  },
  "/services/cession-reprise": {
    key: "cession",
    title: "Céder ou reprendre une entreprise ne se résume pas à trouver un acheteur ou une cible.",
    intro: "Valeur, rentabilité, risques, dépendance au dirigeant, financement, calendrier : une opération mal préparée peut compliquer la négociation. Le premier travail consiste donc à savoir où vous en êtes réellement.",
    tag: "Cession & reprise",
    icon: TrendingUp,
    gradient: "linear-gradient(135deg,#081d3a 0%,#315b7d 58%,#a77d4f 100%)",
    pain: [
      "Vous envisagez de vendre, mais vous ne savez pas encore si l'entreprise est prête.",
      "Vous souhaitez reprendre une entreprise sans savoir comment cadrer la cible.",
      "Vous avez un projet, mais les chiffres, risques ou étapes ne sont pas encore structurés.",
      "Vous craignez de négocier trop tôt ou sur de mauvaises bases."
    ],
    promise: "Transformer une opération complexe en prochaines étapes lisibles.",
    bullets: [
      "Cadrage du projet : cession, reprise ou exploration",
      "Lecture financière et identification des points de vigilance",
      "Préparation des étapes et éléments du dossier",
      "Orientation vers les expertises spécialisées nécessaires"
    ],
    questions: [
      { k:"role", q:"Quelle est votre situation ?", opts:["Je veux céder","Je cherche à reprendre","Je compare les deux possibilités","Je suis encore en exploration"] },
      { k:"state", q:"Où en est le projet ?", opts:["Je n'ai encore rien préparé","J'ai commencé à travailler le dossier","J'ai déjà identifié une cible / un repreneur","Les négociations ont commencé"] },
      { k:"horizon", q:"Quel est votre horizon ?", opts:["Moins de 6 mois","6 à 12 mois","Plus d'un an","Je veux d'abord mesurer la faisabilité"] }
    ],
    result: "Votre cadrage permet d'identifier les diagnostics à prioriser avant d'engager les étapes les plus sensibles de l'opération.",
    cta: "Cadrer mon projet de cession / reprise"
  }
};

export default function ServiceTunnel(){
  const { pathname } = useLocation();
  const cfg = CONFIG[pathname] || CONFIG["/services/finance-pilotage"];
  const Icon = cfg.icon;
  const [answers,setAnswers] = useState({});
  const complete = Object.keys(answers).length === cfg.questions.length;
  const progress = Object.keys(answers).length / cfg.questions.length;
  const recommendation = useMemo(() => {
    if (cfg.key === "finance") return "Un cadrage financier ciblé est le meilleur prochain pas.";
    if (cfg.key === "gestion") return "Un cadrage de délégation permet d'identifier ce qui mérite réellement de sortir de votre agenda.";
    if (cfg.key === "creation") return "Un cadrage de structuration permet de sécuriser les prochaines décisions avant d'accélérer.";
    return "Un cadrage de l'opération permet de savoir quels diagnostics et quelles étapes prioriser.";
  }, [cfg.key]);

  return <div className="min-h-screen bg-[#f7f2e9] text-[#1d242d]">
    <Helmet>
      <title>{cfg.title} | ZAYADO</title>
      <meta name="description" content={cfg.intro}/>
      <link rel="canonical" href={`https://zayado.net${pathname}`}/>
      <meta name="robots" content="index,follow"/>
    </Helmet>
    <PublicHeader/>
    <main>
      <section className="relative overflow-hidden text-white" style={{background:cfg.gradient}}>
        <div className="absolute inset-0 opacity-20" style={{background:"radial-gradient(circle at 80% 10%,rgba(245,223,177,.45),transparent 28%),radial-gradient(circle at 15% 90%,rgba(255,255,255,.12),transparent 30%)"}}/>
        <div className="relative max-w-6xl mx-auto px-5 md:px-8 py-16 md:py-24">
          <div className="flex items-center gap-3 text-xs uppercase tracking-[.25em] text-[#f0d9a8]"><Icon size={15}/> {cfg.tag}</div>
          <div className="grid lg:grid-cols-[1.2fr_.8fr] gap-12 items-end mt-6">
            <div>
              <h1 className="text-4xl md:text-6xl xl:text-7xl font-serif leading-[.98] max-w-5xl">{cfg.title}</h1>
              <p className="mt-6 max-w-3xl text-lg md:text-xl leading-relaxed text-white/75">{cfg.intro}</p>
              <a href="#diagnostic" className="mt-8 inline-flex items-center gap-2 rounded-full px-6 py-3.5 font-semibold text-[#102945] bg-gradient-to-r from-[#f4e4bf] to-[#c99d53] shadow-lg">Parler de ma situation <ArrowRight size={16}/></a>
            </div>
            <div className="rounded-[28px] border border-white/15 bg-white/10 backdrop-blur p-6 md:p-7">
              <div className="text-xs uppercase tracking-[.2em] text-white/50">Vous vous reconnaissez ?</div>
              <div className="mt-5 space-y-4">{cfg.pain.slice(0,4).map((p)=><div key={p} className="flex gap-3"><span className="mt-2 w-1.5 h-1.5 rounded-full bg-[#f0d9a8] shrink-0"/><span className="text-white/85 text-sm leading-relaxed">{p}</span></div>)}</div>
            </div>
          </div>
        </div>
      </section>

      <section className="max-w-6xl mx-auto px-5 md:px-8 -mt-7 relative z-10">
        <div className="rounded-[28px] bg-white border border-[#e4dccd] shadow-xl p-6 md:p-8 grid md:grid-cols-3 gap-4">
          {["Vous décrivez votre situation","Nous identifions le vrai besoin","Vous recevez le prochain parcours"].map((s,i)=><div key={s} className="rounded-2xl bg-[#fbf7ef] p-5"><div className="text-xs uppercase tracking-widest text-[#9d7a43]">Étape 0{i+1}</div><div className="font-semibold mt-2 text-[#183654]">{s}</div></div>)}
        </div>
      </section>

      <section className="max-w-6xl mx-auto px-5 md:px-8 py-16 md:py-20 grid lg:grid-cols-[.9fr_1.1fr] gap-10">
        <div>
          <div className="text-xs uppercase tracking-[.22em] text-[#9d7a43]">Ce que Zayado cherche à résoudre</div>
          <h2 className="mt-3 text-3xl md:text-4xl font-serif text-[#102945]">Pas une prestation de plus. Une réponse à votre problème actuel.</h2>
          <div className="mt-7 space-y-4">{cfg.bullets.map(b=><div key={b} className="flex gap-3"><Check size={18} className="mt-1 shrink-0 text-[#aa874b]"/><span className="text-[#5f655f] leading-relaxed">{b}</span></div>)}</div>
          <div className="mt-8 rounded-[24px] bg-gradient-to-br from-[#edf2f7] to-[#f8f0e2] border border-[#dfd5c3] p-6"><div className="text-xs uppercase tracking-[.2em] text-[#8e7043]">Notre objectif</div><p className="mt-2 text-xl font-serif text-[#183654]">{cfg.promise}</p></div>
        </div>

        <div id="diagnostic" className="rounded-[30px] bg-white border border-[#e2d9c8] shadow-sm p-6 md:p-8 scroll-mt-28">
          <div className="flex items-start justify-between gap-4"><div><div className="text-xs uppercase tracking-[.22em] text-[#9d7a43]">Diagnostic de cadrage</div><h2 className="mt-2 text-2xl md:text-3xl font-serif text-[#102945]">Quelques réponses suffisent pour arrêter de tourner en rond.</h2></div><div className="text-sm font-semibold text-[#88714f]">{Math.round(progress*100)}%</div></div>
          <div className="h-2 rounded-full bg-[#eee7da] mt-5 overflow-hidden"><div className="h-full rounded-full transition-all duration-500 bg-gradient-to-r from-[#f0ddb5] to-[#b98b48]" style={{width:`${progress*100}%`}}/></div>
          <div className="mt-7 space-y-7">
            {cfg.questions.map((q)=>!answers[q.k] ? <div key={q.k}><div className="font-semibold text-[#213246] mb-3">{q.q}</div><div className="grid sm:grid-cols-2 gap-2.5">{q.opts.map(o=><button key={o} onClick={()=>setAnswers(a=>({...a,[q.k]:o}))} className="text-left rounded-2xl border border-[#e0d7c7] px-4 py-3.5 text-sm text-[#3f454b] hover:border-[#ae884d] hover:bg-[#fbf7ef] transition">{o}</button>)}</div></div> : null)}
          </div>

          {complete && <div className="mt-8 rounded-[24px] bg-gradient-to-br from-[#eef3f8] to-[#f6ede0] border border-[#ddd2bf] p-6">
            <div className="text-xs uppercase tracking-[.2em] text-[#8e7043]">Votre prochaine étape</div>
            <h3 className="mt-2 text-xl font-semibold text-[#183654]">{recommendation}</h3>
            <p className="mt-3 text-sm leading-relaxed text-[#63645f]">{cfg.result}</p>
            <div className="mt-5 flex flex-wrap gap-3"><Link to={`/contact?service=${encodeURIComponent(cfg.tag)}&source=tunnel`} className="inline-flex items-center gap-2 rounded-full px-5 py-3 text-sm font-semibold text-[#102945] bg-gradient-to-r from-[#f1dfb7] to-[#c99c51]">{cfg.cta} <ArrowRight size={15}/></Link><button onClick={()=>setAnswers({})} className="inline-flex items-center gap-2 rounded-full px-5 py-3 text-sm font-semibold text-[#5e554a] border border-[#d7ccba] bg-white">Recommencer</button></div>
          </div>}
        </div>
      </section>

      <section className="border-y border-[#e6decf] bg-white"><div className="max-w-6xl mx-auto px-5 md:px-8 py-12 grid md:grid-cols-3 gap-7"><div className="flex gap-4"><ShieldCheck className="text-[#a17c44] shrink-0" size={22}/><div><div className="font-semibold text-[#183654]">Un cadrage avant le devis</div><p className="mt-1 text-sm text-[#6b6c68]">Vous expliquez votre problème avant qu'on vous parle de prestation.</p></div></div><div className="flex gap-4"><Clock3 className="text-[#a17c44] shrink-0" size={22}/><div><div className="font-semibold text-[#183654]">Un parcours adapté</div><p className="mt-1 text-sm text-[#6b6c68]">Le bon niveau d'intervention dépend de votre situation réelle.</p></div></div><div className="flex gap-4"><MessageCircle className="text-[#a17c44] shrink-0" size={22}/><div><div className="font-semibold text-[#183654]">Zayado reste votre point d'entrée</div><p className="mt-1 text-sm text-[#6b6c68]">Quand une expertise externe est nécessaire, nous vous orientons vers le bon spécialiste.</p></div></div></div></section>

      <section className="max-w-6xl mx-auto px-5 md:px-8 py-16"><div className="rounded-[30px] bg-gradient-to-br from-[#102945] to-[#1f4a73] p-8 md:p-12 text-white flex flex-col lg:flex-row items-start lg:items-center justify-between gap-8"><div><div className="text-xs uppercase tracking-[.22em] text-[#efdbb2]">ZAYADO SERVICES</div><h2 className="mt-3 text-3xl md:text-4xl font-serif">Vous n'avez pas besoin de tout gérer seul.</h2><p className="mt-3 text-white/70 max-w-2xl">Commencez par votre problème actuel. Nous verrons ensuite si Zayado peut l'opérer directement ou s'il faut mobiliser un partenaire.</p></div><a href="#diagnostic" className="shrink-0 inline-flex items-center gap-2 rounded-full px-6 py-3.5 font-semibold text-[#102945] bg-gradient-to-r from-[#f4e4bf] to-[#c99d53]">Commencer <ArrowRight size={16}/></a></div></section>
    </main>
    <UnifiedFooter/>
  </div>
}
