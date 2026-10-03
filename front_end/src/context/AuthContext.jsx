import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, SESSION_EXPIREE, tokenStorage } from "../services/api";

const AuthContext = createContext(null);

/** Lit l'expiration (exp, en secondes) d'un JWT sans le valider : la validation reste côté serveur. */
function jetonExpire(token) {
  try {
    const payload = JSON.parse(atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")));
    return typeof payload.exp === "number" && payload.exp * 1000 <= Date.now();
  } catch {
    return true;
  }
}

function jetonInitial() {
  const token = tokenStorage.get();
  if (token && jetonExpire(token)) {
    tokenStorage.clear();
    return null;
  }
  return token;
}

export const AuthProvider = ({ children }) => {
  const navigate = useNavigate();
  const [token, setToken] = useState(jetonInitial);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(() => Boolean(jetonInitial()));

  const logout = useCallback(() => {
    api.logout();
    setUser(null);
    setToken(null);
    navigate("/login", { replace: true });
  }, [navigate]);

  // Toute réponse 401 de l'API (jeton expiré, compte désactivé…) ferme la session
  useEffect(() => {
    window.addEventListener(SESSION_EXPIREE, logout);
    return () => window.removeEventListener(SESSION_EXPIREE, logout);
  }, [logout]);

  useEffect(() => {
    if (!token) return;
    const controller = new AbortController();
    api
      .getCurrentUser(controller.signal)
      .then(setUser)
      .catch((err) => {
        if (err.name !== "AbortError") logout();
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [token, logout]);

  const login = useCallback(async (email, password) => {
    const data = await api.login(email, password);
    setLoading(true);
    setToken(data.access_token);
  }, []);

  const value = useMemo(
    () => ({ user, token, login, logout, loading, isAuthenticated: Boolean(token && user) }),
    [user, token, login, logout, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth doit être utilisé dans un AuthProvider");
  return context;
};
