import React, { useState, useEffect } from "react";
import TopNav from "@fm/components/layout/TopNav";
import FloatingBottomBar from "@fm/components/layout/FloatingBottomBar";
import MobileBottomNav from "@fm/components/layout/MobileBottomNav";
import EspacePanel from "@fm/components/panels/EspacePanel";
import EnergiePanel from "@fm/components/panels/EnergiePanel";
import CollaborateurPanel from "@fm/components/panels/CollaborateurPanel";
import { Activity, Sparkles, Flame, AlertTriangle, ShoppingBag, CheckCircle2, Send, UserPlus, BookOpen, Lock, ChevronRight } from "lucide-react";
import { LineChart, Line, ResponsiveContainer, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from "recharts";
import TrimestrielModal from "@fm/components/TrimestrielModal";
import { wellnessApi } from "@fm/lib/api";
import { toast, Toaster } from "sonner";

const DEFAULT_TODAY = { physique: 6, mentale: 6, stress: 4, verdict: "Modérée", raison: "Énergie moyenne, stress contenu.", rituel: [], citation: "" };

const BienEtre = () => {
  const [today, setToday] = useState(DEFAULT_TODAY);
  const [energyHistory, setEnergyHistory] = useState([]);
  const [bilanHistory, setBilanHistory] = useState([]);
  const [boutiqueRecos, setBoutiqueRecos] = useState([]);
  const [weeklyReview, setWeeklyReview] = useState([]);
  const [loading, setLoading] = useState(true);
  const [phys, setPhys] = useState(6);
  const [ment, setMent] = useState(6);
  const [str, setStr] = useState(4);
  const [done, setDone] = useState(false);
  const [trimOpen, setTrimOpen] = useState(false);
  const [trimQuarter, setTrimQuarter] = useState("q4-2025");
  const [panel, setPanel] = useState(null);
  const [sending, setSending] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const data = await wellnessApi.getState();
        if (data?.today) {
          setToday(data.today);
          setPhys(data.today.physique || 6);
          setMent(data.today.mentale || 6);
          setStr(data.today.stress || 4);
        }
        // Bug #7 : normaliser le shape (series | energyHistory | items | array)
        const rawHist = data?.energyHistory || data?.series || data?.history || [];
        const normalized = rawHist.map((pt) => ({
          date: pt.date || pt.day || pt.label || "",
          physique: typeof pt.physique !== "undefined" ? pt.physique : (pt.value ?? 0),
          mentale: pt.mentale ?? (pt.mental ?? 0),
          stress: pt.stress ?? 0,
        }));
        setEnergyHistory(normalized);
        setBilanHistory(data?.bilanHistory || []);
        // boutiqueRecos: handle both shapes (legacy {name,why,image} + backend {title,raison})
        const rawRecos = data?.boutiqueRecos || [];
        setBoutiqueRecos(rawRecos.map((p) => ({
          name: p.name || p.title || "",
          why: p.why || p.raison || "",
          price: p.price || "",
          image: p.image || `https://placehold.co/400x240/F6F3EE/1F3B73?text=${encodeURIComponent(p.name || p.title || "Produit")}`,
        })));
        // weeklyReview.questions can be array of strings (legacy) or objects {question, placeholder}
        const rawQ = data?.weeklyReview?.questions || [];
        const normalizedQ = rawQ.map((q) =>
          typeof q === "string" ? { question: q, placeholder: "Note libre…" } : q
        );
        setWeeklyReview(normalizedQ);
      } catch (e) {
        // Empty states — page reste utilisable
      } finally { setLoading(false); }
    })();
  }, []);

  const energyToday = today;

  const sendBilan = async () => {
    setSending(true);
    try {
      const res = await wellnessApi.sendBilan({
        physique: phys, mentale: ment, stress: str,
        quarter: trimQuarter,
      });
      toast.success(res?.message || "Bilan envoyé à votre email + support@zayado.net");
    } catch (e) {
      toast.error(e?.detail || "Envoi indisponible — réessayez plus tard.");
    } finally { setSending(false); }
  };

  return (
    <div className="min-h-screen canvas-bg relative overflow-x-hidden text-[#1F2937]">
      <Toaster richColors position="top-center" />
      <TopNav active="bien-etre" onOpenChat={() => setPanel("collaborateur")} />
      <main data-testid="page-bien-etre" className="relative z-10 pt-[100px] pb-32 px-4 sm:px-6 lg:px-10 max-w-[1400px] mx-auto fade-up">
        <section className="mb-8 rise" data-testid="bienetre-header">
          <p className="text-[11px] uppercase tracking-[0.22em] text-ink-soft font-semibold">Rituel &amp; énergie du fondateur</p>
          <h1 className="font-display text-[36px] md:text-[44px] leading-[1.1] text-navy">
            Bien-<span className="font-serif-italic text-gold-deep">être</span>
          </h1>
        </section>

      <div className="space-y-7">
        {/* Morning ritual */}
        <div className="card-z p-8 grid lg:grid-cols-[1.3fr_1fr] gap-8" data-testid="morning-ritual">
          <div>
            <div className="text-[11px] tracking-[0.22em] uppercase text-[#6B7280] mb-2">
              Rituel du matin · 2 min
            </div>
            <h2 className="font-serif text-[30px] leading-tight mb-2">
              Comment te sens-tu aujourd&apos;hui ?
            </h2>
            <p className="text-[14px] text-[#6B7280] mb-6">
              Trois curseurs honnêtes. L&apos;IA adaptera ta charge du jour en conséquence.
            </p>

            <Slider label="Énergie physique" value={phys} setValue={setPhys} icon={<Activity size={14} />} />
            <Slider label="Clarté mentale" value={ment} setValue={setMent} icon={<Sparkles size={14} />} />
            <Slider label="Niveau de stress" value={str} setValue={setStr} icon={<Flame size={14} />} inverse />

            <div className="flex items-center gap-3 mt-6">
              <button
                onClick={() => setDone(true)}
                className="btn-cta"
                data-testid="bien-etre-save"
              >
                {done ? <><CheckCircle2 size={14} /> Enregistré</> : <>Valider le rituel</>}
              </button>
              <span className="text-[12px] text-[#6B7280]">
                Streak {energyToday.streak || 0} jours · privé, jamais partagé.
              </span>
            </div>
          </div>

          <div className="rounded-2xl p-6 border border-[var(--border)] bg-[var(--bg)] self-stretch flex flex-col">
            <div className="text-[11px] tracking-[0.22em] uppercase text-[#6B7280] mb-2">
              Verdict du co-pilote
            </div>
            <h3 className="font-serif text-[24px] leading-tight mb-3">
              Charge suggérée : <span style={{ color: "var(--gold)" }}>Modérée</span>
            </h3>
            <p className="text-[13px] text-[#6B7280] mb-4 leading-relaxed">
              Avec une énergie de {Math.round((phys + ment) / 2)}/10 et un stress à {str}/10,
              je te propose de garder une décision stratégique pour aujourd&apos;hui — et de déléguer le reste.
            </p>
            <ul className="space-y-2 text-[13px] mb-auto">
              <li>· 1 décision importante max</li>
              <li>· 3 tâches IA à valider (15 min)</li>
              <li>· Pas d&apos;appel client à froid</li>
            </ul>
            <div className="mt-4 text-[11px] italic text-[#6B7280]">
              « On ralentit pour décider juste. »
            </div>
          </div>
        </div>

        {/* Overload alert */}
        <div className="card-z p-5 flex items-center gap-4 border-l-4 border-l-[var(--gold)]" data-testid="overload-alert">
          <div className="w-10 h-10 rounded-full grid place-items-center" style={{ background: "#FBF6EA", color: "#1F3B73" }}>
            <AlertTriangle size={16} />
          </div>
          <div className="flex-1">
            <div className="font-medium text-[14px]">Tu as validé 11 tâches en 3 jours.</div>
            <div className="text-[12px] text-[#6B7280]">
              Le co-pilote te suggère de confier davantage de drafts à l&apos;IA cette semaine.
            </div>
          </div>
          <button className="btn-ghost !py-2 !px-4 text-[13px]">Confier 3 tâches</button>
        </div>

        {/* Energy 30 days */}
        <div className="card-z p-7" data-testid="energy-history">
          <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
            <div>
              <div className="text-[11px] tracking-[0.22em] uppercase text-[#6B7280] mb-1">
                Énergie & stress · 30 derniers jours
              </div>
              <h3 className="font-serif text-[22px]">Voir où tu en es vraiment</h3>
            </div>
            <div className="flex items-center gap-4 text-[11px] text-[#6B7280]">
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full" style={{ background: "#1F3B73" }} /> Énergie
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full" style={{ background: "#B85450" }} /> Stress
              </span>
            </div>
          </div>
          <div className="h-[220px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={energyHistory} margin={{ top: 8, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E8E2D9" vertical={false} />
                <XAxis dataKey="jour" tick={{ fill: "#5C6B7B", fontSize: 10 }} axisLine={false} tickLine={false} interval={4} />
                <YAxis domain={[0, 10]} tick={{ fill: "#5C6B7B", fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{ background: "#fff", border: "1px solid #E8E2D9", borderRadius: 12 }}
                />
                <Line type="monotone" dataKey="energie" stroke="#1F3A6A" strokeWidth={2.5} dot={false} />
                <Line type="monotone" dataKey="stress" stroke="#8B0000" strokeWidth={2} dot={false} strokeDasharray="4 4" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Bilan trimestriel privé */}
        <div
          className="card-z overflow-hidden grain-overlay relative"
          style={{ background: "var(--navy-deep)" }}
          data-testid="trim-card"
        >
          <div className="relative p-8 md:p-10 grid md:grid-cols-[1.4fr_1fr] gap-8">
            <div>
              <div className="flex items-center gap-2 text-[11px] tracking-[0.22em] uppercase opacity-75 mb-3" style={{ color: "var(--gold)" }}>
                <Lock size={11} /> Bilan trimestriel · privé
              </div>
              <h2 className="text-[26px] md:text-[32px] leading-tight mb-4 font-bold" style={{ color: "var(--bg)", letterSpacing: "-0.02em" }}>
                90 jours de toi, en 2 pages.
              </h2>
              <p className="text-[14px] leading-relaxed max-w-[560px] mb-5" style={{ color: "rgba(253,251,247,0.82)" }}>
                Tous les 3 mois, ton co-pilote te prépare un objet privé :
                courbe d&apos;énergie, décisions clés validées, verdict IA personnel.
                À garder pour toi, ou à imprimer comme repère.
              </p>
              <div className="flex flex-wrap gap-3">
                <button
                  className="btn-cta"
                  onClick={() => { setTrimQuarter("q4-2025"); setTrimOpen(true); }}
                  data-testid="open-trim-modal"
                >
                  <BookOpen size={14} /> Voir mon bilan Q4 2025
                </button>
              </div>
            </div>

            <div
              className="rounded-2xl p-5 flex flex-col"
              style={{
                borderColor: "rgba(201,166,107,0.35)",
                border: "1px solid rgba(201,166,107,0.35)",
                background: "rgba(255,255,255,0.04)",
              }}
              data-testid="trim-history-list"
            >
              <div className="text-[10px] tracking-[0.22em] uppercase opacity-75 mb-3" style={{ color: "var(--gold)" }}>
                Historique des bilans
              </div>
              <div className="space-y-1.5 flex-1">
                {bilanHistory.map((b) => (
                  <button
                    key={b.id}
                    onClick={() => { setTrimQuarter(b.id); setTrimOpen(true); }}
                    data-testid={`trim-history-${b.id}`}
                    className="w-full flex items-center justify-between gap-3 px-3 py-2.5 rounded-lg transition group"
                    style={{ color: "var(--bg)" }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.08)")}
                    onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      {b.locked && <Lock size={11} className="opacity-60 shrink-0" />}
                      <div className="text-left min-w-0">
                        <div className="text-[13px] font-semibold leading-tight">{b.label}</div>
                        <div className="text-[10px] opacity-65 truncate">{b.highlight}</div>
                      </div>
                    </div>
                    <ChevronRight size={14} className="opacity-50 group-hover:opacity-100 shrink-0" />
                  </button>
                ))}
              </div>
              <div className="mt-3 pt-3 border-t border-white/10 text-[10px] tracking-[0.18em] uppercase" style={{ color: "rgba(201,166,107,0.85)" }}>
                Prochain bilan · dans 12 jours
              </div>
            </div>
          </div>
        </div>

        {/* Boutique recos */}
        <div data-testid="boutique-recos">
          <div className="flex items-end justify-between mb-5">
            <div>
              <div className="text-[11px] tracking-[0.22em] uppercase text-[#6B7280] mb-1">
                Recommandations boutique
              </div>
              <h2 className="font-serif text-[26px] leading-none">Ce que ton énergie suggère</h2>
            </div>
            <button className="btn-ghost"><ShoppingBag size={14} /> Visiter la boutique</button>
          </div>
          <div className="grid md:grid-cols-3 gap-5">
            {boutiqueRecos.map((p) => (
              <div key={p.name} className="card-z overflow-hidden flex flex-col">
                <div className="h-[180px] overflow-hidden">
                  <img src={p.image} alt={p.name} className="w-full h-full object-cover" />
                </div>
                <div className="p-5 flex flex-col flex-1">
                  <h3 className="font-serif text-[20px] leading-tight mb-1">{p.name}</h3>
                  <div className="text-[12px] text-[#6B7280] italic mb-4 leading-relaxed">{p.why}</div>
                  <div className="mt-auto flex items-center justify-between">
                    <div className="font-serif text-[20px]">{p.price}</div>
                    <button className="btn-cta !py-2 !px-4 text-[13px]">Découvrir</button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Weekly review */}
        <div className="card-z p-7" data-testid="weekly-review">
          <div className="flex items-center justify-between mb-5">
            <div>
              <div className="text-[11px] tracking-[0.22em] uppercase text-[#6B7280] mb-1">
                Bilan de semaine · vendredi
              </div>
              <h2 className="font-serif text-[26px] leading-none">5 questions, 5 minutes.</h2>
            </div>
            <span className="chip chip-gold">Privé — jamais partagé</span>
          </div>
          <div className="grid md:grid-cols-2 gap-4">
            {weeklyReview.map((q, i) => (
              <div key={i} className="p-4 rounded-xl border border-[var(--border)] bg-[var(--bg)]">
                <div className="text-[13px] font-medium mb-2">{q.question}</div>
                <textarea
                  placeholder={q.placeholder}
                  rows={2}
                  className="w-full bg-white border border-[var(--border)] rounded-lg p-3 text-[13px] outline-none resize-none focus:border-[var(--gold)]"
                  data-testid={`weekly-q-${i}`}
                />
              </div>
            ))}
          </div>
          <div className="flex flex-wrap gap-3 mt-5">
            <button onClick={sendBilan} disabled={sending} className="btn-cta inline-flex items-center gap-2 px-4 py-2 rounded-full bg-navy text-cream text-[12.5px] font-semibold hover:bg-navy/90 disabled:opacity-50 transition" data-testid="send-weekly-review"><Send size={14} /> {sending ? "Envoi…" : "Envoyer le bilan à moi-même"}</button>
            <button className="btn-ghost" data-testid="share-accompagnateur"><UserPlus size={14} /> Partager avec mon accompagnateur</button>
          </div>
        </div>
      </div>

      {trimOpen && (
        <TrimestrielModal
          onClose={() => setTrimOpen(false)}
          initialQuarterId={trimQuarter}
          bilanHistory={bilanHistory}
          user={{ name: "Vous" }}
        />
      )}
      </main>

      <FloatingBottomBar activePanel={panel} onOpen={(id) => setPanel(id)} />
      <MobileBottomNav
        onOpenCollab={() => setPanel("collaborateur")}
        onOpenEspace={() => setPanel("espace")}
      />

      <EspacePanel open={panel === "espace"} onClose={() => setPanel(null)} />
      <EnergiePanel open={panel === "energie"} onClose={() => setPanel(null)} onSave={() => setPanel(null)} />
      <CollaborateurPanel open={panel === "collaborateur"} onClose={() => setPanel(null)} context="Bien-être" />
    </div>
  );
};

const Slider = ({ label, value, setValue, icon, inverse }) => {
  const good = inverse ? value <= 4 : value >= 6;
  return (
    <div className="mb-4">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2 text-[12px] tracking-[0.18em] uppercase text-[#6B7280]">
          {icon} {label}
        </div>
        <div className="font-serif text-[20px] leading-none">{value}/10</div>
      </div>
      <input
        type="range"
        min={0}
        max={10}
        value={value}
        onChange={(e) => setValue(Number(e.target.value))}
        className="w-full accent-[#1F3B73]"
        style={{ accentColor: good ? "#16A34A" : "#B85450" }}
      />
    </div>
  );
};

export default BienEtre;