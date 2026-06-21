import React, { useState } from 'react';
import { Bell, Mail, Smartphone, Zap, ShieldAlert } from 'lucide-react';
import { Switch } from '../ui/switch';
import { notificationPrefs } from '../../mock/mockData';

const iconMap = { Mail, Smartphone, Zap, ShieldAlert };

const NotificationSection = () => {
  const [prefs, setPrefs] = useState(notificationPrefs);

  const toggle = (id) =>
    setPrefs((p) => p.map((n) => (n.id === id ? { ...n, enabled: !n.enabled } : n)));

  return (
    <section className="zy-card rounded-2xl p-6 lg:p-8">
      <div className="flex items-start gap-4 mb-6">
        <div className="w-12 h-12 rounded-xl zy-tile flex items-center justify-center flex-shrink-0">
          <Bell className="w-5 h-5 text-[#2952a3] dark:text-[#d4b78c]" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-foreground">Notification Preferences</h2>
          <p className="text-sm text-muted-foreground">Choisissez les notifications à recevoir</p>
        </div>
      </div>

      <div className="flex flex-col gap-3">
        {prefs.map((n) => {
          const Icon = iconMap[n.icon] || Bell;
          return (
            <div
              key={n.id}
              className="flex items-center justify-between gap-4 p-4 rounded-xl border border-border/60 bg-secondary/40 hover:bg-secondary/70 transition"
            >
              <div className="flex items-center gap-3 min-w-0">
                <Icon className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                <div className="min-w-0">
                  <p className="text-sm font-medium text-foreground truncate">{n.title}</p>
                  <p className="text-xs text-muted-foreground truncate">{n.desc}</p>
                </div>
              </div>
              <Switch checked={n.enabled} onCheckedChange={() => toggle(n.id)} />
            </div>
          );
        })}
      </div>
    </section>
  );
};

export default NotificationSection;
