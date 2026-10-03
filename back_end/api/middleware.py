"""Middlewares transverses : identifiant de requête, journal d'accès, en-têtes de sécurité, erreurs génériques."""
import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from config import settings

logger = logging.getLogger("greenguard.http")

# Swagger/ReDoc chargent leurs scripts depuis un CDN : CSP assouplie uniquement sur ces pages
CHEMINS_DOCUMENTATION = ("/docs", "/redoc", "/openapi.json")
CSP_API = "default-src 'none'; frame-ancestors 'none'"


def installer_middlewares(app: FastAPI) -> None:
    @app.middleware("http")
    async def securite_et_journal(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        debut = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            # Jamais de trace technique côté client : détail dans les logs, référence dans la réponse
            logger.exception("Erreur non gérée", extra={"request_id": request_id, "path": request.url.path})
            response = JSONResponse(status_code=500,
                                    content={"detail": "Erreur interne du serveur.", "request_id": request_id})

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        if not request.url.path.startswith(CHEMINS_DOCUMENTATION):
            response.headers["Content-Security-Policy"] = CSP_API
        if settings.hsts:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        logger.info(
            "%s %s %s", request.method, request.url.path, response.status_code,
            extra={
                "request_id": request_id, "method": request.method, "path": request.url.path,
                "status": response.status_code, "duration_ms": round((time.perf_counter() - debut) * 1000, 1),
            },
        )
        return response
