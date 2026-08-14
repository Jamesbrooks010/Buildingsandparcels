"""JSON loading helpers used until full Adelaide GIS datasets are added."""

from __future__ import annotations

import json
from pathlib import Path

from .models import BuildingEnvelope, Parcel


def load_envelope(path: str | Path) -> BuildingEnvelope:
    """Load a building envelope JSON file."""

    return BuildingEnvelope.model_validate(_load_json(path))


def load_parcels(path: str | Path) -> list[Parcel]:
    """Load a JSON array of parcel records."""

    payload = _load_json(path)
    if not isinstance(payload, list):
        raise ValueError("Parcel data must be a JSON array.")
    return [Parcel.model_validate(parcel) for parcel in payload]


def _load_json(path: str | Path) -> object:
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)
