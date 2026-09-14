import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { createPortal } from "react-dom";
import {
  Moon, LayoutGrid, PanelLeft, Palette, User, Globe, Check,
  Plug, Link2, Trash2, ShieldCheck, Loader2, Images, Quote,
  Bell, Heart, Lock, Brain, CreditCard, X, Download,
  Save, ChevronRight, Upload, Image as ImageIcon,
  Search, Zap, BellRing, Settings as SettingsIcon, LineChart,
  AlertTriangle, Battery, CheckCircle2, FileText, FileUp, Filter,
  GraduationCap, Kanban, MapPin, MessageSquare, MoreHorizontal, Plus,
  Radar, Send, ShieldAlert, ShoppingBag, Sparkles, StickyNote, Newspaper,
  ThumbsUp, TrendingUp, Wallet, Wand2,
} from "lucide-react";
import {
  getProfile, setProfile, getReminders, setReminders,
  getInspiration, setInspirationImage, exportCsvUrl,
  getVisionMemory, setVisionMemory, getPlan, setPlan,
  getNewsPreferences, setNewsPreferences,
  getOdooConfig, setOdooConfig, syncOdoo,
  getBankAggregatorConfig, setBankAggregatorConfig, syncBankAggregator,
  authMe,
} from "../lib/api";
import { isPushSubscribed, subscribeToPush, unsubscribeFromPush, sendTestPush } from "../lib/pwa";
import { toast } from "sonner";

const PREFERENCE_KEY = "cours-main-settings-preferences";
const TRANSLATIONS = {
  settings: "Paramètres", set_saved: "Préférences enregistrées", set_appearance: "Apparence",
  set_theme: "Choisissez l'apparence de votre cockpit", theme_dark: "Mode sombre", theme_light: "Mode clair",
  set_menu: "Position du menu", menu_bottom: "Menu bas", menu_left: "Menu latéral", language: "Langue",
  set_profile: "Profil", set_name: "Nom affiché", set_email: "Email",
};

function usePrefs() {
  const [prefs, setPrefs] = useState(() => {
    try { return JSON.parse(localStorage.getItem(PREFERENCE_KEY) || "{}"); } catch { return {}; }
  });
  const setPref = (patch) => setPrefs((current) => {
    const next = { ...current, ...patch };
    localStorage.setItem(PREFERENCE_KEY, JSON.stringify(next));
    return next;
  });
  return { prefs, setPref, t: (key) => TRANSLATIONS[key] || key };
}

// Plan affiché dans Facturation : vraiment persisté côté backend maintenant
// (avant : toujours "free" en dur, jamais réellement lu nulle part). Limite
// assumée, documentée aussi côté backend (routes /settings/plan) : ce SaaS
// n'a pas de webhook Mollie relié à cette base — pas de mise à jour
// automatique après un paiement réel sur la page tarifs publique tant que
// cette intégration n'existe pas. Activable manuellement en attendant
// (bouton dans l'onglet Facturation).
function useAuth() {
  const [plan, setPlanState] = useState("free");
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  useEffect(() => { getPlan().then((r) => setPlanState(r.plan)).catch(() => {}); }, []);
  // Corrige un vrai bug : l'email de connexion (Paramètres → Sécurité)
  // affichait toujours "—" car cet objet renvoyait un email codé en dur,
  // jamais chargé depuis le serveur.
  useEffect(() => { authMe().then((u) => { setEmail(u?.email || ""); setName(u?.first_name || u?.name || ""); }).catch(() => {}); }, []);
  return { user: { name, email, plan }, setPlan: async (p) => { await setPlan(p); setPlanState(p); } };
}

const growthApi = {
  getSettings: async () => {
    const [profile, inspiration, vision] = await Promise.all([getProfile(), getInspiration(), getVisionMemory()]);
    return { profile: { name: profile?.first_name || "", email: "" }, vision: vision?.memory || {}, inspiration_photo: inspiration?.image_url || "" };
  },
  saveSettings: async (data) => {
    if (data?.profile?.name !== undefined) await setProfile(data.profile.name);
    if (data?.vision) await setVisionMemory(data.vision);
    return { ok: true };
  },
};

const integrationsApi = {
  list: async () => ({ items: [], connected_count: 0 }),
  save: async () => ({ ok: false, message: "Les intégrations seront raccordées à votre backend de production." }),
  remove: async () => ({ ok: true }),
  test: async () => ({ valid: false, message: "Aucune intégration configurée." }),
};

const visionExtApi = { uploadPhoto: async () => { throw new Error("Utilisez une URL d'image dans cette version."); } };
const sendMagicLink = async () => { throw new Error("Aucun compte email n'est configuré dans la prévisualisation."); };
const accountApi = { exportData: async () => ({ exported_at: new Date().toISOString() }), deleteAccount: async () => { throw new Error("Suppression indisponible dans la prévisualisation."); } };
const paymentsApi = { transactions: async () => [], downloadInvoice: async () => { throw new Error("Facture indisponible."); } };
function AutomatisationSettings() { return <UnavailableSection title="Automatisation" detail="Les agents et automatisations seront disponibles lorsque les connecteurs de production seront configurés." />; }
function PricingScreen() { return null; }
function UnavailableSection({ title, detail }) { return <div className="settings-glass-card"><p className="settings-card-title">{title}</p><p className="settings-muted">{detail}</p></div>; }

function CoursCockpitProfile() {
  const [firstName, setFirstName] = useState("");
  const [saving, setSaving] = useState(false);
  useEffect(() => { getProfile().then((data) => setFirstName(data?.first_name || "")).catch(() => {}); }, []);
  const save = async () => {
    setSaving(true);
    try { await setProfile(firstName.trim()); toast.success("Prénom du cockpit enregistré"); }
    catch { toast.error("Échec de l'enregistrement"); }
    finally { setSaving(false); }
  };
  return (
    <div className="settings-glass-card" data-testid="settings-cockpit-profile">
      <p className="settings-card-title"><User size={14} /> Prénom affiché dans votre cockpit</p>
      <p className="settings-muted">Utilisé dans les salutations et dans le Copilote.</p>
      <div className="settings-field-row">
        <input value={firstName} onChange={(e) => setFirstName(e.target.value)} onBlur={save} onKeyDown={(e) => e.key === "Enter" && e.currentTarget.blur()} placeholder="Votre prénom" className="settings-input" data-testid="settings-firstname-input" />
        {saving && <Loader2 size={16} className="animate-spin text-white/50" />}
      </div>
    </div>
  );
}

function CoursRemindersSection() {
  const [weeklyReview, setWeeklyReview] = useState(false);
  const [pushSubscribed, setPushSubscribed] = useState(false);
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    Promise.all([getReminders(), isPushSubscribed()]).then(([reminders, subscribed]) => {
      setWeeklyReview(!!reminders?.weekly_review); setPushSubscribed(!!subscribed);
    }).catch(() => {});
  }, []);
  const toggleWeekly = async () => {
    const next = !weeklyReview; setWeeklyReview(next);
    try { await setReminders(next); toast.success("Rappel hebdomadaire enregistré"); }
    catch { setWeeklyReview(!next); toast.error("Échec de l'enregistrement"); }
  };
  const togglePush = async () => {
    setBusy(true);
    try {
      if (pushSubscribed) { await unsubscribeFromPush(); setPushSubscribed(false); toast.success("Notifications désactivées"); }
      else { const result = await subscribeToPush(); if (!result?.ok) throw new Error(result?.error); setPushSubscribed(true); toast.success("Notifications activées"); }
    } catch (error) { toast.error(error?.message || "Impossible de modifier les notifications"); }
    finally { setBusy(false); }
  };
  return (
    <div className="settings-glass-card" data-testid="settings-cours-reminders">
      <p className="settings-card-title"><BellRing size={14} /> Rappels d’actions</p>
      <div className="settings-row">
        <div><p className="settings-row-label">Revue hebdomadaire</p><p className="settings-muted">Un temps dédié pour revoir priorités, progrès et blocages.</p></div>
        <Toggle on={weeklyReview} onChange={toggleWeekly} testid="settings-weekly-review-toggle" />
      </div>
      <div className="settings-row settings-row-last">
        <div><p className="settings-row-label">Notifications push</p><p className="settings-muted">Alertes et encouragements même lorsque l’application est fermée.</p></div>
        <button onClick={togglePush} disabled={busy} className="settings-action-button" data-testid="settings-push-toggle">{busy ? <Loader2 size={14} className="animate-spin" /> : <BellRing size={14} />}{pushSubscribed ? "Désactiver" : "Activer"}</button>
      </div>
      {pushSubscribed && <button onClick={() => sendTestPush().then(() => toast.success("Notification de test envoyée")).catch(() => toast.error("Échec de l’envoi"))} className="settings-link-button" data-testid="settings-push-test">Tester une notification</button>}
    </div>
  );
}

function CoursSecurityExport() {
  return (
    <div className="settings-glass-card" data-testid="settings-cours-export">
      <p className="settings-card-title"><Download size={14} /> Export comptable Cours-main</p>
      <p className="settings-muted">Téléchargez vos factures et dépenses au format CSV compatible avec les outils comptables courants.</p>
      <a href={exportCsvUrl()} download className="settings-action-button" data-testid="settings-export-csv"><Download size={14} /> Exporter mes données CSV</a>
    </div>
  );
}

function CoursInspirationUrl() {
  const [url, setUrl] = useState("");
  const [saving, setSaving] = useState(false);
  useEffect(() => { getInspiration().then((data) => setUrl(data?.image_url || "")).catch(() => {}); }, []);
  const save = async () => {
    setSaving(true);
    try { await setInspirationImage(url.trim()); toast.success("Image d’inspiration enregistrée"); }
    catch { toast.error("Échec de l’enregistrement"); }
    finally { setSaving(false); }
  };
  return (
    <div className="settings-glass-card" data-testid="settings-inspiration-url">
      <p className="settings-card-title"><ImageIcon size={14} /> URL de votre image d’inspiration</p>
      <p className="settings-muted">Collez le lien d’une image déjà en ligne. Elle sera utilisée sur votre espace Vision.</p>
      <div className="settings-field-row"><input value={url} onChange={(e) => setUrl(e.target.value)} onBlur={save} placeholder="https://…" className="settings-input" data-testid="settings-inspiration-input" />{saving && <Loader2 size={16} className="animate-spin text-white/50" />}</div>
      {url && <img src={url} alt="Aperçu d'inspiration" className="settings-inspiration-preview" onError={(event) => { event.currentTarget.style.display = "none"; }} />}
    </div>
  );
}

// ─── COMPOSANTS EXISTANTS (inchangés) ─────────────────────────
const Opt = ({ active, onClick, Icon, label, testid }) => (
  <button onClick={onClick} data-testid={testid}
    className="zbtn" style={{ flex: 1, minWidth: 150, height: 56, justifyContent: "flex-start", gap: 10,
      border: active ? "2px solid #DEC2A3" : "1px solid var(--glass-border)", position: "relative" }}>
    <Icon size={18} /> {label}
    {active && <Check size={16} style={{ position: "absolute", right: 12, color: "#DEC2A3" }} />}
  </button>
);

const FIELD_LABELS = {
  api_key: "Clé API", webhook_url: "URL Webhook",
  phone: "Téléphone (+33…)", sender_email: "Email expéditeur", sender_name: "Nom expéditeur",
};

function OdooIntegrationCard() {
  const [url, setUrl] = useState("");
  const [dbName, setDbName] = useState("");
  const [email, setEmail] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [connected, setConnected] = useState(false);
  const [saving, setSaving] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncMsg, setSyncMsg] = useState("");

  useEffect(() => {
    getOdooConfig().then((r) => { setUrl(r.url || ""); setConnected(!!r.connected); }).catch(() => {});
  }, []);

  const save = async () => {
    if (!url || !dbName || !email || !apiKey) return;
    setSaving(true);
    try {
      await setOdooConfig({ url, db_name: dbName, email, api_key: apiKey });
      setConnected(true);
      toast.success("Odoo connecté");
    } catch { toast.error("Échec de la connexion à Odoo"); }
    finally { setSaving(false); }
  };

  const sync = async () => {
    setSyncing(true); setSyncMsg("");
    try {
      const r = await syncOdoo();
      setSyncMsg(r.message);
      if (r.ok) toast.success(r.message); else toast.error(r.message);
    } catch { toast.error("Échec de la synchronisation"); }
    finally { setSyncing(false); }
  };

  return (
    <div className="glass-card" data-testid="odoo-integration-card" style={{ marginBottom: 4 }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
        <span style={{ fontWeight: 600, fontSize: 14 }}>Odoo</span>
        <span className="zchip" style={{ fontSize: 11, background: connected ? "rgba(52,211,153,0.15)" : "var(--glass-soft)", color: connected ? "#34d399" : "var(--muted)" }}>
          {connected ? "Connecté" : "Non connecté"}
        </span>
      </div>
      <p className="muted" style={{ fontSize: 12, margin: "0 0 10px" }}>Importe tes factures et dépenses réelles depuis Odoo dans Pilotage — lecture seule, Odoo reste ton système principal.</p>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 8 }}>
        <input placeholder="URL (https://monentreprise.odoo.com)" value={url} onChange={(e) => setUrl(e.target.value)} className="zinput" data-testid="odoo-url" />
        <input placeholder="Base de données" value={dbName} onChange={(e) => setDbName(e.target.value)} className="zinput" data-testid="odoo-db" />
        <input placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} className="zinput" data-testid="odoo-email" />
        <input placeholder="Clé API" type="password" value={apiKey} onChange={(e) => setApiKey(e.target.value)} className="zinput" data-testid="odoo-api-key" />
      </div>
      <div style={{ display: "flex", gap: 8 }}>
        <button onClick={save} disabled={saving} className="zbtn" data-testid="odoo-save">{saving ? "…" : connected ? "Mettre à jour" : "Connecter"}</button>
        {connected && <button disabled title="La synchronisation Odoo n'est pas encore construite côté serveur — la connexion enregistre vos identifiants, mais aucune donnée n'est encore importée." className="zbtn-primary" style={{ opacity: 0.5, cursor: "not-allowed" }} data-testid="odoo-sync">Synchroniser — Bientôt</button>}
      </div>
      {syncMsg && <p className="muted" style={{ fontSize: 12, marginTop: 8 }}>{syncMsg}</p>}
    </div>
  );
}

function BankAggregatorCard() {
  const [apiKey, setApiKey] = useState("");
  const [connected, setConnected] = useState(false);
  const [saving, setSaving] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncMsg, setSyncMsg] = useState("");

  useEffect(() => {
    getBankAggregatorConfig().then((r) => setConnected(!!r.connected)).catch(() => {});
  }, []);

  const save = async () => {
    if (!apiKey.trim()) return;
    setSaving(true);
    try {
      await setBankAggregatorConfig({ api_key: apiKey.trim() });
      setConnected(true);
      toast.success("Clé enregistrée");
    } catch { toast.error("Échec de l'enregistrement"); }
    finally { setSaving(false); }
  };

  const sync = async () => {
    setSyncing(true); setSyncMsg("");
    try { const r = await syncBankAggregator(); setSyncMsg(r.message); }
    catch { toast.error("Échec"); }
    finally { setSyncing(false); }
  };

  return (
    <div className="glass-card" data-testid="bank-aggregator-card" style={{ marginBottom: 12 }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
        <span style={{ fontWeight: 600, fontSize: 14 }}>Agrégateur bancaire</span>
        <span className="zchip" style={{ fontSize: 11, background: connected ? "rgba(52,211,153,0.15)" : "var(--glass-soft)", color: connected ? "#34d399" : "var(--muted)" }}>
          {connected ? "Clé enregistrée" : "Non connecté"}
        </span>
      </div>
      <p className="muted" style={{ fontSize: 12, margin: "0 0 10px" }}>
        Une seule inscription (type Enable Banking, Bridge, Powens) donne accès à des dizaines de banques françaises — même principe qu'Odoo. Nécessite un compte développeur chez le fournisseur choisi.
      </p>
      <div style={{ display: "flex", gap: 8 }}>
        <input placeholder="Clé API de l'agrégateur" type="password" value={apiKey} onChange={(e) => setApiKey(e.target.value)} className="zinput" style={{ flex: 1 }} data-testid="aggregator-api-key" />
        <button onClick={save} disabled={saving} className="zbtn" data-testid="aggregator-save">{saving ? "…" : "Enregistrer"}</button>
      </div>
      {connected && (
        <button disabled title="La synchronisation bancaire n'est pas encore construite côté serveur — la clé est enregistrée, mais aucune donnée n'est encore importée." className="zbtn-primary" style={{ marginTop: 8, opacity: 0.5, cursor: "not-allowed" }} data-testid="aggregator-sync">
          Synchroniser — Bientôt
        </button>
      )}
      {syncMsg && <p className="muted" style={{ fontSize: 12, marginTop: 8 }}>{syncMsg}</p>}
    </div>
  );
}

function PlannedFinancialIntegrationCard({ name, detail, testid }) {
  return (
    <div className="glass-card" data-testid={testid} style={{ marginBottom: 12 }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, minWidth: 0 }}>
          <div style={{ width: 40, height: 40, borderRadius: 12, display: "flex", alignItems: "center", justifyContent: "center", background: "var(--glass-soft)", flexShrink: 0 }}><Plug size={18} style={{ color: "#DEC2A3" }} /></div>
          <div>
            <p style={{ fontWeight: 600, fontSize: 14, margin: 0 }}>{name}</p>
            <p className="muted" style={{ fontSize: 12, margin: "4px 0 0" }}>{detail}</p>
          </div>
        </div>
        <span className="zchip" style={{ fontSize: 11, background: "var(--glass-soft)", color: "var(--muted)", whiteSpace: "nowrap" }}>À connecter</span>
      </div>
      <p className="muted" style={{ fontSize: 11, margin: "10px 0 0" }}>Ce connecteur sera activé après l’ajout de son autorisation sécurisée côté backend. Aucune donnée n’est importée avant votre consentement.</p>
    </div>
  );
}

function IntegrationCard({ item, onSaved }) {
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({});
  const [busy, setBusy] = useState(false);
  const connected = item.configured;
  const save = async () => {
    setBusy(true);
    try { const res = await integrationsApi.save(item.key, form); if (res.ok) { toast.success(res.message || "Connecté"); setOpen(false); setForm({}); onSaved(); } else toast.error(res.message); }
    catch { toast.error("Erreur réseau"); } finally { setBusy(false); }
  };
  const disconnect = async () => { setBusy(true); try { await integrationsApi.remove(item.key); toast.success("Déconnecté"); onSaved(); } catch { toast.error("Erreur"); } finally { setBusy(false); } };
  const testKey = async () => { setBusy(true); try { const r = await integrationsApi.test(item.key); r.valid ? toast.success(r.message) : toast.error(r.message); } catch { toast.error("Erreur"); } finally { setBusy(false); } };
  return (
    <div className="glass-card" style={{ padding: 16 }} data-testid={`integration-${item.key}`}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, minWidth: 0 }}>
          <div style={{ width: 40, height: 40, borderRadius: 12, display: "flex", alignItems: "center", justifyContent: "center", background: connected ? "rgba(94,138,90,0.18)" : "var(--glass-soft)", flexShrink: 0 }}>
            <Plug size={18} style={{ color: connected ? "#5e8a5a" : "var(--muted)" }} />
          </div>
          <div style={{ minWidth: 0 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ fontWeight: 600, color: "var(--txt)" }}>{item.label}</span>
              <span className="zchip" style={{ fontSize: 10, background: "var(--glass-soft)", color: "var(--muted)" }}>{item.category}</span>
            </div>
            <p className="muted" style={{ fontSize: 12, margin: "4px 0 0" }}>{item.help}</p>
            {connected && item.preview && <p className="muted" style={{ fontSize: 11, margin: "4px 0 0", fontFamily: "monospace" }}>{item.preview}</p>}
          </div>
        </div>
        <span className="zchip" data-testid={`integration-status-${item.key}`}
          style={{ flexShrink: 0, background: connected ? "rgba(94,138,90,0.18)" : "rgba(150,150,150,0.12)", color: connected ? "#5e8a5a" : "var(--muted)", fontSize: 11 }}>
          {connected ? "Connecté" : "Non connecté"}
        </span>
      </div>
      <div style={{ display: "flex", gap: 8, marginTop: 12, flexWrap: "wrap" }}>
        {!open && <button className="zbtn" style={{ height: 40, padding: "0 14px", gap: 8 }} onClick={() => setOpen(true)} data-testid={`integration-connect-${item.key}`}><Link2 size={15} /> {connected ? "Modifier" : "Connecter"}</button>}
        {connected && <><button className="zbtn" style={{ height: 40, padding: "0 14px", gap: 8 }} onClick={testKey} disabled={busy} data-testid={`integration-test-${item.key}`}>{busy ? <Loader2 size={15} className="spin" /> : <ShieldCheck size={15} />} Tester</button><button className="zbtn" style={{ height: 40, padding: "0 14px", gap: 8, color: "#c26b4a" }} onClick={disconnect} disabled={busy} data-testid={`integration-remove-${item.key}`}><Trash2 size={15} /> Déconnecter</button></>}
      </div>
      {open && (
        <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 10 }}>
          {item.fields.map((f) => (<input key={f} className="zinput" type={f === "api_key" ? "password" : "text"} placeholder={FIELD_LABELS[f] || f} value={form[f] || ""} onChange={(e) => setForm({ ...form, [f]: e.target.value })} data-testid={`integration-input-${item.key}-${f}`} />))}
          <div style={{ display: "flex", gap: 8 }}>
            <button className="zbtn zbtn-primary" style={{ height: 40, padding: "0 16px", gap: 8 }} onClick={save} disabled={busy} data-testid={`integration-save-${item.key}`}>{busy ? <Loader2 size={15} className="spin" /> : <Check size={15} />} Enregistrer</button>
            <button className="zbtn" style={{ height: 40, padding: "0 16px" }} onClick={() => { setOpen(false); setForm({}); }}>Annuler</button>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── TOGGLE SWITCH ─────────────────────────────────────────────
function Toggle({ on, onChange, testid }) {
  return (
    <button onClick={() => onChange(!on)} data-testid={testid}
      style={{ position: "relative", width: 44, height: 24, borderRadius: 12, border: "none", cursor: "pointer", background: on ? "#DEC2A3" : "var(--glass-soft)", transition: "background 0.2s", flexShrink: 0 }}>
      <span style={{ position: "absolute", top: 2, left: on ? 22 : 2, width: 20, height: 20, borderRadius: "50%", background: "white", transition: "left 0.2s", display: "block" }} />
    </button>
  );
}

// ─── ROW SETTING ───────────────────────────────────────────────
function SettingRow({ label, sub, action, border = true }) {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "12px 0", borderBottom: border ? "1px solid var(--glass-border)" : "none" }}>
      <div style={{ flex: 1, minWidth: 0, marginRight: 12 }}>
        <p style={{ fontSize: 14, color: "var(--txt)" }}>{label}</p>
        {sub && <p className="muted" style={{ fontSize: 12, marginTop: 2, lineHeight: 1.4 }}>{sub}</p>}
      </div>
      {action && <div style={{ flexShrink: 0 }}>{action}</div>}
    </div>
  );
}

// ─── NOUVELLES SECTIONS ─────────────────────────────────────────

function MemoireSection() {
  const [vision, setVision] = useState({ why: "", what: "", who: "", how: "" });
  const [saving, setSaving] = useState(false);
  useEffect(() => { growthApi.getSettings().then(s => { if (s?.vision) setVision(s.vision); }).catch(() => {}); }, []);
  const save = async () => { setSaving(true); try { await growthApi.saveSettings({ vision }); toast.success("Mémoire IA mise à jour !"); } catch { toast.error("Erreur"); } finally { setSaving(false); } };
  return (
    <div className="glass-card" style={{ marginBottom: 16 }} data-testid="settings-memoire">
      <div className="card-label"><Brain size={14} /> Mémoire IA</div>
      <p className="muted" style={{ fontSize: 13, margin: "6px 0 12px", lineHeight: 1.6 }}>
        Ces informations alimentent votre Co-pilote pour des conseils personnalisés.
      </p>
      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {[
          { key: "why", label: "Pourquoi (votre raison d'être)", placeholder: "Pourquoi faites-vous ce que vous faites ?" },
          { key: "what", label: "Quoi (votre offre)", placeholder: "Que proposez-vous concrètement ?" },
          { key: "who", label: "Pour qui (votre cible)", placeholder: "Qui aidez-vous ?" },
          { key: "how", label: "Comment (votre approche)", placeholder: "Qu'est-ce qui vous différencie ?" },
        ].map(f => (
          <div key={f.key}>
            <label className="muted" style={{ fontSize: 12, display: "block", marginBottom: 4 }}>{f.label}</label>
            <textarea value={vision[f.key]} rows={2} onChange={e => setVision(p => ({ ...p, [f.key]: e.target.value }))} placeholder={f.placeholder} className="zinput" style={{ resize: "none", minHeight: 56, fontFamily: "inherit", width: "100%", boxSizing: "border-box" }} data-testid={`memoire-${f.key}`} />
          </div>
        ))}
        <button className="zbtn zbtn-primary" style={{ height: 40, padding: "0 16px", gap: 8, width: "fit-content" }} onClick={save} disabled={saving} data-testid="btn-save-memoire">
          {saving ? <Loader2 size={15} className="spin" /> : <Save size={15} />} Sauvegarder
        </button>
      </div>
    </div>
  );
}

function NotificationsSection({ prefs, setPref }) {
  const notifs = [
    { key: "notif_task_email", label: "Email tâche Agent", sub: "Notification quand une tâche est traitée" },
    { key: "notif_exclusive_content", label: "Contenu exclusif", sub: "Offres, mises à jour et guides Zayado" },
    { key: "notif_credit_alert", label: "Alerte crédits faibles", sub: "Quand votre solde passe sous le seuil" },
    { key: "notif_energie_popup", label: "Rappel énergie matinal", sub: "Check-in énergie quotidien" },
    { key: "notif_swot_monthly", label: "Analyse SWOT mensuelle", sub: "Rapport mensuel généré par l'IA" },
    { key: "notif_vision_rappels", label: "Rappels Vision Board", sub: "Rappels J+30/J+90/J+180/J+365 style Google Photos" },
  ];
  return (
    <div className="glass-card" style={{ marginBottom: 16 }} data-testid="settings-notifications">
      <div className="card-label"><Bell size={14} /> Notifications</div>
      <div style={{ display: "flex", flexDirection: "column" }}>
        {notifs.map((n, i) => (
          <SettingRow key={n.key} label={n.label} sub={n.sub} border={i < notifs.length - 1}
            action={<Toggle on={prefs[n.key] !== false} onChange={v => setPref({ [n.key]: v })} testid={`toggle-${n.key}`} />} />
        ))}
      </div>
    </div>
  );
}

function InspirationSection({ prefs, setPref }) {
  const [uploading, setUploading] = useState(false);
  const [pendingFile, setPendingFile] = useState(null);   // fichier choisi, pas encore confirmé
  const [previewUrl, setPreviewUrl] = useState(null);     // aperçu local instantané (URL.createObjectURL)
  const fileRef = React.useRef(null);
  const currentImage = prefs.inspiration_photo || null;

  const handleChoose = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith("image/")) return toast.error("Merci de choisir une image.");
    if (file.size > 8 * 1024 * 1024) return toast.error("Image trop lourde (max 8 Mo).");
    setPendingFile(file);
    setPreviewUrl(URL.createObjectURL(file));
  };

  const confirmUpload = async () => {
    if (!pendingFile) return;
    setUploading(true);
    try {
      const res = await visionExtApi.uploadPhoto(pendingFile);
      setPref({ inspiration_photo: res?.url || res?.data?.url });
      toast.success("Image enregistrée — disponible sur ton Dashboard (bloc « Ma Vision ») et sur l'écran d'inspiration.", { duration: 5000 });
      setPendingFile(null);
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    } catch {
      toast.error("Échec de l'envoi — réessayez.");
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const cancelPreview = () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null); setPendingFile(null);
    if (fileRef.current) fileRef.current.value = "";
  };

  const removeImage = () => {
    setPref({ inspiration_photo: null });
    toast.success("Image retirée — l'image Zayado par défaut sera utilisée.");
  };

  return (
    <div className="glass-card" style={{ marginBottom: 16 }} data-testid="settings-inspiration">
      <div className="card-label"><Heart size={14} /> Inspiration & images</div>
      <p style={{ fontSize: 13, color: "var(--txt)", margin: "0 0 6px", fontWeight: 500 }}>Écran d'inspiration au démarrage</p>
      <p className="muted" style={{ fontSize: 12, marginBottom: 10, lineHeight: 1.5 }}>
        Photo + vision + KPIs, affiché avant le Dashboard, à la fréquence de votre choix.
      </p>
      <div style={{ display: "flex", gap: 10, marginBottom: 12, flexWrap: "wrap" }} data-testid="inspiration-frequency">
        {[["daily", "Quotidien"], ["weekly", "Hebdomadaire"], ["never", "Jamais"]].map(([id, label]) => {
          const current = prefs.show_inspiration_screen === false ? "never" : (prefs.inspiration_frequency || "daily");
          return (
            <Opt key={id} active={current === id}
              onClick={() => setPref({ inspiration_frequency: id, show_inspiration_screen: id !== "never" })}
              Icon={Heart} label={label} testid={`set-inspiration-freq-${id}`} />
          );
        })}
      </div>
      <button
        onClick={() => window.dispatchEvent(new CustomEvent("zayado:show-inspiration"))}
        data-testid="replay-inspiration-btn"
        style={{
          fontSize: 12.5, fontWeight: 600, padding: "8px 16px", borderRadius: 999,
          border: "1px solid var(--glass-border)", background: "transparent", color: "var(--txt)",
          cursor: "pointer", marginBottom: 18,
        }}>
        Revoir l'écran d'inspiration maintenant
      </button>
      <p style={{ fontSize: 13, color: "var(--txt)", margin: "14px 0 6px", fontWeight: 500 }}>Ambiance des citations</p>
      <div style={{ display: "flex", gap: 10, marginBottom: 18, flexWrap: "wrap" }}>
        <Opt active={prefs.ambiance === "clarte" || !prefs.ambiance} onClick={() => setPref({ ambiance: "clarte" })} Icon={Heart} label="Univers Clarté" testid="set-ambiance-clarte" />
        <Opt active={prefs.ambiance === "sens"} onClick={() => setPref({ ambiance: "sens" })} Icon={Heart} label="Univers Sens" testid="set-ambiance-sens" />
        <Opt active={prefs.ambiance === "foi"} onClick={() => setPref({ ambiance: "foi" })} Icon={Heart} label="Univers Foi" testid="set-ambiance-foi" />
      </div>

      <p style={{ fontSize: 13, color: "var(--txt)", marginBottom: 6, fontWeight: 500 }}>Mon image d'inspiration</p>
      <p className="muted" style={{ fontSize: 12, marginBottom: 14, lineHeight: 1.5 }}>
        Une seule image, la vôtre — celle qui vous rappelle pourquoi vous entreprenez.
        Elle apparaît sur l'écran d'inspiration chaque matin.
      </p>

      {/* Aperçu live — simule l'écran d'inspiration réel avant validation */}
      {previewUrl ? (
        <div style={{ marginBottom: 14 }} data-testid="inspiration-live-preview">
          <div style={{
            position: "relative", width: "100%", maxWidth: 320, height: 180, borderRadius: 16, overflow: "hidden",
            backgroundImage: `url(${previewUrl})`, backgroundSize: "cover", backgroundPosition: "center",
            border: "2px solid #DEC2A3",
          }}>
            <div style={{ position: "absolute", inset: 0, background: "linear-gradient(180deg, rgba(11,31,58,0.15), rgba(11,31,58,0.75))" }} />
            <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, padding: 14 }}>
              <p style={{ fontFamily: "'Bricolage Grotesque', sans-serif", fontStyle: "italic", color: "#F6F2EA", fontSize: 14, margin: 0 }}>« Aperçu de votre écran d'inspiration »</p>
            </div>
            <span className="zchip" style={{ position: "absolute", top: 10, right: 10, background: "rgba(222, 194, 163,0.9)", color: "#0B1F3A", fontSize: 10 }}>Aperçu</span>
          </div>
          <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
            <button className="zbtn zbtn-primary" style={{ height: 36, gap: 6, fontSize: 13 }} disabled={uploading}
              onClick={confirmUpload} data-testid="inspiration-confirm-btn">
              {uploading ? <Loader2 size={13} className="spin" /> : <Check size={13} />} Confirmer cette image
            </button>
            <button className="zbtn" style={{ height: 36, fontSize: 13 }} onClick={cancelPreview} data-testid="inspiration-cancel-btn">
              Annuler
            </button>
          </div>
        </div>
      ) : (
        <div style={{ display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap" }}>
          <div style={{
            width: 96, height: 96, borderRadius: 14, overflow: "hidden",
            border: currentImage ? "2px solid #DEC2A3" : "1px dashed var(--glass-border)",
            background: "var(--glass-soft)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
          }}>
            {currentImage ? (
              <img src={currentImage} alt="Inspiration" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            ) : (
              <ImageIcon size={22} className="muted" />
            )}
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <input ref={fileRef} type="file" accept="image/*" onChange={handleChoose} style={{ display: "none" }} data-testid="inspiration-upload-input" />
            <button className="zbtn zbtn-primary" style={{ height: 38, gap: 6 }}
              onClick={() => fileRef.current?.click()} data-testid="inspiration-upload-btn">
              <Upload size={14} /> {currentImage ? "Changer l'image" : "Mettre mon image"}
            </button>
            {currentImage && (
              <button className="zbtn" style={{ height: 32, fontSize: 12 }} onClick={removeImage} data-testid="inspiration-remove-btn">
                Retirer et utiliser l'image par défaut
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function SecuriteSection() {
  const { user } = useAuth();
  const [sending, setSending] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(false);
  const [confirmText, setConfirmText] = useState("");
  const [deleting, setDeleting] = useState(false);

  const sendLink = async () => {
    if (!user?.email) return toast.error("Aucun email associé à ce compte.");
    setSending(true);
    try { await sendMagicLink(user.email); toast.success("Lien de connexion envoyé !"); }
    catch { toast.error("Échec de l'envoi — réessayez."); }
    finally { setSending(false); }
  };

  const exportData = async () => {
    setExporting(true);
    try {
      const data = await accountApi.exportData();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = `zayado-mes-donnees-${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success("Export téléchargé !");
    } catch { toast.error("Échec de l'export — réessayez."); }
    finally { setExporting(false); }
  };

  const deleteAccount = async () => {
    if (confirmText.trim().toUpperCase() !== "SUPPRIMER") return toast.error("Tapez SUPPRIMER");
    setDeleting(true);
    try {
      await accountApi.deleteAccount();
      toast.success("Compte supprimé. À bientôt.");
      setTimeout(() => { window.location.href = "/login"; }, 1200);
    } catch { toast.error("Échec de la suppression — réessayez."); setDeleting(false); }
  };
  return (
    <div className="glass-card" style={{ marginBottom: 16 }} data-testid="settings-securite">
      <div className="card-label"><Lock size={14} /> Sécurité & données</div>
      <SettingRow label="Email de connexion" sub={user?.email || "—"} />
      <SettingRow label="Lien magique" sub="Connexion sans mot de passe — lien envoyé par email"
        action={<button className="zbtn" style={{ height: 36, padding: "0 12px", gap: 6, fontSize: 13 }} onClick={sendLink} disabled={sending} data-testid="btn-send-magic-link">{sending ? <Loader2 size={13} className="spin" /> : null} Envoyer</button>} />
      <SettingRow label="Exporter mes données" sub="Télécharger toutes vos données JSON (RGPD)"
        action={<button className="zbtn" style={{ height: 36, padding: "0 12px", gap: 6, fontSize: 13 }} onClick={exportData} disabled={exporting} data-testid="btn-export-data">{exporting ? <Loader2 size={13} className="spin" /> : <Download size={13} />} Télécharger</button>} />
      <div style={{ padding: "12px 0" }}>
        <p style={{ fontSize: 14, color: "var(--txt)" }}>Supprimer mon compte</p>
        <p className="muted" style={{ fontSize: 12, marginTop: 2, marginBottom: 10 }}>Suppression définitive — anonymisation conforme RGPD</p>
        {!deleteConfirm ? (
          <button onClick={() => setDeleteConfirm(true)} style={{ height: 36, padding: "0 14px", borderRadius: 8, border: "none", cursor: "pointer", background: "rgba(220,50,50,0.12)", color: "#e05050", fontSize: 13, fontWeight: 500 }} data-testid="btn-delete-trigger">Supprimer mon compte</button>
        ) : (
          <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
            <input value={confirmText} onChange={e => setConfirmText(e.target.value)} placeholder="Tapez SUPPRIMER" className="zinput" style={{ width: 160 }} data-testid="confirm-delete-input" />
            <button onClick={deleteAccount}
              disabled={confirmText.trim().toUpperCase() !== "SUPPRIMER" || deleting}
              style={{ height: 36, padding: "0 14px", borderRadius: 8, border: "none", cursor: "pointer", background: "#c0392b", color: "white", fontSize: 13, fontWeight: 500, opacity: (confirmText.trim().toUpperCase() !== "SUPPRIMER" || deleting) ? 0.4 : 1 }} data-testid="btn-delete-confirm">
              {deleting ? <Loader2 size={13} className="spin" /> : "Confirmer"}
            </button>
            <button onClick={() => { setDeleteConfirm(false); setConfirmText(""); }} className="zbtn" style={{ height: 36 }}><X size={13} /></button>
          </div>
        )}
      </div>
    </div>
  );
}

function FacturationSection() {
  const { user } = useAuth();
  const [pricingOpen, setPricingOpen] = useState(false);
  const currentPlan = user?.plan || "free";
  // Ordre pensé pour l'effet d'ancrage : SERENITY (le plus cher) en premier et mis en avant,
  // ce qui fait paraître GROW comme la valeur "raisonnable" juste en dessous.
  // Chaque plan promet un résultat concret plutôt qu'une liste de features.
  const plans = [
    { id: "serenity", label: "SERENITY", price: "149€/mois", promise: "Délègue tout à l'IA.", desc: "DAF inclus + domiciliation Paris 2e", highlight: true },
    { id: "grow", label: "GROW", price: "79€/mois", promise: "10k€ de CA mensuel.", desc: "Expansion Agent complet + Canva Équipe" },
    { id: "start", label: "START", price: "29€/mois", promise: "Tes 3 premiers clients.", desc: "1 projet, fonctionnalités de base" },
  ].map(p => ({ ...p, current: p.id === currentPlan }));
  const choosePlan = () => {
    // Ouvre la page tarifs publique (iframe zayado.net) — le paiement se fait via Mollie sur cette page.
    setPricingOpen(true);
  };
  return (
    <div className="glass-card" style={{ marginBottom: 16 }} data-testid="settings-facturation">
      <div className="card-label" style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}><CreditCard size={14} /> Offre & facturation</span>
        <button onClick={() => setPricingOpen(true)} data-testid="see-all-plans-btn"
          className="zbtn" style={{ height: 30, padding: "0 12px", fontSize: 12 }}>Voir tous les forfaits</button>
      </div>
      <PricingScreen open={pricingOpen} onClose={() => setPricingOpen(false)} />
      {currentPlan === "free" && (
        <p className="muted" style={{ fontSize: 12, margin: "6px 0 12px" }}>Vous êtes actuellement en accès gratuit — sans engagement.</p>
      )}
      <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 12 }}>
        {plans.map(p => (
          <div key={p.id} style={{
            display: "flex", alignItems: "center", justifyContent: "space-between",
            padding: p.highlight ? "18px 16px" : "12px 14px", borderRadius: 10,
            border: p.current ? "2px solid #DEC2A3" : p.highlight ? "1px solid rgba(222, 194, 163,0.5)" : "1px solid var(--glass-border)",
            background: p.current ? "rgba(222, 194, 163,0.06)" : p.highlight ? "linear-gradient(135deg, rgba(222, 194, 163,0.1), rgba(30,60,130,0.15))" : "var(--glass-soft)",
          }} data-testid={`plan-${p.id}`}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ fontWeight: 700, color: p.current ? "#DEC2A3" : "var(--txt)", fontSize: p.highlight ? 16 : 14 }}>{p.label}</span>
                <span style={{ fontSize: p.highlight ? 15 : 13, color: "var(--muted)" }}>{p.price}</span>
              </div>
              <p style={{ fontSize: p.highlight ? 13.5 : 12.5, fontWeight: 600, color: "#DEC2A3", margin: "4px 0 0" }}>{p.promise}</p>
              <p className="muted" style={{ fontSize: 12, marginTop: 2 }}>{p.desc}</p>
            </div>
            {p.current ? <span className="zchip" style={{ background: "rgba(222, 194, 163,0.15)", color: "#DEC2A3", border: "1px solid rgba(222, 194, 163,0.3)" }}>Actif</span> : <button onClick={() => choosePlan(p.id)} className="zbtn" style={{ height: 32, padding: "0 12px", fontSize: 12 }} data-testid={`plan-${p.id}-choose`}>Choisir</button>}
          </div>
        ))}
      </div>

      <BillingHistory />
    </div>
  );
}

// ─── HISTORIQUE DE FACTURATION (factures PDF téléchargeables) ──
function BillingHistory() {
  const [txs, setTxs] = useState(null);
  const [downloading, setDownloading] = useState(null);

  useEffect(() => {
    paymentsApi.transactions()
      .then((data) => setTxs(Array.isArray(data) ? data : []))
      .catch(() => setTxs([]));
  }, []);

  const download = async (tx) => {
    setDownloading(tx.id);
    try {
      await paymentsApi.downloadInvoice(tx.id, tx.invoice_number);
      toast.success("Facture téléchargée");
    } catch {
      toast.error("Facture indisponible");
    } finally {
      setDownloading(null);
    }
  };

  const fmtDate = (iso) => {
    if (!iso) return "";
    try { return new Date(iso).toLocaleDateString("fr-FR", { day: "2-digit", month: "short", year: "numeric" }); }
    catch { return ""; }
  };

  return (
    <div style={{ marginTop: 22, paddingTop: 18, borderTop: "1px solid var(--glass-border)" }} data-testid="billing-history">
      <div className="card-label" style={{ marginBottom: 12 }}>
        <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}><Download size={14} /> Historique & factures</span>
      </div>

      {txs === null ? (
        <div style={{ display: "flex", alignItems: "center", gap: 8, color: "var(--muted)", fontSize: 13, padding: "8px 0" }}>
          <Loader2 size={14} className="spin" /> Chargement…
        </div>
      ) : txs.length === 0 ? (
        <p className="muted" style={{ fontSize: 13, margin: "4px 0" }} data-testid="billing-empty">
          Aucune facture pour le moment. Vos paiements apparaîtront ici avec leur facture PDF.
        </p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {txs.map((tx) => (
            <div key={tx.id} data-testid={`invoice-row-${tx.id}`} style={{
              display: "flex", alignItems: "center", justifyContent: "space-between",
              gap: 12, padding: "12px 14px", borderRadius: 10,
              border: "1px solid var(--glass-border)", background: "var(--glass-soft)",
            }}>
              <div style={{ minWidth: 0 }}>
                <div style={{ fontWeight: 600, color: "var(--txt)", fontSize: 13.5 }}>{tx.description}</div>
                <div className="muted" style={{ fontSize: 11.5, marginTop: 2 }}>
                  {fmtDate(tx.date)} · N° {tx.invoice_number}
                </div>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 12, flexShrink: 0 }}>
                <span style={{ fontWeight: 700, color: "var(--txt)", fontSize: 14 }}>{Number(tx.amount).toFixed(2)} €</span>
                {tx.downloadable ? (
                  <button onClick={() => download(tx)} disabled={downloading === tx.id}
                    data-testid={`invoice-download-${tx.id}`}
                    className="zbtn" style={{ height: 32, padding: "0 12px", fontSize: 12, gap: 6 }}>
                    {downloading === tx.id ? <Loader2 size={13} className="spin" /> : <Download size={13} />} Facture
                  </button>
                ) : (
                  <span className="zchip" style={{ fontSize: 11, color: "var(--muted)", background: "var(--glass-soft)" }}>
                    {tx.status === "pending" ? "En attente" : tx.status}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── MODALE AIDE (?) ──────────────────────────────────────────
const PAGE_HELP = {
  "/": { title: "Dashboard — Cockpit", tips: ["Votre vue globale en moins de 30 secondes.", "Cliquez sur une KPI card pour accéder au module correspondant.", "Le Co-pilote à droite prépare vos suggestions — vous validez.", "Votre score d'énergie influence les priorités proposées."] },
  "/vision-board": { title: "Vision Board", tips: ["Créez votre canvas mind map en ajoutant des blocs.", "Glissez-déposez pour réorganiser votre vision.", "L'IA génère SWOT et scores depuis vos blocs.", "Exportez en Vision Book PDF depuis la toolbar."] },
  "/pilotage": { title: "Pilotage financier", tips: ["Le KPI 'Salaire possible ce mois' est votre indicateur clé.", "La courbe compare votre CA réel vs votre objectif Vision Board.", "Une alerte trésorerie s'active si vous passez sous votre seuil.", "Connectez votre banque dans Paramètres > Intégrations."] },
  "/bien-etre": { title: "Bien-être", tips: ["Check-in énergie en 1 clic — 5 niveaux.", "L'historique 30 jours détecte vos patterns.", "Une alerte douce s'active si votre énergie baisse 3 jours de suite.", "Seul SaaS business avec prévention burn-out intégrée."] },
  "/croissance": { title: "Croissance — Expansion Agent", tips: ["L'IA détecte les leads sur Reddit, LinkedIn, Google Maps.", "Les messages de contact sont rédigés par l'IA — vous validez avant envoi.", "Pipeline Kanban : Détecté → Contacté → En discussion → Signé.", "Configurez votre ICP (client idéal) pour des leads plus pertinents."] },
};

export function HelpModal({ path, onClose }) {
  const help = PAGE_HELP[path] || PAGE_HELP["/"];
  return (
    <AnimatePresence>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
        style={{ position: "fixed", inset: 0, background: "rgba(11,31,58,0.65)", backdropFilter: "blur(6px)", zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center", padding: 20 }}
        onClick={onClose}>
        <motion.div initial={{ scale: 0.92, y: 16 }} animate={{ scale: 1, y: 0 }} exit={{ scale: 0.92, y: 16 }}
          style={{ background: "var(--glass-bg)", border: "1px solid var(--glass-border)", borderRadius: 20, padding: 28, maxWidth: 440, width: "100%", position: "relative" }}
          onClick={e => e.stopPropagation()}>
          <button onClick={onClose} style={{ position: "absolute", top: 14, right: 14, background: "none", border: "none", cursor: "pointer", color: "var(--muted)", padding: 4 }}><X size={18} /></button>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 18 }}>
            <div style={{ width: 36, height: 36, borderRadius: 10, background: "rgba(222, 194, 163,0.12)", border: "1px solid rgba(222, 194, 163,0.3)", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <span style={{ fontSize: 16 }}>💡</span>
            </div>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: "var(--txt)", margin: 0 }}>{help.title}</h3>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {help.tips.map((tip, i) => (
              <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: 10 }}>
                <span style={{ width: 20, height: 20, borderRadius: "50%", background: "rgba(222, 194, 163,0.15)", color: "#DEC2A3", fontSize: 11, fontWeight: 700, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, marginTop: 1 }}>{i + 1}</span>
                <p style={{ fontSize: 13, color: "var(--txt)", lineHeight: 1.5, margin: 0 }}>{tip}</p>
              </div>
            ))}
          </div>
          <button onClick={onClose} className="zbtn zbtn-primary" style={{ width: "100%", height: 40, marginTop: 20, justifyContent: "center" }}>Compris, merci !</button>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

// ─── MODALE ONBOARDING PAGE (première visite) ─────────────────
// ─── AIDE CONTEXTUELLE ACTIONNABLE ────────────────────────────
// Chaque entrée est un vrai APERÇU VISUEL du bouton à trouver sur la page :
//   - `icon`  : icône Lucide (le composant lui-même) — MÊME icône que dans l'app
//   - `btn`   : libellé exact affiché sur le bouton
//   - `where` : localisation à l'écran (« En bas au centre », « Bandeau du haut »)
//   - `do`    : phrase d'action (« Clique pour… »)
//   - `tip`   : astuce optionnelle
// L'aperçu visuel dans la modale est stylé comme le vrai bouton (pilule dorée)
// pour que l'œil reconnaisse instantanément la cible sur la page.
const ONBOARDING_STEPS = {
  "/": {
    icon: "🚀",
    title: "Cockpit — mode d'emploi",
    subtitle: "Ta vue de tête, 30 sec par jour. Cherche ces 4 boutons.",
    actions: [
      { icon: LineChart, btn: "Bandeau des 4 KPIs", where: "En haut de l'écran", do: "Regarde CA du mois, Trésorerie, Prospects, Énergie. Un chiffre en rouge = action à prendre.", tip: "Clique un KPI pour ouvrir sa page détaillée." },
      { icon: Brain, btn: "Co-pilote — cartes de tâches", where: "Colonne centrale", do: "Valide (✓) ou reporte (→) chaque suggestion. L'IA prépare, tu décides — aucun envoi automatique.", tip: "Swipe droite = accepter, swipe gauche = ignorer." },
      { icon: Plus, btn: "Nouveau", where: "En haut à droite", do: "Ajoute une facture, un prospect ou une dépense sans quitter le cockpit.", tip: "Raccourci clavier : N." },
      { icon: Sparkles, btn: "Carrousel Vision", where: "Panneau de droite", do: "Ta phrase de vision + prochaines actions. Clique pour ouvrir ton Vision Board.", tip: "Change ta phrase dans Réglages → Profil." },
    ],
  },
  "/vision-board": {
    icon: "✨",
    title: "Vision Board — mode d'emploi",
    subtitle: "Un canvas qui nourrit ton Coach IA. Cherche ces 4 boutons.",
    actions: [
      { icon: Plus, btn: "Ajouter", where: "Barre du bas — bouton doré central", do: "Ajoute une carte : Note, Objectif, Palette — ou choisis un Modèle prêt (Lancement / Croissance / Équilibre / Rayonnement).", tip: "Les Modèles posent 5 cartes en 1 tap." },
      { icon: MoreHorizontal, btn: "Plus (⋯)", where: "Barre du bas — à droite", do: "Ouvre les actions : Coach Vision, Modèles de départ, Rappels doux hebdo, Recadrer, Exporter, Vider.", tip: "Le seul menu à connaître pour tout piloter." },
      { icon: Sparkles, btn: "Coach Vision — 3 prochaines actions", where: "Menu ⋯ → 1ère entrée", do: "L'IA lit ton canvas et propose 3 actions. Chaque action a un bouton « Ajouter comme objectif » qui pose la carte automatiquement.", tip: "Fonctionne mieux avec 3+ cartes déjà posées." },
      { icon: Bell, btn: "Rappels doux hebdo", where: "Menu ⋯ → 3ᵉ entrée", do: "Active/suspend l'email du lundi 7h qui rappelle tes 3 prochaines actions.", tip: "Activé par défaut. Toggle à tout moment." },
      { icon: FileText, btn: "Exporter en Vision Book", where: "Menu ⋯ → avant-dernière entrée", do: "Génère un PDF 7 pages (Cover, Vision, Piliers, Valeurs, SWOT, Plan d'action) partageable en 1 clic.", tip: "Idéal à envoyer à un mentor ou associé." },
    ],
  },
  "/pilotage": {
    icon: "📊",
    title: "Pilotage — mode d'emploi",
    subtitle: "Ton tableau de bord financier. Voici les 4 zones à regarder chaque semaine.",
    actions: [
      { icon: Wallet, btn: "Carte « Salaire possible »", where: "En haut à gauche", do: "= CA encaissé − charges − cotisations. C'est LE chiffre pour un indépendant : combien tu peux te verser sans risquer l'entreprise.", tip: "Vise à ce qu'il monte régulièrement, pas en pic." },
      { icon: AlertTriangle, btn: "Alertes trésorerie (bandeau rouge)", where: "En haut, s'affiche seulement en cas d'alerte", do: "Clique pour voir la cause : facture en retard, cotisation à venir, etc.", tip: "Le seuil d'alerte se règle dans Notifications." },
      { icon: TrendingUp, btn: "Graphique « Réel vs Vision »", where: "Zone centrale", do: "Compare ton CA réel à ton objectif Vision Board. L'écart est ta boussole hebdo.", tip: "Ajuste l'objectif Vision si l'écart est stable > 3 mois." },
      { icon: Plus, btn: "Ajouter facture / dépense", where: "Bouton doré, en bas", do: "Saisie rapide, ou import auto via l'intégration Qonto / Stripe (Réglages → Intégrations).", tip: "Automatise via intégration pour éviter la saisie manuelle." },
    ],
  },
  "/bien-etre": {
    icon: "💚",
    title: "Bien-être — mode d'emploi",
    subtitle: "Ton énergie est ton actif principal. Cherche ces 3 zones.",
    actions: [
      { icon: Battery, btn: "Check-in énergie (5 niveaux)", where: "En haut de la page", do: "Clique le niveau qui matche ton état, en 3 secondes. Fais-le chaque matin pour bâtir ton historique.", tip: "Le pattern se révèle après 10 jours de saisie." },
      { icon: ShieldAlert, btn: "Alerte burn-out (bandeau ambre)", where: "S'affiche si énergie basse 3 jours d'affilée", do: "Le Co-pilote adapte tes priorités du jour. Clique pour voir ce qui a été retiré de ta to-do.", tip: "Tu peux forcer un reset dans Réglages → Profil." },
      { icon: ShoppingBag, btn: "Recommandations Zayado", where: "En bas de page", do: "Selon ton score, la boutique suggère des outils (lampe, thé, coussin). Aucune obligation.", tip: "Filtre par prix dans le menu ⋯ de la boutique." },
    ],
  },
  "/croissance": {
    icon: "🎯",
    title: "Croissance — mode d'emploi",
    subtitle: "L'agent qui chasse tes prospects pour toi. Cherche ces 4 boutons.",
    actions: [
      { icon: Radar, btn: "Lancer une chasse", where: "Bouton doré en haut à droite", do: "Décris ton client idéal en 1 phrase. L'IA scanne Reddit / LinkedIn / Google Maps et te ramène 10 leads chauds.", tip: "Précise « SAAS B2B » ou « artisan Paris » pour affiner." },
      { icon: Kanban, btn: "Colonnes Kanban", where: "Zone centrale", do: "Fais glisser les cartes : Détecté → Contacté → En discussion → Signé. Le pipeline se met à jour tout seul.", tip: "Une carte inactive > 3 jours déclenche une relance suggérée." },
      { icon: MessageSquare, btn: "Générer un message", where: "Sur chaque carte prospect", do: "L'IA rédige un message dans ta voix. Tu relis, tu ajustes, tu valides — puis envoi via Gmail / LinkedIn.", tip: "Ton « ton » se configure dans Profil → Mémoire IA." },
      { icon: Filter, btn: "Onglet Sources", where: "Barre d'onglets en haut", do: "Choisis les canaux à surveiller. NET → Reddit, LinkedIn, X. TERRAIN → Google Maps, forums, Nextdoor.", tip: "Coche max 3 sources pour de la qualité, pas du volume." },
    ],
  },
  "/simulation": {
    icon: "🧪",
    title: "Simulation — mode d'emploi",
    subtitle: "Entraîne-toi sur des clients virtuels IA calibrés à ton programme. 4 gestes clés.",
    actions: [
      { icon: GraduationCap, btn: "Décris ton programme", where: "Champ texte en haut de la page", do: "Tape ton domaine et niveau (Master 2 Marketing Digital, Licence Pro RH, MBA Finance…) — l'IA calibre 3 clients virtuels adaptés.", tip: "Sois précis : plus le programme est clair, plus les clients sont réalistes." },
      { icon: Sparkles, btn: "Démarrer la simulation", where: "Bouton doré, sous le champ programme", do: "Un clic génère tes 3 premiers clients virtuels et leur première mission chacun. Bêta gratuite illimitée (20 tâches/jour max).", tip: "Tu peux relancer autant de simulations que nécessaire." },
      { icon: MessageSquare, btn: "Répondre au client", where: "Colonne centrale — zone de texte", do: "Rédige ta réponse professionnelle comme si tu écrivais vraiment au client. L'IA évalue le fond, la forme et l'adaptation au client.", tip: "Traite le client virtuel comme un vrai — c'est comme ça que tu progresses." },
      { icon: Send, btn: "Envoyer ma réponse", where: "Bouton doré sous la zone de réponse", do: "L'IA analyse ta réponse, te donne un score /10, tes points forts et tes axes d'amélioration.", tip: "Lis TOUS les feedbacks : c'est là que se construit la vraie expertise." },
    ],
  },
  "/parametres": {
    icon: "⚙️",
    title: "Paramètres — mode d'emploi",
    subtitle: "8 sections pour tout piloter. Une fois configuré, plus besoin d'y revenir souvent.",
    actions: [
      { icon: User, btn: "Ton profil", where: "Anneau doré en haut à droite", do: "Complète ton nom, ton email et ton avatar. L'anneau indique le % de complétion — plus il est plein, plus le Coach est précis.", tip: "Un profil à 100% débloque toutes les fonctions IA." },
      { icon: Search, btn: "Rechercher un réglage", where: "Barre de recherche en haut de la page", do: "Tape un mot-clé (notification, mémoire, Stripe, langue…) pour sauter directement à la bonne section.", tip: "Idéal quand tu ne sais pas où se trouve un réglage." },
      { icon: Brain, btn: "Mémoire du Co-pilote", where: "Section « Mémoire IA »", do: "Décris ta vision, ton client idéal, tes valeurs. Le Coach s'appuie dessus pour toutes ses suggestions et messages.", tip: "5 minutes ici = des mois de gain de pertinence." },
      { icon: Plug, btn: "Intégrations", where: "Section « Intégrations »", do: "Connecte Stripe, Qonto, Google Drive, LinkedIn, Brevo… pour que Zayado remplisse Pilotage et Croissance tout seul.", tip: "Stripe + Qonto = 90% de la saisie manuelle qui disparaît." },
      { icon: CreditCard, btn: "Facturation", where: "Section « Facturation »", do: "Change de forfait, télécharge tes factures, applique un code promo. Tout est ici, jamais caché.", tip: "Le forfait annuel économise ~2 mois vs mensuel." },
      { icon: ShieldCheck, btn: "Sécurité & données", where: "Section « Sécurité »", do: "Magic link, export RGPD complet, suppression de compte. Tes données t'appartiennent — toujours exportables.", tip: "Fais un export mensuel comme sauvegarde perso." },
    ],
  },
  "/roadmap": {
    icon: "🗺️",
    title: "Roadmap — mode d'emploi",
    subtitle: "Ce qu'on construit, en toute transparence. 3 colonnes pour tout voir en un regard.",
    actions: [
      { icon: CheckCircle2, btn: "Livré", where: "Colonne de gauche (verte)", do: "Ce qui est déjà en production. Les dernières fonctionnalités ajoutées apparaissent en haut avec leur date.", tip: "Une fonction manque ? Regarde d'abord ici — elle est peut-être déjà là." },
      { icon: Loader2, btn: "En cours", where: "Colonne centrale (dorée)", do: "Ce qu'on développe actuellement avec une estimation trimestrielle. C'est ici que ça bouge le plus vite.", tip: "Les ETA sont indicatives, jamais garanties." },
      { icon: ThumbsUp, btn: "Voter pour une idée", where: "Colonne de droite — bouton ▲ sur chaque carte", do: "Vote ▲ pour les fonctionnalités qui te seraient utiles. Les plus demandées passent en priorité au prochain sprint.", tip: "Un vote engagé compte plus qu'un vote au hasard — vote ce qui te bloque vraiment." },
    ],
  },
  "/bureau": {
    icon: "🗂️",
    title: "Mon Bureau — mode d'emploi",
    subtitle: "Ton espace missions, documents et notes. Cherche ces 4 zones.",
    actions: [
      { icon: Kanban, btn: "Onglet Missions", where: "1er onglet en haut", do: "Tape ta tâche + une date. Glisse-la ensuite entre À faire / En cours / Fait.", tip: "Les tâches en retard (rouge) remontent automatiquement en tête." },
      { icon: Wand2, btn: "Générer mes missions", where: "Bouton doré en haut du Kanban", do: "L'IA lit ton Vision Board et propose 5-10 missions de la semaine. Tu valides une par une.", tip: "Refais-le chaque lundi pour une to-do calée sur ta vision." },
      { icon: FileUp, btn: "Onglet Documents", where: "2ᵉ onglet en haut", do: "Dépose factures, contrats, devis (drag & drop ou +). L'IA les OCRise et remplit auto les montants dans Pilotage.", tip: "Nomme tes docs « FR-2025-001 » pour un tri auto par pièce." },
      { icon: StickyNote, btn: "Onglet Notes", where: "3ᵉ onglet en haut", do: "Journal libre. Chaque note enrichit la mémoire du Coach IA pour affiner ses conseils.", tip: "Note ce que tu apprends après un rendez-vous — l'IA le rappellera au prochain contact." },
    ],
  },
};

export function PageOnboardingModal({ path, onClose }) {
  const { prefs, setPref } = usePrefs();
  const data = ONBOARDING_STEPS[path];
  if (!data) return null;
  const storageKey = `zayado_onboarding_seen_${path.replace(/\//g, "_")}`;

  // Persiste "vu" côté local ET serveur pour ne jamais réapparaître.
  const dismiss = ({ neverAgain = true } = {}) => {
    if (neverAgain) {
      localStorage.setItem(storageKey, "1");
      const seen = prefs.page_tours_seen || [];
      if (!seen.includes(path)) setPref({ page_tours_seen: [...seen, path] });
    }
    onClose();
  };

  return (
    <AnimatePresence>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
        style={{ position: "fixed", inset: 0, background: "rgba(11,31,58,0.72)", backdropFilter: "blur(10px)", zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center", padding: 20 }}>
        <motion.div initial={{ scale: 0.92, y: 16, opacity: 0 }} animate={{ scale: 1, y: 0, opacity: 1 }} exit={{ scale: 0.92, opacity: 0 }}
          data-testid="page-onboarding-modal"
          style={{
            background: "var(--glass-bg)",
            border: "1px solid var(--glass-border)",
            borderRadius: 24, padding: 28,
            maxWidth: 520, width: "100%",
            maxHeight: "88vh", overflowY: "auto",
            position: "relative",
          }}>

          {/* Bouton fermer */}
          <button onClick={() => dismiss({ neverAgain: false })} data-testid="page-onboarding-close"
            style={{ position: "absolute", top: 14, right: 14, background: "none", border: "none", cursor: "pointer", color: "var(--muted)", padding: 4 }}
            aria-label="Fermer">
            <X size={18} />
          </button>

          {/* Header : icône + titre */}
          <div style={{ display: "flex", alignItems: "flex-start", gap: 14, marginBottom: 18 }}>
            <span style={{
              fontSize: 26, lineHeight: 1,
              width: 52, height: 52,
              display: "flex", alignItems: "center", justifyContent: "center",
              background: "var(--glass-soft)", borderRadius: 16,
              flexShrink: 0,
            }}>{data.icon}</span>
            <div style={{ minWidth: 0 }}>
              <h2 style={{ fontSize: 18, fontWeight: 700, color: "var(--txt)", margin: "0 0 4px" }}>{data.title}</h2>
              <p style={{ fontSize: 13.5, color: "var(--muted)", lineHeight: 1.5, margin: 0 }}>{data.subtitle}</p>
            </div>
          </div>

          {/* Liste des actions : chaque entrée = APERÇU VISUEL du bouton à trouver */}
          <div style={{ display: "flex", flexDirection: "column", gap: 12, margin: "18px 0 20px" }}>
            {data.actions.map((a, i) => {
              const Icon = a.icon;
              return (
                <div key={i} data-testid={`page-onboarding-action-${i}`}
                  style={{
                    padding: "14px",
                    background: "rgba(255,255,255,0.03)",
                    border: "1px solid var(--glass-border)",
                    borderRadius: 14,
                    display: "flex", gap: 12, alignItems: "flex-start",
                  }}>
                  {/* Numéro d'étape */}
                  <span style={{
                    flexShrink: 0,
                    width: 22, height: 22, lineHeight: "22px", textAlign: "center",
                    borderRadius: 999, background: "#DEC2A3", color: "#0a1f4e",
                    fontSize: 11, fontWeight: 800,
                    marginTop: 4,
                  }}>{i + 1}</span>

                  <div style={{ flex: 1, minWidth: 0 }}>
                    {/* APERÇU VISUEL du bouton — pilule dorée avec icône réelle */}
                    <div style={{
                      display: "inline-flex", alignItems: "center", gap: 7,
                      padding: "6px 12px",
                      background: "linear-gradient(180deg, rgba(222, 194, 163,0.22) 0%, rgba(222, 194, 163,0.14) 100%)",
                      border: "1px solid rgba(222, 194, 163,0.55)",
                      borderRadius: 999,
                      boxShadow: "0 2px 8px rgba(222, 194, 163,0.15), inset 0 1px 0 rgba(255,255,255,0.08)",
                      marginBottom: 6,
                      maxWidth: "100%",
                    }}>
                      {Icon && (
                        <span style={{
                          display: "flex", alignItems: "center", justifyContent: "center",
                          width: 22, height: 22, borderRadius: 999,
                          background: "#DEC2A3", color: "#0a1f4e",
                          flexShrink: 0,
                        }}>
                          <Icon size={13} strokeWidth={2.5} />
                        </span>
                      )}
                      <span style={{
                        fontSize: 13, fontWeight: 700, color: "var(--gold-strong)",
                        whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis",
                      }}>{a.btn}</span>
                    </div>

                    {/* Localisation à l'écran */}
                    {a.where && (
                      <p style={{
                        display: "flex", alignItems: "center", gap: 5,
                        margin: "0 0 8px", fontSize: 11.5,
                        color: "var(--muted)",
                        textTransform: "uppercase", letterSpacing: 0.4, fontWeight: 600,
                      }}>
                        <MapPin size={11} style={{ opacity: 0.7 }} />
                        {a.where}
                      </p>
                    )}

                    {/* Ce que ça fait / ce que tu dois faire */}
                    <p style={{ fontSize: 13.5, color: "var(--txt)", lineHeight: 1.55, margin: "0 0 6px" }}>{a.do}</p>

                    {/* Astuce optionnelle */}
                    {a.tip && (
                      <p style={{
                        fontSize: 12, color: "var(--muted)", lineHeight: 1.5, margin: 0,
                        fontStyle: "italic", opacity: 0.85,
                      }}>
                        <span style={{ color: "#DEC2A3", fontStyle: "normal", fontWeight: 700 }}>✦ Astuce : </span>{a.tip}
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Actions bas */}
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <button onClick={() => dismiss({ neverAgain: false })} data-testid="page-onboarding-later"
              className="zbtn" style={{ height: 42, flex: 1, minWidth: 140, justifyContent: "center" }}>
              Fermer
            </button>
            <button onClick={() => dismiss({ neverAgain: true })} data-testid="page-onboarding-dismiss"
              className="zbtn zbtn-primary" style={{ height: 42, flex: 2, minWidth: 180, justifyContent: "center" }}>
              Compris, ne plus afficher 🚀
            </button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

// ─── NAVIGATION PAR CATÉGORIES (façon Claude.ai) ──────────────
const SETTINGS_SECTIONS = [
  { id: "general",      label: "Général",         Icon: Palette,     keywords: "apparence thème couleur menu langue français english" },
  { id: "profil",       label: "Profil",          Icon: User,        keywords: "nom email mémoire ia identité business pourquoi quoi qui comment" },
  { id: "vision",       label: "Vision & Inspiration", Icon: Images, keywords: "photo image inspiration écran démarrage ambiance carrousel" },
  { id: "notifications",label: "Notifications",   Icon: Bell,        keywords: "email alerte crédit énergie swot rappel" },
  { id: "automatisation", label: "Automatisation", Icon: Zap,        keywords: "agent ia automatisation zapier make workflow relance email tâche répétitive déléguer bien-être" },
  { id: "integrations", label: "Intégrations",     Icon: Plug,       keywords: "drive onedrive notion trello jira slack whatsapp telegram brevo hubspot make linkedin youtube stripe qonto" },
  { id: "securite",     label: "Sécurité",         Icon: ShieldCheck,keywords: "lien magique export données rgpd supprimer compte" },
  { id: "facturation",  label: "Facturation",      Icon: CreditCard, keywords: "plan abonnement start grow serenity prix" },
];

function SettingsNav({ active, onSelect, connectedCount, query }) {
  const q = query.trim().toLowerCase();
  const visible = q
    ? SETTINGS_SECTIONS.filter(s => (s.label + " " + s.keywords).toLowerCase().includes(q))
    : SETTINGS_SECTIONS;
  return (
    <>
      {/* Desktop — sidebar verticale */}
      <nav className="settings-nav-desktop" data-testid="settings-nav-desktop">
        {visible.map(s => (
          <button key={s.id} onClick={() => onSelect(s.id)}
            className={`settings-nav-item ${active === s.id ? "active" : ""}`}
            data-testid={`settings-nav-${s.id}`}>
            <s.Icon size={16} />
            <span>{s.label}</span>
            {s.id === "integrations" && connectedCount > 0 && (
              <span className="settings-nav-badge">{connectedCount}</span>
            )}
          </button>
        ))}
        {visible.length === 0 && <p className="muted" style={{ fontSize: 12, padding: "8px 12px" }}>Aucun résultat.</p>}
      </nav>

      {/* Mobile — barre scrollable horizontale */}
      <nav className="settings-nav-mobile" data-testid="settings-nav-mobile">
        {visible.map(s => (
          <button key={s.id} onClick={() => onSelect(s.id)}
            className={`settings-nav-item-mobile ${active === s.id ? "active" : ""}`}
            data-testid={`settings-nav-mobile-${s.id}`}>
            <s.Icon size={15} />
            <span>{s.label}</span>
          </button>
        ))}
      </nav>
    </>
  );
}

// ─── CONTENU PARTAGÉ (utilisé par la modale ET la page) ────────
function SettingsContent({ initialSection = "general" }) {
  const { prefs, setPref, t } = usePrefs();
  const { user } = useAuth();
  const [active, setActive] = useState(initialSection);
  const [searchQuery, setSearchQuery] = useState("");
  const [profile, setProfile] = useState({ name: "", email: "" });
  const [vision, setVisionData] = useState(null);
  const [integrations, setIntegrations] = useState([]);
  const [connectedCount, setConnectedCount] = useState(0);
  const [newsPrefs, setNewsPrefsState] = useState({ sector: "", region: "France", frequency_per_week: 1 });

  const loadIntegrations = () => {
    integrationsApi.list().then(d => { setIntegrations(d.items || []); setConnectedCount(d.connected_count || 0); }).catch(() => {});
  };
  useEffect(() => {
    growthApi.getSettings().then(s => {
      setProfile({ name: s.profile?.name || user?.name || "", email: s.profile?.email || user?.email || "" });
      setVisionData(s.vision || {});
    }).catch(() => setProfile({ name: user?.name || "", email: user?.email || "" }));
    loadIntegrations();
    getNewsPreferences().then((data) => setNewsPrefsState({ sector: data?.sector || "", region: data?.region || "France", frequency_per_week: Number(data?.frequency_per_week) === 2 ? 2 : 1 })).catch(() => {});
  }, [user?.email, user?.name]);
  useEffect(() => { setActive(initialSection || "general"); }, [initialSection]);

  // Complétion du profil — nom, email, 4 champs mémoire IA, image d'inspiration
  const completionItems = [
    !!profile.name, !!profile.email,
    !!vision?.why, !!vision?.what, !!vision?.who, !!vision?.how,
    !!prefs.inspiration_photo,
  ];
  const completionPct = Math.round((completionItems.filter(Boolean).length / completionItems.length) * 100);

  const saveProfile = (patch) => {
    const next = { ...profile, ...patch };
    setProfile(next);
    growthApi.saveSettings({ profile: next }).then(() => toast.success(t("set_saved"))).catch(() => {});
  };
  const change = (patch, msg) => { setPref(patch); toast.success(msg || t("set_saved")); };
  const saveNewsPrefs = () => {
    setNewsPreferences(newsPrefs).then(() => toast.success("Flux d’actualité enregistré")).catch(() => toast.error("Impossible d’enregistrer le flux d’actualité"));
  };

  return (
    <div className="settings-shell" data-testid="settings-shell">
      <div className="settings-nav-wrap">
        <div className="settings-search-box" data-testid="settings-search-box">
          <Search size={14} style={{ color: "var(--muted)", flexShrink: 0 }} />
          <input value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
            placeholder="Rechercher un réglage…" data-testid="settings-search-input" />
        </div>

        {/* Indicateur de complétion profil */}
        <div className="settings-completion" data-testid="settings-completion" onClick={() => setActive("profil")}>
          <div className="settings-completion-ring" style={{ "--pct": completionPct }}>
            <span>{completionPct}%</span>
          </div>
          <div>
            <p style={{ fontSize: 12.5, fontWeight: 600, color: "var(--txt)", margin: 0 }}>Profil complété</p>
            <p className="muted" style={{ fontSize: 11, margin: 0 }}>{completionPct < 100 ? "Complétez votre profil" : "Profil complet !"}</p>
          </div>
        </div>

        <SettingsNav active={active} onSelect={setActive} connectedCount={connectedCount} query={searchQuery} />
      </div>

      <div className="settings-panel" data-testid={`settings-panel-${active}`}>
        {active === "general" && (
          <>
            <div className="glass-card" style={{ marginBottom: 16 }} data-testid="settings-appearance">
              <div className="card-label"><Palette size={14} /> {t("set_appearance")}</div>
              <p className="muted" style={{ fontSize: 13, margin: "6px 0 12px" }}>{t("set_theme")}</p>
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                <Opt active={prefs.theme !== "light"} onClick={() => change({ theme: "dark" })} Icon={Moon} label={t("theme_dark")} testid="set-theme-dark" />
              </div>
            </div>
            <div className="glass-card" data-testid="settings-language">
              <div className="card-label"><Globe size={14} /> {t("language")}</div>
              <p className="muted" style={{ fontSize: 12, margin: "6px 0 12px" }}>Détectée automatiquement selon votre position — modifiable ici.</p>
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                <Opt active={prefs.language === "fr"} onClick={() => change({ language: "fr" })} Icon={Globe} label="Français" testid="set-lang-fr" />
                <Opt active={prefs.language === "en"} onClick={() => change({ language: "en" })} Icon={Globe} label="English" testid="set-lang-en" />
              </div>
            </div>
            <div className="glass-card" style={{ marginTop: 16 }} data-testid="settings-news-preferences">
              <div className="card-label"><Newspaper size={14} /> Flux d’actualité</div>
              <p className="muted" style={{ fontSize: 12, margin: "6px 0 14px" }}>Le Copilote utilisera automatiquement ces critères pour sa veille sectorielle.</p>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))", gap: 12 }}>
                <label style={{ display: "flex", flexDirection: "column", gap: 6, fontSize: 12, color: "var(--muted)" }}>
                  Secteur d’intérêt
                  <input className="settings-input" value={newsPrefs.sector} onChange={(e) => setNewsPrefsState((current) => ({ ...current, sector: e.target.value }))} placeholder="Ex. SaaS, e-commerce, finance" data-testid="settings-news-sector" />
                </label>
                <label style={{ display: "flex", flexDirection: "column", gap: 6, fontSize: 12, color: "var(--muted)" }}>
                  Région / pays
                  <input className="settings-input" value={newsPrefs.region} onChange={(e) => setNewsPrefsState((current) => ({ ...current, region: e.target.value }))} placeholder="Ex. France, Europe, Canada" data-testid="settings-news-region" />
                </label>
                <label style={{ display: "flex", flexDirection: "column", gap: 6, fontSize: 12, color: "var(--muted)" }}>
                  Fréquence automatique
                  <select className="settings-input" value={newsPrefs.frequency_per_week} onChange={(e) => setNewsPrefsState((current) => ({ ...current, frequency_per_week: Number(e.target.value) }))} data-testid="settings-news-frequency">
                    <option value={1}>1 fois par semaine</option>
                    <option value={2}>2 fois par semaine</option>
                  </select>
                </label>
              </div>
              <button onClick={saveNewsPrefs} style={{ marginTop: 14 }} className="settings-action-button" data-testid="settings-news-save"><Save size={14} /> Enregistrer le flux</button>
            </div>
          </>
        )}

        {active === "profil" && (
          <>
            <CoursCockpitProfile />
            <MemoireSection />
          </>
        )}

        {active === "vision" && (
          <>
            <div className="glass-card" style={{ marginBottom: 16 }} data-testid="settings-preferences">
              <div className="card-label"><Images size={14} /> Affichage de ma vision sur le dashboard</div>
              <p className="muted" style={{ fontSize: 13, margin: "6px 0 12px" }}>Choisis ce qui s'affiche à droite de ton cockpit.</p>
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                <Opt active={prefs.vision_display === "carousel"} onClick={() => change({ vision_display: "carousel" })} Icon={Images} label="Carrousel de mes photos" testid="set-vision-carousel" />
                <Opt active={prefs.vision_display === "phrase" || !prefs.vision_display} onClick={() => change({ vision_display: "phrase" })} Icon={Quote} label="Ma phrase de vision" testid="set-vision-phrase" />
                <Opt active={prefs.vision_display === "image"} onClick={() => change({ vision_display: "image" })} Icon={ImageIcon} label="Image seule" testid="set-vision-image" />
              </div>
            </div>
            <InspirationSection prefs={prefs} setPref={setPref} />
            <CoursInspirationUrl />
          </>
        )}

        {active === "notifications" && (
          <>
            <CoursRemindersSection />
            <NotificationsSection prefs={prefs} setPref={setPref} />
          </>
        )}

        {active === "automatisation" && <AutomatisationSettings />}

        {active === "integrations" && (
          <div className="glass-card" data-testid="settings-integrations">
            <div className="card-label" style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}><Plug size={14} /> Intégrations</span>
              <span className="zchip" style={{ fontSize: 11, background: "var(--glass-soft)", color: "var(--muted)" }}>{connectedCount} service(s) connecté(s)</span>
            </div>
            <p className="muted" style={{ fontSize: 13, margin: "6px 0 14px" }}>Connecte tes services. Les clés sont enregistrées en base.</p>
            <OdooIntegrationCard />
            <PlannedFinancialIntegrationCard name="Pennylane" detail="Lecture des factures, dépenses et indicateurs comptables autorisés." testid="pennylane-integration-card" />
            <PlannedFinancialIntegrationCard name="Qonto" detail="Lecture des comptes, soldes et transactions autorisées, sans capacité de paiement." testid="qonto-integration-card" />
            <BankAggregatorCard />
            <div style={{ display: "flex", flexDirection: "column", gap: 12, marginTop: 12 }}>
              {integrations.map(it => <IntegrationCard key={it.key} item={it} onSaved={loadIntegrations} />)}
              {integrations.length === 0 && <p className="muted" style={{ fontSize: 13, textAlign: "center", padding: 20 }}>Chargement du catalogue…</p>}
            </div>
          </div>
        )}

        {active === "securite" && <><CoursSecurityExport /><SecuriteSection /></>}
        {active === "facturation" && <FacturationSection />}
      </div>
    </div>
  );
}

// ─── MODALE PARAMÈTRES ────────────────────────────────────────
export function SettingsModal({ open, onClose, initialSection = "general" }) {
  const { t } = usePrefs();
  if (!open || typeof document === "undefined") return null;
  return createPortal(
    <AnimatePresence>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
        style={{ position: "fixed", inset: 0, background: "rgba(5,8,26,0.72)", backdropFilter: "blur(10px)", zIndex: 3000, display: "flex", alignItems: "center", justifyContent: "center", padding: 16 }}
        onClick={onClose}>
        <motion.div initial={{ y: 24, opacity: 0, scale: 0.98 }} animate={{ y: 0, opacity: 1, scale: 1 }} exit={{ y: 24, opacity: 0, scale: 0.98 }} transition={{ type: "spring", damping: 30, stiffness: 320 }}
          style={{ background: "var(--glass-bg)", border: "1px solid var(--glass-border)", borderRadius: 22, width: "100%", maxWidth: 980, height: "86vh", maxHeight: "86vh", overflow: "hidden", display: "flex", flexDirection: "column", boxShadow: "0 24px 80px rgba(0,0,0,0.45)" }}
          onClick={e => e.stopPropagation()}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "18px 24px", borderBottom: "1px solid var(--glass-border)", flexShrink: 0 }}>
            <h2 style={{ fontSize: 18, fontWeight: 700, color: "var(--txt)", margin: 0 }}>{t("settings")}</h2>
            <button onClick={onClose} data-testid="settings-modal-close" style={{ background: "none", border: "none", cursor: "pointer", color: "var(--muted)", padding: 4 }}><X size={20} /></button>
          </div>
          <div style={{ overflow: "hidden", flex: 1, minHeight: 0, display: "flex" }}>
            <SettingsContent initialSection={initialSection} />
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>,
    document.body,
  );
}


export default SettingsModal;
