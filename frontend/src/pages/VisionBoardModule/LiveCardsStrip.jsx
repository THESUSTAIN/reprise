import React, { useEffect, useState, useCallback } from "react";
import { visionCardsApi } from "../../lib/finalVisionModuleApi";
import useVisionEvents from "@/hooks/useVisionEvents";

const MODULE_ROUTE = { pilotage: "/pilotage", "bien-etre": "/bien-etre", croissance: "/croissance" };
// Les cartes "aggregate" du modèle unifié gardent les mêmes entity_id que l'ancien
// système (voir backend/routes/vision_cards.py::_resolve_aggregate) → on garde le
// même routage par module pour ne rien casser côté navigation.
const AGGREGATE_MODULE = { ca_month: "pilotage", wellness_latest: "bien-etre", prospects_count: "croissance" };

/**
 * #4 Live Cards — cartes du Vision Board reliées aux données live des autres
 * modules (CA Pilotage, streak/score Bien-être, prospects Croissance).
 * Backend : modèle unifié /api/vision/cards (chaque carte référence une entité
 * réelle et est résolue à chaque lecture — plus de valeur codée en dur).
 */
export default function LiveCardsStrip() {
  const [cards, setCards] = useState([]);

  useEffect(() => {
    let alive = true;

    const load = () =>
      visionCardsApi
        .migrateLegacy() // idempotent : ne fait rien si des cartes existent déjà pour ce board
        .catch(() => {})
        .then(() => visionCardsApi.list())
        .then((d) => {
          if (!alive) return;
          const aggregateCards = (d.cards || [])
            .filter((c) => c.entity_type === "aggregate" && AGGREGATE_MODULE[c.entity_id])
            .map((c) => ({
              key: c.entity_id,
              label: c.label,
              value: c.value,
              sub: c.sub,
              progress: c.progress,
              module: AGGREGATE_MODULE[c.entity_id],
              orphan: c.orphan,
            }));
          setCards(aggregateCards);
        })
        .catch(() => {});

    load();
    return () => { alive = false; };
     
  }, []);

  // Backlog #2 — flux SSE temps réel : le strip se rafraîchit dès qu'une
  // VisionCard est créée/modifiée/supprimée (event "card_update", poussé par
  // le backend au moment même de l'écriture), plus un "tick" ~60s en filet
  // pour les changements côté finance/leads/tâches non encore branchés sur le
  // bus. Remplace l'ancien `setInterval(load, 60000)`.
  const reload = useCallback(() => {
    visionCardsApi
      .list()
      .then((d) => {
        const aggregateCards = (d.cards || [])
          .filter((c) => c.entity_type === "aggregate" && AGGREGATE_MODULE[c.entity_id])
          .map((c) => ({
            key: c.entity_id,
            label: c.label,
            value: c.value,
            sub: c.sub,
            progress: c.progress,
            module: AGGREGATE_MODULE[c.entity_id],
            orphan: c.orphan,
          }));
        setCards(aggregateCards);
      })
      .catch(() => {});
  }, []);

  useVisionEvents({
    onTick: reload,
    onCardUpdate: reload,
    onFallbackPoll: reload,
  });

  if (!cards.length) return null;

  return (
    <div className="mb-3 flex gap-3 overflow-x-auto pb-1" data-testid="vision-live-cards">
      {cards.map((c) => (
        <a
          key={c.key}
          href={MODULE_ROUTE[c.module] || "#"}
          data-testid={`live-card-${c.key}`}
          className="group min-w-[150px] flex-1 rounded-xl border border-[var(--app-border)] bg-[var(--app-surface)] p-3 no-underline transition-colors hover:border-[var(--app-accent)]"
        >
          <div className="flex items-center gap-1.5 text-[11px] uppercase tracking-wide text-[var(--app-text-muted,#8a8a8a)]">
            <span className="h-1.5 w-1.5 rounded-full bg-[var(--app-accent,#DEC2A3)] animate-pulse" />
            {c.label}
          </div>
          <div className="mt-1 text-xl font-semibold text-[var(--app-text)]" data-testid={`live-card-${c.key}-value`}>
            {c.value}
          </div>
          <div className="text-[11px] text-[var(--app-text-muted,#8a8a8a)]">{c.sub}</div>
          {c.progress != null && (
            <div className="mt-2 h-1 w-full overflow-hidden rounded-full bg-[var(--app-border)]">
              <div className="h-full rounded-full bg-[var(--app-accent,#DEC2A3)]" style={{ width: `${Math.min(100, c.progress)}%` }} />
            </div>
          )}
        </a>
      ))}
    </div>
  );
}
