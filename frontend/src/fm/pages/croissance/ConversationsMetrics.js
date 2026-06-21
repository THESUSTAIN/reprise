import React, { useState, useEffect } from "react";
import { growthApi } from "@fm/lib/api";

const CHANNEL_LABELS = {
  linkedin: "LinkedIn", reddit: "Reddit", whatsapp: "WhatsApp",
  email: "Email", twitter: "Twitter", facebook: "Facebook",
  youtube: "YouTube", instagram: "Instagram",
};

function MetricTile({ label, value, accent, testid }) {
  return (
    <div data-testid={testid} className={`p-3.5 rounded-xl border ${accent ? "bg-navy text-cream border-navy" : "bg-white border-sand-200"}`}>
      <p className={`font-display text-[26px] ${accent ? "text-gold" : "text-navy"} leading-none tabular-nums`}>{value}</p>
      <p className={`text-[11px] uppercase tracking-[0.18em] mt-1 ${accent ? "text-cream/70" : "text-ink-soft"}`}>{label}</p>
    </div>
  );
}

export default function ConversationsMetrics() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    growthApi.conversationsMetrics()
      .then(setData)
      .catch(() => setData({ dms_sent: 0, replies: 0, reply_rate: 0, by_channel: {}, recent: [] }))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return null;
  const channels = Object.entries(data.by_channel || {});

  return (
    <div className="mt-6 p-5 rounded-2xl bg-cream-soft border border-sand-200" data-testid="conversations-metrics">
      <p className="uppercase-eyebrow">Conversations</p>
      <p className="text-[12.5px] text-ink-soft mt-1 mb-3">DMs envoyés, réponses reçues et taux de réponse par canal.</p>
      <div className="grid grid-cols-3 gap-3">
        <MetricTile label="DMs envoyés" value={data.dms_sent} testid="metric-dms-sent" />
        <MetricTile label="Réponses" value={data.replies} testid="metric-replies" />
        <MetricTile label="Reply rate" value={`${data.reply_rate}%`} accent testid="metric-reply-rate" />
      </div>
      {channels.length > 0 && (
        <div className="mt-4 space-y-2" data-testid="metric-by-channel">
          {channels.map(([ch, v]) => (
            <div key={ch} className="flex items-center gap-3 text-[12.5px]">
              <span className="w-20 text-ink font-medium">{CHANNEL_LABELS[ch] || ch}</span>
              <div className="flex-1 h-2 rounded-full bg-white overflow-hidden border border-sand-200">
                <div className="h-full bg-gradient-to-r from-navy to-gold-deep" style={{ width: `${Math.min(100, v.reply_rate)}%` }} />
              </div>
              <span className="text-ink-soft tabular-nums w-32 text-right">{v.received}/{v.sent} · {v.reply_rate}%</span>
            </div>
          ))}
        </div>
      )}
      {data.recent?.length === 0 && (
        <p className="mt-4 text-[12px] text-ink-muted italic">
          Aucune conversation enregistrée — les messages envoyés par le Growth Agent apparaîtront ici.
        </p>
      )}
    </div>
  );
}
