// components/navbar/Navbar.jsx
import { NavLink, useLocation } from "react-router-dom";
import { Bell, MapPin, Sun, ChevronRight, Search } from "lucide-react";
import MeteoWidget from "./MeteoWidget"; // Import du nouveau widget
import Notifications from "./Notifications"; // Import du composant de notifications

function Navbar({ children }) {
  const location = useLocation();

  // 2. Logique : Mapping du fil d'Ariane dynamique
  const getBreadcrumbs = () => {
    const pathnames = location.pathname.split("/").filter((x) => x);
    if (pathnames.length === 0) return [{ label: "Tableau de bord", to: "/" }];
    
    return pathnames.map((name, index) => {
      const routeTo = `/${pathnames.slice(0, index + 1).join("/")}`;
      const labels = {
        "espaces": "Espaces & Sites",
        "catalogues": "Catalogue",
        "rapports": "Rapports",
        "parametres": "Paramètres"
      };
      return { label: labels[name] || name, to: routeTo };
    });
  };

  const breadcrumbs = getBreadcrumbs();

  return (
    <div className="flex min-h-screen w-full bg-gray-900">
      {/* Sidebar (Code inchangé) */}
      <aside className="bg-gray-800 border-r border-gray-700 flex flex-col shrink-0 shadow-xl z-20 w-20 md:w-38 lg:w-64 transition-all duration-700">
        <div className="h-16 flex items-center px-6 border-b border-gray-700">
          <div className="w-8 h-8 bg-gradient-to-br from-green-500 to-green-800 rounded-lg flex items-center justify-center shadow-lg">
            <span className="text-white font-bold text-lg">G</span>
          </div>
          <h1 className="hidden md:block ml-3 text-lg font-bold text-white tracking-wide">GREEN GUARD</h1>
        </div>

        <nav className="flex-1 px-2 py-6 space-y-1">
          {[
            { to: "/", icon: "📊", label: "Tableau de bord" },
            { to: "/espaces", icon: "🌿", label: "Espaces & Sites" },
            { to: "/catalogues", icon: "🌻", label: "Catalogue" },
            { to: "/rapports", icon: "🛡️", label: "Rapports" },
            { to: "/parametres", icon: "⚙️", label: "Paramètres" },
          ].map((item) => (
            <NavLink key={item.to} to={item.to} end>
              {({ isActive }) => (
                <button className={`group w-full flex items-center px-3 py-3 text-sm font-medium rounded-lg transition-all ${isActive ? "bg-gray-700 text-white" : "text-slate-400 hover:bg-gray-700 hover:text-white"}`}>
                  <span className={`text-xl`}>{item.icon}</span>
                  <span className="ml-3 hidden md:block">{item.label}</span>
                </button>
              )}
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden bg-gray-900">
        
        <header className="h-16 bg-gray-800/90 backdrop-blur-md border-b border-gray-700 flex items-center justify-between px-6 sticky top-0 z-10">
          
          <div className="flex items-center gap-2">
            <div className="p-2 bg-gray-700/50 rounded-lg md:hidden">
               <span className="text-lg">🌿</span>
            </div>
            <nav className="flex items-center gap-2 text-sm">
              <span className="text-gray-500">GreenGuard</span>
              {breadcrumbs.map((crumb, index) => (
                <div key={index} className="flex items-center gap-2">
                  <ChevronRight size={14} className="text-gray-600" />
                  <span className={index === breadcrumbs.length - 1 ? "text-white font-medium" : "text-gray-400"}>
                    {crumb.label}
                  </span>
                </div>
              ))}
            </nav>
          </div>

          <div className="flex items-center gap-4">
            
            <MeteoWidget />

            <div className="h-8 w-px bg-gray-700 mx-1 hidden sm:block" />

            <Notifications />

            <button className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-full sm:hidden">
              <Search size={20} />
            </button>
          </div>
        </header>

        {/* Page Content */}
        <div className="flex-1 overflow-y-auto">
          <div className="p-6">{children}</div>
        </div>
      </div>
    </div>
  );
}

export default Navbar;