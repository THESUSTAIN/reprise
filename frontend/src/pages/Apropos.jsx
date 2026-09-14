/* Page À propos /a-propos — manifeste Zayado */
import React from "react";
import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { Heart, Compass, Sparkles, Leaf, ArrowRight } from "lucide-react";
import { useWPPage, parseWPContent } from "@/lib/wpContent";

const NAVY = "var(--zayado-navy)";
const GOLD = "var(--zayado-gold)";
const GOLD_SOFT = "var(--zayado-gold-soft)";
const MUTED = "var(--zayado-muted)";

export default function Apropos() {
  const { page: wpPage } = useWPPage("a-propos");
  const wp = wpPage ? parseWPContent(wpPage.content?.rendered || "") : null;
  const heroTitle = wp?.title || "Entreprendre, <em>autrement.</em>";
  const heroSubtitle = wp?.subtitle || "Zayado est né d'un constat simple : <em>la performance ne devrait pas se faire au détriment du calme.</em> Nous accompagnons les entrepreneurs et leurs équipes à construire leur trajectoire avec lucidité.";
  return (
    <>
    <Helmet>
      <title>À propos — Zayado, entreprendre avec sens, clarté et stabilité</title>
      <meta name="description" content="Découvrez la vision de Zayado : une marketplace et un accompagnement pensés pour les indépendants et petites structures, entre performance et bien-être." />
      <link rel="canonical" href="https://zayado.net/a-propos" />
    </Helmet>
    <div className="max-w-[1100px] mx-auto px-4 md:px-6 py-12" data-testid="apropos-page">
      <section className="text-center mb-16">
        <div className="text-[11px] uppercase tracking-[0.3em] mb-3" style={{ color: GOLD }}>Notre histoire</div>
        <h1 className="font-display italic leading-[1.05] mb-6"
            style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)",
                     fontSize: "clamp(2.4rem, 6vw, 4rem)", color: "var(--zayado-text)" }}
            data-testid="apropos-title"
            dangerouslySetInnerHTML={{ __html: heroTitle }} />
        <p className="text-base md:text-xl max-w-2xl mx-auto leading-relaxed" style={{ color: MUTED }}
           data-testid="apropos-subtitle"
           dangerouslySetInnerHTML={{ __html: heroSubtitle }} />
      </section>

      <section className="grid md:grid-cols-[1.1fr_1fr] gap-8 md:gap-12 mb-16 items-center">
        <div>
          <div className="text-[11px] uppercase tracking-[0.25em] mb-2" style={{ color: GOLD }}>Le rituel</div>
          <h2 className="font-display italic mb-4"
              style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)",
                       fontSize: "clamp(1.7rem, 3.5vw, 2.6rem)", color: "var(--zayado-text)" }}>
            5 minutes pour <em>recentrer.</em>
          </h2>
          <p className="text-sm md:text-base leading-relaxed mb-4" style={{ color: MUTED }}>
            Avant la première réunion. Avant la première décision. Allumez une bougie d'intention.
            Posez vos lunettes Z-Focus. Diffusez deux gouttes d'huile essentielle. Trois gestes simples,
            validés par 1 200+ entrepreneurs accompagnés.
          </p>
          <p className="text-sm md:text-base leading-relaxed mb-5" style={{ color: MUTED }}>
            Le reste suivra. La clarté mentale ne vient pas d'une nouvelle app ou d'un nouveau process.
            Elle vient d'un cadre de vie aligné avec vos intentions.
          </p>
          {/* Stats pour remplir l'espace */}
          <div className="grid grid-cols-3 gap-4 pt-5 border-t border-[var(--zayado-border)]">
            <div>
              <div className="font-display italic text-2xl md:text-3xl mb-0.5"
                   style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)", color: NAVY }}>
                1 200+
              </div>
              <div className="text-xs" style={{ color: MUTED }}>entrepreneurs accompagnés</div>
            </div>
            <div>
              <div className="font-display italic text-2xl md:text-3xl mb-0.5"
                   style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)", color: NAVY }}>
                97%
              </div>
              <div className="text-xs" style={{ color: MUTED }}>recommandent Zayado</div>
            </div>
            <div>
              <div className="font-display italic text-2xl md:text-3xl mb-0.5"
                   style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)", color: NAVY }}>
                100%
              </div>
              <div className="text-xs" style={{ color: MUTED }}>production France & Europe</div>
            </div>
          </div>
        </div>
        <img src="https://images.unsplash.com/photo-1545389336-cf090694435e?auto=format&w=800&q=85"
             alt="Rituel matinal" className="rounded-xl aspect-[4/5] object-cover w-full" />
      </section>

      <section className="mb-16">
        <h2 className="font-display italic mb-8 text-center"
            style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)",
                     fontSize: "clamp(1.7rem, 3.5vw, 2.6rem)", color: "var(--zayado-text)" }}>
          Nos valeurs.
        </h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-5">
          {[
            { icon: Heart, title: "Lucidité", desc: "On dit la vérité, même quand elle dérange. À nos clients, à nos équipes, à nous-mêmes." },
            { icon: Compass, title: "Trajectoire", desc: "Pas de hacks. Que des décisions cohérentes avec vos intentions à 10 ans." },
            { icon: Sparkles, title: "Beauté du geste", desc: "Chaque objet, chaque mot, chaque interface est pensé pour ralentir, pas pour exciter." },
            { icon: Leaf, title: "Durabilité", desc: "Production locale, petites séries, marques familiales engagées. Pas de greenwashing." },
          ].map((v, i) => {
            const I = v.icon;
            return (
              <div key={i} className="p-5 rounded-xl border border-[var(--zayado-border)] bg-white">
                <div className="w-10 h-10 rounded-lg flex items-center justify-center mb-3"
                     style={{ background: "var(--zayado-gold-bg)", color: GOLD }}>
                  <I size={17} />
                </div>
                <h3 className="font-display text-lg mb-2" style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)", color: "var(--zayado-text)" }}>{v.title}</h3>
                <p className="text-sm leading-relaxed" style={{ color: MUTED }}>{v.desc}</p>
              </div>
            );
          })}
        </div>
      </section>

      <section className="text-center p-8 md:p-12 rounded-2xl text-white" style={{ background: NAVY }}>
        <h2 className="font-display italic mb-4"
            style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)",
                     fontSize: "clamp(1.7rem, 3.5vw, 2.6rem)" }}>
          Prêt·e à construire <em style={{ color: GOLD_SOFT }}>votre trajectoire</em> ?
        </h2>
        <div className="flex flex-wrap gap-2 justify-center mt-6">
          <Link to="/boutique" className="px-5 py-2.5 rounded-full bg-white text-[var(--zayado-navy)] font-medium text-sm">
            Découvrir la boutique <ArrowRight size={13} className="inline ml-1" />
          </Link>
          <a
            href={typeof window !== "undefined" && window.location.hostname.includes("preview.emergentagent")
              ? "/login"
              : "https://app.zayado.net/login"}
            className="px-5 py-2.5 rounded-full border border-white/40 font-medium text-sm hover:bg-white/10"
            data-testid="apropos-cta-saas"
          >
            Essayer Zayado SaaS
          </a>
        </div>
      </section>
    </div>
    </>
  );
}
