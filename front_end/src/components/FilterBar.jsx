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
          placeholder="Nom ou ID..."
          className="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:border-green-500 outline-none transition-colors"
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
          className="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:border-green-500 outline-none"
        >
          <option value="">Toutes</option>
          {cities.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </div>

      {/* Health - مقادیر اینجا با داده‌های اصلی شما هماهنگ شد */}
      <div className="w-40">
        <label className="block text-xs font-bold text-slate-400 uppercase mb-1">
          Santé
        </label>
        <select
          value={health}
          onChange={(e) => setHealth(e.target.value)}
          className="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:border-green-500 outline-none"
        >
          <option value="">Tous</option>
          <option value="excellent">Excellent</option>
          <option value="stress">Stress Hydrique</option>
        </select>
      </div>

      <button
        onClick={onFilter}
        className="bg-green-600 hover:bg-green-700 text-white px-5 py-2 rounded-lg text-sm font-bold transition-colors"
      >
        Filtrer
      </button>
    </div>
  );
}

export default FilterBar;