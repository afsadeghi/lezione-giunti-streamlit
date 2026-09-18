"""Salvataggio persistente dei percorsi didattici tramite Supabase REST."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


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
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise ProgressStoreError("Non riesco a recuperare il percorso salvato.") from exc
        return progress if isinstance(progress, dict) else None

    def save(self, student_code: str, progress: Mapping[str, Any]) -> None:
        try:
            self._post(
                "save_lesson_progress",
                {"p_student_code": student_code, "p_progress": dict(progress)},
            )
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise ProgressStoreError("Non riesco a salvare il percorso in questo momento.") from exc

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
