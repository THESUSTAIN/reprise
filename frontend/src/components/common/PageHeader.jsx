import React from "react";
import { motion } from "framer-motion";

// Reusable page header with serif title + subtitle.
export function PageHeader({ title, subtitle, icon: Icon, action }) {
  return (
    <div className="flex items-start justify-between gap-4 mb-6">
      <div className="flex items-start gap-3">
        {Icon && (
          <div className="mt-1 h-11 w-11 shrink-0 rounded-xl grid place-items-center bg-gold/10 border border-gold/25 text-gold">
            <Icon className="h-5 w-5" />
          </div>
        )}
        <div>
          <motion.h1
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="text-2xl sm:text-3xl font-semibold tracking-tight"
          >
            {title}
          </motion.h1>
          {subtitle && <p className="text-sm text-muted-foreground mt-1 max-w-2xl">{subtitle}</p>}
        </div>
      </div>
      {action}
    </div>
  );
}

export default PageHeader;
