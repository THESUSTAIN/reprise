/**
 * /tester-son-projet — Page conversion : score audit projet entrepreneurial.
 */
import React, { useState } from "react";
import api, { SAAS_URL } from "@/lib/api";
import { Helmet } from "react-helmet-async";
import { Sparkles, CheckCircle2, XCircle, ArrowRight, BarChart3, Brain, Target } from "lucide-react";
import ZayadoLayout from "@/components/ZayadoLayout";



const QUESTIONS = [
  { id: "q1", label: "Mon projet a déjà 3 clients payants" },
  { id: "q2", label: "J'ai validé mon positionnement en parlant à 10 prospects" },
  { id: "q3", label: "Je sais qui est mon client idéal (persona précis)" },
  { id: "q4", label: "J'ai une offre claire avec un prix défini" },
  { id: "q5", label: "Je travaille moins de 50h/semaine" },
  { id: "q6", label: "Mon revenu mensuel est prévisible" },
];

export default function TesterSonProjet() {
  const [answers, setAnswers] = useState({});
  const [submitted, setSubmitted] = useState(false);

  // Envoyer le score à Brevo (lead capture) si >= 60
  const captureLeadIfReady = async (score) => {
    if (score < 60 || submitted) return;
    setSubmitted(true);
    try {
      await api.post("/contact/send", {
        subject: "Audit projet public",
        message: `Score: ${score}/100 — Profil Zayado public`,
        source: "tester-son-projet",
        score,
      });
    } catch { /* silencieux */ }
  };
  const score = Object.values(answers).filter(Boolean).length;
  const total = QUESTIONS.length;
  const pct = Math.round((score / total) * 100);
  const verdict = pct >= 70 ? "Croissance" : pct >= 40 ? "Validation" : "Idéation";
  const verdictColor = pct >= 70 ? "#1f6c3a" : pct >= 40 ? "#8a6b06" : "#a01722";

  return (
    <ZayadoLayout>
      <div data-testid="audit-conversion">
      <Helmet>
        <title>Tester son projet entrepreneurial — Audit IA gratuit | Zayado</title>
        <meta name="description" content="Évaluez la maturité de votre projet en 2 minutes. Score IA, recommandations personnalisées, prochaines étapes. Gratuit." />
        <link rel="canonical" href="https://zayado.net/tester-son-projet" />
      </Helmet>

      <section className="relative overflow-hidden" style={{background: "var(--zayado-navy-gradient)"}}>
        <div className="relative max-w-5xl mx-auto px-6 lg:px-10 py-16 md:py-20 text-cream text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-cream/10 backdrop-blur border border-cream/20 text-[11px] uppercase tracking-[0.25em] mb-6 text-gold-soft">
            <Sparkles className="w-3 h-3" /> Audit IA · 100% gratuit
          </div>
          <h1 className="font-display italic leading-[1.05] mb-5" style={{fontSize: "clamp(2.2rem, 5.5vw, 3.8rem)"}}>
            Testez votre projet en <em className="text-gold-soft not-italic font-display italic">2 minutes</em>.
          </h1>
          <p className="text-base md:text-lg text-cream/85 max-w-2xl mx-auto">
            6 questions. Un score business. Des recommandations IA personnalisées sur les <b>3 prochaines étapes prioritaires</b> de votre trajectoire.
          </p>
        </div>
      </section>

      <section className="py-16" data-testid="audit-form">
        <div className="max-w-3xl mx-auto px-6">
          <div className="bg-white border border-outline rounded-3xl p-8 md:p-10">
            <div className="text-xs uppercase tracking-[0.18em] text-aubergine/70 mb-2">Étape 1 · Diagnostic</div>
            <h2 className="font-display italic mb-6" style={{fontSize: "clamp(1.4rem, 2.5vw, 2rem)", color: "var(--zayado-text)"}}>
              Cochez ce qui est <em className="text-aubergine">déjà vrai</em>.
            </h2>
            <div className="space-y-3 mb-8">
              {QUESTIONS.map((q) => {
                const checked = !!answers[q.id];
                return (
                  <button
                    key={q.id}
                    onClick={() => setAnswers({...answers, [q.id]: !checked})}
                    data-testid={`audit-${q.id}`}
                    className={`w-full flex items-center gap-3 p-4 rounded-xl border text-left transition ${checked ? "border-aubergine bg-aubergine/5" : "border-outline bg-white hover:border-aubergine/30"}`}
                  >
                    {checked ? <CheckCircle2 className="w-5 h-5 text-aubergine shrink-0" /> : <div className="w-5 h-5 rounded-full border-2 border-outline shrink-0" />}
                    <span className="text-sm text-ink">{q.label}</span>
                  </button>
                );
              })}
            </div>

            {/* Result preview */}
            <div className="bg-canvasSoft border border-outline rounded-2xl p-6">
              <div className="flex items-baseline justify-between mb-3">
                <div>
                  <div className="text-xs uppercase tracking-wider text-inkMuted">Votre score</div>
                  <div className="font-display italic text-4xl text-ink mt-1">{pct}<span className="text-xl text-inkMuted">/100</span></div>
                </div>
                <div className="text-right">
                  <div className="text-xs uppercase tracking-wider text-inkMuted">Phase</div>
                  <div className="text-lg font-medium mt-1" style={{color: verdictColor}}>{verdict}</div>
                </div>
              </div>
              <div className="h-2 bg-white rounded-full overflow-hidden mb-4">
                <div className="h-full transition-all" style={{width: `${pct}%`, background: verdictColor}} />
              </div>
              <p className="text-sm text-ink/80 leading-relaxed">
                {pct >= 70 && "Vous êtes en phase Croissance. L'IA Zayado vous aidera à industrialiser ce qui fonctionne et à scaler sans vous brûler."}
                {pct < 70 && pct >= 40 && "Vous êtes en phase Validation. L'IA Zayado vous guidera sur les 3 priorités à valider avant d'investir plus."}
                {pct < 40 && "Vous êtes en phase Idéation. L'IA Zayado vous aidera à structurer votre vision et tester rapidement vos hypothèses."}
              </p>
            </div>

            <div className="mt-6 text-center">
              <a href={`${SAAS_URL}/login?next=/app/tester-mon-projet&score=${pct}`} data-testid="audit-cta-unlock" className="inline-flex items-center gap-2 px-7 py-3.5 rounded-full bg-aubergine text-cream font-medium text-sm hover:bg-aubergine-deep transition">
                <Brain className="w-4 h-4" /> Débloquer mon plan d&apos;action IA personnalisé
              </a>
              <p className="text-xs text-inkMuted mt-3">Essai gratuit · Sans CB · Annulable en 1 clic</p>
            </div>
          </div>

          {/* What you get */}
          <div className="mt-10 grid sm:grid-cols-3 gap-4">
            {[
              { icon: BarChart3, title: "Score détaillé", desc: "5 piliers : demande, marge, énergie, récurrence, notoriété" },
              { icon: Target, title: "3 prochaines actions", desc: "Personnalisées par l'IA selon votre phase" },
              { icon: Brain, title: "Roadmap 90 jours", desc: "Étapes hebdomadaires actionnables" },
            ].map((b, i) => (
              <div key={i} className="bg-white border border-outline rounded-2xl p-5">
                <b.icon className="w-5 h-5 text-aubergine mb-3" />
                <div className="font-medium text-ink text-sm mb-1">{b.title}</div>
                <div className="text-xs text-inkMuted">{b.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      </div>
    </ZayadoLayout>
  );
}
