#cette page transforme le dossier entities en un module  and exposes the main domain entities for easier import.
from .espace_vert import EspaceVertEntity
from .notification import NotificationEntity
from .bilan_hydrique import BilanHydriqueJournalierEntity
from .user import UserEntity
# Ajouter ces lignes
from .zone_intelligente import ZoneIntelligenteEntity
from .clustering_config import ClusteringConfigEntity, Granularite
from .espece_vegetale import EspeceVegetaleEntity
from .capteur import CapteurEntity, TypeCapteur
from .intervention import InterventionEntity, TypeIntervention
