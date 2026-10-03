"""Journalisation : format texte en développement, JSON (une ligne par événement) en production."""
import json
import logging
from datetime import UTC, datetime

CHAMPS_EXTRA = ("request_id", "method", "path", "status", "duration_ms")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        evenement = {
            "ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for champ in CHAMPS_EXTRA:
            if hasattr(record, champ):
                evenement[champ] = getattr(record, champ)
        if record.exc_info:
            evenement["exception"] = self.formatException(record.exc_info)
        return json.dumps(evenement, ensure_ascii=False)


def configurer_logs(niveau: str = "INFO", format_: str = "text") -> None:
    handler = logging.StreamHandler()
    if format_ == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"))
    racine = logging.getLogger()
    racine.handlers[:] = [handler]
    racine.setLevel(niveau)
