/* Espace "Mon Compte" Zayado — style Kiabi adapté palette navy/or.

   Hub dashboard utilisateur connecté. 4 sections :
   1. Mes commandes (achats + retours Shopify)
   2. Espace Trajectoire Zayado (rebrand fidélité — niveau, avantages, progression)
   3. Mon profil (informations + préférences)
   4. Besoin d'aide

   La page utilise GET /api/account/me + GET /api/account/orders.
   Sur 401 → l'intercepteur redirige automatiquement vers /login.

   Sous-pages : /compte (hub), /compte/commandes, /compte/profil, /compte/preferences. */
import React, { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import {
  Package, RotateCcw, Award, FileText, Bell,
  HelpCircle, LogOut, ChevronRight, Sparkles, ArrowLeft,
  Check, Mail, User as UserIcon, Phone, Loader2,
} from "lucide-react";
import api from "@/lib/api";

const NAVY = "var(--zayado-navy)";
const GOLD = "var(--zayado-gold)";
const MUTED = "var(--zayado-muted)";

// Couleurs par niveau Trajectoire
const LEVEL_COLORS = {
  Explorateur: { bg: "linear-gradient(135deg, #f7f4ee 0%, #e8dfc9 100%)", text: NAVY },
  Constructeur: { bg: "linear-gradient(135deg, #d4af37 0%, #b8941f 100%)", text: "#fff" },
  Stratège: { bg: "linear-gradient(135deg, #1a2742 0%, #2d3e60 100%)", text: "#fff" },
  Visionnaire: { bg: "linear-gradient(135deg, #0f1729 0%, #d4af37 100%)", text: "#fff" },
};

// ── Bloc utilitaire : ligne d'action avec icône + chevron ─────────────────
function ActionRow({ to, icon: Icon, label, sublabel, testId }) {
  return (
    <Link to={to} data-testid={testId}
          className="flex items-center justify-between gap-3 bg-white border border-[var(--zayado-border)] rounded-2xl px-5 py-4 hover:border-[var(--zayado-navy)] transition-colors group">
      <div className="flex items-center gap-4">
        <Icon size={18} style={{ color: NAVY }} className="shrink-0" />
        <div>
          <div className="text-sm font-medium" style={{ color: "var(--zayado-text)" }}>{label}</div>
          {sublabel && <div className="text-xs mt-0.5" style={{ color: MUTED }}>{sublabel}</div>}
        </div>
      </div>
      <ChevronRight size={16} style={{ color: MUTED }} className="group-hover:translate-x-0.5 transition-transform" />
    </Link>
  );
}

function SectionTitle({ children }) {
  return (
    <div className="text-xs uppercase tracking-[0.25em] mb-3 font-bold mt-8" style={{ color: NAVY }}>
      {children}
    </div>
  );
}

// ── HUB principal /compte ─────────────────────────────────────────────────
function AccountHub({ me }) {
  const navigate = useNavigate();
  const traj = me?.trajectory || {};
  const colors = LEVEL_COLORS[traj.level] || LEVEL_COLORS.Explorateur;

  const onLogout = async () => {
    try { await api.post("/auth/logout"); } catch {}
    window.location.href = "/";
  };

  return (
    <div className="max-w-[860px] mx-auto px-4 md:px-6 py-10" data-testid="account-hub">
      {/* Greeting */}
      <h1 className="font-display italic mb-1"
          style={{ fontFamily: "'DM Serif Display', serif",
                   fontSize: "clamp(1.8rem, 4vw, 2.6rem)", color: NAVY }}>
        Bonjour {me?.user?.first_name || me?.user?.email?.split("@")[0] || "vous"}.
      </h1>
      <p className="text-sm mb-8" style={{ color: MUTED }} data-testid="account-email">
        {me?.user?.email}
      </p>

      {/* Section Mes commandes */}
      <SectionTitle>Mes commandes</SectionTitle>
      <div className="space-y-3">
        <ActionRow to="/compte/commandes" icon={Package} label="Mes achats"
                   sublabel="Historique et suivi de vos commandes Boutique"
                   testId="account-action-orders" />
        <ActionRow to="/compte/commandes?tab=retours" icon={RotateCcw} label="Mes retours"
                   sublabel="Demander un retour ou un échange"
                   testId="account-action-returns" />
      </div>

      {/* Section Espace Trajectoire (rebrand fidélité) */}
      <SectionTitle>Mon espace Trajectoire</SectionTitle>
      <div className="rounded-2xl p-6 md:p-7 mb-3"
           style={{ background: colors.bg, color: colors.text }}
           data-testid="account-trajectory-card">
        <div className="flex items-start justify-between gap-4 mb-4">
          <div>
            <div className="text-[11px] uppercase tracking-[0.25em] opacity-80 mb-1">Votre niveau</div>
            <div className="font-display italic"
                 style={{ fontFamily: "'DM Serif Display', serif",
                          fontSize: "clamp(1.6rem, 3.5vw, 2.2rem)", lineHeight: 1.1 }}>
              {traj.level || "Explorateur"}
            </div>
          </div>
          <Sparkles size={26} style={{ color: traj.level === "Explorateur" ? GOLD : "currentColor", opacity: 0.85 }} />
        </div>

        {/* Score / progression */}
        <div className="mb-4">
          <div className="flex items-center justify-between text-xs mb-1.5 opacity-90">
            <span>Score · {traj.score || 0}</span>
            {traj.next_level && <span>Prochain : {traj.next_level} ({traj.next_threshold} pts)</span>}
          </div>
          <div className="h-1.5 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.25)" }}>
            <div className="h-full rounded-full transition-all duration-700"
                 style={{ width: `${traj.progress_pct || 0}%`,
                          background: traj.level === "Explorateur" ? NAVY : "rgba(255,255,255,0.9)" }} />
          </div>
        </div>

        {/* Avantages */}
        <div className="space-y-1.5">
          <div className="text-[11px] uppercase tracking-[0.2em] opacity-80 mb-2">Vos avantages actifs</div>
          {(traj.benefits || []).map((b, i) => (
            <div key={i} className="flex items-center gap-2 text-sm">
              <Check size={13} className="shrink-0" />
              <span>{b}</span>
            </div>
          ))}
        </div>

        <div className="text-[11px] opacity-70 mt-4 leading-relaxed">
          {traj.months_active} mois actif{(traj.months_active || 0) > 1 ? "s" : ""} ·
          {" "}{traj.projects_count} projet{(traj.projects_count || 0) > 1 ? "s" : ""} ·
          {" "}{traj.ideas_count} idée{(traj.ideas_count || 0) > 1 ? "s" : ""}
        </div>
      </div>

      {/* Section Mon profil */}
      <SectionTitle>Mon profil</SectionTitle>
      <div className="space-y-3">
        <ActionRow to="/compte/profil" icon={FileText} label="Informations"
                   sublabel="Nom, prénom, téléphone, adresse"
                   testId="account-action-profile" />
        <ActionRow to="/compte/preferences" icon={Bell} label="Préférences et confidentialité"
                   sublabel="Newsletter, SMS, données personnelles"
                   testId="account-action-preferences" />
      </div>

      {/* Section Aide */}
      <SectionTitle>Besoin d'aide ?</SectionTitle>
      <ActionRow to="/contact" icon={HelpCircle} label="Contacter le service client"
                 sublabel="Réponse sous 24h ouvrées"
                 testId="account-action-help" />

      {/* Logout */}
      <button onClick={onLogout}
              className="mt-10 text-sm flex items-center gap-2 hover:underline mx-auto"
              style={{ color: MUTED }}
              data-testid="account-logout">
        <LogOut size={14} /> Se déconnecter
      </button>
    </div>
  );
}

// ── Sous-page : Mes commandes ─────────────────────────────────────────────
function AccountOrders() {
  const [loading, setLoading] = useState(true);
  const [orders, setOrders] = useState([]);
  const [wcConnected, setWcConnected] = useState(true);

  useEffect(() => {
    api.get("/account/orders")
      .then((r) => {
        setOrders(r.data?.orders || []);
        setWcConnected(r.data?.wc_connected ?? true);
      })
      .catch(() => setOrders([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-[900px] mx-auto px-4 md:px-6 py-10" data-testid="account-orders-page">
      <Link to="/compte" className="text-xs hover:underline inline-flex items-center gap-1 mb-6" style={{ color: MUTED }}>
        <ArrowLeft size={11} /> Retour
      </Link>

      <h1 className="font-display italic mb-1"
          style={{ fontFamily: "'DM Serif Display', serif", fontSize: "clamp(1.6rem, 3.5vw, 2.2rem)", color: NAVY }}>
        Mes commandes
      </h1>
      <p className="text-sm mb-7" style={{ color: MUTED }}>
        Toutes vos commandes Boutique Zayado.
      </p>

      {loading && (
        <div className="flex items-center gap-2 text-sm py-12 justify-center" style={{ color: MUTED }}>
          <Loader2 size={16} className="animate-spin" /> Chargement…
        </div>
      )}

      {!loading && orders.length === 0 && (
        <div className="bg-white border border-[var(--zayado-border)] rounded-2xl p-10 text-center" data-testid="account-orders-empty">
          <Package size={32} className="mx-auto mb-3" style={{ color: GOLD }} />
          <h3 className="font-bold text-lg mb-2" style={{ color: NAVY }}>Aucune commande pour l'instant</h3>
          <p className="text-sm mb-5" style={{ color: MUTED }}>
            Découvrez la boutique des entrepreneurs apaisés.
          </p>
          <Link to="/boutique"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full text-white text-sm font-medium"
                style={{ background: NAVY }}
                data-testid="account-orders-browse">
            Voir la boutique
          </Link>
          {!wcConnected && (
            <div className="text-[11px] mt-4" style={{ color: MUTED }}>
              <em>Boutique Shopify non configurée côté backend.</em>
            </div>
          )}
        </div>
      )}

      {!loading && orders.length > 0 && (
        <div className="space-y-3" data-testid="account-orders-list">
          {orders.map((o) => (
            <div key={o.id} className="bg-white border border-[var(--zayado-border)] rounded-2xl p-5">
              <div className="flex items-center justify-between gap-3 mb-3">
                <div>
                  <div className="text-xs uppercase tracking-wide" style={{ color: MUTED }}>
                    Commande #{o.number}
                  </div>
                  <div className="text-sm mt-0.5" style={{ color: "var(--zayado-text)" }}>
                    {o.date_created ? new Date(o.date_created).toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" }) : ""}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-bold" style={{ color: NAVY }}>{o.total} €</div>
                  <span className="inline-block text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full font-bold"
                        style={{
                          background: o.status === "completed" ? "#d1fae5" : o.status === "processing" ? "#fef3c7" : "#fee2e2",
                          color: o.status === "completed" ? "#065f46" : o.status === "processing" ? "#92400e" : "#991b1b",
                        }}>
                    {o.status === "completed" ? "Livrée" : o.status === "processing" ? "En préparation" : o.status}
                  </span>
                </div>
              </div>
              {o.line_items?.length > 0 && (
                <div className="border-t border-[var(--zayado-border)] pt-3 text-xs" style={{ color: MUTED }}>
                  {o.line_items.length} article{o.line_items.length > 1 ? "s" : ""} ·
                  {" "}{o.line_items.slice(0, 2).map((li) => li.name).join(", ")}
                  {o.line_items.length > 2 && "…"}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Sous-page : Profil + Préférences ──────────────────────────────────────
function AccountProfile({ me, refresh, isPreferences }) {
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    first_name: me?.user?.first_name || "",
    last_name: me?.user?.last_name || "",
    phone: me?.user?.phone || "",
  });
  const [savedMsg, setSavedMsg] = useState("");

  const onSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setSavedMsg("");
    try {
      await api.patch("/account/profile", form);
      setSavedMsg("Modifications enregistrées.");
      refresh && refresh();
    } catch (err) {
      setSavedMsg("Erreur : " + (err.response?.data?.detail || err.message));
    } finally {
      setSaving(false);
      setTimeout(() => setSavedMsg(""), 4000);
    }
  };

  return (
    <div className="max-w-[700px] mx-auto px-4 md:px-6 py-10" data-testid={isPreferences ? "account-preferences-page" : "account-profile-page"}>
      <Link to="/compte" className="text-xs hover:underline inline-flex items-center gap-1 mb-6" style={{ color: MUTED }}>
        <ArrowLeft size={11} /> Retour
      </Link>

      <h1 className="font-display italic mb-1"
          style={{ fontFamily: "'DM Serif Display', serif", fontSize: "clamp(1.6rem, 3.5vw, 2.2rem)", color: NAVY }}>
        {isPreferences ? "Préférences" : "Informations personnelles"}
      </h1>
      <p className="text-sm mb-7" style={{ color: MUTED }}>
        {isPreferences
          ? "Gérez vos abonnements newsletter, SMS et confidentialité."
          : "Mettez à jour vos coordonnées."}
      </p>

      {!isPreferences && (
        <form onSubmit={onSubmit} className="bg-white border border-[var(--zayado-border)] rounded-2xl p-6 space-y-5">
          <div className="flex items-center gap-3 pb-4 border-b border-[var(--zayado-border)] text-sm" style={{ color: MUTED }}>
            <Mail size={14} /> {me?.user?.email}
          </div>

          <div className="grid sm:grid-cols-2 gap-4">
            <label className="block">
              <span className="text-xs font-medium uppercase tracking-wider" style={{ color: NAVY }}>Prénom</span>
              <input type="text" value={form.first_name}
                     onChange={(e) => setForm({ ...form, first_name: e.target.value })}
                     className="mt-1 w-full px-3 py-2.5 border border-[var(--zayado-border)] rounded-lg text-sm focus:outline-none focus:border-[var(--zayado-navy)]"
                     data-testid="profile-first-name" />
            </label>
            <label className="block">
              <span className="text-xs font-medium uppercase tracking-wider" style={{ color: NAVY }}>Nom</span>
              <input type="text" value={form.last_name}
                     onChange={(e) => setForm({ ...form, last_name: e.target.value })}
                     className="mt-1 w-full px-3 py-2.5 border border-[var(--zayado-border)] rounded-lg text-sm focus:outline-none focus:border-[var(--zayado-navy)]"
                     data-testid="profile-last-name" />
            </label>
          </div>

          <label className="block">
            <span className="text-xs font-medium uppercase tracking-wider" style={{ color: NAVY }}>Téléphone</span>
            <input type="tel" value={form.phone}
                   onChange={(e) => setForm({ ...form, phone: e.target.value })}
                   placeholder="+33 6 00 00 00 00"
                   className="mt-1 w-full px-3 py-2.5 border border-[var(--zayado-border)] rounded-lg text-sm focus:outline-none focus:border-[var(--zayado-navy)]"
                   data-testid="profile-phone" />
          </label>

          <div className="flex items-center justify-between pt-2">
            {savedMsg && <div className="text-xs" style={{ color: savedMsg.startsWith("Erreur") ? "#991b1b" : "#065f46" }}>{savedMsg}</div>}
            <button type="submit" disabled={saving}
                    className="ml-auto px-6 py-2.5 rounded-full text-white text-sm font-medium disabled:opacity-50"
                    style={{ background: NAVY }}
                    data-testid="profile-save">
              {saving ? <Loader2 size={14} className="animate-spin inline mr-1" /> : null}
              Enregistrer
            </button>
          </div>
        </form>
      )}

      {isPreferences && (
        <PreferencesPanel me={me} />
      )}
    </div>
  );
}

// ── Sous-section : Préférences (newsletter + SMS) ─────────────────────────
function PreferencesPanel({ me }) {
  const [prefs, setPrefs] = useState({
    newsletter_optin: me?.preferences?.newsletter_optin ?? true,
    sms_optin: me?.preferences?.sms_optin ?? false,
  });
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState("");

  const togglePref = async (key) => {
    const next = { ...prefs, [key]: !prefs[key] };
    setPrefs(next);
    setSaving(true);
    setMsg("");
    try {
      await api.patch("/account/preferences", next);
      setMsg("Modification enregistrée.");
    } catch (e) {
      setPrefs(prefs); // rollback UI
      setMsg("Erreur : " + (e.response?.data?.detail || e.message));
    } finally {
      setSaving(false);
      setTimeout(() => setMsg(""), 3000);
    }
  };

  return (
    <div className="bg-white border border-[var(--zayado-border)] rounded-2xl p-6 space-y-4">
      <div className="flex items-center justify-between py-2">
        <div>
          <div className="text-sm font-medium" style={{ color: "var(--zayado-text)" }}>Newsletter Zayado</div>
          <div className="text-xs mt-0.5" style={{ color: MUTED }}>Conseils entrepreneurs · 1 email / semaine</div>
        </div>
        <input type="checkbox" checked={prefs.newsletter_optin}
               onChange={() => togglePref("newsletter_optin")}
               disabled={saving}
               className="w-5 h-5 accent-[var(--zayado-navy)] cursor-pointer"
               data-testid="pref-newsletter" />
      </div>
      <div className="border-t border-[var(--zayado-border)]" />
      <div className="flex items-center justify-between py-2">
        <div>
          <div className="text-sm font-medium" style={{ color: "var(--zayado-text)" }}>Alertes SMS</div>
          <div className="text-xs mt-0.5" style={{ color: MUTED }}>Suivi de commande uniquement</div>
        </div>
        <input type="checkbox" checked={prefs.sms_optin}
               onChange={() => togglePref("sms_optin")}
               disabled={saving}
               className="w-5 h-5 accent-[var(--zayado-navy)] cursor-pointer"
               data-testid="pref-sms" />
      </div>
      <div className="border-t border-[var(--zayado-border)]" />
      <Link to="/legal/politique-confidentialite"
            className="block text-sm hover:underline pt-2"
            style={{ color: NAVY }}>
        → Gérer mes données personnelles (RGPD)
      </Link>
      {msg && (
        <div className="text-xs pt-2" style={{ color: msg.startsWith("Erreur") ? "#991b1b" : "#065f46" }}>{msg}</div>
      )}
    </div>
  );
}

// ── Composant principal /compte ───────────────────────────────────────────
export default function Account() {
  const loc = useLocation();
  const [me, setMe] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchMe = async () => {
    try {
      const r = await api.get("/account/me");
      setMe(r.data);
    } catch {
      // L'intercepteur 401 redirige déjà — pas besoin d'action ici
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchMe(); }, []);

  const seoTitle = { "/compte/commandes": "Mes commandes", "/compte/profil": "Mon profil", "/compte/preferences": "Préférences" }[loc.pathname] || "Mon compte";
  const AccountSEO = () => (
    <Helmet>
      <title>{seoTitle} — Zayado</title>
      <meta name="robots" content="noindex, follow" />
    </Helmet>
  );

  if (loading) {
    return (
      <>
      <AccountSEO />
      <div className="min-h-[60vh] flex items-center justify-center" style={{ background: "var(--zayado-cream)" }}>
        <Loader2 size={22} className="animate-spin" style={{ color: NAVY }} />
      </div>
      </>
    );
  }

  if (!me) {
    return (
      <>
      <AccountSEO />
      <div className="min-h-[60vh] flex flex-col items-center justify-center px-4" style={{ background: "var(--zayado-cream)" }}>
        <UserIcon size={28} className="mb-3" style={{ color: GOLD }} />
        <p className="text-sm mb-4" style={{ color: MUTED }}>Connectez-vous pour accéder à votre espace.</p>
        <Link to="/login" className="px-5 py-2.5 rounded-full text-white text-sm font-medium" style={{ background: NAVY }}>
          Se connecter
        </Link>
      </div>
      </>
    );
  }

  const path = loc.pathname;
  if (path === "/compte/commandes" || path.startsWith("/compte/commandes")) return <><AccountSEO /><AccountOrders /></>;
  if (path === "/compte/profil") return <><AccountSEO /><AccountProfile me={me} refresh={fetchMe} /></>;
  if (path === "/compte/preferences") return <><AccountSEO /><AccountProfile me={me} refresh={fetchMe} isPreferences /></>;
  return <><AccountSEO /><AccountHub me={me} /></>;
}
