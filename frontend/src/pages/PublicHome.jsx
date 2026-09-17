import React from "react";
import { Link } from "react-router-dom";
import { Sparkles, Compass, Brain, ArrowRight, AlertTriangle, Clock3, TrendingDown, HeartCrack, Play } from "lucide-react";

const GRAD = { backgroundImage: "linear-gradient(135deg,#215480,#001d50)" };

const pains = [
  { icon: TrendingDown, t: "Vous avancez sans cap clair", d: "Les objectifs se diluent dans l'urgence quotidienne. Impossible de voir si vous progressez vraiment." },
  { icon: Clock3, t: "Vous perdez des heures en dispersion", d: "Outils éparpillés, relances, décisions reportées : votre énergie fuit dans l'exécution." },
  { icon: HeartCrack, t: "La motivation retombe, seul·e", d: "Sans rituel ni miroir de vos ambitions, l'élan du départ s'essouffle en quelques semaines." },
];

const modules = [
  { icon: Compass, t: "Vision Board", d: "Ancrez vos ambitions dans une planche vivante — vos objectifs deviennent visibles, mesurables, motivants.", to: "/vision-board", cta: "Activer mon Vision Board" },
  { icon: Brain, t: "Copilote IA", d: "Un copilote qui transforme vos intentions en actions concrètes, chaque jour, avec vous.", to: "/vision-board", cta: "Découvrir le Copilote" },
];

export default function PublicHome() {
  return (
    <div className="min-h-screen bg-white text-[#001d50]" style={{ fontFamily: "Poppins, sans-serif" }}>
      {/* Header */}
      <header className="sticky top-0 z-40 border-b border-[#efe7d8] bg-white/85 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4">
          <span className="text-xl font-bold tracking-tight" data-testid="public-logo">Zayado</span>
          <Link to="/vision-board" data-testid="header-cta" className="rounded-full px-5 py-2.5 text-sm font-semibold text-white" style={GRAD}>Commencer</Link>
        </div>
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="pointer-events-none absolute -top-24 right-0 h-80 w-80 rounded-full opacity-20 blur-3xl" style={GRAD} />
        <div className="mx-auto grid max-w-6xl items-center gap-12 px-5 pt-16 pb-14 sm:pt-24 lg:grid-cols-[1.05fr_0.95fr]">
          <div>
            <span className="block leading-none text-[#215480]" style={{ fontFamily: "Corinthia, cursive", fontSize: "2.8rem" }} data-testid="hero-eyebrow">
              votre vie, enfin alignée
            </span>
            <h1 className="mt-2 max-w-3xl text-4xl font-normal leading-[1.05] sm:text-5xl lg:text-6xl" style={{ fontFamily: "Fraunces, serif" }} data-testid="hero-title">
              Reprenez le contrôle de vos ambitions.
            </h1>
            <p className="mt-6 max-w-xl text-base leading-relaxed text-[#41506a] sm:text-lg">
              Zayado relie votre vision, vos décisions et votre exécution en un seul écosystème piloté par l'IA. Fini la dispersion — place à l'élan.
            </p>
            <div className="mt-9 flex flex-wrap gap-3">
              <Link to="/vision-board" data-testid="hero-primary-cta" className="inline-flex items-center gap-2 rounded-full px-6 py-3.5 font-semibold text-white transition-transform hover:-translate-y-0.5" style={GRAD}>
                Activer mon Vision Board <ArrowRight size={18} />
              </Link>
              <a href="#modules" data-testid="hero-secondary-cta" className="inline-flex items-center gap-2 rounded-full border-[1.5px] bg-white px-6 py-3.5 font-semibold text-[#001d50]" style={{ borderColor: "#e7dcc5" }}>
                Voir comment ça marche
              </a>
            </div>
          </div>

          {/* Aperçu vidéo (style VSL) — remplaçable par un vrai gif/vidéo du Vision Board */}
          <div className="relative" data-testid="hero-video">
            <div className="relative overflow-hidden rounded-3xl border border-[#efe7d8] shadow-[0_30px_60px_rgba(0,29,80,.18)]">
              <img
                src="https://images.pexels.com/photos/6931845/pexels-photo-6931845.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=720&w=1040"
                alt="Aperçu du Vision Board Zayado"
                className="h-full w-full object-cover"
                data-testid="hero-image"
              />
              <div className="absolute inset-0" style={{ background: "linear-gradient(180deg, rgba(0,29,80,.05), rgba(0,29,80,.5))" }} />
              <button className="absolute inset-0 grid place-items-center" aria-label="Lire la présentation" data-testid="hero-play">
                <span className="grid h-16 w-16 place-items-center rounded-full bg-white/90 text-[#001d50] shadow-xl transition-transform hover:scale-110">
                  <Play size={26} className="ml-1" fill="currentColor" />
                </span>
              </button>
              <span className="absolute bottom-3 left-3 rounded-full bg-[#001d50]/85 px-3 py-1 text-xs font-semibold text-white backdrop-blur">
                Présentation du Vision Board · 90s
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* PAIN — section mise en évidence */}
      <section className="border-y border-[#efe7d8]" style={{ background: "#f8f3eb" }} data-testid="pain-section">
        <div className="mx-auto max-w-6xl px-5 py-16">
          <div className="mb-3 inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-bold uppercase tracking-wider text-white" style={{ background: "#a10e10" }}>
            <AlertTriangle size={14} /> Le vrai problème
          </div>
          <h2 className="max-w-2xl text-2xl font-normal leading-tight sm:text-3xl" style={{ fontFamily: "Fraunces, serif" }}>
            Ce n'est pas le manque d'ambition. C'est le manque d'un système qui la porte.
          </h2>
          <div className="mt-10 grid gap-5 md:grid-cols-3">
            {pains.map((p) => (
              <div key={p.t} className="rounded-2xl border border-[#e9dcc4] bg-white p-6 shadow-[0_12px_30px_rgba(0,29,80,.06)]">
                <span className="grid h-11 w-11 place-items-center rounded-xl text-white" style={{ background: "#a10e10" }}>
                  <p.icon size={20} />
                </span>
                <h3 className="mt-4 text-lg font-semibold" style={{ fontFamily: "Fraunces, serif" }}>{p.t}</h3>
                <p className="mt-2 text-sm leading-relaxed text-[#41506a]">{p.d}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Modules mis en évidence */}
      <section id="modules" className="mx-auto max-w-6xl px-5 py-16" data-testid="modules-section">
        <span className="text-sm font-semibold uppercase tracking-wider text-[#215480]">La solution</span>
        <h2 className="mt-2 max-w-2xl text-2xl font-normal sm:text-3xl" style={{ fontFamily: "Fraunces, serif" }}>
          Deux piliers pour transformer l'intention en résultats.
        </h2>
        <div className="mt-10 grid gap-6 md:grid-cols-2">
          {modules.map((m) => (
            <div key={m.t} className="group rounded-3xl border border-[#efe7d8] bg-white p-8 shadow-[0_12px_30px_rgba(0,29,80,.06)] transition-transform hover:-translate-y-1">
              <span className="grid h-12 w-12 place-items-center rounded-2xl text-white" style={GRAD}>
                <m.icon size={22} />
              </span>
              <h3 className="mt-5 text-xl font-semibold" style={{ fontFamily: "Fraunces, serif" }}>{m.t}</h3>
              <p className="mt-2 text-[#41506a]">{m.d}</p>
              <Link to={m.to} className="mt-6 inline-flex items-center gap-2 font-semibold text-[#215480]">
                {m.cta} <ArrowRight size={16} className="transition-transform group-hover:translate-x-1" />
              </Link>
            </div>
          ))}
        </div>
      </section>

      {/* CTA final */}
      <section className="px-5 pb-20">
        <div className="mx-auto max-w-6xl rounded-[34px] p-10 text-white sm:p-14" style={GRAD} data-testid="final-cta">
          <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-white/80">
            <Sparkles size={16} /> Prêt·e à changer de trajectoire ?
          </div>
          <h2 className="mt-3 max-w-2xl text-3xl font-normal sm:text-4xl" style={{ fontFamily: "Fraunces, serif" }}>
            Votre première victoire commence aujourd'hui.
          </h2>
          <Link to="/vision-board" className="mt-8 inline-flex items-center gap-2 rounded-full border-[1.5px] bg-white px-7 py-3.5 font-semibold text-[#001d50]" style={{ borderColor: "#e7dcc5" }}>
            Activer mon Vision Board <ArrowRight size={18} />
          </Link>
        </div>
      </section>

      <footer className="border-t border-[#efe7d8] py-8 text-center text-sm text-[#7a869c]">
        © {new Date().getFullYear()} Zayado — l'écosystème qui agit pour vous.
      </footer>
    </div>
  );
}
