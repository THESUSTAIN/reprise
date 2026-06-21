import React from "react";
import { useNavigate } from "react-router-dom";
import { Target, ClipboardList, Rocket, BarChart3, ArrowRight, Bell, Megaphone } from "lucide-react";
import { DASH } from "@fm/constants/testIds";

/**
 * Pillar cards — restored to original mockup style:
 *   - Cream/white background
 *   - LEFT column: eyebrow + icon, big serif number, body text, footer pill
 *   - RIGHT column: a small image (zen stone for Vision, dried plant for Missions, etc.)
 * The image only occupies a narrow strip on the right side of the card.
 */

const ART = {
  vision:    "linear-gradient(135deg, #E8D8B8 0%, #C9B58A 100%)",
  missions:  "linear-gradient(135deg, #C8D5BB 0%, #8FA68E 100%)",
  dev:       "linear-gradient(135deg, #D9C7A8 0%, #B89A6F 100%)",
  pilotage:  "linear-gradient(135deg, #BFC9D6 0%, #7A8AA0 100%)",
};

function FooterLink({ children, testId, to }) {
  const navigate = useNavigate();
  return (
    <button
      data-testid={testId}
      onClick={() => to && navigate(to)}
      className="group mt-5 inline-flex items-center justify-between gap-2 px-5 h-12 rounded-2xl bg-cream-soft hover:bg-sand-200 text-navy text-[14px] font-semibold transition-all"
    >
      {children}
      <ArrowRight
        size={16}
        strokeWidth={2.2}
        className="transition-transform group-hover:translate-x-0.5"
      />
    </button>
  );
}

/**
 * CardShell: 2-column layout with text on left and image strip on right
 */
function CardShell({ icon: Icon, eyebrow, image, children, footer, delay }) {
  return (
    <div
      className="card-cream overflow-hidden flex flex-col rise relative rounded-2xl"
      style={{ animationDelay: delay }}
    >
      <div className="grid grid-cols-[1fr_72px] md:grid-cols-[1fr_88px]">
        {/* Left column - content */}
        <div className="p-6 md:p-7 flex flex-col">
          <div className="flex items-center gap-2.5 mb-5">
            <Icon size={16} strokeWidth={1.7} className="text-navy" />
            <p className="uppercase-eyebrow !text-navy">{eyebrow}</p>
          </div>
          {children}
          {footer}
        </div>
        {/* Right strip - color gradient (remplace les images Unsplash 503) */}
        <div
          className="relative overflow-hidden"
          style={{
            background: image,
          }}
        >
          <div className="absolute inset-0 bg-gradient-to-l from-transparent via-cream/20 to-cream/70" />
        </div>
      </div>
    </div>
  );
}

export function VisionCard({ data }) {
  const pct = data?.alignment_percent;
  const nextStep = data?.next_step || "Définir votre prochaine étape";
  return (
    <CardShell
      icon={Target}
      eyebrow="Vision"
      image={ART.vision}
      delay="60ms"
      footer={
        <FooterLink testId={DASH.visionCardLink} to="/vision">Voir ma vision</FooterLink>
      }
    >
      <div>
        <p className="font-display text-[52px] md:text-[60px] leading-none text-navy tracking-tight" data-testid="vision-alignment">
          {pct == null ? "—" : pct}<span className="text-[22px] align-top ml-1 font-normal text-ink-soft">{pct == null ? "" : "%"}</span>
        </p>
        <p className="text-[12.5px] text-ink-soft mt-2">{pct == null ? "Définissez votre vision pour démarrer" : "aligné avec votre objectif"}</p>
      </div>
      <div className="mt-5 space-y-4 text-[13px]">
        <div>
          <p className="font-display text-[16px] text-navy">Prochaine étape</p>
          <p className="text-ink-soft mt-1 leading-relaxed">{nextStep}</p>
        </div>
        {data?.summary && (
          <div>
            <p className="font-display text-[16px] text-navy">Résumé</p>
            <p className="text-ink-soft mt-1 leading-relaxed line-clamp-2">{data.summary}</p>
          </div>
        )}
      </div>
    </CardShell>
  );
}

export function MissionsCard({ data }) {
  const done = data?.done ?? 0;
  const total = data?.total ?? 0;
  const inProgress = data?.in_progress ?? 0;
  const blocked = data?.blocked ?? 0;
  return (
    <CardShell
      icon={ClipboardList}
      eyebrow="Missions"
      image={ART.missions}
      delay="140ms"
      footer={
        <FooterLink testId={DASH.missionsCardLink} to="/espace?tab=missions">Voir mes missions</FooterLink>
      }
    >
      <div>
        <p className="font-display text-[52px] md:text-[60px] leading-none text-navy tracking-tight" data-testid="missions-progress">
          {done}<span className="text-[22px] text-ink-muted ml-2 align-top font-normal">/ {total || "—"}</span>
        </p>
        <p className="text-[12.5px] text-ink-soft mt-2">tâches aujourd&apos;hui</p>
      </div>
      <ul className="mt-5 space-y-2 text-[13px]">
        <li className="flex items-center justify-between">
          <span className="text-ink-soft">En cours</span>
          <span className="font-semibold text-navy tabular-nums">{inProgress}</span>
        </li>
        <li className="flex items-center justify-between">
          <span className="text-ink-soft">Terminées</span>
          <span className="font-semibold text-navy tabular-nums">{done}</span>
        </li>
        <li className="flex items-center justify-between">
          <span className="text-ink-soft">Bloquées</span>
          <span className="font-semibold text-navy tabular-nums">{blocked}</span>
        </li>
      </ul>
    </CardShell>
  );
}

export function DeveloppementCard({ data }) {
  const prospects = data?.prospects ?? 0;
  const inDisc = data?.in_discussion ?? 0;
  const clients = data?.clients ?? 0;
  const ambass = data?.ambassadors ?? 0;
  const hot = data?.hot_opportunity;  // { channel, title, detected_ago, score }
  return (
    <CardShell
      icon={Rocket}
      eyebrow="Développement"
      image={ART.dev}
      delay="220ms"
      footer={
        <FooterLink testId={DASH.developmentCardLink} to="/croissance">Accéder au CRM</FooterLink>
      }
    >
      <ul className="space-y-2.5 text-[13.5px] mt-1" data-testid="dev-kpis">
        {[
          { l: "Prospects", v: prospects },
          { l: "En discussion", v: inDisc },
          { l: "Clients", v: clients },
          { l: "Ambassadeurs", v: ambass },
        ].map((it, i) => (
          <li key={i} className="flex items-center justify-between">
            <span className="text-ink-soft">{it.l}</span>
            <span className="font-semibold text-navy tabular-nums">{it.v}</span>
          </li>
        ))}
      </ul>
      {hot ? (
        <div className="mt-5 rounded-2xl bg-gold/15 ring-1 ring-gold/20 p-4" data-testid="hot-opportunity">
          <div className="flex items-center justify-between gap-2 mb-1.5">
            <p className="text-[10.5px] tracking-[0.22em] uppercase font-semibold text-gold-deep">
              Opportunité chaude
            </p>
            {hot.channel && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-white/70 ring-1 ring-gold/30 text-[10px] font-semibold text-gold-deep" data-testid="opp-source-channel">
                <Megaphone size={10} strokeWidth={2} />
                {hot.channel}
              </span>
            )}
          </div>
          <p className="mt-1 text-[13px] text-navy leading-snug">{hot.title}</p>
          {(hot.detected_ago || hot.score != null) && (
            <p className="mt-1.5 text-[11px] text-ink-soft">
              {hot.detected_ago && `Détectée ${hot.detected_ago}`}
              {hot.detected_ago && hot.score != null && " · "}
              {hot.score != null && `Score ${hot.score}/100`}
            </p>
          )}
        </div>
      ) : (
        <div className="mt-5 rounded-2xl bg-cream/40 ring-1 ring-sand-200 p-4 text-center" data-testid="hot-opportunity-empty">
          <p className="text-[11px] tracking-[0.18em] uppercase font-semibold text-ink-soft">
            Aucune opportunité détectée
          </p>
          <p className="mt-1.5 text-[12px] text-ink-soft leading-snug">
            Activez la veille IA dans Croissance pour détecter les leads chauds.
          </p>
        </div>
      )}
    </CardShell>
  );
}

export function PilotageCard({ data }) {
  const ca = data?.ca_month_eur ?? 0;
  const obj = data?.objective_eur ?? 10000;
  const pct = data?.progress_percent ?? 0;
  const fmt = (n) => new Intl.NumberFormat("fr-FR").format(n);
  return (
    <CardShell
      icon={BarChart3}
      eyebrow="Pilotage financier"
      image={ART.pilotage}
      delay="300ms"
      footer={
        <FooterLink testId={DASH.pilotageCardLink} to="/pilotage">
          Voir le tableau de bord
        </FooterLink>
      }
    >
      <div>
        <p className="text-[11px] tracking-wider text-ink-soft uppercase">CA du mois</p>
        <p className="font-display text-[36px] md:text-[42px] leading-tight text-navy tracking-tight mt-1" data-testid="pilot-ca">
          {fmt(ca)} <span className="text-gold-deep">€</span>
        </p>
      </div>
      <div className="mt-4 space-y-3 text-[13px]">
        <div className="flex items-center justify-between">
          <span className="text-ink-soft">Objectif</span>
          <span className="font-display text-[16px] text-navy">{fmt(obj)} €</span>
        </div>
        <div>
          <div className="flex items-center justify-between text-[12.5px] mb-1">
            <span className="text-ink-soft">Progression</span>
            <span className="font-semibold text-navy">{pct}%</span>
          </div>
          <div className="h-2 rounded-full bg-sand-200 overflow-hidden">
            <div className="h-full bg-gradient-to-r from-navy to-navy-bright rounded-full transition-all duration-700" style={{ width: `${Math.min(100, pct)}%` }} />
          </div>
        </div>
      </div>
    </CardShell>
  );
}
