import SpaceRow from "./SpacesRow";

function SpacesTable({ spaces }) {
  return (
    <div className="flex-1 bg-gray-800 rounded-2xl border border-gray-700 overflow-hidden shadow-xl flex flex-col">

      {/* TABLE */}
      <div className="overflow-auto flex-1">
        <table className="w-full text-sm text-left">
          <thead className="bg-gray-900/80 text-slate-400 uppercase text-xs font-semibold sticky top-0">
            <tr>
              <th className="px-6 py-4">ID</th>
              <th className="px-6 py-4">Nom de l'espace</th>
              <th className="px-6 py-4">Ville / Zone</th>
              <th className="px-6 py-4">Surface</th>
              <th className="px-6 py-4">État de santé</th>
              <th className="px-6 py-4 text-right">Actions</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-gray-700 text-slate-300">
            {spaces.map((space) => (
              <SpaceRow key={space.id} space={space} />
            ))}
          </tbody>
        </table>
      </div>

      <div className="h-14 border-t border-gray-700 flex items-center justify-between px-6">
        <span className="text-xs text-slate-400">
          Affichage 1-{spaces.length}
        </span>

        <div className="flex gap-1">
          <button className="w-8 h-8 border border-gray-600 text-slate-400 rounded-lg">
            «
          </button>
          <button className="w-8 h-8 bg-green-600 text-white rounded-lg font-bold">
            1
          </button>
          <button className="w-8 h-8 border border-gray-600 text-slate-400 rounded-lg">
            »
          </button>
        </div>
      </div>
    </div>
  );
}

export default SpacesTable;
