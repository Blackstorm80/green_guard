import { useState } from "react";
import { NavLink } from "react-router-dom";
import { 
  LayoutDashboard, 
  Trees, 
  FileText, 
  Settings, 
  Sprout, 
  Menu
} from "lucide-react";
import { cn } from "../lib/utils"; // <--- C'EST ICI QUE ÇA A CHANGÉ (../ au lieu de ../../)

export function Sidebar() {
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  const navigation = [
    { name: "Tableau de bord", href: "/", icon: LayoutDashboard },
    { name: "Espaces & Sites", href: "/espaces", icon: Trees },
    { name: "Catalogue", href: "/catalogues", icon: Sprout },
    { name: "Rapports", href: "/rapports", icon: FileText },
    { name: "Paramètres", href: "/parametres", icon: Settings },
  ];

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

        {/* Navigation */}
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

        {/* Profil Utilisateur (Bas) */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-slate-800">
          <div className="flex items-center gap-3 px-2">
            <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-green-500 to-emerald-700 border border-slate-600 flex items-center justify-center text-xs font-bold text-white shadow-md">
              AD
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">Admin Principal</p>
              <p className="text-xs text-slate-500 truncate">Responsable RSE</p>
            </div>
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