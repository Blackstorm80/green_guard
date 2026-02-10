# Utiliser une image Python officielle et légère
FROM python:3.11-slim

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier le fichier des dépendances
COPY requirements.txt .

# Installer les dépendances
# --no-cache-dir pour garder l'image légère
# --upgrade pip pour s'assurer d'avoir la dernière version
RUN pip install --no-cache-dir --upgrade pip -r requirements.txt

# Copier tout le code du backend dans un sous-dossier 'back_end'
# Cela permet aux imports 'from back_end...' de fonctionner correctement
COPY . back_end/

# Ajouter /app au PYTHONPATH pour que python trouve le package 'back_end'
ENV PYTHONPATH=/app

# Exposer le port sur lequel Uvicorn va écouter
EXPOSE 8000

# Commande pour lancer l'application
CMD ["uvicorn", "back_end.main:app", "--host", "0.0.0.0", "--port", "8000"]