/**
 * Parametres.jsx — Modal + Page Paramètres
 * Branché sur les APIs du projet final-main
 *
 * Exports :
 *   export function ParametresModal({ open, onClose })  ← modale flottante
 *   export default Parametres                           ← page plein écran /settings
 *
 * Usage modal :
 *   <ParametresModal open={settingsOpen} onClose={() => setSettingsOpen(false)} />
 */

import React, { useEffect, useState, useCallback } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "@fm/context/AuthContext";
import {
  meApi, energyApi, paymentsApi, integrationsApi,
  analyseApi, streakApi, api, quoteApi, automationsApi,
} from "@fm/lib/api";
import usePageTitle from "@fm/hooks/usePageTitle";
import { toast } from "sonner";
import TopNav from "@fm/components/layout/TopNav";
import FloatingBottomBar from "@fm/components/layout/FloatingBottomBar";
import MobileBottomNav from "@fm/components/layout/MobileBottomNav";
import {
  User, Brain, Lock, Bell, Heart, Zap, Plug, CreditCard, Trash2,
  Check, Download, ExternalLink, ShieldCheck, Cloud, AlertTriangle,
  Calendar, MessageCircle, Users, X, Loader2, Gauge, Save,
  ChevronRight, ArrowUpRight, BarChart3,
} from "lucide-react";

// ─────────────────────────────────────────────────────────────
// NAV sidebar
// ─────────────────────────────────────────────────────────────
const NAV = [
  {
    title: "Mon compte",
    items: [
      { id: "profil",       label: "Mon profil",    icon: User },
      { id: "memoire",      label: "Mémoire IA",    icon: Brain },
      { id: "securite",     label: "Sécurité",      icon: Lock },
    ],
  },
  {
    title: "Préférences",
    items: [
      { id: "notifications", label: "Notifications",  icon: Bell },
      { id: "inspiration",   label: "Inspiration",    icon: Heart },
      { id: "energie",       label: "Énergie & Pulse", icon: Zap },
    ],
  },
  {
    title: "Connexions",
    items: [
      { id: "stockage",      label: "Stockage & Drive", icon: Cloud },
      { id: "integrations",  label: "Intégrations",     icon: Plug },
      { id: "equipe",        label: "Équipe & accès",   icon: Users },
    ],
  },
  {
    title: "Offre",
    items: [
      { id: "consommation",  label: "Consommation",      icon: Gauge },
      { id: "facturation",   label: "Offre & facturation", icon: CreditCard },
    ],
  },
  {
    title: "Danger",
    items: [
      { id: "danger",        label: "Zone de danger",    icon: AlertTriangle },
    ],
  },
];

// ─────────────────────────────────────────────────────────────
// Petits composants réutilisables
// ─────────────────────────────────────────────────────────────
const SectionTitle = ({ children }) => (
  <h2 className="font-display text-[22px] text-navy mb-5">{children}</h2>
);

const Card = ({ title, children, testId }) => (
  <div className="card-z p-6 mb-4" data-testid={testId}>
    {title && <h3 className="font-semibold text-[15px] text-navy mb-4">{title}</h3>}
    {children}
  </div>
);

const Row = ({ label, sub, action, testId }) => (
  <div className="flex items-center justify-between py-3 border-b border-sand-100 last:border-0" data-testid={testId}>
    <div>
      <p className="text-[14px] text-ink">{label}</p>
      {sub && <p className="text-[12px] text-ink-soft mt-0.5">{sub}</p>}
    </div>
    <div className="shrink-0 ml-4">{action}</div>
  </div>
);

const Toggle = ({ on, onChange, testId, disabled }) => (
  <button
    onClick={() => !disabled && onChange(!on)}
    disabled={disabled}
    data-testid={testId}
    className={`relative w-11 h-6 rounded-full transition-colors disabled:opacity-40
      ${on ? "bg-navy" : "bg-sand-300"}`}
  >
    <span className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform
      ${on ? "translate-x-5" : ""}`} />
  </button>
);

const ConnItem = ({ icon: Icon, bg, color, title, sub, action, testId }) => (
  <div className="flex items-center gap-4 py-3.5 border-b border-sand-100 last:border-0" data-testid={testId}>
    <div className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
      style={{ background: bg }}>
      <Icon size={18} style={{ color }} />
    </div>
    <div className="flex-1 min-w-0">
      <p className="text-[14px] font-medium text-ink">{title}</p>
      {sub && <p className="text-[12px] text-ink-soft">{sub}</p>}
    </div>
    {action}
  </div>
);

const btnNavy = "px-4 py-1.5 bg-navy text-cream text-[13px] rounded-full hover:bg-navy/90 transition";
const btnGhost = "px-4 py-1.5 border border-sand-300 text-ink text-[13px] rounded-full hover:border-navy/40 transition";

// ─────────────────────────────────────────────────────────────
// SECTIONS
// ─────────────────────────────────────────────────────────────

// ── Profil ──────────────────────────────────────────────────
function ProfilSection() {
  const { user, refresh } = useAuth();
  const [form, setForm] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    meApi.profile().then(p => setForm(p)).catch(() => {});
  }, []);

  const save = async () => {
    if (!form) return;
    setSaving(true);
    try {
      await meApi.updateProfile({
        first_name:         form.first_name,
        sector:             form.sector,
        stage:              form.stage,
        wa_personal_number: form.wa_personal_number,
        spirituality:       form.spirituality,
        lang:               form.lang,
      });
      await refresh();
      toast.success("Profil enregistré !");
    } catch (e) {
      toast.error(e.message || "Erreur d'enregistrement");
    } finally { setSaving(false); }
  };

  if (!form) return (
    <div className="flex justify-center py-10">
      <Loader2 size={20} className="animate-spin text-navy/40" />
    </div>
  );

  const fields = [
    { key: "first_name",         label: "Prénom",              placeholder: "Votre prénom" },
    { key: "sector",             label: "Secteur d'activité",  placeholder: "Ex: Coaching, SaaS…" },
    { key: "stage",              label: "Stade de développement", placeholder: "Ex: Idée, MVP, Croissance" },
    { key: "wa_personal_number", label: "Numéro WhatsApp",     placeholder: "+33612345678" },
  ];

  return (
    <div data-testid="section-profil">
      <SectionTitle>Mon profil</SectionTitle>
      <Card>
        <div className="space-y-4">
          <Row label="Adresse e-mail" sub={user?.email}
            action={<span className="text-[12px] text-ink-soft bg-sand-100 px-2 py-0.5 rounded-full">
              Plan {(form.plan || "gratuit").charAt(0).toUpperCase() + (form.plan || "gratuit").slice(1)}
            </span>} />
          {fields.map(f => (
            <div key={f.key}>
              <label className="text-[12px] text-ink-soft block mb-1">{f.label}</label>
              <input value={form[f.key] || ""}
                onChange={e => setForm(p => ({ ...p, [f.key]: e.target.value }))}
                placeholder={f.placeholder}
                className="w-full px-4 py-2.5 rounded-xl border border-sand-200 text-[14px] focus:outline-none focus:border-navy/40 bg-white"
                data-testid={`input-${f.key}`} />
            </div>
          ))}
          <div>
            <label className="text-[12px] text-ink-soft block mb-1">Langue</label>
            <select value={form.lang || "fr"}
              onChange={e => setForm(p => ({ ...p, lang: e.target.value }))}
              className="w-full px-4 py-2.5 rounded-xl border border-sand-200 text-[14px] focus:outline-none bg-white"
              data-testid="select-lang">
              <option value="fr">Français</option>
              <option value="en">English</option>
            </select>
          </div>
          <button onClick={save} disabled={saving}
            className={`${btnNavy} flex items-center gap-2 disabled:opacity-50`}
            data-testid="btn-save-profil">
            {saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
            Enregistrer
          </button>
        </div>
      </Card>
    </div>
  );
}

// ── Mémoire IA ───────────────────────────────────────────────
function MemoireSection() {
  const [vision, setVision]   = useState(null);
  const [saving, setSaving]   = useState(false);
  const [analyse, setAnalyse] = useState(null);

  useEffect(() => {
    api.get("/api/vision").then(d => setVision(d?.data || d)).catch(() => setVision({}));
    analyseApi.get().then(d => setAnalyse(d?.data || d)).catch(() => {});
  }, []);

  const save = async () => {
    if (!vision) return;
    setSaving(true);
    try {
      await api.patch("/api/vision", vision);
      toast.success("Mémoire IA mise à jour !");
    } catch { toast.error("Erreur de sauvegarde"); }
    finally { setSaving(false); }
  };

  return (
    <div data-testid="section-memoire">
      <SectionTitle>Mémoire IA</SectionTitle>
      <Card title="Contexte partagé avec le Collaborateur IA">
        <p className="text-[13px] text-ink-soft mb-4 leading-relaxed">
          Ces informations sont réinjectées dans chaque conversation avec votre Collaborateur IA
          pour des conseils personnalisés.
        </p>
        {vision === null ? (
          <div className="flex justify-center py-6">
            <Loader2 size={18} className="animate-spin text-navy/40" />
          </div>
        ) : (
          <div className="space-y-3">
            {[
              { key: "why",   label: "Pourquoi (votre raison d'être)",       placeholder: "Pourquoi faites-vous ce que vous faites ?" },
              { key: "what",  label: "Quoi (votre offre / proposition)",     placeholder: "Que proposez-vous concrètement ?" },
              { key: "who",   label: "Pour qui (votre cible)",               placeholder: "Qui aidez-vous ?" },
              { key: "how",   label: "Comment (votre approche unique)",      placeholder: "Qu'est-ce qui vous différencie ?" },
            ].map(f => (
              <div key={f.key}>
                <label className="text-[12px] text-ink-soft block mb-1">{f.label}</label>
                <textarea
                  value={vision?.[f.key] || ""}
                  onChange={e => setVision(p => ({ ...p, [f.key]: e.target.value }))}
                  placeholder={f.placeholder}
                  rows={2}
                  className="w-full px-4 py-2.5 rounded-xl border border-sand-200 text-[13px] resize-none focus:outline-none focus:border-navy/40 bg-white"
                  data-testid={`vision-${f.key}`}
                />
              </div>
            ))}
            <button onClick={save} disabled={saving}
              className={`${btnNavy} flex items-center gap-2 disabled:opacity-50`}
              data-testid="btn-save-memoire">
              {saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
              Sauvegarder
            </button>
          </div>
        )}
      </Card>

      {analyse && (
        <Card title="Dernière analyse">
          <Row label="Score business" action={
            <span className="font-display text-[22px] text-navy">{analyse.score ?? "—"}<span className="text-[14px] text-ink-soft">/100</span></span>
          } />
          {analyse.verdict?.continue && (
            <Row label="Recommandation IA" sub={analyse.verdict.continue} />
          )}
          <button onClick={() => analyseApi.run().then(analyseApi.get).then(setAnalyse).catch(() => {})}
            className={`${btnGhost} mt-2 flex items-center gap-2 text-[13px]`}
            data-testid="btn-run-analyse">
            Relancer l'analyse
          </button>
        </Card>
      )}
    </div>
  );
}

// ── Sécurité ─────────────────────────────────────────────────
function SecuriteSection() {
  const { user } = useAuth();
  const [sending, setSending] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(false);
  const [confirmText, setConfirmText] = useState("");

  const sendReset = async () => {
    setSending(true);
    try {
      await api.post("/api/auth/magic/request-link", { email: user?.email });
      toast.success("Lien de connexion envoyé par email !");
    } catch { toast.error("Erreur d'envoi"); }
    finally { setSending(false); }
  };

  const exportData = async () => {
    setExporting(true);
    try {
      const token = localStorage.getItem("mxai_token") || "";
      const r = await fetch(`${process.env.REACT_APP_BACKEND_URL || ""}/api/auth/export-data`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (r.ok) {
        const data = await r.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = `zayado-export-${user?.email}.json`;
        a.click();
        URL.revokeObjectURL(a.href);
        toast.success("Données exportées !");
      } else {
        toast.error("Erreur d'export");
      }
    } catch { toast.error("Erreur d'export"); }
    finally { setExporting(false); }
  };

  const deleteAccount = async () => {
    if (confirmText.trim().toUpperCase() !== "SUPPRIMER") {
      toast.error("Tapez SUPPRIMER pour confirmer");
      return;
    }
    setDeleting(true);
    try {
      const token = localStorage.getItem("mxai_token") || "";
      const r = await fetch(`${process.env.REACT_APP_BACKEND_URL || ""}/api/auth/delete-account`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ confirm: "SUPPRIMER" }),
      });
      if (r.ok) {
        toast.success("Compte supprimé. Au revoir.");
        localStorage.clear();
        setTimeout(() => { window.location.href = "/login"; }, 1500);
      } else {
        toast.error("Suppression impossible");
      }
    } catch { toast.error("Erreur"); }
    finally { setDeleting(false); }
  };

  return (
    <div data-testid="section-securite">
      <SectionTitle>Sécurité</SectionTitle>
      <Card title="Accès & authentification">
        <Row label="Email de connexion" sub={user?.email} />
        <Row label="Lien magique"
          sub="Connexion sans mot de passe — lien envoyé par email"
          action={
            <button onClick={sendReset} disabled={sending}
              className={`${btnNavy} flex items-center gap-2 disabled:opacity-50 text-[13px]`}
              data-testid="btn-send-link">
              {sending ? <Loader2 size={13} className="animate-spin" /> : null}
              Envoyer un lien
            </button>
          } />
      </Card>
      <Card title="Données personnelles (RGPD)">
        <Row label="Exporter mes données"
          sub="Télécharger toutes vos données au format JSON"
          action={
            <button onClick={exportData} disabled={exporting}
              className={`${btnGhost} flex items-center gap-2 text-[13px]`}
              data-testid="btn-export-data">
              {exporting ? <Loader2 size={13} className="animate-spin" /> : <Download size={13} />}
              Télécharger
            </button>
          } />
        <Row label="Supprimer mon compte"
          sub="Suppression définitive — anonymisation conforme RGPD"
          action={
            !deleteConfirm ? (
              <button
                onClick={() => setDeleteConfirm(true)}
                className="px-3.5 py-2 rounded-full text-[13px] font-medium transition"
                style={{ background: "#fde2e2", color: "#a01722" }}
                data-testid="btn-delete-account-trigger">
                Supprimer
              </button>
            ) : (
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={confirmText}
                  onChange={(e) => setConfirmText(e.target.value)}
                  placeholder="Tapez SUPPRIMER"
                  className="px-3 py-2 rounded-full text-[12px] bg-white outline-none shadow-sm w-[140px]"
                  data-testid="confirm-delete-input"
                />
                <button
                  onClick={deleteAccount}
                  disabled={deleting || confirmText.trim().toUpperCase() !== "SUPPRIMER"}
                  className="px-3 py-2 rounded-full text-[12px] font-semibold disabled:opacity-50"
                  style={{ background: "#a01722", color: "white" }}
                  data-testid="btn-delete-confirm">
                  {deleting ? <Loader2 size={12} className="animate-spin" /> : "Confirmer"}
                </button>
                <button
                  onClick={() => { setDeleteConfirm(false); setConfirmText(""); }}
                  className="px-3 py-2 rounded-full text-[12px]"
                  style={{ background: "#f6f3ee", color: "#1a3a6e" }}
                  data-testid="btn-delete-cancel">
                  Annuler
                </button>
              </div>
            )
          } />
      </Card>
    </div>
  );
}

// ── Notifications ─────────────────────────────────────────────
function NotificationsSection() {
  const [prefs, setPrefs] = useState({
    task_email: true,
    exclusive_content: true,
    credit_alert: true,
    wa_notifications: false,
  });
  const [swot, setSwot] = useState({ enabled: true, last_sent_at: null });
  const [sendingSwot, setSendingSwot] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem("zayado_notif_prefs");
    if (stored) { try { setPrefs(JSON.parse(stored)); } catch { /* ignore */ } }
    api.get("/api/prefs/swot").then(d => {
      const v = d?.data || d;
      setSwot({ enabled: v?.swot_monthly !== false, last_sent_at: v?.swot_last_sent_at || null });
    }).catch(() => {});
  }, []);

  const toggleSwot = async (on) => {
    setSwot(s => ({ ...s, enabled: on }));
    try { await api.patch("/api/prefs/swot", { swot_monthly: on }); }
    catch { toast.error("Impossible de sauvegarder"); }
  };

  const sendSwotNow = async () => {
    setSendingSwot(true);
    try {
      const d = await api.post("/api/prefs/swot/send-now", {});
      const sent = d?.data?.sent ?? d?.sent;
      if (sent) toast.success("Analyse SWOT envoyée par email 🚀");
      else toast.error("Envoi impossible — réessayez plus tard");
    } catch { toast.error("Erreur d'envoi"); }
    finally { setSendingSwot(false); }
  };

  const save = async () => {
    setSaving(true);
    localStorage.setItem("zayado_notif_prefs", JSON.stringify(prefs));
    try {
      await meApi.updateProfile({ show_energy_popup: prefs.wa_notifications });
    } catch { /* ignore */ }
    setSaving(false);
    toast.success("Préférences enregistrées !");
  };

  const items = [
    { key: "task_email",        label: "Email tâche Agent",       sub: "Notification quand une tâche Agent est traitée" },
    { key: "exclusive_content", label: "Contenu exclusif",        sub: "Offres, mises à jour et guides" },
    { key: "credit_alert",      label: "Alerte crédits faibles",  sub: "Notification quand votre solde passe sous 100" },
    { key: "wa_notifications",  label: "Popup énergie matinale",  sub: "Rappel pour votre check-in énergie quotidien" },
  ];

  return (
    <div data-testid="section-notifications">
      <SectionTitle>Notifications</SectionTitle>
      <Card>
        {items.map(it => (
          <Row key={it.key} label={it.label} sub={it.sub}
            action={<Toggle on={prefs[it.key]} onChange={v => setPrefs(p => ({ ...p, [it.key]: v }))}
              testId={`toggle-${it.key}`} />} />
        ))}
        <button onClick={save} disabled={saving}
          className={`${btnNavy} mt-4 flex items-center gap-2 disabled:opacity-50`}
          data-testid="btn-save-notifs">
          {saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
          Enregistrer
        </button>
      </Card>

      <Card title="Analyse SWOT mensuelle">
        <p className="text-[13px] text-ink-soft mb-3 leading-relaxed">
          Recevez chaque mois par email une analyse SWOT personnalisée de votre business,
          générée automatiquement par Claude (IA stratégique).
        </p>
        <Row
          label="Activer l'envoi mensuel"
          sub={swot.last_sent_at ? `Dernier envoi : ${new Date(swot.last_sent_at).toLocaleDateString("fr-FR")}` : "Pas encore envoyé"}
          action={<Toggle on={swot.enabled} onChange={toggleSwot} testId="toggle-swot-monthly" />}
        />
        <button onClick={sendSwotNow} disabled={sendingSwot}
          className={`${btnNavy} mt-3 flex items-center gap-2 disabled:opacity-50`}
          data-testid="btn-send-swot-now">
          {sendingSwot ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
          {sendingSwot ? "Génération en cours (30-60s)…" : "Envoyer maintenant"}
        </button>
      </Card>
    </div>
  );
}

// ── Inspiration (citation du jour) ────────────────────────────
function InspirationSection() {
  const [quote, setQuote] = useState(null);

  useEffect(() => {
    quoteApi.today().then(d => setQuote(d?.data || d)).catch(() => {});
  }, []);

  return (
    <div data-testid="section-inspiration">
      <SectionTitle>Inspiration</SectionTitle>
      <Card>
        {quote ? (
          <div className="space-y-4">
            <blockquote className="text-[18px] font-display text-navy leading-relaxed italic">
              "{quote.quote || quote.text || quote.content}"
            </blockquote>
            {(quote.author || quote.source) && (
              <p className="text-[13px] text-ink-soft">— {quote.author || quote.source}</p>
            )}
            <p className="text-[12px] text-ink-soft bg-sand-50 px-3 py-2 rounded-lg">
              La citation du jour est sélectionnée automatiquement par l'IA selon votre contexte.
            </p>
          </div>
        ) : (
          <div className="flex justify-center py-8">
            <Loader2 size={18} className="animate-spin text-navy/40" />
          </div>
        )}
      </Card>
    </div>
  );
}

// ── Énergie & Pulse ───────────────────────────────────────────
function EnergieSection() {
  const [today, setToday]   = useState(null);
  const [streak, setStreak] = useState(0);
  const [vals, setVals]     = useState({ physique: 5, mentale: 5, stress: 5 });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    energyApi.today().then(d => {
      setToday(d);
      setStreak(d.streak_days || 0);
      if (d.physique) setVals({ physique: d.physique, mentale: d.mentale, stress: d.stress });
    }).catch(() => {});
    streakApi.get().then(d => setStreak(d.streak_days || 0)).catch(() => {});
  }, []);

  const save = async () => {
    setSaving(true);
    try {
      await energyApi.ritual(vals.physique, vals.mentale, vals.stress);
      toast.success("Check-in enregistré !");
      const d = await energyApi.today();
      setStreak(d.streak_days || 0);
    } catch { toast.error("Erreur d'enregistrement"); }
    finally { setSaving(false); }
  };

  const sliders = [
    { key: "physique", label: "Énergie physique", color: "#27500a" },
    { key: "mentale",  label: "Clarté mentale",   color: "#185fa5" },
    { key: "stress",   label: "Niveau de stress",  color: "#a01722" },
  ];

  return (
    <div data-testid="section-energie">
      <SectionTitle>Énergie & Pulse</SectionTitle>
      <Card>
        <div className="flex items-center gap-4 mb-5 p-4 bg-sand-50 rounded-xl">
          <div className="text-center">
            <div className="font-display text-[36px] text-navy leading-none">{streak}</div>
            <div className="text-[11px] text-ink-soft uppercase tracking-wide mt-0.5">jours de streak</div>
          </div>
          {today?.saved_today && (
            <div className="flex items-center gap-2 text-[13px] text-green-700 bg-green-50 px-3 py-2 rounded-xl">
              <Check size={14} /> Check-in du jour effectué
            </div>
          )}
        </div>
        <div className="space-y-5">
          {sliders.map(s => (
            <div key={s.key}>
              <div className="flex justify-between mb-2">
                <label className="text-[13px] text-ink">{s.label}</label>
                <span className="font-semibold text-[14px]" style={{ color: s.color }}>{vals[s.key]}/10</span>
              </div>
              <input type="range" min={1} max={10} value={vals[s.key]}
                onChange={e => setVals(p => ({ ...p, [s.key]: +e.target.value }))}
                className="w-full accent-navy"
                data-testid={`slider-${s.key}`} />
            </div>
          ))}
          <button onClick={save} disabled={saving}
            className={`${btnNavy} flex items-center gap-2 disabled:opacity-50`}
            data-testid="btn-save-energie">
            {saving ? <Loader2 size={14} className="animate-spin" /> : <Zap size={14} />}
            Enregistrer le check-in
          </button>
        </div>
      </Card>
    </div>
  );
}

// ── Stockage & Drive ──────────────────────────────────────────
function StockageSection() {
  const [google, setGoogle] = useState(null);
  const [ms,     setMs]     = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    Promise.allSettled([
      integrationsApi.google.status(),
      integrationsApi.microsoft.status(),
    ]).then(([g, m]) => {
      if (g.status === "fulfilled") setGoogle(g.value);
      if (m.status === "fulfilled") setMs(m.value);
      setLoading(false);
    });
  }, []);

  useEffect(() => { load(); }, [load]);

  const connectGoogle = async () => {
    try {
      const d = await integrationsApi.google.start();
      if (d.authorization_url) window.location.href = d.authorization_url;
    } catch { toast.error("Erreur de connexion Google"); }
  };

  const connectMs = async () => {
    try {
      const d = await integrationsApi.microsoft.start();
      if (d.authorization_url) window.location.href = d.authorization_url;
    } catch { toast.error("Erreur de connexion Microsoft"); }
  };

  const disconnect = async (provider) => {
    try {
      if (provider === "google") await integrationsApi.google.disconnect();
      else await integrationsApi.microsoft.disconnect();
      toast.success(`${provider === "google" ? "Google Drive" : "OneDrive"} déconnecté`);
      load();
    } catch { toast.error("Erreur"); }
  };

  if (loading) return (
    <div className="flex justify-center py-10"><Loader2 size={18} className="animate-spin text-navy/40" /></div>
  );

  return (
    <div data-testid="section-stockage">
      <SectionTitle>Stockage & Drive</SectionTitle>
      <Card title="Stockage cloud">
        <ConnItem icon={Cloud} bg="#e6f1fb" color="#185fa5"
          title="Google Drive"
          sub={google?.connected ? "Connecté · synchronisation active" : "Non connecté"}
          testId="conn-gdrive"
          action={google?.connected
            ? <button onClick={() => disconnect("google")} className="text-[13px] text-red-500 hover:underline">Déconnecter</button>
            : <button onClick={connectGoogle} className={btnNavy}>Connecter</button>}
        />
        <ConnItem icon={Cloud} bg="#e6f1fb" color="#0078d4"
          title="OneDrive / Microsoft"
          sub={ms?.connected ? "Connecté · OneDrive + SharePoint" : "Non connecté"}
          testId="conn-onedrive"
          action={ms?.connected
            ? <button onClick={() => disconnect("microsoft")} className="text-[13px] text-red-500 hover:underline">Déconnecter</button>
            : <button onClick={connectMs} className={btnNavy}>Connecter</button>}
        />
      </Card>
      <Card title="Synchronisation automatique">
        <p className="text-[13px] text-ink-soft mb-3 leading-relaxed">
          Les conversations et livrables IA longs sont sauvegardés automatiquement sur votre drive connecté.
        </p>
        <Row label="Source active"
          action={
            <select defaultValue={localStorage.getItem("zayado_autosync_source") || "none"}
              onChange={e => {
                localStorage.setItem("zayado_autosync_source", e.target.value);
                toast.success(`Sync auto : ${e.target.value === "none" ? "désactivée" : e.target.value}`);
              }}
              className="px-3 py-1.5 rounded-xl border border-sand-200 text-[13px] bg-white"
              data-testid="select-sync-source">
              <option value="none">Désactivée</option>
              {google?.connected && <option value="gdrive">Google Drive</option>}
              {ms?.connected && <option value="onedrive">OneDrive</option>}
            </select>
          } />
      </Card>
    </div>
  );
}

// ── Intégrations ──────────────────────────────────────────────
// Catalogue d'outils & canaux gérés via Make/Zapier (hub universel)
const TOOL_CATALOG = [
  { id: "stripe",   name: "Stripe",            category: "Paiement",     note: "CA temps réel · webhooks Make" },
  { id: "mollie",   name: "Mollie",            category: "Paiement",     note: "Encaissements EU · via Make" },
  { id: "paypal",   name: "PayPal",            category: "Paiement",     note: "Encaissements · via Make" },
  { id: "woo",      name: "WooCommerce",       category: "Boutique",     note: "Commandes & clients · webhook direct ou Make" },
  { id: "shopify",  name: "Shopify",           category: "Boutique",     note: "Commandes · via Make" },
  { id: "fbads",    name: "Facebook Ads",      category: "Acquisition",  note: "Leads Ads · via Make" },
  { id: "fbgroup",  name: "Facebook Groupes",  category: "Conversations", note: "Posts & messages communauté · via Make" },
  { id: "youtube",  name: "YouTube",           category: "Commentaires", note: "Commentaires & réponses · via Make" },
  { id: "instagram",name: "Instagram",         category: "DMs",          note: "Messages directs · via Make" },
  { id: "gmail",    name: "Gmail",             category: "Email",        note: "Drafts & envois IA · via Make" },
  { id: "brevo",    name: "Brevo",             category: "Newsletter",   note: "Listes & campagnes · API directe" },
  { id: "notion",   name: "Notion",            category: "Notes",        note: "Bilans hebdo & roadmap · via Make" },
  { id: "odoo",     name: "Odoo",              category: "ERP",          note: "Factures & clients · via Make" },
  { id: "telegram", name: "Telegram",          category: "Messagerie",   note: "Notifications légères · via Make" },
  { id: "ms365",    name: "Microsoft 365",     category: "Documents",    note: "Alternative Google Drive · OAuth" },
  { id: "gdrive",   name: "Google Drive",      category: "Documents",    note: "Dépôt livrables IA · OAuth" },
];

// Automatisations préconfigurées (state local)
const DEFAULT_AUTOMATIONS = [
  { id: "a1", title: "Nouveau client Stripe → email bienvenue + fiche CRM",
    when: "Quand un paiement Stripe arrive",
    then: "L'IA génère un email Brevo personnalisé + crée la fiche CRM", enabled: true },
  { id: "a2", title: "Commentaire YouTube → réponse IA proposée",
    when: "Quand un commentaire est posté sur tes vidéos",
    then: "Brouillon de réponse cohérent avec ton ton, prêt à valider", enabled: true },
  { id: "a3", title: "Message Facebook Groupe → résumé quotidien",
    when: "Chaque jour à 18h",
    then: "Synthèse des conversations & questions importantes", enabled: false },
  { id: "a4", title: "Lead Facebook Ads → relance WhatsApp",
    when: "Quand un lead Ads est capté",
    then: "Message de bienvenue WhatsApp + ajout dans Brevo", enabled: true },
  { id: "a5", title: "Compte-rendu de semaine automatique",
    when: "Tous les vendredis à 17h",
    then: "Synthèse envoyée par email + déposée Notion", enabled: true },
];

function IntegrationsSection() {
  const [ai, setAi] = useState({ agenda: true });
  const set = (k, v) => setAi(p => ({ ...p, [k]: v }));

  const [waStatus, setWaStatus]   = useState(null);
  const [waLoading, setWaLoading] = useState(true);
  const [revenueStatus, setRevenueStatus] = useState(null);
  const [brevoStatus, setBrevoStatus] = useState(null);
  const [waPersonal, setWaPersonal] = useState({ service_url: "", service_secret: "" });
  const [savingWa, setSavingWa] = useState(false);

  // Automatisations — persistées en DB via /api/automations
  const [autos, setAutos] = useState(DEFAULT_AUTOMATIONS);
  const [autoRunning, setAutoRunning] = useState(null);

  useEffect(() => {
    automationsApi.list()
      .then((d) => { if (d?.automations) setAutos(d.automations); })
      .catch(() => {});
  }, []);

  const toggleAuto = async (id) => {
    const current = autos.find((a) => a.id === id);
    if (!current) return;
    const next = !current.enabled;
    setAutos((prev) => prev.map((a) => a.id === id ? { ...a, enabled: next } : a));
    try {
      await automationsApi.toggle(id, next);
    } catch (e) {
      toast.error(e.message || "Erreur de mise à jour");
      setAutos((prev) => prev.map((a) => a.id === id ? { ...a, enabled: !next } : a));
    }
  };

  const runAutoManual = async (id) => {
    setAutoRunning(id);
    try {
      const result = await automationsApi.run(id);
      if (result?.status === "success") toast.success(`Automatisation exécutée : ${result.message}`);
      else if (result?.status === "skipped") toast.info(result.message || "Automatisation ignorée");
      else toast.error(result?.message || "Erreur d'exécution");
      // Rafraîchir les données
      const updated = await automationsApi.list();
      if (updated?.automations) setAutos(updated.automations);
    } catch (e) {
      toast.error(e.message || "Exécution échouée");
    } finally {
      setAutoRunning(null);
    }
  };

  const apiBase = process.env.REACT_APP_BACKEND_URL || "";
  const webhookUrl = `${apiBase}/api/revenue/webhook`;

  useEffect(() => {
    api.get("/api/whatsapp/status")
      .then(d => setWaStatus(d))
      .catch(() => setWaStatus(null))
      .finally(() => setWaLoading(false));
    api.get("/api/revenue/sources/status").then(setRevenueStatus).catch(() => {});
    api.get("/api/integrations/brevo/status").then(setBrevoStatus).catch(() => {});
    api.get("/api/integrations/whatsapp-personal/status").then((d) => setWaPersonal((p) => ({ ...p, ...d }))).catch(() => {});
  }, []);

  const copyWebhook = () => { navigator.clipboard.writeText(webhookUrl); toast.success("URL copiée"); };

  const saveWaPersonal = async () => {
    setSavingWa(true);
    try {
      await api.post("/api/integrations/whatsapp-personal", waPersonal);
      toast.success("WhatsApp Railway enregistré");
    } catch (e) {
      toast.error(e?.detail || "Échec de la sauvegarde");
    } finally { setSavingWa(false); }
  };

  return (
    <div data-testid="section-integrations">
      <SectionTitle>Intégrations</SectionTitle>

      <Card title="Hub universel · Make / Zapier" testId="card-revenue">
        <p className="text-[12.5px] text-ink-soft -mt-1 mb-4">
          Un seul webhook pour <strong>tout</strong> : paiements, leads, conversations communauté, commentaires, DMs.
          Aucun OAuth, aucune clé sensible ici — vous gardez la main depuis Make/Zapier.
        </p>

        <ConnItem icon={Plug} bg="#fdf5d9" color="#8a6b06"
          title="Webhook universel"
          sub={<>
            <span className="block mb-2">
              <strong>Paiements :</strong> Stripe · Mollie · PayPal · WooCommerce · Shopify
            </span>
            <span className="block mb-2">
              <strong>Acquisition :</strong> Facebook Ads · Google Ads · TikTok Ads
            </span>
            <span className="block mb-2">
              <strong>Conversations & communauté :</strong> Facebook Groupes · YouTube (commentaires) · Instagram DMs · Telegram
            </span>
            <span className="block mb-3">
              <strong>Productivité :</strong> Gmail · Notion · Odoo · Airtable…
            </span>
            <span className="block mb-2 text-ink-soft">
              <strong>3 étapes :</strong> 1) Créez un scénario dans Make/Zapier ·
              2) Source = l'outil voulu · 3) Action = HTTP POST vers l'URL ci-dessous.
            </span>
            <code className="block px-2 py-1.5 bg-sand-100 rounded text-[11px] text-ink truncate">{webhookUrl}</code>
            <span className="block mt-2 text-[11px] text-ink-soft italic">
              Payload attendu : <code>{`{ user_id, amount_eur, source, occurred_at }`}</code>
            </span>
          </>}
          testId="int-webhook"
          action={<button onClick={copyWebhook} className={btnNavy} data-testid="webhook-copy">Copier l&apos;URL</button>}
        />

        <ConnItem icon={Plug} bg="#e8f4ec" color="#1f6c3a"
          title="WooCommerce (branchement direct)"
          sub={revenueStatus?.woocommerce?.connected
            ? "Webhook actif"
            : "Si vous n'utilisez pas Make : Settings → Advanced → Webhooks → Topic 'Order completed' → URL ci-dessus."}
          testId="int-woo"
          action={<button className={btnGhost} onClick={copyWebhook}>Copier l&apos;URL</button>}
        />
      </Card>

      {/* ── Vos outils & canaux (grille catalogue) ─────────────── */}
      <Card title="Vos outils & canaux" testId="card-tools-grid">
        <p className="text-[12.5px] text-ink-soft -mt-1 mb-4">
          L'IA travaille avec votre stack. Connectez-les en un scénario Make/Zapier vers le webhook ci-dessus —
          pas besoin de coller des clés API ici.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3" data-testid="tools-grid">
          {TOOL_CATALOG.map((t) => (
            <div key={t.id}
              className="flex items-start gap-3 p-3 rounded-xl border border-sand-200 bg-white hover:border-navy/20 transition"
              data-testid={`tool-${t.id}`}>
              <div className="w-9 h-9 rounded-xl grid place-items-center shrink-0 bg-sand-100 text-navy">
                <Plug size={15} />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 flex-wrap mb-0.5">
                  <span className="text-[13.5px] font-medium text-ink">{t.name}</span>
                  <span className="text-[10px] uppercase tracking-wide text-ink-soft bg-sand-50 px-1.5 py-0.5 rounded">
                    {t.category}
                  </span>
                </div>
                <p className="text-[11.5px] text-ink-soft leading-snug">{t.note}</p>
              </div>
            </div>
          ))}
        </div>
        <p className="text-[11px] text-ink-soft italic mt-3">
          Vous ne voyez pas votre outil ? Make/Zapier supporte +1500 apps. Branchez-les sur le webhook.
        </p>
      </Card>

      {/* ── Automatisations préconfigurées ──────────────────────── */}
      <Card title="Automatisations préconfigurées" testId="card-automations">
        <p className="text-[12.5px] text-ink-soft -mt-1 mb-4">
          Proposées par l'IA, jamais imposées. Activez celles qui collent à votre rythme.
        </p>
        <div className="space-y-2.5" data-testid="automations-list">
          {autos.map((a) => (
            <div key={a.id}
              className="flex items-start gap-3 p-3.5 rounded-xl border border-sand-200 bg-white"
              data-testid={`auto-${a.id}`}>
              <div className="w-9 h-9 rounded-full grid place-items-center shrink-0"
                style={{ background: a.enabled ? "#fdf5d9" : "#f5f1ea", color: "#8a6b06" }}>
                <Zap size={14} />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-[13.5px] font-medium text-ink mb-1">{a.title}</p>
                <p className="text-[11.5px] text-ink-soft leading-relaxed">
                  <span className="font-medium text-ink">Quand</span> {a.when} → <span className="font-medium text-ink">Alors</span> {a.then}
                </p>
                {a.last_run && (
                  <p className="text-[11px] text-ink-muted mt-1">
                    Dernier run : {new Date(a.last_run).toLocaleString()} · {a.run_count || 0} exécutions
                  </p>
                )}
                {a.enabled && (
                  <button
                    data-testid={`auto-run-${a.id}`}
                    onClick={() => runAutoManual(a.id)}
                    disabled={autoRunning === a.id}
                    className="mt-2 inline-flex items-center gap-1.5 px-3 h-7 rounded-full bg-cream-soft border border-sand-300 text-[11.5px] text-navy font-medium hover:bg-sand-200 disabled:opacity-50"
                  >
                    {autoRunning === a.id ? <Loader2 size={11} className="animate-spin" /> : <Zap size={11} />}
                    Tester maintenant
                  </button>
                )}
              </div>
              <Toggle
                on={a.enabled}
                onChange={() => toggleAuto(a.id)}
                testId={`auto-toggle-${a.id}`}
              />
            </div>
          ))}
        </div>
      </Card>

      <Card title="CRM · Leads" testId="card-brevo">
        <ConnItem icon={Users} bg="#e6f1fb" color="#185fa5"
          title="Brevo · CRM"
          sub={brevoStatus?.connected
            ? `Connecté · liste #${brevoStatus.list_id || "—"}`
            : "Les leads captés par tes Growth Agents (web + WhatsApp) atterriront dans la liste Brevo choisie."}
          testId="int-brevo"
          action={
            brevoStatus?.connected
              ? <span className="text-[12px] bg-green-50 text-green-700 px-2 py-0.5 rounded-full">✓ Connectée</span>
              : <button className={btnGhost} onClick={() => toast.info("Définis BREVO_API_KEY dans tes variables d'environnement puis recharge cette page.")}>Charger mes listes</button>
          }
        />
      </Card>

      <Card title="Growth Agents — WhatsApp" testId="card-wa">
        <ConnItem icon={MessageCircle} bg="#faeeda" color="#633806"
          title="WhatsApp Business (Cockpit)"
          sub={waLoading ? "Vérification…" : waStatus?.connected ? `Connecté · ${waStatus.phone || ""}` : "Growth Agent · Non connecté"}
          testId="int-whatsapp"
          action={
            waStatus?.connected
              ? <span className="text-[12px] bg-green-50 text-green-700 px-2 py-0.5 rounded-full">✓ Actif</span>
              : <button onClick={() => toast.info("Ouvre le Growth Agent puis 'Connecter WhatsApp'")} className={btnNavy}>Connecter</button>
          }
        />
        <Row label="Backend Railway personnel"
          sub="Micro-service WhatsApp-Web hébergé sur Railway. Configuré selon ton offre."
          action={<span className="text-[11px] text-ink-soft italic">{waPersonal?.service_url ? "Configuré" : "Non configuré"}</span>}
        />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mt-2">
          <input value={waPersonal.service_url || ""} onChange={(e) => setWaPersonal({ ...waPersonal, service_url: e.target.value })} placeholder="https://whatsapp-svc-xxx.up.railway.app" className="px-3 py-2 border border-sand-200 rounded-xl text-[13px] bg-white" data-testid="wa-svc-url" />
          <input value={waPersonal.service_secret || ""} onChange={(e) => setWaPersonal({ ...waPersonal, service_secret: e.target.value })} placeholder="Service secret" type="password" className="px-3 py-2 border border-sand-200 rounded-xl text-[13px] bg-white" data-testid="wa-svc-secret" />
        </div>
        <div className="mt-2 flex justify-end">
          <button onClick={saveWaPersonal} disabled={savingWa} className={btnNavy} data-testid="wa-svc-save">
            {savingWa ? <Loader2 size={12} className="animate-spin" /> : "Enregistrer"}
          </button>
        </div>
      </Card>

      <Card title="Collaborateur IA — configuration" testId="card-collab">
        <Row label="Mode par défaut"
          sub="Onglet ouvert au lancement du chat"
          action={
            <select defaultValue={localStorage.getItem("collab_default_mode") || "rapide"}
              onChange={e => localStorage.setItem("collab_default_mode", e.target.value)}
              className="px-3 py-1.5 rounded-xl border border-sand-200 text-[13px] bg-white"
              data-testid="select-collab-mode">
              <option value="rapide">Rapide</option>
              <option value="avance">Avancé</option>
              <option value="document">Document</option>
            </select>
          } />
        <Row label="Suggestions contextuelles"
          sub="Boutons d'action selon la page ouverte"
          action={<Toggle
            on={localStorage.getItem("collab_suggestions") !== "false"}
            onChange={v => localStorage.setItem("collab_suggestions", v ? "true" : "false")}
            testId="toggle-suggestions" />}
        />
      </Card>

      <Card title="Autres connexions" testId="card-others">
        <ConnItem icon={Calendar} bg="#e6f1fb" color="#185fa5"
          title="Google Agenda"
          sub="Prise de RDV Growth Agent"
          testId="int-agenda"
          action={<Toggle on={ai.agenda !== false} onChange={v => set("agenda", v)} testId="toggle-agenda" />}
        />
        <ConnItem icon={Users} bg="#eeedfe" color="#3c3489"
          title="Microsoft Teams"
          sub="Disponible offre Business"
          testId="int-teams"
          action={<span className="text-[12px] bg-sand-100 text-ink-soft px-2 py-0.5 rounded-full">Business</span>}
        />
        <ConnItem icon={Plug} bg="#eaf3de" color="#27500a"
          title="API personnalisée"
          sub="Connecter votre propre système"
          testId="int-api"
          action={<button className={btnGhost}>Configurer</button>}
        />
      </Card>
    </div>
  );
}

// ── Équipe ────────────────────────────────────────────────────
function EquipeSection() {
  const { user } = useAuth();
  const isPro = ["pro", "premium", "business", "team"].includes(user?.plan);

  return (
    <div data-testid="section-equipe">
      <SectionTitle>Équipe & accès</SectionTitle>
      {!isPro ? (
        <Card>
          <div className="text-center py-4">
            <Users size={28} className="mx-auto mb-3 text-navy/30" />
            <p className="text-[14px] text-ink-soft mb-3">La gestion d'équipe est disponible à partir du plan Pro.</p>
            <button onClick={() => window.location.href = "/pricing"}
              className={`${btnNavy} inline-flex items-center gap-2`}
              data-testid="btn-upgrade-team">
              Voir les offres <ChevronRight size={14} />
            </button>
          </div>
        </Card>
      ) : (
        <Card title="Membres de l'équipe">
          <p className="text-[13px] text-ink-soft">Gestion d'équipe disponible — contactez le support pour configurer.</p>
        </Card>
      )}
    </div>
  );
}

// ── Consommation ──────────────────────────────────────────────
function ConsommationSection() {
  const { user } = useAuth();
  const [analyse, setAnalyse] = useState(null);
  const [streak, setStreak]   = useState(0);
  const [revenue, setRevenue] = useState([]);

  useEffect(() => {
    analyseApi.get().then(setAnalyse).catch(() => {});
    streakApi.get().then(d => setStreak(d.streak_days || 0)).catch(() => {});
    api.get("/api/revenue/monthly").then(d => setRevenue(Array.isArray(d) ? d : [])).catch(() => {});
  }, []);

  const lastRev = revenue.at(-1);
  const stats = [
    { label: "Plan actuel",      value: user?.plan || "Gratuit",     color: "#185fa5" },
    { label: "Score business",   value: analyse ? `${analyse.score}/100` : "—", color: "#1e3a5f" },
    { label: "Streak",           value: `${streak} jours`,           color: "#27500a" },
    { label: "CA dernier mois",  value: lastRev ? `${lastRev.ca || lastRev.amount || 0} €` : "—", color: "#8a7340" },
  ];

  return (
    <div data-testid="section-consommation">
      <SectionTitle>Consommation</SectionTitle>
      <div className="grid grid-cols-2 gap-3 mb-4">
        {stats.map(s => (
          <div key={s.label} className="card-z p-4 text-center">
            <div className="font-display text-[24px] leading-none mb-1" style={{ color: s.color }}>{s.value}</div>
            <div className="text-[11px] uppercase tracking-wide text-ink-soft">{s.label}</div>
          </div>
        ))}
      </div>
      {analyse && (
        <Card title="Recommandations IA">
          {analyse.verdict?.continue && (
            <Row label="Continuez" sub={analyse.verdict.continue}
              action={<Check size={16} className="text-green-600" />} />
          )}
          {analyse.verdict?.adjust && (
            <Row label="Ajustez" sub={analyse.verdict.adjust} />
          )}
          {analyse.verdict?.stop && (
            <Row label="Arrêtez" sub={analyse.verdict.stop}
              action={<AlertTriangle size={16} className="text-red-500" />} />
          )}
        </Card>
      )}
    </div>
  );
}

// ── Facturation ───────────────────────────────────────────────
function FacturationSection() {
  const { user } = useAuth();
  const [plan,     setPlan]     = useState(null);
  const [loading,  setLoading]  = useState(true);
  const [upgrading, setUpgrading] = useState(false);

  useEffect(() => {
    paymentsApi.status().then(setPlan).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const upgrade = async (p) => {
    setUpgrading(true);
    try {
      const { checkout_url } = await paymentsApi.checkout(p);
      window.location.href = checkout_url;
    } catch (e) {
      toast.error(e.message || "Mollie indisponible");
      setUpgrading(false);
    }
  };

  return (
    <div data-testid="section-facturation">
      <SectionTitle>Offre & facturation</SectionTitle>
      {loading ? (
        <div className="flex justify-center py-10"><Loader2 size={18} className="animate-spin text-navy/40" /></div>
      ) : (
        <>
          <Card>
            <Row label="Plan actuel"
              action={<span className="chip chip-navy capitalize">{plan?.plan || "Gratuit"}</span>} />
            {plan?.since && (
              <Row label="Actif depuis" sub={new Date(plan.since).toLocaleDateString("fr-FR")} />
            )}
            <div className="mt-4">
              <button onClick={() => upgrade("premium")} disabled={upgrading}
                className={`${btnNavy} flex items-center gap-2 disabled:opacity-50`}
                data-testid="btn-upgrade">
                {upgrading ? <Loader2 size={14} className="animate-spin" /> : <ArrowUpRight size={14} />}
                Changer d'offre
              </button>
            </div>
          </Card>

          <Card title="Offres disponibles">
            {[
              { id: "solo",     label: "Solo",     price: "19€/mois",  desc: "Idéal pour démarrer" },
              { id: "premium",  label: "Pro",       price: "49€/mois",  desc: "Le plus populaire ⭐" },
              { id: "business", label: "Business",  price: "99€/mois",  desc: "Équipe & fonctionnalités avancées" },
            ].map(o => (
              <div key={o.id} className="flex items-center justify-between py-3 border-b border-sand-100 last:border-0">
                <div>
                  <p className="text-[14px] font-medium text-ink">{o.label}</p>
                  <p className="text-[12px] text-ink-soft">{o.desc}</p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-[14px] font-semibold text-navy">{o.price}</span>
                  {plan?.plan !== o.id && (
                    <button onClick={() => upgrade(o.id)} disabled={upgrading}
                      className={btnGhost + " text-[13px]"}
                      data-testid={`btn-upgrade-${o.id}`}>
                      Choisir
                    </button>
                  )}
                  {plan?.plan === o.id && (
                    <span className="text-[12px] bg-green-50 text-green-700 px-2 py-0.5 rounded-full">Actuel</span>
                  )}
                </div>
              </div>
            ))}
          </Card>
        </>
      )}
    </div>
  );
}

// ── Zone de danger ────────────────────────────────────────────
function DangerSection() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [confirming, setConfirming] = useState(false);
  const [deleting,   setDeleting]   = useState(false);

  const deleteAccount = async () => {
    setDeleting(true);
    try {
      const token = localStorage.getItem("mxai_token") || "";
      await fetch(`${process.env.REACT_APP_BACKEND_URL || ""}/api/auth/me`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Demande de suppression enregistrée.");
      logout();
      navigate("/");
    } catch {
      toast.error("Erreur — contactez le support.");
    } finally {
      setDeleting(false);
      setConfirming(false);
    }
  };

  return (
    <div data-testid="section-danger">
      <SectionTitle>Zone de danger</SectionTitle>
      <Card>
        <div className="p-4 border border-red-200 rounded-xl bg-red-50/40">
          <div className="flex items-start gap-3 mb-4">
            <AlertTriangle size={18} className="text-red-500 mt-0.5 shrink-0" />
            <div>
              <p className="text-[14px] font-semibold text-red-700">Supprimer mon compte</p>
              <p className="text-[12px] text-red-600 mt-0.5 leading-relaxed">
                Cette action est irréversible. Toutes vos données, projets et conversations seront supprimés définitivement.
              </p>
            </div>
          </div>
          {!confirming ? (
            <button onClick={() => setConfirming(true)}
              className="px-4 py-2 bg-red-600 text-white text-[13px] rounded-xl hover:bg-red-700 transition"
              data-testid="btn-delete-init">
              Supprimer mon compte
            </button>
          ) : (
            <div className="space-y-3">
              <p className="text-[13px] text-red-700 font-medium">
                Confirmez-vous la suppression du compte <strong>{user?.email}</strong> ?
              </p>
              <div className="flex gap-2">
                <button onClick={deleteAccount} disabled={deleting}
                  className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white text-[13px] rounded-xl hover:bg-red-700 transition disabled:opacity-50"
                  data-testid="btn-delete-confirm">
                  {deleting ? <Loader2 size={13} className="animate-spin" /> : <Trash2 size={13} />}
                  Confirmer la suppression
                </button>
                <button onClick={() => setConfirming(false)}
                  className={`${btnGhost} text-[13px]`}
                  data-testid="btn-delete-cancel">
                  Annuler
                </button>
              </div>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Contenu principal (partagé page + modal)
// ─────────────────────────────────────────────────────────────
const SECTIONS = {
  profil:        <ProfilSection />,
  memoire:       <MemoireSection />,
  securite:      <SecuriteSection />,
  notifications: <NotificationsSection />,
  inspiration:   <InspirationSection />,
  energie:       <EnergieSection />,
  stockage:      <StockageSection />,
  integrations:  <IntegrationsSection />,
  equipe:        <EquipeSection />,
  consommation:  <ConsommationSection />,
  facturation:   <FacturationSection />,
  danger:        <DangerSection />,
};

function ParametresContent({ onClose, initialSection = "profil" }) {
  const [active, setActive] = useState(initialSection);
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  // Flatten all items for mobile horizontal tabs
  const allItems = NAV.flatMap((g) => g.items);
  const activeLabel = allItems.find((i) => i.id === active)?.label || "Paramètres";

  return (
    <div className="flex flex-col md:flex-row h-full min-h-0" data-testid="parametres-content">
      {/* ── Header mobile (titre + close + tabs horizontaux scrollables) ───────── */}
      <div className="md:hidden flex flex-col border-b border-sand-200 bg-white shrink-0">
        <div className="flex items-center justify-between px-4 py-3">
          <div>
            <h1 className="font-display text-[18px] text-navy leading-none">Paramètres</h1>
            <p className="text-[11px] text-ink-soft mt-0.5 truncate">{activeLabel}</p>
          </div>
          {onClose && (
            <button onClick={onClose}
              className="p-2 rounded-full hover:bg-sand-100 text-ink-soft transition"
              data-testid="btn-close-parametres-mobile" aria-label="Fermer">
              <X size={18} />
            </button>
          )}
        </div>
        <div className="overflow-x-auto no-scrollbar border-t border-sand-100">
          <div className="flex items-center gap-1 px-3 py-2 min-w-max">
            {allItems.map((item) => {
              const Icon = item.icon;
              const isActive = active === item.id;
              const isDanger = item.id === "danger";
              return (
                <button
                  key={item.id}
                  onClick={() => setActive(item.id)}
                  data-testid={`mob-nav-${item.id}`}
                  className={`shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[12.5px] whitespace-nowrap transition
                    ${isActive
                      ? isDanger ? "bg-red-50 text-red-700 font-medium border border-red-200" : "bg-navy text-cream font-medium"
                      : isDanger ? "text-red-500 hover:bg-red-50" : "text-ink-soft hover:bg-sand-100"
                    }`}>
                  <Icon size={13} className="shrink-0" />
                  {item.label}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* ── Sidebar desktop ───────────────────────────────────────────────────── */}
      <aside className="hidden md:block w-[220px] shrink-0 border-r border-sand-200 bg-white overflow-y-auto py-4 px-2">
        <div className="flex items-center justify-between px-3 mb-4">
          <h1 className="font-display text-[18px] text-navy">Paramètres</h1>
          {onClose && (
            <button onClick={onClose}
              className="p-1.5 rounded-xl hover:bg-sand-100 text-ink-soft transition"
              data-testid="btn-close-parametres">
              <X size={16} />
            </button>
          )}
        </div>

        {NAV.map(group => (
          <div key={group.title} className="mb-4">
            <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-ink-soft px-3 mb-1.5">
              {group.title}
            </p>
            {group.items.map(item => {
              const Icon = item.icon;
              const isActive = active === item.id;
              const isDanger = item.id === "danger";
              return (
                <button key={item.id} onClick={() => setActive(item.id)}
                  data-testid={`nav-${item.id}`}
                  className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-[13.5px] transition mb-0.5
                    ${isActive
                      ? isDanger ? "bg-red-50 text-red-700 font-medium" : "bg-navy/8 text-navy font-medium"
                      : isDanger ? "text-red-500 hover:bg-red-50" : "text-ink-soft hover:bg-sand-50 hover:text-ink"
                    }`}>
                  <Icon size={15} className="shrink-0" />
                  {item.label}
                </button>
              );
            })}
          </div>
        ))}

        {/* Déconnexion */}
        <div className="mt-4 pt-4 border-t border-sand-200 px-2">
          <button
            onClick={() => { logout(); onClose?.(); navigate("/login"); }}
            className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-[13.5px] text-ink-soft hover:bg-sand-50 hover:text-ink transition"
            data-testid="btn-logout">
            <ShieldCheck size={15} className="shrink-0" />
            Se déconnecter
          </button>
        </div>
      </aside>

      {/* ── Contenu principal ────────────────────────────────────────────────── */}
      <main className="flex-1 overflow-y-auto bg-cream-base px-4 md:px-8 py-5 md:py-7 min-h-0" data-testid="parametres-main">
        {/* Bouton À jour (modal seulement, desktop) */}
        {onClose && (
          <div className="hidden md:flex justify-end mb-4">
            <button
              onClick={onClose}
              className="flex items-center gap-2 px-4 py-1.5 bg-navy text-cream text-[13px] rounded-full hover:bg-navy/90 transition"
              data-testid="btn-a-jour">
              <Check size={13} /> À jour
            </button>
          </div>
        )}
        {SECTIONS[active] || <p className="text-ink-soft">Section à venir.</p>}

        {/* Déconnexion mobile (en bas du contenu, sans sidebar) */}
        <div className="md:hidden mt-6 pt-5 border-t border-sand-200">
          <button
            onClick={() => { logout(); onClose?.(); navigate("/login"); }}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-full text-[13.5px] text-red-600 border border-red-200 hover:bg-red-50 transition"
            data-testid="btn-logout-mobile">
            <ShieldCheck size={15} />
            Se déconnecter
          </button>
        </div>
      </main>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// MODAL
// ─────────────────────────────────────────────────────────────
export function ParametresModal({ open, onClose, initialSection }) {
  useEffect(() => {
    const onKey = (e) => { if (e.key === "Escape" && open) onClose?.(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  // Lock body scroll quand la modal est ouverte (sinon c'est la page qui scrolle, pas la modal)
  useEffect(() => {
    if (!open) return;
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = prevOverflow; };
  }, [open]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[80] flex items-center justify-center p-0 md:p-6"
      data-testid="parametres-modal"
      style={{ overscrollBehavior: "contain" }}>
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full h-full md:h-[90vh] md:max-w-[920px] md:rounded-2xl overflow-hidden shadow-2xl flex flex-col bg-white"
           style={{ overscrollBehavior: "contain" }}>
        <ParametresContent onClose={onClose} initialSection={initialSection} />
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// PAGE PLEIN ÉCRAN (/settings)
// ─────────────────────────────────────────────────────────────
export default function Parametres() {
  usePageTitle("Paramètres");
  const [panel, setPanel] = useState(null);
  const location = useLocation();
  const initialSection = new URLSearchParams(location.search).get("section") || "profil";

  return (
    <div className="min-h-screen bg-cream-base">
      <TopNav onOpenChat={() => setPanel("collaborateur")} />
      <div className="pt-[72px] h-screen flex flex-col">
        <ParametresContent initialSection={initialSection} />
      </div>
      <FloatingBottomBar activePanel={panel} onOpen={setPanel} />
      <MobileBottomNav onOpenCollab={() => setPanel("collaborateur")} />
    </div>
  );
}
