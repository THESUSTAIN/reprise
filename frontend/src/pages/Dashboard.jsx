import React from 'react';
import {
  TrendingUp,
  Wallet,
  Users,
  HeartPulse,
  ArrowUpRight,
  ArrowDownRight,
  Calendar,
  FileText,
  UserPlus,
  CreditCard,
  FileEdit,
  Target,
  AlertTriangle,
  Sparkles,
  Radar,
  LineChart,
  HeartHandshake,
  Eye,
  Wand2,
  Quote,
  ChevronRight,
} from 'lucide-react';
import {
  dashboardKpis,
  dashboardActivity,
  dashboardAgents,
  dashboardQuickActions,
  userProfile,
} from '../mock/mockData';
import { toast } from 'sonner';

const kpiIconMap = { TrendingUp, Wallet, Users, HeartPulse };
const activityIconMap = { UserPlus, CreditCard, FileEdit, Target, AlertTriangle };
const agentIconMap = { Sparkles, Radar, LineChart, HeartHandshake };
const actionIconMap = { Eye, Radar, LineChart, Wand2 };

const Dashboard = () => {
  const firstName = userProfile.fullName.split(' ')[0];

  return (
    <div className="pb-6">
      {/* Page header */}
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4 mb-7">
        <div>
          <h1 className="zy-heading text-3xl md:text-[34px] font-bold text-foreground leading-tight">
            Bonjour {firstName} 👋
          </h1>
          <p className="text-sm text-muted-foreground mt-1.5">
            Voici ton cockpit du jour — tout ce qu’il te faut en moins de 30 secondes.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button className="inline-flex items-center gap-2 h-10 px-3.5 rounded-lg border border-border bg-secondary/40 hover:bg-secondary text-sm transition">
            <Calendar className="w-4 h-4" /> 7 derniers jours
          </button>
          <button
            onClick={() => toast.info('Rapport hebdomadaire — mock')}
            className="zy-btn-primary inline-flex items-center gap-2 h-10 px-4 rounded-lg text-sm font-medium transition"
          >
            <FileText className="w-4 h-4" /> Rapport
          </button>
        </div>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-5 mb-6">
        {dashboardKpis.map((k) => {
          const Icon = kpiIconMap[k.icon] || TrendingUp;
          const toneTile = k.tone === 'gold' ? 'zy-tile-gold' : k.tone === 'green' ? 'zy-tile-green' : 'zy-tile';
          return (
            <div key={k.id} className="zy-card rounded-2xl p-5 zy-lift">
              <div className="flex items-start justify-between mb-4">
                <div className={`w-10 h-10 rounded-xl ${toneTile} flex items-center justify-center`}>
                  <Icon className="w-[18px] h-[18px] text-[#2952a3] dark:text-[#d4b78c]" />
                </div>
                <span
                  className={`inline-flex items-center gap-1 text-[11px] font-medium px-2 py-1 rounded-md ${
                    k.deltaPositive ? 'text-emerald-500 bg-emerald-500/10' : 'text-red-500 bg-red-500/10'
                  }`}
                >
                  {k.deltaPositive ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                  {k.delta}
                </span>
              </div>
              <p className="text-xs text-muted-foreground">{k.label}</p>
              <p className="zy-heading text-[28px] font-bold text-foreground mt-0.5 leading-tight">{k.value}</p>
              <p className="text-xs text-muted-foreground mt-1">{k.sub}</p>
              <div className="mt-3 h-1.5 w-full bg-secondary rounded-full overflow-hidden">
                <div className="h-full zy-spark" style={{ width: '70%' }} />
              </div>
              <p className="text-[11px] text-muted-foreground mt-2">{k.deltaNote}</p>
            </div>
          );
        })}
      </div>

      {/* Citation du jour (large hero card) */}
      <div className="zy-card rounded-2xl p-6 md:p-8 mb-6 relative overflow-hidden">
        <div className="absolute -right-6 -top-6 w-40 h-40 rounded-full bg-[#d4b78c]/10 blur-3xl pointer-events-none" />
        <div className="flex items-start gap-4 relative">
          <div className="w-12 h-12 rounded-xl zy-tile-gold flex items-center justify-center flex-shrink-0">
            <Quote className="w-5 h-5 text-[#0a1f4e] dark:text-[#d4b78c]" />
          </div>
          <div className="flex-1">
            <p className="text-[11px] tracking-[0.18em] uppercase text-muted-foreground mb-2">
              Citation du jour · Univers Sens
            </p>
            <p className="zy-serif text-2xl md:text-[28px] text-foreground leading-snug">
              «&nbsp;La foi, c’est prendre le premier pas, même quand on ne voit pas tout l’escalier.&nbsp;»
            </p>
            <p className="text-xs text-muted-foreground mt-3">Renouvelée chaque matin à 7h00.</p>
          </div>
        </div>
      </div>

      {/* Two-column area: activity + side widgets */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Activity feed */}
        <div className="lg:col-span-2 zy-card rounded-2xl p-6">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="text-base font-semibold text-foreground">Activité récente</h3>
              <p className="text-xs text-muted-foreground mt-0.5">
                Ce que ton Co-pilote et tes agents ont fait pour toi
              </p>
            </div>
            <button className="text-xs text-[#2952a3] dark:text-[#d4b78c] hover:underline flex items-center gap-1">
              Voir tout <ChevronRight className="w-3 h-3" />
            </button>
          </div>

          <ul className="flex flex-col">
            {dashboardActivity.map((a, idx) => {
              const Icon = activityIconMap[a.icon] || UserPlus;
              const tile =
                a.tone === 'gold' ? 'zy-tile-gold' : a.tone === 'green' ? 'zy-tile-green' : a.tone === 'danger' ? 'bg-red-500/15 border border-red-500/25' : 'zy-tile';
              return (
                <li key={a.id} className={`flex items-start gap-3 py-3.5 ${idx !== dashboardActivity.length - 1 ? 'border-b border-border/50' : ''}`}>
                  <div className={`w-9 h-9 rounded-lg ${tile} flex items-center justify-center flex-shrink-0`}>
                    <Icon className="w-4 h-4 text-[#2952a3] dark:text-[#d4b78c]" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-foreground">{a.title}</p>
                    <p className="text-xs text-muted-foreground">{a.desc}</p>
                  </div>
                  <span className="text-[11px] text-muted-foreground flex-shrink-0">{a.time}</span>
                </li>
              );
            })}
          </ul>
        </div>

        {/* Right: Agents + Quick actions */}
        <div className="flex flex-col gap-6">
          {/* Agents */}
          <div className="zy-card rounded-2xl p-6">
            <div className="mb-4">
              <h3 className="text-base font-semibold text-foreground">Tes agents IA</h3>
              <p className="text-xs text-muted-foreground mt-0.5">Modules actifs cette semaine</p>
            </div>
            <ul className="flex flex-col gap-3">
              {dashboardAgents.map((m) => {
                const Icon = agentIconMap[m.icon] || Sparkles;
                const active = m.status === 'Actif';
                return (
                  <li key={m.id} className="flex items-center gap-3 p-3 rounded-xl border border-border/60 bg-secondary/30 hover:bg-secondary/60 transition zy-lift">
                    <div className="w-9 h-9 rounded-lg zy-tile flex items-center justify-center flex-shrink-0">
                      <Icon className="w-4 h-4 text-[#2952a3] dark:text-[#d4b78c]" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium text-foreground truncate">{m.name}</p>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${active ? 'bg-emerald-500/15 text-emerald-500' : 'bg-muted text-muted-foreground'}`}>
                          {m.status}
                        </span>
                      </div>
                      <p className="text-[11px] text-muted-foreground truncate">
                        {m.requests} · {m.avg}
                      </p>
                    </div>
                  </li>
                );
              })}
            </ul>
          </div>

          {/* Quick actions */}
          <div className="zy-card rounded-2xl p-6">
            <h3 className="text-base font-semibold text-foreground mb-1">Actions rapides</h3>
            <p className="text-xs text-muted-foreground mb-4">Saute là où tu en as besoin</p>
            <div className="grid grid-cols-2 gap-3">
              {dashboardQuickActions.map((a) => {
                const Icon = actionIconMap[a.icon] || Eye;
                return (
                  <button
                    key={a.id}
                    onClick={() => toast.info(`${a.label} — mock`)}
                    className="group flex flex-col items-start gap-2 h-[88px] p-3 rounded-xl border border-border/60 bg-secondary/30 hover:border-[#d4b78c]/40 hover:bg-secondary/60 transition zy-lift"
                  >
                    <div className="w-8 h-8 rounded-lg zy-tile flex items-center justify-center">
                      <Icon className="w-4 h-4 text-[#2952a3] dark:text-[#d4b78c]" />
                    </div>
                    <span className="text-xs font-medium text-foreground text-left leading-tight">{a.label}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
