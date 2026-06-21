import React, { useEffect, useState, useCallback } from 'react';
import { wellnessApi } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import { toast } from 'sonner';
import { HeartPulse, Battery, Smile, Activity, Moon, Loader2, CheckCircle2 } from 'lucide-react';

const SCALES = [
  { key: 'energy', label: 'Énergie', icon: Battery },
  { key: 'mood', label: 'Humeur', icon: Smile },
  { key: 'stress', label: 'Stress', icon: Activity },
  { key: 'sleep', label: 'Sommeil', icon: Moon },
];

export default function BienEtre() {
  const { user } = useAuth();
  const [today, setToday] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ energy: 3, mood: 3, stress: 3, sleep: 3, notes: '' });
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [t, h] = await Promise.all([wellnessApi.today(), wellnessApi.history()]);
      setToday(t);
      setHistory(Array.isArray(h) ? h : (h?.history || []));
    } catch (e) { /* gate */ } finally { setLoading(false); }
  }, []);

  useEffect(() => { if (user) load(); }, [user, load]);

  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const res = await wellnessApi.checkin(form);
      toast.success('Check-in enregistré');
      setToday({ has_checkin: true, ...res });
      load();
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Erreur lors du check-in');
    } finally { setSaving(false); }
  };


  return (
    <div data-testid="bienetre-page" className="space-y-6">
      <div>
        <h1 className="zy-heading text-3xl font-bold text-foreground">Bien-être</h1>
        <p className="text-muted-foreground mt-1">Check-in énergie quotidien, prévention burn-out, carnet de bord.</p>
      </div>

      {loading ? (
        <div className="flex items-center gap-2 text-muted-foreground"><Loader2 className="w-5 h-5 animate-spin" /> Chargement…</div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Check-in form */}
          <div className="lg:col-span-2 zy-card rounded-2xl p-6" data-testid="checkin-card">
            <div className="flex items-center gap-2 mb-5">
              <HeartPulse className="w-5 h-5 text-foreground" />
              <h3 className="font-semibold text-foreground">Check-in du jour</h3>
              {today?.has_checkin && (
                <span className="ml-auto inline-flex items-center gap-1 text-xs text-green-600">
                  <CheckCircle2 className="w-4 h-4" /> Déjà fait aujourd'hui
                </span>
              )}
            </div>
            <form onSubmit={submit} className="space-y-5">
              {SCALES.map(({ key, label, icon: Icon }) => (
                <div key={key} data-testid={`scale-${key}`}>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="flex items-center gap-2 text-sm font-medium text-foreground"><Icon className="w-4 h-4" /> {label}</span>
                    <span className="text-sm font-bold text-foreground">{form[key]}/5</span>
                  </div>
                  <div className="flex gap-2">
                    {[1, 2, 3, 4, 5].map((v) => (
                      <button key={v} type="button" data-testid={`scale-${key}-${v}`}
                        onClick={() => setForm({ ...form, [key]: v })}
                        className={`flex-1 h-9 rounded-lg text-sm font-medium transition ${form[key] === v ? 'text-white' : 'text-muted-foreground border border-border hover:bg-secondary/60'}`}
                        style={form[key] === v ? { background: 'linear-gradient(135deg,#1f4377,#142b45)' } : {}}>
                        {v}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
              <textarea data-testid="checkin-notes" placeholder="Notes (optionnel)" value={form.notes}
                onChange={(e) => setForm({ ...form, notes: e.target.value })} rows={2}
                className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground" />
              <button data-testid="checkin-submit" type="submit" disabled={saving}
                className="zy-btn-primary h-10 px-5 rounded-lg text-sm font-medium inline-flex items-center gap-2 disabled:opacity-60">
                {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />} Enregistrer mon check-in
              </button>
            </form>
          </div>

          {/* History */}
          <div className="zy-card rounded-2xl p-6" data-testid="history-card">
            <h3 className="font-semibold text-foreground mb-4">Historique récent</h3>
            {history.length === 0 ? (
              <p className="text-sm text-muted-foreground">Aucun check-in pour le moment. Faites votre premier aujourd'hui !</p>
            ) : (
              <ul className="space-y-3">
                {history.slice(0, 8).map((h, i) => (
                  <li key={i} className="flex items-center justify-between p-3 rounded-xl border border-border/60" data-testid={`history-${i}`}>
                    <span className="text-sm text-muted-foreground">
                      {h.date ? new Date(h.date).toLocaleDateString('fr-FR') : `Jour ${i + 1}`}
                    </span>
                    <span className="text-sm font-semibold text-foreground">Score {h.score ?? '—'}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
