import React, { useState, useEffect } from 'react';
import api from '../../services/api'; // Client API configuré
import { BellIcon, CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

const NotificationCenter = () => {
  const [notifications, setNotifications] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchNotifications = async () => {
      try {
        const response = await api.get('/notifications/me');
        setNotifications(response.data);
      } catch (error) {
        console.error("Erreur lors de la récupération des notifications:", error);
        //  afficher une notification d'erreur cas ou 
      } finally {
        setIsLoading(false);
      }
    };

    fetchNotifications();
  }, []);

  const getIcon = (type) => {
    switch (type) {
      case 'alerte':
        return <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />;
      case 'succes':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      default:
        return <BellIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  return (
    <div className="p-4">
      <h3 className="font-semibold text-gray-800 mb-4">Centre de notifications</h3>
      {isLoading ? (
        <p>Chargement...</p>
      ) : notifications.length === 0 ? (
        <p className="text-sm text-gray-500">Aucune nouvelle notification.</p>
      ) : (
        <ul className="space-y-3">
          {notifications.map(notif => (
            <li key={notif.id} className="flex items-start p-2 rounded-md bg-gray-50">
              <div className="flex-shrink-0 mr-3 mt-1">{getIcon(notif.type)}</div>
              <p className="text-sm text-gray-700">{notif.message}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default NotificationCenter;
