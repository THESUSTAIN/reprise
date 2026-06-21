/**
 * Croissance.js — Orchestrateur principal (porté FIDÈLEMENT depuis final-main)
 * Inséré dans la coquille reprise (Header + Sidebar) : la nav final-main
 * (TopNav / FloatingBottomBar / MobileBottomNav) est neutralisée, seul le
 * CONTENU s'affiche dans la zone de contenu de l'app.
 *
 * Sous-composants (./croissance/) :
 *   HubView · AnalyseView · TerrainView · AgentView · MomTestModal
 *   AddLeadModal · WaComposer · PipelineView · ConversationsMetrics
 */

import React, { useState, useEffect } from "react";
import TopNav from "@fm/components/layout/TopNav";
import FloatingBottomBar from "@fm/components/layout/FloatingBottomBar";
import MobileBottomNav from "@fm/components/layout/MobileBottomNav";
import LeafBackdrop from "@fm/components/dashboard/LeafBackdrop";
import EspacePanel from "@fm/components/panels/EspacePanel";
import EnergiePanel from "@fm/components/panels/EnergiePanel";
import CollaborateurPanel from "@fm/components/panels/CollaborateurPanel";
import { useAuth } from "@fm/context/AuthContext";
import { leadsApi } from "@fm/lib/api";
import usePageTitle from "@fm/hooks/usePageTitle";
import useWelcomeModal from "@fm/hooks/useWelcomeModal";
import WelcomeModal from "@fm/components/WelcomeModal";
import { BarChart3, Search, MapPin, Bot } from "lucide-react";

import HubView from "./croissance/HubView";
import AnalyseView from "./croissance/AnalyseView";
import TerrainView from "./croissance/TerrainView";
import AgentView from "./croissance/AgentView";
import PaywallGate from "@fm/components/PaywallGate";

const TABS = [
  { id: "hub",     label: "Vue d'ensemble", icon: BarChart3 },
  { id: "analyse", label: "Analyse marché", icon: Search },
  { id: "terrain", label: "Terrain",        icon: MapPin },
  { id: "agent",   label: "Growth Agent",   icon: Bot, addon: true },
];

export default function Croissance() {
  usePageTitle("Croissance");
  const { user } = useAuth();
  const welcome = useWelcomeModal("croissance");
  const firstName = user?.first_name || "Julien";
  const [tab, setTab] = useState("hub");
  const [panel, setPanel] = useState(null);
  const [data, setData] = useState({
    items: [],
    sources: [],
    kpis: { prospects: 0, conversations: 0, leads: 0, rdv: 0 },
  });

  useEffect(() => {
    leadsApi.list().then((d) => setData(d)).catch(() => {});
  }, []);

  return (
    <div data-testid="page-croissance" className="min-h-screen canvas-bg relative overflow-x-hidden overflow-y-auto">
      <TopNav onOpenChat={() => setPanel("collaborateur")} />
      <LeafBackdrop />

      <main className="relative z-10 pt-[100px] pb-48 px-4 sm:px-6 lg:px-10">
        <div className="mx-auto max-w-[1400px]">
          <header className="mb-8 rise">
            <h1 className="font-display text-[36px] md:text-[44px] leading-[1.1] text-navy">
              <span className="font-serif-italic text-gold-deep">Croissance</span>
            </h1>
            <p className="mt-3 text-ink-soft text-[15px]">
              Valider · Trouver · Convertir. Votre entonnoir de croissance complet.
            </p>
          </header>

          <div
            className="mb-8 inline-flex bg-white/85 backdrop-blur-sm border border-sand-200 rounded-full p-1.5 shadow-soft flex-wrap"
            data-testid="croissance-tabs"
          >
            {TABS.map((t) => {
              const Icon = t.icon;
              const isActive = tab === t.id;
              return (
                <button
                  key={t.id}
                  data-testid={`croissance-tab-${t.id}`}
                  onClick={() => setTab(t.id)}
                  className={`inline-flex items-center gap-2 px-5 h-11 rounded-full text-[13.5px] font-medium transition-all ${
                    isActive ? "bg-navy text-cream shadow-soft" : "text-ink hover:bg-cream-soft"
                  }`}
                >
                  <Icon size={15} strokeWidth={1.8} />
                  {t.label}
                  {t.addon && (
                    <span
                      className={`text-[9.5px] uppercase tracking-wider font-bold px-1.5 py-0.5 rounded-full border ${
                        isActive ? "bg-gold/20 text-gold border-gold/40" : "bg-gold/15 text-gold-deep border-gold/40"
                      }`}
                      data-testid="growth-agent-addon-badge"
                    >
                      Addon
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          {tab === "hub"     && <HubView     data={data} onOpenChat={() => setPanel("collaborateur")} onChangeTab={setTab} />}
          {tab === "analyse" && <AnalyseView />}
          {tab === "terrain" && <TerrainView leads={data.items || []} onLeadsChange={(items) => setData({ ...data, items })} />}
          {tab === "agent"   && (
            <PaywallGate feature="croissance_agent">
              <AgentView />
            </PaywallGate>
          )}
        </div>
      </main>

      <FloatingBottomBar activePanel={panel} onOpen={(id) => setPanel(id)} />
      <MobileBottomNav />
      <EspacePanel open={panel === "espace"} onClose={() => setPanel(null)} />
      <EnergiePanel open={panel === "energie"} onClose={() => setPanel(null)} onSave={() => setPanel(null)} />
      <CollaborateurPanel open={panel === "collaborateur"} onClose={() => setPanel(null)} context="Croissance" userFirstName={firstName} />
      <WelcomeModal open={welcome.show} onClose={welcome.close} {...(welcome.content || {})} />
    </div>
  );
}
