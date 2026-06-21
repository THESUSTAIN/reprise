import { useAuth } from "@fm/context/AuthContext";

/**
 * Tiers de plans (du plus bas au plus haut).
 * Ordre canonique utilisé par `hasPlan()` pour les comparaisons.
 */
export const PLAN_TIER = {
  free: 0,
  start: 1,
  grow: 2,
  serenity: 3,
  // Legacy / admin
  trajectoire: 1,
  serenite: 3,
  business: 99,
  admin: 99,
};

/**
 * Liste de features par plan. Source de vérité côté UI.
 * Le backend reste la vraie barrière (cf. `utils.py:SUBSCRIPTION_PLANS`),
 * mais on cache visuellement les CTAs non éligibles.
 */
export const PLAN_FEATURES = {
  // Modules SaaS
  ai_chat: { min: "free", limit_free: 10 },          // 10 msgs/mois en free
  vision_board: { min: "free" },
  pilotage: { min: "start" },
  croissance_hub: { min: "start" },
  croissance_agent: { min: "grow" },
  expansion_leads: { min: "grow" },
  bien_etre: { min: "start" },
  studio_serenite_humain: { min: "serenity" },
  hot_opportunities: { min: "grow" },
  adresse_paris: { min: "serenity" },
  daf_supervision: { min: "serenity" },
  mutualisation_premium: { min: "serenity" },
  multi_projets: { min: "grow" },
};

export function planTier(plan) {
  if (!plan) return PLAN_TIER.free;
  const k = String(plan).toLowerCase();
  return PLAN_TIER[k] ?? PLAN_TIER.free;
}

/**
 * Hook principal — expose le plan actif et un helper `has(feature)` simple.
 */
export default function usePlan() {
  const { user } = useAuth();
  const plan = String(user?.plan || "free").toLowerCase();
  const isAdmin = Boolean(user?.is_admin || user?.role === "admin" || user?.role === "super_admin");
  const tier = planTier(plan);

  const has = (featureKey) => {
    if (isAdmin) return true;
    const feat = PLAN_FEATURES[featureKey];
    if (!feat) return true; // unknown → unrestricted
    return tier >= planTier(feat.min);
  };

  const minRequired = (featureKey) => PLAN_FEATURES[featureKey]?.min || "free";

  return { plan, tier, isAdmin, has, minRequired };
}
