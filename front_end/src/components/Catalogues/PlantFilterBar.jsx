function PlantFilterBar({
  search,
  setSearch,
  water,
  setWater,
  exposure,
  setExposure,
  onFilter,
}) {
  return (
    <div className="bg-gray-800 rounded-2xl border border-gray-700 p-4 flex flex-wrap gap-4 items-end shadow-md">
      {/* SEARCH */}
      <div className="flex-1 min-w-[200px]">
        <label className="block text-xs font-bold text-slate-400 uppercase mb-1">
          Recherche
        </label>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Nom de plante, type..."
          className="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:border-green-500 outline-none"
        />
      </div>

      {/* WATER */}
      <div className="w-40">
        <label className="block text-xs font-bold text-slate-400 uppercase mb-1">
          Besoin en eau
        </label>
        <select
          value={water}
          onChange={(e) => setWater(e.target.value)}
          className="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white outline-none"
        >
          <option value="">Tous</option>
          <option value="Faible">Faible</option>
          <option value="Moyen">Moyen</option>
          <option value="Élevé">Élevé</option>
        </select>
      </div>

      {/* EXPOSURE */}
      <div className="w-40">
        <label className="block text-xs font-bold text-slate-400 uppercase mb-1">
          Exposition
        </label>
        <select
          value={exposure}
          onChange={(e) => setExposure(e.target.value)}
          className="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white outline-none"
        >
          <option value="">Toutes</option>
          <option value="Soleil">Plein soleil</option>
          <option value="Mi-ombre">Mi-ombre</option>
          <option value="Ombre">Ombre</option>
        </select>
      </div>

      <button
        onClick={onFilter}
        className="bg-green-600 hover:bg-green-500 text-white px-5 py-2 rounded-lg text-sm font-bold shadow-lg shadow-green-900/50 transition h-[38px]"
      >
        Filtrer
      </button>
    </div>
  );
}

export default PlantFilterBar;
