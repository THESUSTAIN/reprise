import React, { useState } from 'react';
import { ShieldHalf, KeyRound, Database, Key, Eye, Download } from 'lucide-react';
import { Switch } from '../ui/switch';
import { securityToggles } from '../../mock/mockData';
import { toast } from 'sonner';

const iconMap = { KeyRound, Database };

const SecurityCard = () => {
  const [toggles, setToggles] = useState(securityToggles);

  const flip = (id) =>
    setToggles((p) => p.map((s) => (s.id === id ? { ...s, enabled: !s.enabled } : s)));

  return (
    <section className="zy-card rounded-2xl p-6">
      <div className="flex items-start gap-3 mb-5">
        <div className="w-11 h-11 rounded-xl zy-tile-green flex items-center justify-center flex-shrink-0">
          <ShieldHalf className="w-5 h-5 text-emerald-500" />
        </div>
        <div>
          <h3 className="text-base font-semibold text-foreground">Security &amp; Privacy</h3>
          <p className="text-xs text-muted-foreground">Gérez vos paramètres de sécurité</p>
        </div>
      </div>

      <div className="flex flex-col gap-3 mb-4">
        {toggles.map((s) => {
          const Icon = iconMap[s.icon] || KeyRound;
          return (
            <div
              key={s.id}
              className="flex items-center justify-between gap-3 p-3.5 rounded-xl border border-border/60 bg-secondary/40"
            >
              <div className="flex items-center gap-3 min-w-0">
                <Icon className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                <div className="min-w-0">
                  <p className="text-sm font-medium text-foreground truncate">{s.title}</p>
                  <p className="text-[11px] text-muted-foreground truncate">{s.desc}</p>
                </div>
              </div>
              <Switch checked={s.enabled} onCheckedChange={() => flip(s.id)} />
            </div>
          );
        })}
      </div>

      <div className="flex flex-col gap-2">
        <ActionRow icon={Key} label="Changer le mot de passe" onClick={() => toast.info('Changer le mot de passe — mock')} />
        <ActionRow icon={Eye} label="Sessions actives" onClick={() => toast.info('Sessions actives — mock')} />
        <ActionRow icon={Download} label="Télécharger mes données" onClick={() => toast.info('Téléchargement lancé (mock)')} />
      </div>
    </section>
  );
};

const ActionRow = ({ icon: Icon, label, onClick }) => (
  <button
    onClick={onClick}
    className="flex items-center gap-3 h-11 px-4 rounded-xl border border-border bg-secondary/30 hover:bg-secondary text-sm text-foreground transition zy-lift"
  >
    <Icon className="w-4 h-4 text-muted-foreground" />
    <span>{label}</span>
  </button>
);

export default SecurityCard;
