// front_end/src/components/auth/ProtectedRoute.jsx
import { Navigate, Outlet } from "react-router-dom";

export default function ProtectedRoute() {
  const token = localStorage.getItem("access_token");
  
  // Si pas de token, redirection immediate vers /login
  if (!token) {
    return <Navigate to="/login" replace />;
  }

  // Si authentifie, affiche le contenu des routes enfants
  return <Outlet />;
}
