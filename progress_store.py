"""Salvataggio persistente dei percorsi didattici tramite Supabase REST."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


LOGGER = logging.getLogger(__name__)


class ProgressStoreError(RuntimeError):
    """Errore leggibile dall'interfaccia durante il salvataggio o il recupero."""


@dataclass(frozen=True)
class ProgressStore:
    base_url: str
    api_key: str
    timeout: float = 8.0

    @classmethod
    def from_secrets(cls, secrets: Mapping[str, Any]) -> "ProgressStore | None":
        """Crea lo store se i due segreti richiesti sono configurati."""
        try:
            section = secrets.get("supabase", {})
            base_url = str(section.get("url", "")).strip().rstrip("/")
            api_key = str(section.get("anon_key", "")).strip()
        except (AttributeError, TypeError):
            return None
        if not base_url or not api_key:
            return None
        return cls(base_url=base_url, api_key=api_key)

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "apikey": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def load(self, student_code: str) -> dict[str, Any] | None:
        try:
            progress = self._post(
                "get_lesson_progress",
                {"p_student_code": student_code},
            )
        except HTTPError as exc:
            self._log_http_error("recupero", exc)
            raise ProgressStoreError(self._friendly_http_error("recuperare", exc.code)) from exc
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            LOGGER.exception("Errore di rete o risposta non valida durante il recupero Supabase")
            raise ProgressStoreError(
                "Non riesco a collegarmi al database per recuperare il percorso salvato."
            ) from exc
        return progress if isinstance(progress, dict) else None

    def save(self, student_code: str, progress: Mapping[str, Any]) -> None:
        try:
            self._post(
                "save_lesson_progress",
                {"p_student_code": student_code, "p_progress": dict(progress)},
            )
        except HTTPError as exc:
            self._log_http_error("salvataggio", exc)
            raise ProgressStoreError(self._friendly_http_error("salvare", exc.code)) from exc
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            LOGGER.exception("Errore di rete o risposta non valida durante il salvataggio Supabase")
            raise ProgressStoreError(
                "Non riesco a collegarmi al database per salvare il percorso."
            ) from exc

    def _post(self, function_name: str, payload: Mapping[str, Any]) -> Any:
        request = Request(
            f"{self.base_url}/rest/v1/rpc/{function_name}",
            data=json.dumps(dict(payload), ensure_ascii=False).encode("utf-8"),
            headers=self._headers,
            method="POST",
        )
        with urlopen(request, timeout=self.timeout) as response:
            body = response.read()
        return json.loads(body.decode("utf-8")) if body else None

    @staticmethod
    def _friendly_http_error(action: str, status: int) -> str:
        if status in (401, 403):
            detail = "La chiave Supabase non è valida oppure non ha i permessi necessari."
        elif status == 404:
            detail = "La funzione richiesta non esiste nel progetto Supabase indicato."
        else:
            detail = f"Supabase ha restituito l'errore HTTP {status}."
        return f"Non riesco a {action} il percorso. {detail}"

    @staticmethod
    def _log_http_error(operation: str, exc: HTTPError) -> None:
        """Registra il dettaglio Supabase senza esporre URL o chiavi segrete."""
        try:
            response_body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            response_body = "<risposta non leggibile>"
        LOGGER.error(
            "Errore Supabase durante %s: HTTP %s - %s",
            operation,
            exc.code,
            response_body[:2000],
        )
