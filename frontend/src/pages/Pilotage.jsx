import React, { useEffect, useState, useCallback } from 'react';
import { financeApi } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import AuthGate from '../components/AuthGate';
import { toast } from 'sonner';
import {
  TrendingUp, TrendingDown, Wallet, Percent, Plus, Loader2, ShieldCheck, LineChart,
} from 'lucide-react';

const euro = (n) => `${Math.round(n || 0).toLocaleString('fr-FR')} €`;

const serenityColor = (level) =>
  level === 'serein' || level === 'confortable' ? '#16a34a'
    : level === 'vigilance' ? '#d4b78c' : '#dc2626';

export default function Pilotage() {
  const { user, loading: authLoading } = useAuth();
  const [overview, setOverview] = useState(null);
  const [serenity, setSerenity] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ type: 'revenu', label: '', amount: '', category: 'Ventes' });
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [o, s, f] = await Promise.all([
        financeApi.overview(), financeApi.serenity(), financeApi.forecast(),
      ]);
      setOverview(o); setSerenity(s); setForecast(f);
    } catch (e) {
      // 401 handled by gate
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { if (user) load(); }, [user, load]);

  const addEntry = async (e) => {
    e.preventDefault();
    if (!form.label || !form.amount) return;
    setSaving(true);
    try {
      await financeApi.addEntry({
        type: form.type, label: form.label, amount: parseFloat(form.amount),
        category: form.category, recurring: false,
      });
      toast.success('Entrée ajoutée');
      setForm({ ...form, label: '', amount: '' });
      load();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Erreur lors de l'ajout");
    } finally {
      setSaving(false);
    }
  };

  if (!authLoading && !user) return <AuthGate title="au Pilotage financier" />;

  const maxWeekly = overview?.weekly?.reduce((m, w) => Math.max(m, w.revenus, w.depenses), 0) || 1;

  return (
    <div data-testid="pilotage-page" className="space-y-6">
      <div>
        <h1 className="zy-heading text-3xl font-bold text-foreground">Pilotage financier</h1>
        <p className="text-muted-foreground mt-1">CA, trésorerie, marge — votre clarté financière en temps réel.</p>
      </div>

      {loading ? (
        <div className="flex items-center gap-2 text-muted-foreground"><Loader2 className="w-5 h-5 animate-spin" /> Chargement…</div>
      ) : (
        <>
          {/* KPIs */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="zy-card rounded-2xl p-5 zy-lift" data-testid="kpi-revenus">
              <div className="w-10 h-10 rounded-xl zy-tile-green flex items-center justify-center mb-3"><TrendingUp className="w-5 h-5" /></div>
              <div className="text-sm text-muted-foreground">Revenus ({overview?.period})</div>
              <div className="zy-heading text-[26px] font-bold text-foreground">{euro(overview?.revenus)}</div>
            </div>
            <div className="zy-card rounded-2xl p-5 zy-lift" data-testid="kpi-depenses">
              <div className="w-10 h-10 rounded-xl zy-tile flex items-center justify-center mb-3"><TrendingDown className="w-5 h-5" /></div>
              <div className="text-sm text-muted-foreground">Dépenses</div>
              <div className="zy-heading text-[26px] font-bold text-foreground">{euro(overview?.depenses)}</div>
            </div>
            <div className="zy-card rounded-2xl p-5 zy-lift" data-testid="kpi-net">
              <div className="w-10 h-10 rounded-xl zy-tile-gold flex items-center justify-center mb-3"><Wallet className="w-5 h-5" /></div>
              <div className="text-sm text-muted-foreground">Résultat net</div>
              <div className="zy-heading text-[26px] font-bold text-foreground">{euro(overview?.net)}</div>
            </div>
            <div className="zy-card rounded-2xl p-5 zy-lift" data-testid="kpi-marge">
              <div className="w-10 h-10 rounded-xl zy-tile flex items-center justify-center mb-3"><Percent className="w-5 h-5" /></div>
              <div className="text-sm text-muted-foreground">Taux de marge</div>
              <div className="zy-heading text-[26px] font-bold text-foreground">{Math.round(overview?.taux_marge || 0)} %</div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Weekly + forecast */}
            <div className="lg:col-span-2 zy-card rounded-2xl p-6">
              <div className="flex items-center gap-2 mb-4">
                <LineChart className="w-5 h-5 text-foreground" />
                <h3 className="font-semibold text-foreground">Cette semaine</h3>
              </div>
              <div className="flex items-end gap-3 h-40">
                {(overview?.weekly || []).map((w, i) => (
                  <div key={i} className="flex-1 flex flex-col items-center gap-1" data-testid={`weekly-bar-${i}`}>
                    <div className="w-full flex items-end justify-center gap-1 h-32">
                      <div className="w-1/2 rounded-t" style={{ height: `${(w.revenus / maxWeekly) * 100}%`, background: '#16a34a', minHeight: 2 }} />
                      <div className="w-1/2 rounded-t" style={{ height: `${(w.depenses / maxWeekly) * 100}%`, background: '#d4b78c', minHeight: 2 }} />
                    </div>
                    <span className="text-[11px] text-muted-foreground">{w.day}</span>
                  </div>
                ))}
              </div>
              <div className="mt-6 pt-4 border-t border-border/60">
                <h4 className="text-sm font-semibold text-foreground mb-2">Prévision 3 mois</h4>
                <div className="grid grid-cols-3 gap-3">
                  {(forecast?.forecast || []).slice(0, 3).map((m, i) => (
                    <div key={i} className="rounded-xl border border-border/60 p-3" data-testid={`forecast-${i}`}>
                      <div className="text-xs text-muted-foreground">{m.month}</div>
                      <div className="font-semibold text-foreground">{euro(m.net_prevu)}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Serenity */}
            <div className="zy-card rounded-2xl p-6" data-testid="serenity-card">
              <div className="flex items-center gap-2 mb-4">
                <ShieldCheck className="w-5 h-5" style={{ color: serenityColor(serenity?.level) }} />
                <h3 className="font-semibold text-foreground">Score de sérénité</h3>
              </div>
              <div className="flex items-center justify-center my-4">
                <div className="relative w-32 h-32 rounded-full flex items-center justify-center"
                  style={{ background: `conic-gradient(${serenityColor(serenity?.level)} ${(serenity?.score || 0) * 3.6}deg, rgba(120,120,120,0.15) 0)` }}>
                  <div className="w-24 h-24 rounded-full bg-card flex flex-col items-center justify-center">
                    <span className="text-3xl font-bold text-foreground">{serenity?.score ?? 0}</span>
                    <span className="text-[11px] uppercase tracking-wide" style={{ color: serenityColor(serenity?.level) }}>{serenity?.level}</span>
                  </div>
                </div>
              </div>
              <p className="text-sm text-muted-foreground text-center">{serenity?.message}</p>
            </div>
          </div>

          {/* Add entry */}
          <div className="zy-card rounded-2xl p-6" data-testid="add-entry-card">
            <h3 className="font-semibold text-foreground mb-4">Ajouter une transaction</h3>
            <form onSubmit={addEntry} className="grid grid-cols-1 sm:grid-cols-5 gap-3">
              <select data-testid="entry-type" value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}
                className="h-10 px-3 rounded-lg border border-border bg-background text-foreground">
                <option value="revenu">Revenu</option>
                <option value="depense">Dépense</option>
              </select>
              <input data-testid="entry-label" placeholder="Libellé" value={form.label} onChange={(e) => setForm({ ...form, label: e.target.value })}
                className="h-10 px-3 rounded-lg border border-border bg-background text-foreground sm:col-span-2" />
              <input data-testid="entry-amount" type="number" step="0.01" placeholder="Montant €" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })}
                className="h-10 px-3 rounded-lg border border-border bg-background text-foreground" />
              <button data-testid="entry-submit" type="submit" disabled={saving}
                className="zy-btn-primary h-10 px-4 rounded-lg text-sm font-medium inline-flex items-center justify-center gap-2 disabled:opacity-60">
                {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />} Ajouter
              </button>
            </form>
          </div>
        </>
      )}
    </div>
  );
}
