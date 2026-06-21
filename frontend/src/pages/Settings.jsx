import React, { useState } from 'react';
import { Save } from 'lucide-react';
import { toast } from 'sonner';
import ProfileSection from '../components/settings/ProfileSection';
import LanguageSection from '../components/settings/LanguageSection';
import NotificationSection from '../components/settings/NotificationSection';
import AccountStatusCard from '../components/settings/AccountStatusCard';
import BillingCard from '../components/settings/BillingCard';
import SecurityCard from '../components/settings/SecurityCard';
import DangerZone from '../components/settings/DangerZone';

const Settings = () => {
  const [, setSaveTick] = useState(0);

  const handleSaveAll = () => {
    setSaveTick((t) => t + 1);
    toast.success('Tous les paramètres ont été sauvegardés', {
      description: 'Vos préférences sont à jour.',
    });
  };

  return (
    <div className="pb-12">
      {/* Page header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-8">
        <div>
          <h1 className="zy-heading text-3xl md:text-4xl font-bold text-foreground">Settings</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Gérez les paramètres et préférences de votre compte
          </p>
        </div>
        <button
          onClick={handleSaveAll}
          className="zy-btn-primary inline-flex items-center gap-2 px-5 h-11 rounded-xl text-sm font-medium transition"
        >
          <Save className="w-4 h-4" />
          Sauvegarder tout
        </button>
      </div>

      {/* Two column grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 flex flex-col gap-6">
          <ProfileSection />
          <LanguageSection />
          <NotificationSection />
        </div>
        <div className="flex flex-col gap-6">
          <AccountStatusCard />
          <BillingCard />
          <SecurityCard />
          <DangerZone />
        </div>
      </div>
    </div>
  );
};

export default Settings;
