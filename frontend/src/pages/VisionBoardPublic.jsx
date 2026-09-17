import React, { useState } from "react";
import { Helmet } from "react-helmet-async";
import { Sparkles, ArrowRight, Play, AlertTriangle, Clock3, TrendingDown, HeartCrack, BookOpen, TrendingUp, GitBranch, Star } from "lucide-react";

const GRAD = { backgroundImage: "linear-gradient(135deg,#215480,#001d50)" };
const API = import.meta.env.VITE_API_URL || "";

const PAINS = [
  { icon: TrendingDown, t: "Une vision floue", d: "Vos ambitions restent dans votre tête, jamais visibles ni mesurables." },
  { icon: Clock3, t: "Zéro temps pour la poser", d: "Entre deux urgences, structurer sa vision passe toujours après." },
  { icon: HeartCrack, t: "La motivation s'essouffle", d: "Sans miroir de vos objectifs, l'élan du départ retombe vite." },
];
const PROOF = [
  { n: "5 min", l: "pour créer votre board" },
  { n: "3", l: "templates éditoriaux IA" },
  { n: "PDF", l: "flipbook + partage protégé" },
];
const TEMPLATES = [
  { id: "magazine", title: "Magazine éditorial", pitch: "Une couverture digne d'un mook : vos valeurs, votre why, vos 10 ans projetés.", icon: BookOpen },
  { id: "trajectoire", title: "Trajectoire 10 ans", pitch: "Votre projection : aujourd'hui → 1 an → 3 ans → 10 ans. Pour les ambitieux.", icon: TrendingUp },
  { id: "arbre", title: "Arbre de vie", pitch: "Racines (valeurs), tronc (mission), branches (domaines). Une visualisation organique.", icon: GitBranch },
];

function LeadForm({ testid }) {
  const [email, setEmail] = useState("");
  const enter = (e) => {
    e.preventDefault();
    try { if (email) localStorage.setItem("zay_lead_email", email); } catch { /* noop */ }
    try {
      const h = window.location.hostname;
      if (/\.preview\.emergentagent\.com$/i.test(h) || h === "localhost" || h === "127.0.0.1") {
        localStorage.setItem("zay_preview_mode", "app");
      }
    } catch { /* noop */ }
    window.location.href = "/";
  };
  return (
    <form onSubmit={enter} className="flex w-full max-w-md flex-col gap-3 sm:flex-row" data-testid={testid}>
      <input
        type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
        placeholder="Votre e-mail" data-testid={`${testid}-input`}
        className="flex-1 rounded-full border border-[#e2dac7] bg-white px-5 py-3.5 text-sm text-[#001d50] outline-none focus:border-[#215480]"
      />
      <button type="submit" data-testid={`${testid}-submit`} className="inline-flex items-center justify-center gap-2 rounded-full px-6 py-3.5 font-semibold text-white transition-transform hover:-translate-y-0.5" style={GRAD}>
        Créer mon Vision Board <ArrowRight size={18} />
      </button>
    </form>
  );
}

export default function VisionBoardPublic() {
  const previewBase = API + "/api/vision/board/preview-public?template=";
  const gif = API + "/vision-board-preview.gif";
  return (
    <div className="min-h-screen bg-white text-[#001d50]" style={{ fontFamily: "Poppins, sans-serif" }} data-testid="vb-public-page">
      <Helmet>
        <title>Vision Board IA · Donnez vie à votre vision — Zayado</title>
        <meta name="description" content="Créez votre Vision Board en 5 minutes. 3 templates éditoriaux générés par IA. PDF flipbook + partage." />
      </Helmet>

      {/* Header minimal */}
      <header className="sticky top-0 z-40 border-b border-[#efe7d8] bg-white/85 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4">
          <a href="/" className="text-xl font-bold tracking-tight" data-testid="vb-logo">Zayado</a>
          <a href="#creer" className="rounded-full px-5 py-2.5 text-sm font-semibold text-white" style={GRAD} data-testid="vb-header-cta">Commencer</a>
        </div>
      </header>

      {/* Hero VSL */}
      <section className="relative overflow-hidden">
        <div className="pointer-events-none absolute -top-24 right-0 h-80 w-80 rounded-full opacity-20 blur-3xl" style={GRAD} />
        <div className="mx-auto grid max-w-6xl items-center gap-12 px-5 pt-14 pb-12 sm:pt-20 lg:grid-cols-[1fr_1fr]">
          <div>
            <span className="block leading-none text-[#215480]" style={{ fontFamily: "Corinthia, cursive", fontSize: "2.8rem" }} data-testid="vb-eyebrow">
              donnez vie à votre vision
            </span>
            <h1 className="mt-2 text-4xl font-normal leading-[1.05] sm:text-5xl" style={{ fontFamily: "Fraunces, serif" }} data-testid="vb-title">
              Votre Vision Board, généré par l'IA en 5 minutes.
            </h1>
            <p className="mt-5 max-w-xl text-base leading-relaxed text-[#41506a] sm:text-lg">
              Répondez à quelques questions : l'IA transforme votre mission, vos valeurs et votre projection en un board éditorial professionnel. Regardez la démo (90 s), puis créez le vôtre.
            </p>
            <div id="creer" className="mt-8"><LeadForm testid="vb-lead-hero" /></div>
            <p className="mt-2 text-xs text-[#7a869c]">Sans carte bancaire · votre e-mail sert à sauvegarder votre board.</p>
          </div>

          {/* Vidéo / GIF de démo */}
          <div className="relative" data-testid="vb-hero-video">
            <div className="relative overflow-hidden rounded-3xl border border-[#efe7d8] shadow-[0_30px_60px_rgba(0,29,80,.18)]">
              <img
                src={gif}
                onError={(e) => { e.currentTarget.src = "https://images.pexels.com/photos/6931845/pexels-photo-6931845.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=720&w=1040"; }}
                alt="Aperçu animé du Vision Board Zayado" className="h-full w-full object-cover" data-testid="vb-hero-image"
              />
              <div className="absolute inset-0" style={{ background: "linear-gradient(180deg, rgba(0,29,80,.05), rgba(0,29,80,.5))" }} />
              <span className="absolute inset-0 grid place-items-center">
                <span className="grid h-16 w-16 place-items-center rounded-full bg-white/90 text-[#001d50] shadow-xl">
                  <Play size={26} className="ml-1" fill="currentColor" />
                </span>
              </span>
              <span className="absolute bottom-3 left-3 rounded-full bg-[#001d50]/85 px-3 py-1 text-xs font-semibold text-white backdrop-blur">Présentation du Vision Board · 90s</span>
            </div>
          </div>
        </div>
      </section>

      {/* Douleur */}
      <section className="border-y border-[#efe7d8]" style={{ background: "#f8f3eb" }} data-testid="vb-pain">
        <div className="mx-auto max-w-6xl px-5 py-14">
          <div className="mb-3 inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-bold uppercase tracking-wider text-white" style={{ background: "#a10e10" }}>
            <AlertTriangle size={14} /> Le vrai problème
          </div>
          <h2 className="max-w-2xl text-2xl font-normal leading-tight sm:text-3xl" style={{ fontFamily: "Fraunces, serif" }}>
            Vous avez la vision. Il vous manque le support qui la rend réelle.
          </h2>
          <div className="mt-8 grid gap-5 md:grid-cols-3">
            {PAINS.map((p) => (
              <div key={p.t} className="rounded-2xl border border-[#e9dcc4] bg-white p-6 shadow-[0_12px_30px_rgba(0,29,80,.06)]">
                <span className="grid h-11 w-11 place-items-center rounded-xl text-white" style={{ background: "#a10e10" }}><p.icon size={20} /></span>
                <h3 className="mt-4 text-lg font-semibold" style={{ fontFamily: "Fraunces, serif" }}>{p.t}</h3>
                <p className="mt-2 text-sm leading-relaxed text-[#41506a]">{p.d}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Preuve / chiffres */}
      <section className="mx-auto max-w-6xl px-5 py-12">
        <div className="grid gap-4 sm:grid-cols-3">
          {PROOF.map((s) => (
            <div key={s.l} className="rounded-2xl border border-[#efe7d8] bg-white p-6 text-center shadow-[0_12px_30px_rgba(0,29,80,.06)]">
              <div className="text-3xl font-black" style={{ color: "#215480", fontFamily: "Fraunces, serif" }}>{s.n}</div>
              <div className="mt-1 text-sm text-[#41506a]">{s.l}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Templates (preuve visuelle) */}
      <section id="templates" className="mx-auto max-w-6xl px-5 pb-12">
        <span className="text-sm font-semibold uppercase tracking-wider text-[#215480]">3 templates éditoriaux</span>
        <h2 className="mt-2 text-2xl font-normal sm:text-3xl" style={{ fontFamily: "Fraunces, serif" }}>Choisissez le style qui vous ressemble.</h2>
        <div className="mt-8 space-y-10">
          {TEMPLATES.map((t, idx) => (
            <article key={t.id} className="overflow-hidden rounded-3xl border border-[#efe7d8] bg-white shadow-[0_12px_30px_rgba(0,29,80,.06)]" data-testid={`vb-template-${t.id}`}>
              <div className={`grid gap-0 lg:grid-cols-12 ${idx % 2 ? "lg:[direction:rtl]" : ""}`}>
                <div className="lg:col-span-7 [direction:ltr]" style={{ background: "#f8f3eb", padding: "1.5rem" }}>
                  <div className="relative mx-auto aspect-[1.41/1] w-full max-w-[640px] overflow-hidden rounded-2xl bg-white shadow-2xl">
                    <iframe src={previewBase + t.id} title={`Aperçu ${t.title}`} loading="lazy"
                      className="border-0 pointer-events-none" data-testid={`vb-iframe-${t.id}`}
                      style={{ transform: "scale(0.75)", transformOrigin: "top left", width: "133.33%", height: "133.33%" }} />
                  </div>
                </div>
                <div className="flex flex-col justify-center p-8 lg:col-span-5 [direction:ltr]">
                  <span className="grid h-12 w-12 place-items-center rounded-2xl text-white" style={GRAD}><t.icon size={22} /></span>
                  <div className="mt-4 text-xs font-bold uppercase tracking-wider text-[#215480]">Template · 0{idx + 1}</div>
                  <h3 className="mt-1 text-2xl font-semibold" style={{ fontFamily: "Fraunces, serif" }}>{t.title}</h3>
                  <p className="mt-2 text-[#41506a]">{t.pitch}</p>
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>

      {/* Témoignage + CTA final */}
      <section className="px-5 pb-20">
        <div className="mx-auto max-w-6xl rounded-[34px] p-10 text-white sm:p-14" style={GRAD} data-testid="vb-final-cta">
          <div className="mb-4 flex items-center gap-1 text-[#f8f3eb]">
            {[0,1,2,3,4].map((i) => <Star key={i} size={16} fill="currentColor" />)}
            <span className="ml-2 text-sm text-white/80">Adoré par les entrepreneurs visionnaires</span>
          </div>
          <h2 className="max-w-2xl text-3xl font-normal sm:text-4xl" style={{ fontFamily: "Fraunces, serif" }}>
            Votre premier Vision Board vous attend.
          </h2>
          <p className="mt-3 max-w-md text-white/85"><Sparkles size={16} className="mr-1 inline" /> 5 minutes suffisent. Entrez votre e-mail et lancez-vous.</p>
          <div className="mt-7"><LeadForm testid="vb-lead-final" /></div>
        </div>
      </section>

      <footer className="border-t border-[#efe7d8] py-8 text-center text-sm text-[#7a869c]">
        © {new Date().getFullYear()} Zayado — l'écosystème qui agit pour vous.
      </footer>
    </div>
  );
}
