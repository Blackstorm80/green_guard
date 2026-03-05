# Étape 1: Builder (compilation des dépendances)
FROM python:3.13-slim AS builder

# Définir le répertoire de travail dans le conteneur
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Étape 2: Image finale (production)
FROM python:3.13-slim

WORKDIR /app

# Installe curl, qui est nécessaire pour le HEALTHCHECK
RUN apt-get update && apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

# Ajoute le répertoire bin de l'utilisateur au PATH pour que `uvicorn` soit trouvable
ENV PATH="/root/.local/bin:${PATH}"

# Copie les dépendances compilées
COPY --from=builder /root/.local /root/.local

# Copie ton code
COPY . .

# Expose le port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/ping || exit 1

# Lance l'API
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port 8000 --reload"]