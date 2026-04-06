import React, { useState, useEffect } from 'react';
import { useLocation, Link } from 'react-router-dom';
import {api} from '../../services/api'; // Assurez-vous que ce client API est configuré

// Hook pour obtenir le nom d'une ressource dynamique (ex: espace vert)
const useDynamicName = (pathSegment, id) => {
    const [name, setName] = useState(`Chargement...`);

    useEffect(() => {
        if (!id || !pathSegment) return;

        const fetchName = async () => {
            try {
                if (pathSegment === 'espaces') {
                    const response = await api.getEspaceVertById(id);
                    setName(response?.nom || `Site #${id}`);
                }
                // Ajoutez d'autres cas pour d'autres ressources dynamiques
            } catch (error) {
                console.error(`Failed to fetch name for ${pathSegment}/${id}`, error);
                setName(`Site #${id}`); // Fallback en cas d'erreur
            }
        };

        fetchName();
    }, [pathSegment, id]);

    return name;
};

// Composant interne pour gérer le nom dynamique
const DynamicBreadcrumbName = ({ pathSegment, id }) => {
    const name = useDynamicName(pathSegment, id);
    return <>{name}</>;
};

const Breadcrumbs = () => {
    const location = useLocation();
    const pathnames = location.pathname.split('/').filter(x => x);

    // Mappage des noms statiques
    const breadcrumbNameMap = {
        'dashboard': 'Tableau de bord',
        'espaces': 'Mes Sites',
        'profil': 'Mon Profil',
        'settings': 'Réglages',
        'catalogues': 'Catalogue',
        'rapports': 'Rapports'
    };

    const renderItems = (isMobile) => {
        let items = [
            <li key="home">
                <Link to="/" className="text-gray-400 hover:text-white">Accueil</Link>
            </li>
        ];

        let processedPathnames = pathnames.map((value, index) => {
            const to = `/${pathnames.slice(0, index + 1).join('/')}`;
            const isLast = index === pathnames.length - 1;
            const isDynamicId = !isNaN(Number(value));
            
            let name;
            if (isDynamicId) {
                const parentSegment = pathnames[index - 1];
                name = <DynamicBreadcrumbName pathSegment={parentSegment} id={value} />;
            } else {
                name = breadcrumbNameMap[value] || value.charAt(0).toUpperCase() + value.slice(1);
            }

            return { to, name, isLast };
        });

        if (isMobile && processedPathnames.length > 1) {
            // Sur mobile, n'afficher que le parent direct
            processedPathnames = [processedPathnames[processedPathnames.length - 2]];
        }

        processedPathnames.forEach((item, index) => {
            items.push(
                <li key={item.to}>
                    <div className="flex items-center">
                        <span className="mx-2 text-gray-600">/</span>
                        {item.isLast ? (
                            <span className="font-medium text-white">{item.name}</span>
                        ) : (
                            <Link to={item.to} className="text-gray-400 hover:text-white">{item.name}</Link>
                        )}
                    </div>
                </li>
            );
        });
        return items;
    };

    return (
        <nav aria-label="Breadcrumb" className="text-sm">
            <ol className="hidden sm:flex items-center space-x-1">{renderItems(false)}</ol>
            <ol className="flex sm:hidden items-center space-x-1">{renderItems(true)}</ol>
        </nav>
    );
};

export default Breadcrumbs;