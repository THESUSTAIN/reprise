import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent } from '../ui/card';
import { Input } from '../ui/input';
import {
  Search, ChevronLeft, ChevronRight, Filter, RefreshCw,
  AlertCircle, AlertTriangle, Info, Zap, Trash2, Activity
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL || '';

const LEVEL_CONFIG = {
  INFO:     { color: 'bg-blue-50 text-blue-700',    icon: <Info className="w-3 h-3" />,          dot: 'bg-blue-400' },
  WARNING:  { color: 'bg-yellow-50 text-yellow-700', icon: <AlertTriangle className="w-3 h-3" />, dot: 'bg-yellow-400' },
  ERROR:    { color: 'bg-red-50 text-red-700',       icon: <AlertCircle className="w-3 h-3" />,   dot: 'bg-red-500' },
  CRITICAL: { color: 'bg-purple-50 text-purple-700', icon: <Zap className="w-3 h-3" />,           dot: 'bg-purple-600' },
};

const FEATURE_LABELS = {
  chat:      { label: 'Chat IA',      color: 'bg-[#1D4E8A]/10 text-[#1D4E8A]' },
  auth:      { label: 'Auth',         color: 'bg-green-50 text-green-700' },
  payment:   { label: 'Paiement',     color: 'bg-emerald-50 text-emerald-700' },
  extension: { label: 'Extension',    color: 'bg-orange-50 text-orange-700' },
  affiliate: { label: 'Affiliation',  color: 'bg-pink-50 text-pink-700' },
  admin:     { label: 'Admin',        color: 'bg-gray-100 text-gray-700' },
  agent:     { label: 'Agent IA',     color: 'bg-violet-50 text-violet-700' },
  oauth:     { label: 'OAuth',        color: 'bg-sky-50 text-sky-700' },
};

const HOURS_OPTIONS = [
  { value: '', label: 'Toutes les périodes' },
  { value: '1', label: 'Dernière heure' },
  { value: '6', label: '6 dernières heures' },
  { value: '24', label: '24 dernières heures' },
  { value: '72', label: '3 derniers jours' },
  { value: '168', label: '7 derniers jours' },
];

export const AppLogsTab = ({ headers }) => {
  const [logs, setLogs] = useState([]);
  const [meta, setMeta] = useState({ total: 0, page: 1, per_page: 100, total_pages: 1 });
  const [summary, setSummary] = useState(null);
  const [page, setPage] = useState(1);
  const [levelFilter, setLevelFilter] = useState('');
  const [featureFilter, setFeatureFilter] = useState('');
  const [hoursFilter, setHoursFilter] = useState('24');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const [expandedLog, setExpandedLog] = useState(null);

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    const params = new URLSearchParams({ skip: ((page - 1) * 100).toString(), limit: '100' });
    if (levelFilter) params.set('level', levelFilter);
    if (featureFilter) params.set('feature', featureFilter);
    if (search) params.set('search', search);
    if (hoursFilter) params.set('hours', hoursFilter);
    try {
      const res = await fetch(`${API}/api/admin/app-logs?${params}`, { headers });
      if (res.ok) {
        const data = await res.json();
        setLogs(data.logs || []);
        setMeta({ total: data.total, page: data.page, per_page: data.per_page, total_pages: data.total_pages });
      }
    } catch {}
    setLoading(false);
  }, [page, levelFilter, featureFilter, search, hoursFilter, headers]);

  const fetchSummary = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/admin/app-logs/summary`, { headers });
      if (res.ok) setSummary(await res.json());
    } catch {}
  }, [headers]);

  useEffect(() => { fetchLogs(); fetchSummary(); }, [fetchLogs, fetchSummary]);

  const handlePurge = async () => {
    if (!window.confirm('Supprimer tous les logs de plus de 30 jours ?')) return;
    try {
      const res = await fetch(`${API}/api/admin/app-logs/purge?days=30`, { method: 'DELETE', headers });
      if (res.ok) { const d = await res.json(); alert(`${d.deleted} logs supprimés.`); fetchLogs(); fetchSummary(); }
    } catch {}
  };

  const resetFilters = () => {
    setLevelFilter(''); setFeatureFilter(''); setSearch(''); setHoursFilter('24'); setPage(1);
  };

  return (
    <div className="space-y-4" data-testid="admin-app-logs">

      {/* ── Résumé 24h ── */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {Object.entries(LEVEL_CONFIG).map(([lvl, cfg]) => (
            <div key={lvl} className="bg-white border border-gray-100 rounded-xl p-3 flex items-center gap-3 shadow-sm cursor-pointer hover:border-gray-300 transition"
              onClick={() => { setLevelFilter(lvl === levelFilter ? '' : lvl); setPage(1); }}>
              <div className={`w-2.5 h-2.5 rounded-full ${cfg.dot} flex-shrink-0`} />
              <div>
                <div className="text-xs text-gray-500 font-medium">{lvl}</div>
                <div className="text-lg font-bold text-[#0F1B2D]">{summary.by_level[lvl] || 0}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── Erreurs récentes ── */}
      {summary && summary.last_errors && summary.last_errors.length > 0 && (
        <Card className="border-red-100">
          <CardContent className="p-3">
            <div className="flex items-center gap-2 mb-2">
              <AlertCircle className="w-4 h-4 text-red-500" />
              <span className="text-sm font-semibold text-red-700">Dernières erreurs (24h)</span>
            </div>
            <div className="space-y-1.5">
              {summary.last_errors.map(err => (
                <div key={err.id} className="flex items-start gap-2 text-xs">
                  <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium flex-shrink-0 ${LEVEL_CONFIG[err.level]?.color || 'bg-gray-100 text-gray-600'}`}>
                    {err.level}
                  </span>
                  <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium flex-shrink-0 ${FEATURE_LABELS[err.feature]?.color || 'bg-gray-100 text-gray-600'}`}>
                    {FEATURE_LABELS[err.feature]?.label || err.feature}
                  </span>
                  <span className="text-gray-600 flex-1 truncate">{err.message}</span>
                  <span className="text-gray-400 flex-shrink-0 whitespace-nowrap">
                    {err.created_at ? new Date(err.created_at).toLocaleTimeString('fr-FR') : '-'}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* ── Header + Filtres ── */}
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <h2 className="text-xl font-bold text-[#1D4E8A] flex items-center gap-2">
            <Activity className="w-5 h-5" />
            Logs applicatifs <span className="text-sm font-normal text-gray-400">({meta.total})</span>
          </h2>
          <div className="flex items-center gap-2">
            <button onClick={() => { fetchLogs(); fetchSummary(); }}
              className="flex items-center gap-1.5 text-xs text-[#1D4E8A] border border-[#1D4E8A]/30 rounded-lg px-3 py-1.5 hover:bg-[#1D4E8A]/5">
              <RefreshCw className="w-3.5 h-3.5" /> Actualiser
            </button>
            <button onClick={handlePurge}
              className="flex items-center gap-1.5 text-xs text-red-500 border border-red-200 rounded-lg px-3 py-1.5 hover:bg-red-50">
              <Trash2 className="w-3.5 h-3.5" /> Purger &gt;30j
            </button>
          </div>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-1.5">
            <Filter className="w-3.5 h-3.5 text-gray-400" />
            <span className="text-xs text-gray-500 font-medium">Filtres :</span>
          </div>

          <select value={levelFilter} onChange={e => { setLevelFilter(e.target.value); setPage(1); }}
            className="text-xs border border-gray-200 rounded-lg px-3 py-1.5 bg-white text-gray-600 cursor-pointer focus:border-[#1D4E8A]">
            <option value="">Tous les niveaux</option>
            {Object.keys(LEVEL_CONFIG).map(l => <option key={l} value={l}>{l}</option>)}
          </select>

          <select value={featureFilter} onChange={e => { setFeatureFilter(e.target.value); setPage(1); }}
            className="text-xs border border-gray-200 rounded-lg px-3 py-1.5 bg-white text-gray-600 cursor-pointer focus:border-[#1D4E8A]">
            <option value="">Toutes les fonctionnalités</option>
            {Object.entries(FEATURE_LABELS).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
          </select>

          <select value={hoursFilter} onChange={e => { setHoursFilter(e.target.value); setPage(1); }}
            className="text-xs border border-gray-200 rounded-lg px-3 py-1.5 bg-white text-gray-600 cursor-pointer focus:border-[#1D4E8A]">
            {HOURS_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>

          <div className="relative flex-1 min-w-[180px] max-w-[260px]">
            <Search className="absolute left-3 top-2.5 w-3.5 h-3.5 text-gray-400" />
            <Input placeholder="Rechercher dans les messages..." className="pl-9 text-xs h-8"
              value={search} onChange={e => { setSearch(e.target.value); setPage(1); }} />
          </div>

          {(levelFilter || featureFilter || search || hoursFilter !== '24') && (
            <button onClick={resetFilters} className="text-[11px] text-[#C7372F] font-medium hover:underline">
              Réinitialiser
            </button>
          )}
        </div>
      </div>

      {/* ── Tableau ── */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left p-3 font-medium text-gray-500 w-32">Date</th>
                  <th className="text-left p-3 font-medium text-gray-500 w-20">Niveau</th>
                  <th className="text-left p-3 font-medium text-gray-500 w-24">Module</th>
                  <th className="text-left p-3 font-medium text-gray-500 w-28">Action</th>
                  <th className="text-left p-3 font-medium text-gray-500 w-32">Utilisateur</th>
                  <th className="text-left p-3 font-medium text-gray-500">Message</th>
                  <th className="text-right p-3 font-medium text-gray-500 w-16">Durée</th>
                </tr>
              </thead>
              <tbody>
                {loading && (
                  <tr><td colSpan={7} className="text-center py-8 text-gray-400 text-sm">Chargement...</td></tr>
                )}
                {!loading && logs.map(log => (
                  <React.Fragment key={log.id}>
                    <tr
                      className={`border-b border-gray-100 hover:bg-gray-50 cursor-pointer ${expandedLog === log.id ? 'bg-gray-50' : ''}`}
                      onClick={() => setExpandedLog(expandedLog === log.id ? null : log.id)}
                    >
                      <td className="p-3 text-xs text-gray-400 whitespace-nowrap">
                        {log.created_at ? new Date(log.created_at).toLocaleString('fr-FR', { day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit', second:'2-digit' }) : '-'}
                      </td>
                      <td className="p-3">
                        <span className={`inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full ${LEVEL_CONFIG[log.level]?.color || 'bg-gray-100 text-gray-600'}`}>
                          {LEVEL_CONFIG[log.level]?.icon}
                          {log.level}
                        </span>
                      </td>
                      <td className="p-3">
                        <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${FEATURE_LABELS[log.feature]?.color || 'bg-gray-100 text-gray-600'}`}>
                          {FEATURE_LABELS[log.feature]?.label || log.feature}
                        </span>
                      </td>
                      <td className="p-3 text-xs text-gray-500 max-w-[100px] truncate">{log.action || '-'}</td>
                      <td className="p-3">
                        {log.user_email ? (
                          <div>
                            <div className="text-xs font-medium text-[#0F1B2D] truncate max-w-[120px]">{log.user_email}</div>
                          </div>
                        ) : <span className="text-xs text-gray-300">-</span>}
                      </td>
                      <td className="p-3 text-xs text-gray-700 max-w-[300px]">
                        <span className={log.level === 'ERROR' || log.level === 'CRITICAL' ? 'text-red-600 font-medium' : ''}>
                          {log.message}
                        </span>
                      </td>
                      <td className="p-3 text-right text-xs text-gray-400">
                        {log.duration_ms != null ? `${log.duration_ms}ms` : '-'}
                      </td>
                    </tr>
                    {expandedLog === log.id && log.details && (
                      <tr className="bg-gray-50 border-b border-gray-200">
                        <td colSpan={7} className="px-4 py-3">
                          <div className="text-xs font-semibold text-gray-500 mb-1.5">Détails :</div>
                          <pre className="text-xs bg-white border border-gray-200 rounded-lg p-3 overflow-x-auto text-gray-700 max-h-48">
                            {(() => { try { return JSON.stringify(JSON.parse(log.details), null, 2); } catch { return log.details; } })()}
                          </pre>
                          {log.ip_address && (
                            <div className="text-xs text-gray-400 mt-1.5">IP : {log.ip_address}</div>
                          )}
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>

          {!loading && logs.length === 0 && (
            <div className="text-center py-10 text-gray-400">
              <Activity className="w-8 h-8 mx-auto mb-2 opacity-30" />
              <div className="text-sm">Aucun log pour cette période.</div>
              <div className="text-xs mt-1">Les événements seront enregistrés automatiquement dès la prochaine activité.</div>
            </div>
          )}

          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100">
            <span className="text-xs text-gray-500">
              {meta.total > 0
                ? `${((meta.page - 1) * meta.per_page) + 1}–${Math.min(meta.page * meta.per_page, meta.total)} sur ${meta.total}`
                : 'Aucun log'}
            </span>
            <div className="flex items-center gap-2">
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page <= 1}
                className="p-1.5 border border-gray-200 rounded-lg disabled:opacity-40 hover:bg-gray-50">
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="text-xs font-bold text-[#1D4E8A] px-2">{meta.page} / {meta.total_pages || 1}</span>
              <button onClick={() => setPage(p => p + 1)} disabled={page >= meta.total_pages}
                className="p-1.5 border border-gray-200 rounded-lg disabled:opacity-40 hover:bg-gray-50">
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AppLogsTab;
