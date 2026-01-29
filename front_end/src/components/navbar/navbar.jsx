// components/navbar/Navbar.jsx
import { NavLink } from "react-router-dom";

function Navbar({ children }) {
  return (
    <div className="flex min-h-screen w-full bg-gray-900">
      {/* Sidebar */}
      <aside className="bg-gray-800 border-r border-gray-700 flex flex-col shrink-0 shadow-xl z-20 w-20 md:w-38 lg:w-64 transition-all duration-700">
        {/* Logo */}
        <div className="h-16 flex items-center px-6 border-b border-gray-700">
          <div className="w-8 h-8 bg-gradient-to-br from-green-500 to-green-800 rounded-lg flex items-center justify-center shadow-lg shadow-green-900/50">
            <span className="text-white font-bold text-lg">G</span>
          </div>
          <h1 className="hidden md:block ml-3 text-lg font-bold text-white tracking-wide">
            CELU
          </h1>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-2 py-6 space-y-1">
          {[
            { to: "/", icon: "📊", label: "Tableau de bord" },
            { to: "/espacesEtSites", icon: "🌿", label: "Espaces & Sites" },
            { to: "/catalogues", icon: "🌻", label: "Catalogue" },
            { to: "/alertes", icon: "🛡️", label: "Alertes" },
            { to: "/parametres", icon: "⚙️", label: "Paramètres" },
          ].map((item) => (
            <NavLink key={item.to} to={item.to} end>
              {({ isActive }) => (
                <button
                  className={`group w-full flex items-center px-3 py-3 text-sm font-medium rounded-lg transition-all ${
                    isActive
                      ? "bg-gray-700 text-white"
                      : "text-slate-400 hover:bg-gray-700 hover:text-white"
                  }`}
                >
                  <span
                    className={`text-xl rounded-full p-1 ${
                      isActive ? "ring-2 ring-white" : ""
                    }`}
                  >
                    {item.icon}
                  </span>
                  <span className="ml-3 opacity-0 w-0 overflow-hidden transition-all duration-300 md:opacity-100 md:w-auto">
                    {item.label}
                  </span>
                </button>
              )}
            </NavLink>
          ))}
        </nav>

        {/* User */}
        <div className="p-4 border-t border-gray-700">
          <div className="flex items-center justify-center md:justify-start">
            <img
              src="https://ui-avatars.com/api/?name=Admin+Vert&background=10b981&color=fff"
              className="w-9 h-9 rounded-full border-2 border-gray-600"
              alt="avatar"
            />
            <div className="hidden md:block ml-3">
              <p className="text-sm font-medium text-white">
                Gérant Principal
              </p>
              <p className="text-xs text-slate-400">Responsable RSE</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden bg-gray-900">
        {/* Header */}
        <header className="h-16 bg-gray-800/90 backdrop-blur-md border-b border-gray-700 flex items-center justify-between px-6 sticky top-0 z-10">
          <div className="flex items-center text-slate-300">
            <span className="text-lg font-semibold text-white">
              Vue d'ensemble
            </span>
            <span className="ml-4 text-xs bg-gray-900 px-2 py-0.5 rounded border border-gray-700 text-slate-500">
              24 Espaces Connectés
            </span>
          </div>

          <div className="flex-1 max-w-md mx-6">
            <div className="relative">
              <span className="absolute left-3 top-2 text-gray-500">🔍</span>
              <input
                type="text"
                placeholder="Recherche globale..."
                className="w-full bg-gray-900 border border-gray-600 rounded-full pl-9 pr-4 py-1.5 text-sm text-white placeholder-gray-400 focus:border-green-500 focus:ring-1 focus:ring-green-500 outline-none"
              />
            </div>
          </div>

          <select className="bg-gray-900 border border-gray-600 text-sm rounded-lg px-3 py-1.5 text-slate-300 focus:ring-2 focus:ring-green-500">
            <option>Cette Année</option>
            <option>Ce mois</option>
          </select>
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
