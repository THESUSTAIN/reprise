import { useEffect } from "react";

const SUFFIX = " — MyExtension AI";

/**
 * Met à jour document.title pour chaque page.
 * Usage : usePageTitle("Tableau de bord")
 */
export default function usePageTitle(title) {
  useEffect(() => {
    document.title = title ? `${title}${SUFFIX}` : `MyExtension AI — by Zayado`;
  }, [title]);
}
