// Pages/parametres/parametres.jsx
function Parametres() {
  return (
    <div className="max-w-7xl mx-auto">
      <div className="bg-gray-800 rounded-2xl border border-gray-700 p-8 shadow-2xl">
        <h1 className="text-2xl font-bold text-white mb-2">
          Paramètres
        </h1>
        <p className="text-slate-400 mb-8">
          Configurez les paramètres de l'application.
        </p>

        <div className="space-y-6">
          <div className="border border-gray-700 rounded-xl p-6">
            <h2 className="text-lg font-semibold text-white mb-4">
              Compte utilisateur
            </h2>
            <p className="text-slate-300">
              Gérez vos informations personnelles et préférences.
            </p>
          </div>

          <div className="border border-gray-700 rounded-xl p-6">
            <h2 className="text-lg font-semibold text-white mb-4">
              Notifications
            </h2>
            <p className="text-slate-300">
              Configurez les alertes et notifications.
            </p>
          </div>

          <div className="border border-gray-700 rounded-xl p-6">
            <h2 className="text-lg font-semibold text-white mb-4">
              Sécurité
            </h2>
            <p className="text-slate-300">
              Paramètres de sécurité et accès.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Parametres;
