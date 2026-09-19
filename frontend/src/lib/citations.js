// Citations Sens & Clarté (univers par défaut, universel) et Foi (chrétien,
// activé volontairement uniquement si l'utilisateur choisit "foi" à
// l'onboarding — jamais imposé, jamais activé par défaut).
//
// Garde-fous : chaque verset biblique cite une vraie référence vérifiable
// (livre + chapitre + verset), jamais une citation inventée ou attribuée
// sans source — cf. INSPIRATION-PROPOSAL.md.

export const CITATIONS_SENS_CLARTE = [
  { text: "La clarté ne supprime pas les choix ; elle aide à choisir le prochain pas.", source: "Zayado" },
  { text: "Avancer avec sens, c'est mesurer son succès à ce que l'on construit et à ce que l'on rend possible.", source: "Zayado" },
  { text: "La sagesse ne cherche pas à tout accélérer ; elle reconnaît ce qui mérite d'être approfondi.", source: "Zayado" },
  { text: "Une décision juste protège à la fois la promesse faite au client et la capacité de la tenir.", source: "Zayado" },
  { text: "Ce qui est fait avec soin dure plus longtemps que ce qui est fait vite.", source: "Zayado" },
  { text: "Diriger, c'est choisir ce qu'on ne fera pas autant que ce qu'on fera.", source: "Zayado" },
];

export const CITATIONS_FOI = [
  { text: "Recommande à l'Éternel tes œuvres, et tes projets réussiront.", source: "Proverbes 16:3" },
  { text: "Je puis tout par celui qui me fortifie.", source: "Philippiens 4:13" },
  { text: "Ne crains rien, car je suis avec toi ; ne t'inquiète pas, car je suis ton Dieu.", source: "Ésaïe 41:10" },
  { text: "Confie-toi en l'Éternel de tout ton cœur, et ne t'appuie pas sur ta sagesse.", source: "Proverbes 3:5" },
  { text: "Tout ce que vous faites, faites-le de bon cœur, comme pour le Seigneur.", source: "Colossiens 3:23" },
  { text: "Que tout ce que vous faites se fasse avec amour.", source: "1 Corinthiens 16:14" },
  { text: "L'Éternel est mon berger : je ne manquerai de rien.", source: "Psaume 23:1" },
];

export function pickCitation(ambiance) {
  const pool = ambiance === "foi" ? CITATIONS_FOI : CITATIONS_SENS_CLARTE;
  return pool[Math.floor(Math.random() * pool.length)];
}
