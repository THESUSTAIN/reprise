import React, { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import TopNav from "@fm/components/layout/TopNav";
import FloatingBottomBar from "@fm/components/layout/FloatingBottomBar";
import MobileBottomNav from "@fm/components/layout/MobileBottomNav";
import EspacePanel from "@fm/components/panels/EspacePanel";
import EnergiePanel from "@fm/components/panels/EnergiePanel";
import CollaborateurPanel from "@fm/components/panels/CollaborateurPanel";
import { AppProvider } from "@fm/context/AppContext";
import { useAuth } from "@fm/context/AuthContext";
import Missions from "./espace/Missions";
import Documents from "./espace/Documents";
import Processus from "./espace/Processus";
import { Target, FileText, GitBranch } from "lucide-react";
import usePageTitle from "@fm/hooks/usePageTitle";
import useWelcomeModal from "@fm/hooks/useWelcomeModal";
import WelcomeModal from "@fm/components/WelcomeModal";

const TABS = [
  { id: "missions",  label: "Missions",   icon: Target,    testId: "espace-tab-missions"  },
  { id: "processus", label: "Processus",  icon: GitBranch, testId: "espace-tab-processus" },
  { id: "documents", label: "Documents",  icon: FileText,  testId: "espace-tab-documents" },
];

export default function EspaceDeTravail() {
  usePageTitle("Espace de travail");
  const welcome = useWelcomeModal("espace");
  const location = useLocation();
  const initialTab = (() => {
    const t = new URLSearchParams(location.search).get("tab");
    return TABS.find((x) => x.id === t)?.id || "missions";
  })();
  const [tab, setTab] = useState(initialTab);
  const [panel, setPanel] = useState(null);
  const { user } = useAuth();
  const firstName = user?.first_name || "Julien";

  useEffect(() => {
    const t = new URLSearchParams(location.search).get("tab");
    if (t && TABS.find((x) => x.id === t)) {
      setTab(t);
    }
  }, [location.search]);

  return (
    <AppProvider>
      <div className="min-h-screen canvas-bg relative overflow-x-hidden overflow-y-auto text-[#1F2937]">
        <TopNav onOpenChat={() => setPanel("collaborateur")} />
        <main className="relative z-10 pt-[100px] pb-48 px-4 sm:px-6 lg:px-10 max-w-[1400px] mx-auto" data-testid="espace-travail">
          {/* Header — même style que VisionBoard */}
          <section className="mb-8 rise" data-testid="espace-header">
            <h1 className="font-display text-[36px] md:text-[44px] leading-[1.1] text-navy">
              Mon <span className="font-serif-italic text-gold-deep">espace</span>
            </h1>
            <p className="mt-3 text-ink-soft text-[15px]">Missions, processus et documents — votre quotidien d&apos;exécution.</p>
          </section>

          {/* Tabs — pill bar style VisionBoard */}
          <div className="flex items-center gap-2 flex-wrap mb-8" data-testid="espace-tabs">
            {TABS.map((t) => {
              const Icon = t.icon;
              const active = tab === t.id;
              return (
                <button
                  key={t.id}
                  data-testid={t.testId}
                  onClick={() => setTab(t.id)}
                  className={`inline-flex items-center gap-2 px-5 h-11 rounded-full text-[14px] font-medium transition-all border ${
                    active
                      ? "bg-navy text-cream border-navy shadow-md"
                      : "bg-white text-ink border-[#E8E2D8] hover:border-navy/40"
                  }`}
                >
                  <Icon size={15} strokeWidth={1.8} />
                  {t.label}
                </button>
              );
            })}
          </div>

          {/* Content */}
          <div data-testid={`espace-content-${tab}`}>
            {tab === "missions"  && <Missions onOpenCollab={() => setPanel("collaborateur")} />}
            {tab === "processus" && <Processus />}
            {tab === "documents" && <Documents />}
          </div>
        </main>

        <FloatingBottomBar activePanel={panel} onOpen={(id) => setPanel(id)} />
        <MobileBottomNav onOpenCollab={() => setPanel("collaborateur")} onOpenEspace={() => setPanel("espace")} />
        <EspacePanel open={panel === "espace"} onClose={() => setPanel(null)} />
        <EnergiePanel open={panel === "energie"} onClose={() => setPanel(null)} onSave={() => setPanel(null)} />
        <CollaborateurPanel open={panel === "collaborateur"} onClose={() => setPanel(null)} context="Espace de travail" userFirstName={firstName} />
        <WelcomeModal open={welcome.show} onClose={welcome.close} {...(welcome.content || {})} />
      </div>
    </AppProvider>
  );
}
