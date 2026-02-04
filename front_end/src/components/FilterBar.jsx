function FilterBar({
  search,
  setSearch,
  city,
  setCity,
  health,
  setHealth,
  cities,
  onFilter,
}) {
  return (
    <div className="bg-gray-800 rounded-2xl border border-gray-700 p-4 flex flex-wrap gap-4 items-end shadow-md">

      {/* Search */}
      <div className="flex-1 min-w-[200px]">
        <label className="block text-xs font-bold text-slate-400 uppercase mb-1">
          Recherche
        </label>
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white"
        />
      </div>

      {/* City */}
      <div className="w-40">
        <label className="block text-xs font-bold text-slate-400 uppercase mb-1">
          Ville
        </label>
        <select
          value={city}
          onChange={(e) => setCity(e.target.value)}
          className="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white"
        >
          <option value="">Toutes</option>

          {cities.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </div>

      {/* Health */}
      <div className="w-40">
        <label className="block text-xs font-bold text-slate-400 uppercase mb-1">
          Santé
        </label>
        <select
          value={health}
          onChange={(e) => setHealth(e.target.value)}
          className="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white"
        >
          <option value="">Tous</option>
          <option value="critique">Critique</option>
          <option value="eleve">Èlevé</option>
          <option value="moyen">Moyen</option>
          <option value="ok">Bon</option>
        </select>
      </div>

      <button
        onClick={onFilter}
        className="bg-green-600 text-white px-5 py-2 rounded-lg text-sm font-bold"
      >
        Filtrer
      </button>
    </div>
  );
}

export default FilterBar;
