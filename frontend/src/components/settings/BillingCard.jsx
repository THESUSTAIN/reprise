import React from 'react';
import { CreditCard } from 'lucide-react';
import { toast } from 'sonner';

const BillingCard = () => {
  return (
    <section className="zy-card rounded-2xl p-6">
      <div className="flex items-start gap-3 mb-5">
        <div className="w-11 h-11 rounded-xl zy-tile flex items-center justify-center flex-shrink-0">
          <CreditCard className="w-5 h-5 text-[#2952a3] dark:text-[#d4b78c]" />
        </div>
        <div>
          <h3 className="text-base font-semibold text-foreground">Billing</h3>
          <p className="text-xs text-muted-foreground">Gérer les moyens de paiement</p>
        </div>
      </div>

      <div className="rounded-xl border border-border bg-secondary/40 p-4 mb-4 zy-lift">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-[#1e3a8a] to-[#2952a3] flex items-center justify-center">
              <CreditCard className="w-4 h-4 text-white" />
            </div>
            <div>
              <p className="text-sm font-semibold text-foreground">•••• 4242</p>
              <p className="text-[11px] text-muted-foreground">Moyen de paiement principal</p>
            </div>
          </div>
          <span className="text-xs text-muted-foreground">Exp. 12/25</span>
        </div>
      </div>

      <button
        onClick={() => toast.info('Gérer la facturation — mock')}
        className="w-full h-11 rounded-xl border border-border bg-secondary/40 hover:bg-secondary text-sm font-medium transition"
      >
        Gérer la facturation
      </button>
    </section>
  );
};

export default BillingCard;
