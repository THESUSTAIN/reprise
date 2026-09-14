import { useState, useEffect } from "react";
import {
  X, Settings as SettingsIcon, Loader2, User, Sparkles, Bell, ShieldCheck,
  Plug, CreditCard, SlidersHorizontal, Download, BellRing,
} from "lucide-react";
import { toast } from "sonner";
import {
  getProfile, setProfile, getReminders, setReminders,
  getInspiration, setInspirationImage, exportCsvUrl,
} from "../lib/api";
import { isPushSubscribed, subscribeToPush, unsubscribeFromPush, sendTestPush } from "../lib/pwa";

/* Modal Paramètres — 7 sections reprenant la structure de final-main.
 * 4 sont réellement branchées sur la base (Profil, Vision & Inspiration,
 * Notifications, Sécurité/export) ; 3 sont des placeholders honnêtes
 * (Automatisation, Intégrations, Facturation) — elles nécessitent une
 * infrastructure que ce SaaS (une session locale, pas de vrais comptes ni
 * paiements) n'a pas, plutôt que de simuler de fausses connexions actives. */
const TABS = [
  { id: "profil", label: "Profil", Icon: User },
  { id: "vision", label: "Vision & Inspiration", Icon: Sparkles },
  { id: "notifications", label: "Notifications", Icon: Bell },
  { id: "securite", label: "Sécurité", Icon: ShieldCheck },
  { id: "automatisation", label: "Automatisation", Icon: SlidersHorizontal, placeholder: true },
  { id: "integrations", label: "Intégrations", Icon: Plug, placeholder: true },
  { id: "facturation", label: "Facturation", Icon: CreditCard, placeholder: true },
];

function Placeholder({ label }) {
  return (
    <div className="rounded-xl border border-dashed border-white/15 bg-white/[0.02] p-5 text-center" data-testid="settings-placeholder">
      <p className="text-sm text-white/60">{label} nécessite une vraie infrastructure (comptes, connexions tierces, paiements) que cette version ne simule pas.</p>
    </div>
  );
}

export default function SettingsModal({ open, onClose }) {
  const [tab, setTab] = useState("profil");
  const [loading, setLoading] = useState(true);

  const [firstName, setFirstName] = useState("");
  const [saving, setSaving] = useState(false);

  const [inspirationUrl, setInspirationUrlState] = useState("");
  const [savingInspiration, setSavingInspiration] = useState(false);

  const [weeklyReview, setWeeklyReview] = useState(false);
  const [pushSubscribed, setPushSubscribed] = useState(false);
  const [pushLoading, setPushLoading] = useState(false);

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    Promise.all([getProfile(), getReminders(), getInspiration(), isPushSubscribed()])
      .then(([p, r, insp, subscribed]) => {
        setFirstName(p.first_name || "");
        setWeeklyReview(!!r.weekly_review);
        setInspirationUrlState(insp.image_url || "");
        setPushSubscribed(!!subscribed);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [open]);

  if (!open) return null;

  const saveFirstName = async () => {
    setSaving(true);
    try { await setProfile(firstName.trim()); toast.success("Prénom enregistré"); }
    catch { toast.error("Échec de l'enregistrement"); }
    finally { setSaving(false); }
  };

  const saveInspiration = async () => {
    setSavingInspiration(true);
    try { await setInspirationImage(inspirationUrl.trim()); toast.success("Image d'inspiration enregistrée"); }
    catch { toast.error("Échec de l'enregistrement"); }
    finally { setSavingInspiration(false); }
  };

  const toggleWeeklyReview = async () => {
    const next = !weeklyReview;
    setWeeklyReview(next);
    try { await setReminders(next); }
    catch { setWeeklyReview(!next); toast.error("Échec de l'enregistrement"); }
  };

  const togglePush = async () => {
    setPushLoading(true);
    try {
      if (pushSubscribed) {
        await unsubscribeFromPush();
        setPushSubscribed(false);
        toast.success("Notifications désactivées");
      } else {
        const res = await subscribeToPush();
        if (res.ok) { setPushSubscribed(true); toast.success("Notifications activées ✦"); }
        else toast.error(res.error || "Impossible d'activer les notifications");
      }
    } finally {
      setPushLoading(false);
    }
  };

  const testPush = async () => {
    try { await sendTestPush(); toast.success("Notification de test envoyée"); }
    catch { toast.error("Échec — vérifiez que les notifications sont activées"); }
  };

  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/50 p-4" onClick={onClose} data-testid="settings-modal-overlay">
      <div className="glass w-full max-w-2xl rounded-2xl p-6 max-h-[85vh] overflow-y-auto" onClick={(e) => e.stopPropagation()} data-testid="settings-modal">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <SettingsIcon size={18} className="text-[#D4AF37]" />
            <h2 className="font-head font-semibold text-white text-[16px]">Paramètres du SaaS</h2>
          </div>
          <button onClick={onClose} className="w-8 h-8 rounded-full flex items-center justify-center text-white/50 hover:text-white hover:bg-white/10" data-testid="settings-modal-close">
            <X size={16} />
          </button>
        </div>

        <nav className="flex flex-wrap gap-1.5 mb-5 border-b border-white/10 pb-4">
          {TABS.map(({ id, label, Icon }) => (
            <button key={id} onClick={() => setTab(id)} data-testid={`settings-tab-${id}`}
              className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[12px] font-semibold transition-colors ${
                tab === id ? "gold-bg text-[#0A1128]" : "bg-white/5 border border-white/10 text-white/60 hover:border-[#D4AF37]/30"
              }`}>
              <Icon size={13} /> {label}
            </button>
          ))}
        </nav>

        {loading ? (
          <div className="flex items-center justify-center py-10 text-white/50"><Loader2 size={20} className="animate-spin" /></div>
        ) : (
          <div className="space-y-5">
            {tab === "profil" && (
              <div>
                <label className="block text-[12px] font-medium text-white/70 mb-1.5">Prénom affiché dans votre cockpit</label>
                <div className="flex items-center gap-2">
                  <input value={firstName} onChange={(e) => setFirstName(e.target.value)} onBlur={saveFirstName}
                    onKeyDown={(e) => e.key === "Enter" && e.currentTarget.blur()} placeholder="Votre prénom"
                    data-testid="settings-firstname-input"
                    className="flex-1 bg-white/5 border border-white/15 rounded-xl px-3.5 py-2.5 text-sm text-white placeholder:text-white/35 focus:outline-none focus:border-[#D4AF37]/50" />
                  {saving && <Loader2 size={16} className="animate-spin text-white/40" />}
                </div>
              </div>
            )}

            {tab === "vision" && (
              <div>
                <label className="block text-[12px] font-medium text-white/70 mb-1.5">Image d'inspiration (URL)</label>
                <p className="text-[11.5px] text-white/45 mb-2">Affichée en fond de votre page Vision pour vous motiver au quotidien.</p>
                <div className="flex items-center gap-2">
                  <input value={inspirationUrl} onChange={(e) => setInspirationUrlState(e.target.value)} onBlur={saveInspiration}
                    placeholder="https://…" data-testid="settings-inspiration-input"
                    className="flex-1 bg-white/5 border border-white/15 rounded-xl px-3.5 py-2.5 text-sm text-white placeholder:text-white/35 focus:outline-none focus:border-[#D4AF37]/50" />
                  {savingInspiration && <Loader2 size={16} className="animate-spin text-white/40" />}
                </div>
                {inspirationUrl && (
                  <img src={inspirationUrl} alt="" className="mt-3 h-28 w-full rounded-xl object-cover border border-white/10"
                    onError={(e) => { e.currentTarget.style.display = "none"; }} />
                )}
              </div>
            )}

            {tab === "notifications" && (
              <div className="space-y-4">
                <div>
                  <p className="text-[12px] font-medium text-white/70 mb-2">Rappels d'actions</p>
                  <button onClick={toggleWeeklyReview} data-testid="settings-weekly-review-toggle"
                    className="w-full flex items-center justify-between rounded-xl px-3.5 py-3 bg-white/5 border border-white/15 hover:border-[#D4AF37]/30 transition-colors">
                    <span className="text-[13px] text-white/85">Revue hebdomadaire</span>
                    <span className={`relative rounded-full transition-colors ${weeklyReview ? "bg-[#D4AF37]" : "bg-white/15"}`} style={{ width: 40, height: 22 }}>
                      <span className={`absolute top-0.5 rounded-full bg-white transition-transform ${weeklyReview ? "translate-x-[19px]" : "translate-x-0.5"}`} style={{ width: 18, height: 18 }} />
                    </span>
                  </button>
                </div>

                <div>
                  <p className="text-[12px] font-medium text-white/70 mb-2">Notifications push</p>
                  <p className="text-[11.5px] text-white/45 mb-2">Encouragements et alertes envoyés même l'application fermée (énergie basse, factures en retard, vision oubliée).</p>
                  <div className="flex items-center gap-2">
                    <button onClick={togglePush} disabled={pushLoading} data-testid="settings-push-toggle"
                      className="flex-1 inline-flex items-center justify-center gap-2 rounded-xl px-3.5 py-2.5 text-[13px] font-semibold bg-white/5 border border-white/15 hover:border-[#D4AF37]/30 text-white/85 disabled:opacity-50">
                      {pushLoading ? <Loader2 size={14} className="animate-spin" /> : <BellRing size={14} />}
                      {pushSubscribed ? "Désactiver" : "Activer les notifications"}
                    </button>
                    {pushSubscribed && (
                      <button onClick={testPush} data-testid="settings-push-test"
                        className="rounded-xl px-3.5 py-2.5 text-[12px] font-semibold text-[#D4AF37] border border-[#D4AF37]/30 hover:bg-[#D4AF37]/10">
                        Tester
                      </button>
                    )}
                  </div>
                </div>
              </div>
            )}

            {tab === "securite" && (
              <div className="space-y-3">
                <p className="text-[12.5px] text-white/55">Export de vos données comptables (format compatible Pennylane/Indy).</p>
                <a href={exportCsvUrl()} download data-testid="settings-export-csv"
                  className="inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-[13px] font-semibold bg-white/5 border border-white/15 hover:border-[#D4AF37]/30 text-white/85">
                  <Download size={14} /> Exporter mes données (CSV)
                </a>
              </div>
            )}

            {tab === "automatisation" && <Placeholder label="L'automatisation par agents IA" />}
            {tab === "integrations" && <Placeholder label="Les intégrations tierces (banque, Slack…)" />}
            {tab === "facturation" && <Placeholder label="La gestion d'abonnement et de facturation" />}
          </div>
        )}
      </div>
    </div>
  );
}
