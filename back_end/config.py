"""Configuration centralisée (ADR-8) : seul module qui lit les variables d'environnement."""
import os
from dataclasses import dataclass, field
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dotenv import load_dotenv

load_dotenv()

LONGUEUR_MIN_SECRET = 32


def _bool(nom: str, defaut: bool) -> bool:
    return os.getenv(nom, str(defaut)).strip().lower() in ("1", "true", "yes", "oui")


def _obligatoire(nom: str, exemple: str) -> str:
    valeur = os.getenv(nom)
    if not valeur:
        raise RuntimeError(f"Variable d'environnement {nom} manquante. Exemple : {exemple}")
    return valeur


@dataclass(frozen=True)
class Settings:
    database_url: str = field(default_factory=lambda: _obligatoire(
        "DATABASE_URL", "postgresql://greenguard:secret@localhost:5432/greenguard"))
    secret_key: str = field(default_factory=lambda: _obligatoire(
        "SECRET_KEY", 'python -c "import secrets; print(secrets.token_hex(32))"'))
    frontend_url: str | None = field(default_factory=lambda: os.getenv("FRONTEND_URL"))

    # Session : jeton JWT transporté dans un cookie httpOnly (ADR-6)
    access_token_minutes: int = field(default_factory=lambda: int(os.getenv("ACCESS_TOKEN_MINUTES", "60")))
    cookie_name: str = "gg_session"
    # Secure par défaut ; ne le désactiver que pour une pile locale servie en HTTP hors localhost
    cookie_secure: bool = field(default_factory=lambda: _bool("COOKIE_SECURE", True))

    # Limitation de débit de l'authentification. Connexion : quota strict par identifiant (bourrage
    # d'identifiants) et quota large par IP (une collectivité entière peut partager une IP de sortie).
    # Inscription : quota strict par IP.
    auth_rate_limit: int = field(default_factory=lambda: int(os.getenv("AUTH_RATE_LIMIT", "10")))
    auth_rate_limit_ip: int = field(default_factory=lambda: int(os.getenv("AUTH_RATE_LIMIT_IP", "100")))
    auth_rate_window_s: int = field(default_factory=lambda: int(os.getenv("AUTH_RATE_WINDOW_S", "60")))
    # Proxys dont les en-têtes X-Forwarded-* sont crus : transmis à uvicorn (--forwarded-allow-ips,
    # CMD du Dockerfile) ; sans cela, toutes les requêtes semblent venir de l'adresse du proxy.
    trusted_proxies: str = field(default_factory=lambda: os.getenv("TRUSTED_PROXIES", "127.0.0.1"))

    # Documentation interactive (/docs, /redoc, /openapi.json) : fermée par défaut (production)
    enable_docs: bool = field(default_factory=lambda: _bool("ENABLE_DOCS", False))

    # Fuseau du « jour » métier : celui de la météo journalière et du bilan hydrique
    fuseau_horaire: str = field(default_factory=lambda: os.getenv("FUSEAU_HORAIRE", "Europe/Paris"))

    # Mode sécheresse : API publique VigiEau (sans clé). URL fixée par l'exploitant, jamais par un utilisateur.
    vigieau_url: str = field(default_factory=lambda: os.getenv("VIGIEAU_URL", "https://api.vigieau.gouv.fr/api/zones"))
    vigieau_timeout_s: float = field(default_factory=lambda: float(os.getenv("VIGIEAU_TIMEOUT_S", "10")))

    # Job planifié : à n'activer que dans UN processus (service worker en production)
    enable_scheduler: bool = field(default_factory=lambda: _bool("ENABLE_SCHEDULER", False))

    # Pool de connexions : à dimensionner avec le nombre de threads du serveur (40 par défaut)
    db_pool_size: int = field(default_factory=lambda: int(os.getenv("DB_POOL_SIZE", "10")))
    db_max_overflow: int = field(default_factory=lambda: int(os.getenv("DB_MAX_OVERFLOW", "20")))
    db_pool_timeout_s: int = field(default_factory=lambda: int(os.getenv("DB_POOL_TIMEOUT_S", "10")))

    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    log_format: str = field(default_factory=lambda: os.getenv("LOG_FORMAT", "text"))  # "text" | "json"
    hsts: bool = field(default_factory=lambda: _bool("HSTS", False))  # à activer derrière HTTPS

    def __post_init__(self):
        # RFC 7518 §3.2 : une clé HS256 doit faire au moins 256 bits
        if len(self.secret_key) < LONGUEUR_MIN_SECRET:
            raise RuntimeError(
                f"SECRET_KEY trop courte ({len(self.secret_key)} caractères, minimum {LONGUEUR_MIN_SECRET}). "
                'Générer : python -c "import secrets; print(secrets.token_hex(32))"'
            )
        if not self.vigieau_url.startswith("https://"):
            raise RuntimeError(f"VIGIEAU_URL doit être une URL https ({self.vigieau_url!r}).")
        if not 0 < self.vigieau_timeout_s <= 60:
            raise RuntimeError(f"VIGIEAU_TIMEOUT_S hors bornes ({self.vigieau_timeout_s}, attendu entre 0 et 60 s).")
        try:
            ZoneInfo(self.fuseau_horaire)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise RuntimeError(
                f"FUSEAU_HORAIRE invalide ({self.fuseau_horaire!r}). Exemple : Europe/Paris"
            ) from exc

    @property
    def fuseau(self) -> ZoneInfo:
        return ZoneInfo(self.fuseau_horaire)

    @property
    def allowed_origins(self) -> list[str]:
        origines = ["http://localhost:3000", "http://localhost:5173"]
        if self.frontend_url and self.frontend_url not in origines:
            origines.append(self.frontend_url)
        return origines


settings = Settings()
