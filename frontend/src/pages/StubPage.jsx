import React from 'react';
import { Construction, Sparkles } from 'lucide-react';

/**
 * StubPage — placeholder displayed before final-main content port.
 * Used for: Pilotage, Bien-être, Espace, Croissance, Onboarding, Login,
 *           Admin, Integrations, WordPress, Parametres.
 */
const StubPage = ({ title, description, testId, sourceFile, status = 'porting' }) => {
  const statusBadge = {
    porting:   { label: 'À porter depuis final-main', color: '#d4b78c' },
    backend:   { label: 'Backend en cours',           color: '#2952a3' },
    soon:      { label: 'Prochaine version',          color: '#10b981' },
  }[status];

  return (
    <div className="space-y-6" data-testid={testId}>
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl zy-tile-gold flex items-center justify-center">
          <Sparkles className="w-5 h-5 text-[#0a1f4e]" strokeWidth={2.1} />
        </div>
        <div>
          <h1 className="zy-heading text-2xl md:text-3xl font-semibold">{title}</h1>
          <p className="text-sm text-muted-foreground">{description}</p>
        </div>
      </div>

      <div className="zy-card rounded-2xl p-8 flex flex-col items-center justify-center text-center gap-4 min-h-[300px]">
        <div className="w-14 h-14 rounded-full bg-gradient-to-br from-[#1e3a8a] to-[#2952a3] flex items-center justify-center shadow-lg">
          <Construction className="w-7 h-7 text-white" />
        </div>
        <div>
          <h2 className="zy-serif text-2xl mb-2">Page en construction</h2>
          <p className="text-sm text-muted-foreground max-w-md">
            Le contenu de cette page sera importé depuis le projet final-main
            dans la prochaine itération.
          </p>
        </div>
        <div
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs font-medium"
          style={{
            backgroundColor: `${statusBadge.color}22`,
            border: `1px solid ${statusBadge.color}55`,
            color: statusBadge.color,
          }}
        >
          <span className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: statusBadge.color }} />
          {statusBadge.label}
        </div>
        {sourceFile && (
          <code className="text-[11px] text-muted-foreground bg-muted/30 px-3 py-1 rounded">
            source: {sourceFile}
          </code>
        )}
      </div>
    </div>
  );
};

export default StubPage;
