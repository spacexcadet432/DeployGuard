from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from deployguard.models.schemas import IncidentMatchResult
from deployguard.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class Incident:
    file_path: str
    incident_date: str
    severity: str
    description: str

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "Incident":
        return Incident(
            file_path=str(d.get("file_path") or ""),
            incident_date=str(d.get("incident_date") or ""),
            severity=str(d.get("severity") or "").lower(),
            description=str(d.get("description") or ""),
        )


class IncidentStore:
    def __init__(self, incidents_path: str | None = None) -> None:
        if incidents_path is None:
            incidents_path = str(Path(__file__).resolve().parent / "incidents.json")
        self._incidents_path = incidents_path
        self._incidents: list[Incident] = []
        self._loaded = False

    def _load_if_needed(self) -> None:
        if self._loaded:
            return
        if not os.path.exists(self._incidents_path):
            raise FileNotFoundError(f"Incident dataset not found: {self._incidents_path}")

        with open(self._incidents_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if not isinstance(raw, list):
            raise ValueError("incidents.json must contain a JSON array")

        incidents: list[Incident] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            inc = Incident.from_dict(item)
            if inc.file_path:
                incidents.append(inc)
        self._incidents = incidents
        self._loaded = True

        logger.info("Loaded %d incidents from dataset.", len(self._incidents))

    def search_incidents(self, files_changed: list[str]) -> IncidentMatchResult:
        """
        Return:
          - number of past incidents per file
          - severity distribution
        Also includes `incident_matches` entries for richer prompt context.
        """
        self._load_if_needed()

        changed_set = {f.strip() for f in files_changed if isinstance(f, str) and f.strip()}
        incidents_by_file: dict[str, int] = {}
        severity_distribution: dict[str, int] = {"low": 0, "medium": 0, "high": 0}
        matches: list[dict[str, Any]] = []

        for inc in self._incidents:
            # Simple match strategy: exact path match. If you want broader matching,
            # you can add suffix matching here.
            if inc.file_path in changed_set:
                incidents_by_file[inc.file_path] = incidents_by_file.get(inc.file_path, 0) + 1
                sev = (inc.severity or "").lower()
                if sev in severity_distribution:
                    severity_distribution[sev] += 1
                else:
                    severity_distribution[sev] = severity_distribution.get(sev, 0) + 1

                matches.append(
                    {
                        "file_path": inc.file_path,
                        "incident_date": inc.incident_date,
                        "severity": inc.severity,
                        "description": inc.description,
                    }
                )

        return IncidentMatchResult(
            incidents_by_file=incidents_by_file,
            severity_distribution=severity_distribution,
            incident_matches=matches,
        )


def get_incident_store() -> IncidentStore:
    return IncidentStore()

