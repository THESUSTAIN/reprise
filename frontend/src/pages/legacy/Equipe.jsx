import React, { useEffect, useState } from "react";
import { UserPlus, Lock, Users, Mail, Crown, Plus, Trash2, Check } from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import api from "@/lib/api";

export default function Equipe() {
  const { user } = useAuth();
  const isBusiness = user?.plan === "business" || user?.plan === "team" || user?.is_admin;
  const [members, setMembers] = useState([]);
  const [teamCtx, setTeamCtx] = useState({ seats_used: 0, seats_max: 5 });
  const [loading, setLoading] = useState(true);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviting, setInviting] = useState(false);
  const [done, setDone] = useState("");

  const reload = async () => {
    try {
      const [m, ctx] = await Promise.all([
        api.get("/team/members"),
        api.get("/team/me"),
      ]);
      setMembers(m.data || []);
      setTeamCtx(ctx.data || { seats_used: 0, seats_max: 5 });
    } catch (e) { /* ignore */ }
  };

  useEffect(() => {
    if (!isBusiness) { setLoading(false); return; }
    reload().finally(() => setLoading(false));
  }, [isBusiness]);

  const invite = async () => {
    if (!inviteEmail) return;
    setInviting(true);
    setDone("");
    try {
      const r = await api.post("/team/invite", { email: inviteEmail });
      setDone(r?.data?.email_sent
        ? `Invitation envoyée à ${inviteEmail}`
        : `Invitation créée pour ${inviteEmail} (email non envoyé — mode dev)`);
      setInviteEmail("");
      await reload();
    } catch (e) {
      setDone("Erreur : " + (e?.response?.data?.detail || "impossible d'envoyer l'invitation"));
    } finally { setInviting(false); }
  };

  const remove = async (memberId) => {
    if (!window.confirm("Retirer ce membre ?")) return;
    try {
      await api.delete(`/team/members/${memberId}`);
      await reload();
    } catch (e) { /* ignore */ }
  };

  // ── Upsell si pas Business ──
  if (!isBusiness) {
    return (
      <div className="space-y-6" data-testid="equipe-page">
        <header>
          <div className="chip mb-3"><UserPlus size={14} /> Équipe</div>
          <h1 className="font-display text-4xl italic">Collaborer sans friction.</h1>
        </header>

        <div className="card-soft p-8 text-center max-w-2xl mx-auto">
          <div className="inline-flex w-14 h-14 rounded-full bg-[var(--zayado-gold-bg)] text-[var(--zayado-gold)] items-center justify-center mb-5">
            <Crown size={24} />
          </div>
          <div className="font-display text-2xl italic mb-3">Offre Business requise</div>
          <p className="text-[var(--zayado-muted)] mb-6 max-w-md mx-auto">
            Invitez des collaborateurs, gérez les accès et partagez vos projets avec l'offre Business à 99€/mois.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8 text-left">
            {[
              { icon: Users, label: "Jusqu'à 5 membres", desc: "Collaborateurs avec accès complet" },
              { icon: Lock, label: "Permissions granulaires", desc: "Lecture seule ou accès total" },
              { icon: Mail, label: "Invitations par email", desc: "Onboarding automatique" },
            ].map(({ icon: Icon, label, desc }) => (
              <div key={label} className="flex gap-3 p-4 rounded-xl bg-[var(--zayado-cream)]">
                <div className="w-8 h-8 rounded-lg bg-[var(--zayado-navy)]/10 flex items-center justify-center shrink-0">
                  <Icon size={15} className="text-[var(--zayado-navy)]" />
                </div>
                <div>
                  <div className="text-sm font-semibold">{label}</div>
                  <div className="text-xs text-[var(--zayado-muted)]">{desc}</div>
                </div>
              </div>
            ))}
          </div>

          <Link to="/app/billing" className="btn-gold btn-press inline-flex items-center gap-2">
            <Crown size={15} /> Passer en Business — 99€/mois
          </Link>
        </div>
      </div>
    );
  }

  // ── Vue Business ──
  const seatsRemaining = Math.max(0, (teamCtx.seats_max || 5) - (teamCtx.seats_used || 0));
  const inviteDisabled = inviting || !inviteEmail || seatsRemaining <= 0;
  return (
    <div className="space-y-6" data-testid="equipe-page">
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="chip mb-3"><Users size={14} /> Équipe</div>
          <h1 className="font-display text-4xl italic">Collaborer sans friction.</h1>
          <p className="text-sm text-[var(--zayado-muted)] mt-2" data-testid="seats-counter">
            <strong>{teamCtx.seats_used || 0}</strong> / {teamCtx.seats_max || 5} membres ·
            {seatsRemaining > 0 ? ` ${seatsRemaining} place(s) disponible(s)` : " limite atteinte"}
          </p>
        </div>
        <div className="flex gap-2 items-center">
          <input
            type="email"
            placeholder="email@collaborateur.fr"
            value={inviteEmail}
            onChange={(e) => setInviteEmail(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && invite()}
            disabled={seatsRemaining <= 0}
            className="px-3 py-2 text-sm border border-[var(--zayado-border)] rounded-xl focus:outline-none focus:border-[var(--zayado-navy)] disabled:bg-gray-100"
            data-testid="invite-email"
          />
          <button onClick={invite} disabled={inviteDisabled}
            className="btn-navy btn-press inline-flex items-center gap-2 disabled:opacity-50"
            data-testid="invite-btn">
            <Plus size={14} /> {inviting ? "Envoi…" : "Inviter"}
          </button>
        </div>
      </header>

      {done && (
        <div className={`text-sm px-4 py-3 rounded-xl ${done.includes("Erreur") ? "bg-red-50 text-red-700" : "bg-emerald-50 text-emerald-700"}`}>
          {done.includes("Erreur") ? "❌" : "✅"} {done}
        </div>
      )}

      {loading ? (
        <div className="text-center py-10 text-[var(--zayado-muted)]">
          <div className="animate-spin w-6 h-6 border-2 border-[var(--zayado-navy)] border-t-transparent rounded-full mx-auto mb-3" />
          Chargement de l'équipe…
        </div>
      ) : (
        <div className="space-y-2">
          {/* Compte propriétaire */}
          <div className="card-soft p-5 flex items-center gap-4" data-testid="owner-row">
            <div className="w-10 h-10 rounded-full bg-[var(--zayado-navy)] text-white flex items-center justify-center font-bold text-lg shrink-0">
              {(user?.name || user?.email || "?")[0].toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <div className="font-semibold truncate">{user?.name || user?.email}</div>
              <div className="text-xs text-[var(--zayado-muted)]">{user?.email} · Propriétaire</div>
            </div>
            <span className="chip chip-gold text-xs">Propriétaire</span>
          </div>

          {/* Membres invités */}
          {members.length === 0 ? (
            <div className="card-soft p-8 text-center text-[var(--zayado-muted)]" data-testid="no-members">
              Aucun collaborateur pour l'instant. Invitez votre premier membre ci-dessus.
            </div>
          ) : members.map((m) => (
            <div key={m.id} className="card-soft p-5 flex items-center gap-4" data-testid={`member-${m.id}`}>
              <div className="w-10 h-10 rounded-full bg-[var(--zayado-cream-dark)] text-[var(--zayado-navy)] flex items-center justify-center font-bold text-lg shrink-0">
                {(m.name || m.email || "?")[0].toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <div className="font-semibold truncate">{m.name || m.email}</div>
                <div className="text-xs text-[var(--zayado-muted)]">{m.email}</div>
              </div>
              <span className={`chip text-xs ${m.status === "active" ? "" : "chip-gold"}`}>
                {m.status === "active" ? "Actif" : m.status === "invited" ? "Invitation envoyée" : m.status}
              </span>
              <button onClick={() => remove(m.id)} className="p-2 rounded-full hover:bg-red-50 text-red-600 transition-colors"
                data-testid={`remove-${m.id}`} title="Retirer">
                <Trash2 size={15} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
