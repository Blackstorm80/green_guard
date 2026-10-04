# Étape 1 : installation des dépendances dans un environnement virtuel isolé
FROM python:3.13-slim AS builder
WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Étape 2 : image d'exécution minimale, sans compilateur ni curl, utilisateur non root
FROM python:3.13-slim
ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
RUN useradd --create-home --uid 1000 greenguard
COPY --from=builder /opt/venv /opt/venv
COPY --chown=greenguard:greenguard . .
USER greenguard

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health/live', timeout=4).status == 200 else 1)"

# Migrations puis API (pas de --reload en production).
# WEB_CONCURRENCY : nombre de processus API, à ajuster aux cœurs de l hébergement (test de charge à rejouer)
# TRUSTED_PROXIES : adresses (ou réseaux CIDR) des proxys dont X-Forwarded-For est cru ; sans cela,
# toutes les requêtes semblent venir du proxy et la limitation de débit devient collective
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips \"${TRUSTED_PROXIES:-127.0.0.1}\" --workers ${WEB_CONCURRENCY:-1}"]
