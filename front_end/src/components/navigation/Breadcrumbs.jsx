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
        'espaces': 'Espaces et zones',
        'catalogues': 'Catalogue',
        'rapports': 'Rapports',
        'parametres': 'Paramètres'
    };

    const renderItems = (isMobile) => {
        let items = [
            <li key="home">
                <Link to="/" className="text-fg-muted hover:text-fg">Accueil</Link>
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
                name = breadcrumbNameMap[value] || 'Page introuvable';
            }

            return { to, name, isLast };
        });

        if (isMobile && processedPathnames.length > 1) {
            // Sur mobile, n'afficher que le parent direct
            processedPathnames = [processedPathnames[processedPathnames.length - 2]];
        }

        processedPathnames.forEach((item) => {
            items.push(
                <li key={item.to}>
                    <div className="flex items-center">
                        <span className="mx-2 text-fg-subtle" aria-hidden>/</span>
                        {item.isLast ? (
                            <span className="font-medium text-fg" aria-current="page">{item.name}</span>
                        ) : (
                            <Link to={item.to} className="text-fg-muted hover:text-fg">{item.name}</Link>
                        )}
                    </div>
                </li>
            );
        });
        return items;
    };

    return (
        <nav aria-label="Fil d'Ariane" className="text-sm">
            <ol className="hidden sm:flex items-center space-x-1">{renderItems(false)}</ol>
            <ol className="flex sm:hidden items-center space-x-1">{renderItems(true)}</ol>
        </nav>
    );
};

export default Breadcrumbs;