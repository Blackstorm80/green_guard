import React, { createContext, useState, useContext, useEffect } from 'react';
import { api } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem('access_token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUser = async () => {
      // Le state 'token' est notre source de vérité.
      if (token) {
        setLoading(true);
        try {
          // On utilise le token du state pour vérifier la session
          const userData = await api.getCurrentUser(token);
          setUser(userData);
        } catch (error) {
          console.error("Session invalide, déconnexion automatique.", error);
          // Si le token est mauvais, on déclenche la déconnexion
          logout();
        } finally {
          setLoading(false);
        }
      } else {
        // S'il n'y a pas de token, on s'assure que l'état est propre
        setUser(null);
        setLoading(false);
      }
    };

    fetchUser();
  }, [token]);

  const login = async (email, password) => {
    try {
      // api.login gère l'appel et sauvegarde le token dans localStorage
      const data = await api.login(email, password);
      // On met à jour le state 'token', ce qui déclenchera le useEffect pour récupérer l'utilisateur
      setToken(data.access_token);
    } catch (error) {
      console.error("Erreur lors de la tentative de connexion :", error);
      // En cas d'échec, on nettoie tout token potentiellement invalide
      localStorage.removeItem('access_token');
      setToken(null);
      setUser(null);
      throw error;
    }
  };

  const logout = () => {
    api.logout(); // Supprime le token du localStorage
    setUser(null);
    setToken(null);
    // La redirection est maintenant gérée ici, dans la couche UI
    window.location.href = "/login";
  };

  const value = {
    user,
    token,
    login,
    logout,
    isAuthenticated: !!token,
    loading
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};