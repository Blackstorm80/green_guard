import React, { useState, useEffect, Fragment } from 'react';
import { useAuth } from '../../context/AuthContext'; 
import api from '../../services/api'; 
import { BellIcon } from '@heroicons/react/24/outline';
import { Menu, Transition } from '@headlessui/react';


const Header = () => {
  const { user, setUser, token } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);


  const fetchNotifications = async () => {
    if (!token) return;
    try {
      // Je présume que l'endpoint est `/api/v1/users/me/notifications`
      const response = await api.get('/users/me/notifications');
      setNotifications(response.data || []);
    } catch (error) {
      console.error("Erreur lors de la récupération des notifications:", error);
      setNotifications([]); // reset en cas d'erreur
    }
  };

  useEffect(() => {
    // Si on a un token mais pas les détails de l'utilisateur (nom, etc.),
    // on va les chercher.
    if (token && user && !user.name) {
      const fetchUser = async () => {
        try {
          const response = await api.get('/users/me');
          setUser(prevUser => ({ ...prevUser, ...response.data }));
        } catch (error) {
          console.error("Erreur lors de la récupération du profil utilisateur:", error);
        }
      };
      fetchUser();
    }
    
    // Fetch notifications on component mount and when token is available
    fetchNotifications();

    // Optionnel: fetch périodiquement
    const interval = setInterval(fetchNotifications, 60000); // toutes les minutes
    return () => clearInterval(interval);

  }, [token, user, setUser]);

  const markAllAsRead = async () => {
    try {
        // Endpoint pour marquer tout comme lu
        await api.post('/notifications/mark-all-read');
        // on rafraichit la liste
        fetchNotifications();
    } catch (error) {
        console.error("Erreur lors de la mise à jour des notifications:", error);
    }
  };


  const unreadCount = notifications.filter(n => !n.is_read).length;

  return (
    <header className="flex items-center justify-end p-4 bg-white border-b print:hidden">
      <div className="flex items-center space-x-4">
        
        <div className="relative">
          <button onClick={() => setIsNotificationsOpen(!isNotificationsOpen)} className="relative">
            <BellIcon className="h-6 w-6 text-gray-600" />
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-xs text-white">
                {unreadCount}
              </span>
            )}
          </button>

          {isNotificationsOpen && (
            <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-xl border z-10">
              <div className="p-4 border-b">
                <h4 className="text-lg font-semibold">Notifications</h4>
              </div>
              <div className="max-h-96 overflow-y-auto">
                {notifications.length > 0 ? (
                  notifications.map(notif => (
                    <div key={notif.id} className={`p-4 border-b ${!notif.is_read ? 'bg-blue-50' : ''}`}>
                      <p className="text-sm text-gray-700">{notif.message}</p>
                      <p className="text-xs text-gray-500 mt-1">{new Date(notif.created_at).toLocaleString()}</p>
                    </div>
                  ))
                ) : (
                  <p className="p-4 text-sm text-gray-500">Aucune notification.</p>
                )}
              </div>
               {unreadCount > 0 && (
                    <div className="p-2 border-t">
                        <button 
                            onClick={markAllAsRead}
                            className="w-full text-center text-sm font-medium text-blue-600 hover:text-blue-800"
                        >
                            Marquer comme lus
                        </button>
                    </div>
                )}
            </div>
          )}
        </div>
        
        {/* LE PROFIL A ÉTÉ DÉPLACÉ VERS LA SIDEBAR */}
      </div>
    </header>
  );
};

export default Header;