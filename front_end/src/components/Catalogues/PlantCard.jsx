function PlantCard({ plant }) {
  return (
    <div className="bg-gray-800 rounded-2xl border border-gray-700 p-4 text-left hover:border-green-500 transition cursor-pointer group">
      <div className="w-full h-32 bg-gray-700 rounded-xl mb-3 flex items-center justify-center text-4xl">
        {plant.icon}
      </div>

      <h3 className="text-sm font-bold text-white group-hover:text-green-400 transition">
        {plant.name}
      </h3>

      <p className="text-xs text-slate-400 mt-1">
        {plant.type}
      </p>

      <div className="mt-3 flex flex-wrap gap-2">
        <span className="text-[10px] bg-blue-900/40 text-blue-300 px-2 py-1 rounded">
          Eau: {plant.water}
        </span>

        <span className="text-[10px] bg-yellow-900/40 text-yellow-300 px-2 py-1 rounded">
          {plant.exposure}
        </span>
      </div>
    </div>
  );
}

export default PlantCard;
