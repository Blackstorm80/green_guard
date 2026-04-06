// front_end/src/components/auth/ProtectedRoute.jsx
import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

export default function ProtectedRoute() {
  const { isAuthenticated } = useAuth();
  
  // Si pas de token, redirection immediate vers /login
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Si authentifie, affiche le contenu des routes enfants
  return <Outlet />;
}
