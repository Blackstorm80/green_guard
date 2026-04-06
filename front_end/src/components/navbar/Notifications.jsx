// front_end/src/components/navbar/Notifications.jsx
import { useState, useEffect, useRef } from "react";
import { Bell, AlertTriangle, CheckCircle, Clock } from "lucide-react";
import { api } from "../../services/api";

const PrioriteIcon = ({ type }) => {
    switch (type) {
        case 'alerte':
            return <AlertTriangle className="text-red-500" size={20} />;
        case 'info':
            return <CheckCircle className="text-green-500" size={20} />;
        default:
            return <Bell className="text-gray-400" size={20} />;
    }
};

const TimeAgo = ({ date }) => {
    const [time, setTime] = useState(() => {
        const seconds = Math.floor((new Date() - new Date(date)) / 1000);
        if (seconds < 60) return "à l'instant";
        const minutes = Math.floor(seconds / 60);
        if (minutes < 60) return `il y a ${minutes} min`;
        const hours = Math.floor(minutes / 60);
        return `il y a ${hours} h`;
    });
    return <span className="text-xs text-gray-500">{time}</span>;
}


const Notifications = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [notifications, setNotifications] = useState([]);
    const [loading, setLoading] = useState(true);
    const dropdownRef = useRef(null);

    useEffect(() => {
        const fetchNotifications = async () => {
            try {
                setLoading(true);
                const response = await api.getNotifications();
                setNotifications(response);
            } catch (error) {
                console.error("Impossible de charger les notifications:", error);
            } finally {
                setLoading(false);
            }
        };
        fetchNotifications();
    }, []);

    const handleMarkAsRead = async (id) => {
        try {
            await api.markNotificationAsRead(id);
            setNotifications(prev => prev.map(n => n.id === id ? { ...n, est_lue: true } : n));
        } catch (error) {
            console.error("Impossible de marquer la notification comme lue:", error);
        }
    };

    // Fermer le dropdown si on clique en dehors
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, []);

    const nonLuesCount = notifications.filter(n => !n.est_lue).length;


    return (
        <div className="relative" ref={dropdownRef}>
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="relative p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-full transition-colors"
            >
                <Bell size={20} />
                {nonLuesCount > 0 && (
                    <span className="absolute top-1.5 right-1.5 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-gray-800 flex items-center justify-center text-xs font-bold">
                    </span>
                )}
            </button>

            {isOpen && (
                <div className="absolute top-full right-0 mt-2 w-80 bg-gray-800 border border-gray-700 rounded-lg shadow-2xl z-50">
                    <div className="p-3 border-b border-gray-700">
                        <h3 className="font-bold text-white">Notifications ({notifications.length})</h3>
                    </div>
                    <div className="max-h-96 overflow-y-auto">
                        {loading ? (
                            <div className="p-4 text-center text-gray-400">Chargement...</div>
                        ) : notifications.length === 0 ? (
                            <div className="p-4 text-center text-gray-400">Aucune notification.</div>
                        ) : (
                            <div>
                                {notifications.map(notif => (
                                    <div key={notif.id} onClick={() => !notif.est_lue && handleMarkAsRead(notif.id)} className={`p-3 flex items-start gap-3 border-b border-gray-700/50 hover:bg-gray-700/50 ${!notif.est_lue ? 'bg-sky-900/20' : ''}`}>
                                        <PrioriteIcon type={notif.type} />
                                        <div className="flex-1">
                                            <p className="text-sm font-semibold text-white">{notif.message}</p>
                                            <div className="flex items-center gap-2 mt-1">
                                                <Clock size={12} className="text-gray-500"/>
                                                <TimeAgo date={notif.cree_le} />
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                     <div className="p-2 bg-gray-900/50 text-center">
                        <button className="text-xs text-cyan-400 hover:underline">
                            Voir toutes les notifications
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Notifications;
