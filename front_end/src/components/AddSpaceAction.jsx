// front_end/src/components/AddSpaceAction.jsx
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, X, MapPin } from 'lucide-react';
import { api } from '../services/api';

import AddSpaceModal from './AddSpaceModal';

const AddSpaceAction = ({ espaces, onSpaceCreated, currentUser }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [shouldPulse, setShouldPulse] = useState(false);

  useEffect(() => {
    if (espaces && espaces.length > 0) {
      const lastCreationDate = espaces.reduce((latest, space) => {
        const spaceDate = new Date(space.cree_le);
        return spaceDate > latest ? spaceDate : latest;
      }, new Date(0));

      const hoursSinceLastCreation = (new Date() - lastCreationDate) / (1000 * 60 * 60);
      setShouldPulse(hoursSinceLastCreation > 24);
    } else {
      setShouldPulse(true); // Pulse if there are no spaces
    }
  }, [espaces]);
  
  const handleSuccess = () => {
    onSpaceCreated();
    setIsModalOpen(false);
  };

  const pulseAnimation = {
    scale: [1, 1.05, 1],
    boxShadow: [
      "0 0 0 0 rgba(34, 197, 94, 0.4)",
      "0 0 0 10px rgba(34, 197, 94, 0)",
      "0 0 0 0 rgba(34, 197, 94, 0)",
    ],
  };

  return (
    <>
      {/* Button */}
      <div className="md:relative fixed bottom-6 right-6 z-10">
        <motion.button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center justify-center bg-green-500 text-white rounded-full md:rounded-md shadow-lg hover:bg-green-600 transition-colors"
          // Responsive size and shape
          style={{ 
            width: 'var(--button-width, 56px)', 
            height: 'var(--button-height, 56px)',
            padding: 'var(--button-padding, 0)'
          }}
          // Animate properties for responsiveness
          initial={false}
          animate={{ 
            '--button-width': window.innerWidth < 768 ? '56px' : '180px',
            '--button-height': window.innerWidth < 768 ? '56px' : '40px',
            '--button-padding': window.innerWidth < 768 ? '0' : '0 16px',
            borderRadius: window.innerWidth < 768 ? '9999px' : '8px',
           }}
          // Pulse animation
          variants={{ pulse: pulseAnimation }}
          animate={shouldPulse ? 'pulse' : ''}
          transition={shouldPulse ? { duration: 2, repeat: Infinity, ease: 'easeInOut' } : {}}
        >
          <span className="md:hidden"><Plus size={24} /></span>
          <span className="hidden md:flex items-center">
            <Plus size={20} className="mr-2" /> Ajouter un espace
          </span>
        </motion.button>
      </div>

      {/* Modal */}
      <AnimatePresence>
        {isModalOpen && (
          <AddSpaceModal 
            onClose={() => setIsModalOpen(false)}
            onSuccess={handleSuccess}
          />
        )}
      </AnimatePresence>
    </>
  );
};

export default AddSpaceAction;
