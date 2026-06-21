import React, { useEffect, useState, useCallback } from 'react';
import { projectsApi } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import { toast } from 'sonner';
import { Briefcase, Plus, Play, Square, Clock, Euro, Loader2, Trash2 } from 'lucide-react';

const fmtTime = (s) => {
  s = Math.max(0, Math.floor(s || 0));
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60);
  return `${h}h ${String(m).padStart(2, '0')}m`;
};

export default function Espace() {
  const { user } = useAuth();
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ name: '', hourly_rate: '', color: '#1f4377' });
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const p = await projectsApi.list();
      setProjects(Array.isArray(p) ? p : []);
    } catch (e) { /* gate */ } finally { setLoading(false); }
  }, []);

  useEffect(() => { if (user) load(); }, [user, load]);

  const create = async (e) => {
    e.preventDefault();
    if (!form.name) return;
    setSaving(true);
    try {
      await projectsApi.create({ name: form.name, hourly_rate: parseFloat(form.hourly_rate) || 0, color: form.color });
      toast.success('Mission créée');
      setForm({ name: '', hourly_rate: '', color: '#1f4377' });
      load();
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Erreur lors de la création');
    } finally { setSaving(false); }
  };

  const toggleTimer = async (p) => {
    try {
      if (p.is_running) await projectsApi.stop(p.id);
      else await projectsApi.start(p.id);
      load();
    } catch (err) { toast.error('Erreur minuteur'); }
  };

  const remove = async (id) => {
    try { await projectsApi.remove(id); toast.success('Mission supprimée'); load(); }
    catch (err) { toast.error('Erreur suppression'); }
  };


  return (
    <div data-testid="espace-page" className="space-y-6">
      <div>
        <h1 className="zy-heading text-3xl font-bold text-foreground">Espace de travail</h1>
        <p className="text-muted-foreground mt-1">Missions, suivi du temps & coût — votre Co-pilote au quotidien.</p>
      </div>

      {/* Create mission */}
      <div className="zy-card rounded-2xl p-6" data-testid="create-mission-card">
        <div className="flex items-center gap-2 mb-4">
          <Briefcase className="w-5 h-5 text-foreground" />
          <h3 className="font-semibold text-foreground">Nouvelle mission</h3>
        </div>
        <form onSubmit={create} className="grid grid-cols-1 sm:grid-cols-4 gap-3">
          <input data-testid="mission-name" placeholder="Nom de la mission" value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="h-10 px-3 rounded-lg border border-border bg-background text-foreground sm:col-span-2" />
          <input data-testid="mission-rate" type="number" step="1" placeholder="Taux horaire €" value={form.hourly_rate}
            onChange={(e) => setForm({ ...form, hourly_rate: e.target.value })}
            className="h-10 px-3 rounded-lg border border-border bg-background text-foreground" />
          <button data-testid="mission-submit" type="submit" disabled={saving}
            className="zy-btn-primary h-10 px-4 rounded-lg text-sm font-medium inline-flex items-center justify-center gap-2 disabled:opacity-60">
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />} Créer
          </button>
        </form>
      </div>

      {/* Missions list */}
      {loading ? (
        <div className="flex items-center gap-2 text-muted-foreground"><Loader2 className="w-5 h-5 animate-spin" /> Chargement…</div>
      ) : projects.length === 0 ? (
        <div className="zy-card rounded-2xl p-10 text-center text-muted-foreground" data-testid="missions-empty">
          Aucune mission pour le moment. Créez votre première mission ci-dessus.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="missions-list">
          {projects.map((p) => (
            <div key={p.id} className="zy-card rounded-2xl p-5 zy-lift" data-testid={`mission-${p.id}`}>
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <span className="w-3 h-3 rounded-full" style={{ background: p.color || '#1f4377' }} />
                  <h4 className="font-semibold text-foreground">{p.name}</h4>
                </div>
                <button onClick={() => remove(p.id)} data-testid={`mission-delete-${p.id}`} className="text-muted-foreground hover:text-red-500">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
              <div className="flex items-center gap-4 text-sm text-muted-foreground mb-4">
                <span className="flex items-center gap-1"><Clock className="w-4 h-4" /> {fmtTime(p.total_time_seconds)}</span>
                <span className="flex items-center gap-1"><Euro className="w-4 h-4" /> {Math.round(p.total_cost || 0)} €</span>
              </div>
              <button onClick={() => toggleTimer(p)} data-testid={`mission-timer-${p.id}`}
                className={`w-full h-9 rounded-lg text-sm font-medium inline-flex items-center justify-center gap-2 ${p.is_running ? 'bg-red-500 text-white' : 'zy-btn-primary'}`}>
                {p.is_running ? <><Square className="w-4 h-4" /> Arrêter</> : <><Play className="w-4 h-4" /> Démarrer</>}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
