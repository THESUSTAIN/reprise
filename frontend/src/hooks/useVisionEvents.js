import { useEffect } from "react";

// Point de compatibilité pour les composants Final-main.
// Cours-main ne publie pas encore de flux serveur Vision ; aucun événement
// n’est simulé et les composants continuent à fonctionner avec leurs requêtes réelles.
export default function useVisionEvents() {
  useEffect(() => undefined, []);
}
