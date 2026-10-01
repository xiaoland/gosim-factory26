"""Interface-neutral strict value models shared by SVC services."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ValueModel(BaseModel):
    """Immutable validated facts without presentation or serialization policy."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
