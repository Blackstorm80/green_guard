function SpaceRow({ space }) {
  return (
    <tr className="hover:bg-gray-700/50 transition group">
      <td className="px-6 py-4 font-mono text-xs text-slate-500">
        #{space.id}
      </td>

      <td className="px-6 py-4 font-bold text-white group-hover:text-green-400">
        {space.name}
      </td>

      <td className="px-6 py-4 text-slate-400">
        {space.city}
      </td>

      <td className="px-6 py-4 font-mono text-slate-400">
        {space.surface} m²
      </td>

      <td className="px-6 py-4">
        <span
          className={`
            inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
            ${space.health === "excellent"
              ? "bg-green-500/10 text-green-400 border border-green-500/20"
              : "bg-red-500/10 text-red-400 border border-red-500/20"}
          `}
        >
          <span
            className={`
              w-1.5 h-1.5 rounded-full mr-1.5
              ${space.health === "excellent"
                ? "bg-green-400"
                : "bg-red-500 animate-pulse"}
            `}
          />
          {space.healthLabel}
        </span>
      </td>

      <td className="px-6 py-4 text-right">
        <button className="text-slate-400 hover:text-white px-3 py-1 border border-gray-600 rounded-lg hover:bg-gray-600 text-xs">
          Détails
        </button>
      </td>
    </tr>
  );
}

export default SpaceRow;