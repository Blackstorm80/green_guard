import React, { useState } from 'react';

const EspaceVertForm = ({ initialData = {}, onSubmit, errors = {} }) => {
  const [formData, setFormData] = useState({
    type_sol: initialData.type_sol || '',
    ph_actuel: initialData.ph_actuel || '',
    exposition: initialData.exposition || '',
    drainage: initialData.drainage || '',
    humidite_cible: initialData.humidite_cible || '',
    frequence_arrosage_auto: initialData.frequence_arrosage_auto || '',
    profondeur_racinaire: initialData.profondeur_racinaire || '',
    type_irrigation: initialData.type_irrigation || '',
    date_derniere_fertilisation: initialData.date_derniere_fertilisation || '',
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  const renderInput = (name, label, type = 'text', placeholder = '') => (
    <div className="mb-4">
      <label htmlFor={name} className="block text-sm font-medium text-gray-700">{label}</label>
      <input
        type={type}
        id={name}
        name={name}
        value={formData[name]}
        onChange={handleChange}
        placeholder={placeholder}
        className="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
      />
      {errors[name] && <p className="mt-1 text-xs text-red-600">{errors[name]}</p>}
    </div>
  );

  const renderSelect = (name, label, options) => (
    <div className="mb-4">
      <label htmlFor={name} className="block text-sm font-medium text-gray-700">{label}</label>
      <select
        id={name}
        name={name}
        value={formData[name]}
        onChange={handleChange}
        className="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
      >
        <option value="">Sélectionnez...</option>
        {options.map(option => (
          <option key={option.value} value={option.value}>{option.label}</option>
        ))}
      </select>
      {errors[name] && <p className="mt-1 text-xs text-red-600">{errors[name]}</p>}
    </div>
  );

  const solOptions = [
    { value: 'argileux', label: 'Argileux' },
    { value: 'limoneux', label: 'Limoneux' },
    { value: 'sableux', label: 'Sableux' },
    { value: 'humifere', label: 'Humifère' },
    { value: 'calcaire', label: 'Calcaire' },
  ];

  const expositionOptions = [
    { value: 'plein_soleil', label: 'Plein soleil' },
    { value: 'mi_ombre', label: 'Mi-ombre' },
    { value: 'ombre', label: 'Ombre' },
  ];

  return (
    <form onSubmit={handleSubmit} className="p-6 bg-white rounded-lg shadow">
      <h2 className="text-lg font-semibold text-gray-900 mb-6">Données Agronomiques du Site</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6">
        {/* Colonne 1 */}
        <div>
          {renderSelect('type_sol', 'Type de sol', solOptions)}
          {renderInput('ph_actuel', 'pH actuel', 'number', 'Ex: 6.8')}
          {renderSelect('exposition', 'Exposition', expositionOptions)}
          {renderInput('drainage', 'Drainage', 'text', 'Ex: Bon, Moyen, Mauvais')}
          {renderInput('humidite_cible', 'Humidité cible (%)', 'number', 'Ex: 60')}
        </div>
        {/* Colonne 2 */}
        <div>
          {renderInput('frequence_arrosage_auto', 'Fréquence arrosage (heures)', 'number', 'Ex: 48')}
          {renderInput('profondeur_racinaire', 'Profondeur racinaire (cm)', 'number', 'Ex: 30')}
          {renderInput('type_irrigation', 'Type d\'irrigation', 'text', 'Ex: Goutte-à-goutte')}
          {renderInput('date_derniere_fertilisation', 'Dernière fertilisation', 'date')}
        </div>
      </div>
      <div className="mt-6 flex justify-end">
        <button
          type="submit"
          className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          Enregistrer les données
        </button>
      </div>
    </form>
  );
};

export default EspaceVertForm;
