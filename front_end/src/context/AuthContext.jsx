import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, SESSION_EXPIREE } from "../services/api";

const AuthContext = createContext(null);

/**
 * La session vit dans un cookie httpOnly que JavaScript ne peut pas lire :
 * l'état « connecté » est donc déduit de /users/me, jamais d'un jeton stocké côté navigateur.
 */
export const AuthProvider = ({ children }) => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const chargerUtilisateur = useCallback(async (signal) => {
    try {
      setUser(await api.getCurrentUser(signal));
    } catch (err) {
      if (err.name === "AbortError") return;
      setUser(null);
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    chargerUtilisateur(controller.signal);
    return () => controller.abort();
  }, [chargerUtilisateur]);

  const logout = useCallback(async () => {
    try {
      await api.logout();
    } catch {
      /* cookie déjà invalide : rien à faire de plus côté serveur */
    }
    setUser(null);
    navigate("/login", { replace: true });
  }, [navigate]);

  // Une réponse 401 en cours de navigation (session expirée, compte désactivé…) ferme la session
  useEffect(() => {
    const surExpiration = () => {
      setUser(null);
      navigate("/login", { replace: true });
    };
    window.addEventListener(SESSION_EXPIREE, surExpiration);
    return () => window.removeEventListener(SESSION_EXPIREE, surExpiration);
  }, [navigate]);

  const login = useCallback(async (email, password) => {
    await api.login(email, password);
    setLoading(true);
    await chargerUtilisateur();
  }, [chargerUtilisateur]);

  // Après un changement de rôle ou de nom d'organisation : relit le profil sans écran de chargement
  const rafraichirUtilisateur = useCallback(() => chargerUtilisateur(), [chargerUtilisateur]);

  const value = useMemo(
    () => ({ user, login, logout, loading, rafraichirUtilisateur, isAuthenticated: Boolean(user) }),
    [user, login, logout, loading, rafraichirUtilisateur]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth doit être utilisé dans un AuthProvider");
  return context;
};
