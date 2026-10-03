import { useCallback, useEffect, useState } from "react";

/** Titre de l'onglet du navigateur (WCAG 2.4.2 : chaque page a un titre qui la décrit). */
export function useTitrePage(titre) {
  useEffect(() => {
    document.title = titre ? `${titre} · GreenGuard` : "GreenGuard";
  }, [titre]);
}

/**
 * Charge une ressource de l'API : état de chargement, erreur lisible, rechargement,
 * annulation automatique si le composant est démonté (AbortController).
 * `charger` reçoit le signal d'annulation et doit être stable (fonction de module ou useCallback).
 */
export function useRequete(charger, valeurInitiale = null) {
  const [donnees, setDonnees] = useState(valeurInitiale);
  const [chargement, setChargement] = useState(true);
  const [erreur, setErreur] = useState(null);
  const [version, setVersion] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    charger(controller.signal)
      .then((resultat) => {
        setDonnees(resultat);
        setErreur(null);
      })
      .catch((err) => {
        if (err.name !== "AbortError") setErreur(err.message || "Erreur de chargement.");
      })
      .finally(() => {
        if (!controller.signal.aborted) setChargement(false);
      });
    return () => controller.abort();
  }, [charger, version]);

  const recharger = useCallback(() => setVersion((v) => v + 1), []);
  return { donnees, setDonnees, chargement, erreur, recharger };
}
