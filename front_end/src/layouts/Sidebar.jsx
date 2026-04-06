//sidebar.jsx
import { useState } from "react";
import { NavLink } from "react-router-dom";
import { 
  LayoutDashboard, 
  Trees, 
  FileText, 
  Settings, 
  Sprout, 
  Menu,
  LogOut // AJOUT DE L'ICÔNE LOGOUT
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { cn } from "../lib/utils";

export function Sidebar() {
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const { user, logout } = useAuth(); // RÉCUPÉRATION DU LOGOUT

  const navigation = [
    { name: "Tableau de bord", href: "/", icon: LayoutDashboard },
    { name: "Espaces & Sites", href: "/espaces", icon: Trees },
    { name: "Catalogue", href: "/catalogues", icon: Sprout },
    { name: "Rapports", href: "/rapports", icon: FileText },
    { name: "Paramètres", href: "/parametres", icon: Settings },
  ];

  // Initiales dynamiques pour l'avatar (optimisé pour ton AuthContext)
  const getInitials = (nameOrEmail = "Admin") => {
    if (!nameOrEmail) return "AD";
    
    // Si c'est un nom complet (ex: "John Doe")
    const names = nameOrEmail.split(' ');
    if (names.length > 1) {
      return `${names[0][0]}${names[1][0]}`.toUpperCase();
    }
    
    // Si c'est un email (ex: "john@exemple.com") → prend les 2 premières lettres
    return nameOrEmail.slice(0, 2).toUpperCase();
  };

  return (
    <>
      {/* Bouton Burger Mobile */}
      <button 
        onClick={() => setIsMobileOpen(!isMobileOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-gray-800 rounded-md text-white shadow-lg"
      >
        <Menu size={24} />
      </button>

      {/* Sidebar Container */}
      <aside className={cn(
        "fixed inset-y-0 left-0 z-40 w-64 bg-slate-900 border-r border-slate-800 transition-transform duration-300 ease-in-out lg:translate-x-0",
        isMobileOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        
        {/* Logo */}
        <div className="h-16 flex items-center px-6 border-b border-slate-800">
          <div className="w-8 h-8 bg-green-600 rounded-lg flex items-center justify-center mr-3 shadow-lg shadow-green-900/50">
            <span className="text-white font-bold">G</span>
          </div>
          <h1 className="text-xl font-bold text-white tracking-tight">
            Green<span className="text-green-500">Tech</span>
          </h1>
        </div>

        {/* Navigation - 100% INCHANGÉE */}
        <nav className="p-4 space-y-2">
          {navigation.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              onClick={() => setIsMobileOpen(false)}
              className={({ isActive }) => cn(
                "flex items-center px-4 py-3 text-sm font-medium rounded-xl transition-all duration-200 group",
                isActive 
                  ? "bg-green-600/10 text-green-400 border border-green-600/20 shadow-sm" 
                  : "text-slate-400 hover:bg-slate-800 hover:text-white"
              )}
            >
              <item.icon className="mr-3 h-5 w-5" />
              {item.name}
            </NavLink>
          ))}
        </nav>

        {/* PROFIL UTILISATEUR AVEC LOGOUT */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-slate-800 bg-slate-900/80 backdrop-blur-sm">
          <div className="flex items-center gap-3 px-2 p-2 rounded-xl transition-all">
            {/* Avatar avec Initiales */}
            <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-green-500 to-emerald-700 border border-slate-600 flex items-center justify-center text-xs font-bold text-white shadow-md shrink-0">
              {getInitials(user?.name || user?.email)}
            </div>
            
            {/* Infos Textuelles */}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">
                {user?.name || user?.email?.split('@')[0] || "Admin Principal"}
              </p>
              <p className="text-[10px] uppercase tracking-wider font-bold text-slate-500 truncate">
                {user?.role || "Responsable SE"}
              </p>
            </div>

            {/* BOUTON DECONNEXION */}
            <button 
              onClick={logout}
              className="p-2 text-slate-500 hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-all"
              title="Déconnexion"
            >
              <LogOut size={18} />
            </button>
          </div>
        </div>
      </aside>

      {/* Overlay Mobile */}
      {isMobileOpen && (
        <div 
          className="fixed inset-0 z-30 bg-black/60 lg:hidden backdrop-blur-sm transition-opacity"
          onClick={() => setIsMobileOpen(false)}
        />
      )}
    </>
  );
}