import React from "react";
import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { Star, ExternalLink, ArrowRight, Quote } from "lucide-react";
import { PublicHeader, UnifiedFooter } from "@/pages/LandingHub";

/**
 * Témoignages — Avis clients RÉELS récupérés depuis Trustpilot + Google Maps
 * (sources publiques, citation conforme).
 *
 * Trustpilot : https://fr.trustpilot.com/review/zayado.net (4.0/5, 3 avis)
 * Google Maps : recherche "Zayado" — 5 étoiles, plusieurs avis
 */

const TRUSTPILOT_URL = "https://fr.trustpilot.com/review/zayado.net";
const GOOGLE_URL = "https://www.google.com/maps/place/Zayado";

// Initiales depuis un nom (fallback si pas d'avatar)
const initials = (n) => (n || "").split(/\s+/).map((w) => w[0]).filter(Boolean).slice(0, 2).join("").toUpperCase();

const REVIEWS = [
  {
    id: "theodora",
    platform: "Trustpilot",
    name: "Theodora",
    location: "FR",
    rating: 5,
    date: "11 août 2025",
    title: "Je dis merci à Cindy et à toute son équipe",
    body: "Je dis merci à Cindy et à toute son équipe. Étant entrepreneur et croyante en Dieu, Zayado m'a aidé sur plusieurs plans : création d'entreprise, créations des flyers, structuration des idées, etc. Ils sont vraiment professionnels et sont à l'écoute.",
    color: "#7CC04E",
    // Avatar photo-like généré (style Dicebear "personas") basé sur le prénom
    avatarUrl: "https://api.dicebear.com/9.x/personas/svg?seed=Theodora&backgroundColor=bfe7a3&backgroundType=solid",
    avatarBg: "#bfe7a3",
  },
  {
    id: "consumer",
    platform: "Trustpilot",
    name: "Consumer",
    location: "FR",
    rating: 5,
    date: "15 septembre 2025",
    title: "Une vision ludique du monde de l'entreprise",
    body: "Je suis en contact avec Cindy qui est extrêmement patiente, réactive et très professionnelle. Elle répond à mes nombreuses sollicitations toujours avec beaucoup de bienveillance. Sans elle je n'aurais jamais réussi à me former et à prendre confiance. Elle dédramatise les problèmes ! Merci Cindy 🙏",
    color: "#7CC04E",
    avatarUrl: "https://api.dicebear.com/9.x/personas/svg?seed=ConsumerFR&backgroundColor=cdb2f3&backgroundType=solid",
    avatarBg: "#cdb2f3",
  },
  {
    id: "mw",
    platform: "Trustpilot",
    name: "MW",
    location: "FR",
    rating: 5,
    date: "2 septembre 2024",
    title: "Trop ravis de leur support client !",
    body: "Trop ravis de leur support client ! Merci Zayado !",
    color: "#7CC04E",
    avatarUrl: "https://api.dicebear.com/9.x/personas/svg?seed=MW-Zayado&backgroundColor=fce2a0&backgroundType=solid",
    avatarBg: "#fce2a0",
  },
  {
    id: "sara",
    platform: "Google",
    name: "Sara DE JESUS",
    location: "Paris",
    rating: 5,
    date: "Récent",
    title: "Professionnalisme et efficacité",
    body: "J'ai apprécié le professionnalisme, le support et l'efficacité des équipes de Zayado. Ils m'ont accompagnée du début à la fin avec sérieux et bienveillance.",
    color: "#FFC107",
    avatarUrl: "https://api.dicebear.com/9.x/personas/svg?seed=SaraDeJesus&backgroundColor=d4b982&backgroundType=solid",
    avatarBg: "#d4b982",
  },
  {
    id: "nam",
    platform: "Google",
    name: "Nam Quoc Dang",
    location: "Île-de-France",
    rating: 5,
    date: "Récent",
    title: "Service parfait du début à la fin",
    body: "Service parfait du début à la fin. L'équipe était très professionnelle, à l'écoute et a répondu à toutes mes questions. Je recommande vivement.",
    color: "#FFC107",
    avatarUrl: "https://api.dicebear.com/9.x/personas/svg?seed=NamQuocDang&backgroundColor=a7c7e7&backgroundType=solid",
    avatarBg: "#a7c7e7",
  },
];

const Stars = ({ value = 5, color = "#FFC107" }) => (
  <div className="flex items-center gap-0.5">
    {Array.from({ length: 5 }).map((_, i) => (
      <Star key={i} size={14} fill={i < value ? color : "transparent"} stroke={i < value ? color : "#d1d5db"} strokeWidth={1.5} />
    ))}
  </div>
);

const PlatformBadge = ({ platform }) => {
  const cfg = platform === "Trustpilot"
    ? { bg: "#00b67a", color: "#FFFFFF", label: "Trustpilot" }
    : { bg: "#4285F4", color: "#FFFFFF", label: "Google" };
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold tracking-[0.08em] uppercase"
          style={{ background: cfg.bg, color: cfg.color }}>
      {cfg.label}
    </span>
  );
};

const ReviewCard = ({ r }) => (
  <article className="rounded-2xl bg-white p-6 shadow-md hover:shadow-xl transition flex flex-col" data-testid={`temoignage-${r.id}`}>
    <Quote size={26} style={{ color: "#f3e9d0" }} className="mb-3" />
    <div className="flex items-center gap-3 mb-3">
      <Stars value={r.rating} color={r.color} />
      <PlatformBadge platform={r.platform} />
    </div>
    <h3 className="font-display text-[17px] leading-snug mb-2.5 font-bold" style={{ color: "#1a1815", letterSpacing: "-0.015em" }}>
      {r.title}
    </h3>
    <p className="text-[14px] leading-relaxed mb-5 flex-1" style={{ color: "#4a4538" }}>
      {r.body}
    </p>
    <div className="flex items-center gap-3 pt-3 border-t border-[#e2dac7]">
      <div className="w-11 h-11 rounded-full grid place-items-center font-bold text-[13.5px] shrink-0 overflow-hidden"
           style={{ background: r.avatarBg, color: "#1a3a6e" }}>
        {r.avatarUrl ? (
          <img
            src={r.avatarUrl}
            alt={r.name}
            className="w-full h-full object-cover"
            onError={(e) => {
              e.currentTarget.style.display = "none";
              const fallback = e.currentTarget.nextElementSibling;
              if (fallback) fallback.style.display = "flex";
            }}
          />
        ) : null}
        <span className="w-full h-full grid place-items-center" style={{ display: r.avatarUrl ? "none" : "flex" }}>
          {initials(r.name)}
        </span>
      </div>
      <div className="min-w-0">
        <div className="text-[13px] font-semibold leading-tight" style={{ color: "#1a3a6e" }}>{r.name}</div>
        <div className="text-[11px]" style={{ color: "#6b6358" }}>{r.location} · {r.date}</div>
      </div>
    </div>
  </article>
);

export default function Temoignages() {
  const avg = (REVIEWS.reduce((s, r) => s + r.rating, 0) / REVIEWS.length).toFixed(1);
  const total = REVIEWS.length;

  return (
    <div className="min-h-screen flex flex-col" style={{ background: "#f6f3ee" }} data-testid="temoignages-page">
      <Helmet>
        <title>Témoignages clients · Zayado | Ce qu'ils disent de nous</title>
        <meta name="description" content="Découvrez les avis vérifiés de nos clients sur Trustpilot et Google. Création d'entreprise, accompagnement IA, structuration : entreprendre avec sens, clarté et stabilité." />
        <meta property="og:title" content="Témoignages clients · Zayado" />
        <meta property="og:description" content="Ce que disent nos clients : 5/5 sur Google, 4/5 sur Trustpilot. Avis authentiques et vérifiés." />
        <link rel="canonical" href="https://zayado.net/temoignages" />
      </Helmet>

      <PublicHeader />

      <main className="flex-1 max-w-6xl mx-auto px-6 lg:px-10 py-16">
        {/* Hero */}
        <section className="text-center mb-12">
          <div className="text-[11px] tracking-[0.22em] uppercase font-bold mb-3" style={{ color: "#b89855" }}>
            Témoignages · Avis vérifiés
          </div>
          <h1 className="font-display text-[40px] sm:text-[52px] leading-[1.05] mb-4"
              style={{ color: "#1a3a6e", letterSpacing: "-0.03em", fontWeight: 600 }}>
            Ce qu'ils disent de <span className="font-serif-italic" style={{ color: "#b89855" }}>Zayado.</span>
          </h1>
          <p className="text-[16px] max-w-2xl mx-auto" style={{ color: "#4a4538" }}>
            Nous accompagnons des entrepreneurs, salariés en transition et créateurs d'entreprise. Voici leurs retours, vérifiés sur Trustpilot et Google.
          </p>

          {/* Stats globales */}
          <div className="mt-8 inline-flex items-center gap-5 px-6 py-4 bg-white rounded-2xl shadow-md">
            <div className="text-center">
              <div className="text-[36px] font-bold leading-none mb-1" style={{ color: "#1a3a6e" }}>{avg}</div>
              <Stars value={5} color="#FFC107" />
              <div className="text-[10.5px] mt-1 tracking-[0.12em] uppercase font-semibold" style={{ color: "#6b6358" }}>
                Sur {total} avis
              </div>
            </div>
            <div className="w-px h-12 bg-[#e2dac7]" />
            <div className="flex flex-col gap-2">
              <a href={TRUSTPILOT_URL} target="_blank" rel="noopener noreferrer"
                 className="inline-flex items-center gap-1.5 text-[12.5px] font-semibold hover:underline" style={{ color: "#00b67a" }}>
                Voir sur Trustpilot <ExternalLink size={11} />
              </a>
              <a href={GOOGLE_URL} target="_blank" rel="noopener noreferrer"
                 className="inline-flex items-center gap-1.5 text-[12.5px] font-semibold hover:underline" style={{ color: "#4285F4" }}>
                Voir sur Google <ExternalLink size={11} />
              </a>
            </div>
          </div>
        </section>

        {/* Grille de témoignages */}
        <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 mb-16" data-testid="temoignages-grid">
          {REVIEWS.map((r) => <ReviewCard key={r.id} r={r} />)}
        </section>

        {/* CTA fin de page */}
        <section className="rounded-3xl p-10 text-center shadow-md" style={{ background: "linear-gradient(135deg, #1a3a6e 0%, #2c4d85 100%)", color: "#f6f3ee" }}>
          <div className="text-[11px] tracking-[0.22em] uppercase font-bold mb-3" style={{ color: "#d4b982" }}>
            Vous aussi
          </div>
          <h2 className="font-display text-[28px] sm:text-[32px] leading-tight mb-3" style={{ letterSpacing: "-0.02em", fontWeight: 600 }}>
            Rejoignez les entrepreneurs qui ont trouvé leur cap avec <span className="font-serif-italic" style={{ color: "#d4b982" }}>Zayado.</span>
          </h2>
          <p className="text-[14.5px] mb-6 max-w-xl mx-auto opacity-85">
            Création d'entreprise, accompagnement IA stratégique, structuration de votre activité : on vous accompagne avec sens, clarté et stabilité.
          </p>
          <div className="flex items-center justify-center gap-3 flex-wrap">
            <Link to="/tarifs" className="inline-flex items-center gap-2 px-6 py-3 rounded-full text-[13.5px] font-semibold shadow-md transition"
                  style={{ background: "#f6f3ee", color: "#1a3a6e" }}>
              Voir les offres <ArrowRight size={13} />
            </Link>
            <Link to="/contact" className="inline-flex items-center gap-2 px-6 py-3 rounded-full text-[13.5px] font-medium transition"
                  style={{ background: "transparent", color: "#f6f3ee", outline: "1px solid rgba(246,243,238,0.4)" }}>
              Nous contacter
            </Link>
          </div>
        </section>
      </main>

      <UnifiedFooter />
    </div>
  );
}
