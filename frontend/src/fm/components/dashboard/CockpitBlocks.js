import React from "react";
import { Link } from "react-router-dom";
import { ArrowRight, FileText, Sparkles, CheckCircle2 } from "lucide-react";

/**
 * Bloc bas de dashboard — réplique du mockup utilisateur.
 *  - MetricsRow : 4 KPIs (CA, Nouveaux clients, Tickets, NPS)
 *  - FileIAValidation : 3 livrables prêts à valider
 *  - EnergieFondateur : rituel matin (physique/mentale/stress)
 *  - TrajectoireChart : sparkline CA 6 derniers mois + badge Stripe
 *  - BibliothequeMini : 4 derniers documents générés
 */

const ChipBadge = ({ children, color = "#b89855" }) => (
  <span className="inline-flex items-center px-2.5 py-1 rounded-full text-[10px] font-bold tracking-[0.14em] uppercase"
        style={{ background: "#f3e9d0", color }}>
    {children}
  </span>
);

const Card = ({ children, className = "", testid }) => (
  <div className={`rounded-2xl bg-white shadow-md p-5 ${className}`} data-testid={testid}>{children}</div>
);

// ── 4 KPI cards ──────────────────────────────────────────────
export function MetricsRow({ kpis }) {
  const hasData = kpis != null;
  const items = [
    { key: "ca",       label: "CA — cette semaine", value: kpis?.ca       ?? "—", delta: kpis?.ca_delta       ?? null, positive: true, emptyMsg: "Connectez votre banque" },
    { key: "clients",  label: "Nouveaux clients",   value: kpis?.clients  ?? "—", delta: kpis?.clients_delta  ?? null, positive: true, emptyMsg: "Aucun client cette semaine" },
    { key: "tickets",  label: "Tickets ouverts",    value: kpis?.tickets  ?? "—", delta: kpis?.tickets_delta  ?? null, positive: true, emptyMsg: "Aucun ticket ouvert" },
    { key: "nps",      label: "NPS simplifié",      value: kpis?.nps      ?? "—", delta: kpis?.nps_delta      ?? null, positive: true, emptyMsg: "Pas encore de retours" },
  ];
  return (
    <section className="mb-6" data-testid="metrics-row">
      <div className="flex items-end justify-between mb-3">
        <div>
          <div className="text-[10.5px] tracking-[0.22em] uppercase font-bold mb-1" style={{ color: "#6b6358" }}>
            Métriques clés
          </div>
          <h3 className="font-display text-[22px] sm:text-[24px] leading-tight font-bold" style={{ color: "#1a1815", letterSpacing: "-0.02em" }}>
            Votre semaine en chiffres
          </h3>
        </div>
        <Link to="/pilotage" className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-[12px] font-semibold transition hover:shadow-md"
              style={{ background: "white", color: "#1a3a6e" }}
              data-testid="metrics-see-pilotage">
          Voir le pilotage <ArrowRight size={11} />
        </Link>
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        {items.map((it) => (
          <Card key={it.key} testid={`kpi-${it.key}`}>
            <div className="text-[10px] tracking-[0.18em] uppercase font-bold mb-2" style={{ color: "#6b6358" }}>
              {it.label}
            </div>
            <div className="text-[26px] sm:text-[28px] font-bold mb-1.5" style={{ color: "#1a3a6e", letterSpacing: "-0.02em" }}>
              {it.value}
            </div>
            <div className="text-[11px]" style={{ color: it.positive ? "#2D6A4F" : "#6b6358" }}>
              {it.delta || (hasData ? "—" : (it.emptyMsg || "—"))}
            </div>
          </Card>
        ))}
      </div>
    </section>
  );
}

// ── FILE IA — 3 livrables à valider ────────────────────────
export function FileIAValidation({ items, onValidate }) {
  const list = Array.isArray(items) ? items.slice(0, 3) : [];
  return (
    <Card testid="file-ia-validation">
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="text-[10.5px] tracking-[0.22em] uppercase font-bold mb-1" style={{ color: "#6b6358" }}>
            File IA — prêtes à valider
          </div>
          <h3 className="font-display text-[20px] font-bold" style={{ color: "#1a1815", letterSpacing: "-0.02em" }}>
            {list.length > 0 ? `${list.length} livrables vous attendent` : "Rien à valider pour l'instant"}
          </h3>
        </div>
        {list.length > 0 && (
          <span className="inline-flex px-2.5 py-1 rounded-full text-[10px] font-bold tracking-[0.14em] uppercase"
                style={{ background: "#f3e9d0", color: "#b89855" }}>
            {list.length} en attente
          </span>
        )}
      </div>

      {list.length === 0 ? (
        <div className="rounded-xl p-6 text-center" style={{ background: "#fbfaf6" }} data-testid="file-ia-empty">
          <Sparkles size={20} className="mx-auto mb-2" style={{ color: "#b89855" }} />
          <p className="text-[13px]" style={{ color: "#6b6358" }}>
            Les livrables générés par votre Collaborateur IA (emails, analyses, contenus…) apparaîtront ici pour validation.
          </p>
        </div>
      ) : (
        <div className="space-y-2.5">
          {list.map((it, i) => (
            <div key={it.id || i}
                 className="rounded-xl p-3.5 flex items-start gap-3 hover:shadow-md transition"
                 style={{ background: "#fbfaf6" }}
                 data-testid={`file-ia-item-${i}`}>
              <div className="w-8 h-8 rounded-lg grid place-items-center shrink-0"
                   style={{ background: "#f3e9d0", color: "#b89855" }}>
                <Sparkles size={14} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <ChipBadge>{it.tag}</ChipBadge>
                  <span className="text-[11px]" style={{ color: "#6b6358" }}>{it.time}</span>
                </div>
                <div className="text-[13.5px] font-semibold mb-0.5" style={{ color: "#1a1815" }}>{it.title}</div>
                <div className="text-[12px] truncate" style={{ color: "#6b6358" }}>{it.excerpt}</div>
              </div>
              <button onClick={() => onValidate && onValidate(it.id)}
                      className="shrink-0 px-3.5 py-1.5 rounded-full text-[12px] font-semibold transition shadow-sm"
                      style={{ background: "#a01722", color: "#f6f3ee" }}
                      data-testid={`file-ia-validate-${i}`}>
                Valider
              </button>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

// ── Énergie du fondateur (rituel matin) ────────────────────
export function EnergieFondateur({ data }) {
  const physique = data?.physique ?? 7;
  const mentale  = data?.mentale  ?? 8;
  const stress   = data?.stress   ?? 3;
  const streak   = data?.streak   ?? 12;
  const charge   = data?.charge   ?? "Modérée";

  const Bar = ({ value, color }) => (
    <div className="h-1.5 rounded-full mt-1.5" style={{ background: "#f0ebe0" }}>
      <div className="h-full rounded-full" style={{ width: `${value * 10}%`, background: color }} />
    </div>
  );

  return (
    <Card testid="energie-fondateur">
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="text-[10.5px] tracking-[0.22em] uppercase font-bold mb-1" style={{ color: "#6b6358" }}>
            Énergie du fondateur
          </div>
          <h3 className="font-display text-[20px] font-bold" style={{ color: "#1a1815", letterSpacing: "-0.02em" }}>
            Ton rituel du matin
          </h3>
        </div>
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10.5px] font-bold tracking-[0.14em] uppercase"
              style={{ background: "rgba(45,106,79,0.12)", color: "#2D6A4F" }}>
          <CheckCircle2 size={11} /> Fait
        </span>
      </div>

      <div className="grid grid-cols-3 gap-3 mb-4">
        {[
          { label: "Physique", val: physique, color: "#2D6A4F" },
          { label: "Mentale",  val: mentale,  color: "#2D6A4F" },
          { label: "Stress",   val: stress,   color: "#b89855" },
        ].map((s, i) => (
          <div key={i}>
            <div className="text-[10px] tracking-[0.18em] uppercase font-bold mb-0.5" style={{ color: "#6b6358" }}>
              {s.label}
            </div>
            <div className="flex items-baseline gap-1">
              <span className="text-[22px] font-bold" style={{ color: "#1a3a6e" }}>{s.val}</span>
              <span className="text-[11px]" style={{ color: "#6b6358" }}>/10</span>
            </div>
            <Bar value={s.val} color={s.color} />
          </div>
        ))}
      </div>

      <div className="text-[12px]" style={{ color: "#6b6358" }}>
        Charge suggérée aujourd'hui : <strong style={{ color: "#1a3a6e" }}>{charge}</strong> · Streak {streak} jours
      </div>
    </Card>
  );
}

// ── Trajectoire mensuelle (sparkline + badge Stripe) ───────
export function TrajectoireChart({ data }) {
  const points = (Array.isArray(data) && data.length ? data : [4800, 5200, 6100, 7400, 8300, 9840]).map((v, i, a) => {
    const max = Math.max(...a);
    const w = 100 / (a.length - 1);
    return { x: i * w, y: 100 - (v / max) * 80 };
  });
  const pathD = points.reduce((acc, p, i) => acc + `${i === 0 ? "M" : "L"} ${p.x} ${p.y} `, "");

  return (
    <Card testid="trajectoire-chart">
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="text-[10.5px] tracking-[0.22em] uppercase font-bold mb-1" style={{ color: "#6b6358" }}>
            Chiffre d'affaires — 6 derniers mois
          </div>
          <h3 className="font-display text-[20px] font-bold" style={{ color: "#1a1815", letterSpacing: "-0.02em" }}>
            Trajectoire mensuelle
          </h3>
        </div>
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold tracking-[0.14em] uppercase"
              style={{ background: "#f3e9d0", color: "#b89855" }}>
          Connecté à Stripe
        </span>
      </div>

      <div className="aspect-[2.5/1] w-full">
        <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="w-full h-full">
          <defs>
            <linearGradient id="trajGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="rgba(26,58,110,0.18)" />
              <stop offset="100%" stopColor="rgba(26,58,110,0)" />
            </linearGradient>
          </defs>
          <path d={`${pathD} L 100 100 L 0 100 Z`} fill="url(#trajGradient)" />
          <path d={pathD} fill="none" stroke="#1a3a6e" strokeWidth="0.6" />
        </svg>
      </div>
      <div className="flex justify-between text-[10px] mt-1.5" style={{ color: "#6b6358" }}>
        <span>Août</span><span>Sept</span><span>Oct</span><span>Nov</span><span>Déc</span><span>Janv</span>
      </div>
    </Card>
  );
}

// ── Bibliothèque (4 derniers documents) ─────────────────────
export function BibliothequeMini({ items }) {
  const list = (Array.isArray(items) ? items : []).slice(0, 4);

  return (
    <Card testid="bibliotheque-mini">
      <div className="mb-4">
        <div className="text-[10.5px] tracking-[0.22em] uppercase font-bold mb-1" style={{ color: "#6b6358" }}>
          Derniers documents générés
        </div>
        <h3 className="font-display text-[20px] font-bold" style={{ color: "#1a1815", letterSpacing: "-0.02em" }}>
          Bibliothèque
        </h3>
      </div>
      {list.length === 0 ? (
        <div className="rounded-xl p-6 text-center" style={{ background: "#fbfaf6" }} data-testid="biblio-empty">
          <FileText size={20} className="mx-auto mb-2" style={{ color: "#b89855" }} />
          <p className="text-[13px]" style={{ color: "#6b6358" }}>
            Vos documents générés (stratégie, roadmap, veille…) apparaîtront ici.
          </p>
        </div>
      ) : (
      <div className="grid grid-cols-2 gap-3">
        {list.map((doc, i) => (
          <div key={i} className="rounded-xl p-3.5 transition hover:shadow-md" style={{ background: "#fbfaf6" }} data-testid={`biblio-${i}`}>
            <div className="flex items-center gap-2 mb-2">
              <FileText size={12} style={{ color: "#b89855" }} />
              <ChipBadge>{doc.tag}</ChipBadge>
            </div>
            <div className="text-[12.5px] font-semibold mb-2 leading-snug line-clamp-2" style={{ color: "#1a1815" }}>
              {doc.title}
            </div>
            <div className="flex items-center justify-between text-[10.5px]" style={{ color: "#6b6358" }}>
              <span>{doc.time}</span>
              <span className="font-semibold" style={{ color: "#b89855" }}>{doc.pct}%</span>
            </div>
            <div className="h-1 mt-1.5 rounded-full" style={{ background: "#f0ebe0" }}>
              <div className="h-full rounded-full" style={{ width: `${doc.pct}%`, background: "#b89855" }} />
            </div>
          </div>
        ))}
      </div>
      )}
    </Card>
  );
}
