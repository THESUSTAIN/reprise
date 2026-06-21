import React from 'react';
import { ShieldCheck } from 'lucide-react';
import { userProfile } from '../../mock/mockData';

const AccountStatusCard = () => {
  return (
    <section className="zy-card rounded-2xl p-6">
      <div className="flex items-start gap-3 mb-5">
        <div className="w-11 h-11 rounded-xl zy-tile-green flex items-center justify-center flex-shrink-0">
          <ShieldCheck className="w-5 h-5 text-emerald-500" />
        </div>
        <div>
          <h3 className="text-base font-semibold text-foreground">Account Status</h3>
          <p className="text-xs text-emerald-500 font-medium">Actif &amp; vérifié</p>
        </div>
      </div>

      <div className="space-y-3 text-sm">
        <Row label="Membre depuis" value={userProfile.memberSince} />
        <Row label="Forfait" value={<span className="text-emerald-500 font-medium">{userProfile.plan}</span>} />
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-muted-foreground">Stockage utilisé</span>
            <span className="text-foreground font-medium">{userProfile.storageUsed}</span>
          </div>
          <div className="h-1.5 w-full rounded-full bg-secondary overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-[#1e3a8a] to-[#d4b78c]"
              style={{ width: `${userProfile.storagePercent}%` }}
            />
          </div>
        </div>
      </div>
    </section>
  );
};

const Row = ({ label, value }) => (
  <div className="flex items-center justify-between">
    <span className="text-muted-foreground">{label}</span>
    <span className="text-foreground font-medium">{value}</span>
  </div>
);

export default AccountStatusCard;
