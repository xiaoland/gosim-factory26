"""Interface-neutral failures raised or observed by application services."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .model import ValueModel


class Failure(ValueModel):
    """An immutable snapshot when a failure is part of a larger service result."""

    code: str
    message: str
    details: dict[str, Any]


@dataclass
class SvcError(Exception):
    """An expected, structured command failure."""

    code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def snapshot(self) -> Failure:
        return Failure(code=self.code, message=self.message, details=dict(self.details))
