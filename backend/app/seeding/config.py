"""Validated deterministic configuration for seed dataset profiles."""

from dataclasses import dataclass
from datetime import datetime, timezone
import re
import secrets
from typing import Literal


@dataclass(frozen=True)
class SeedConfig:
    dataset: str
    profile: Literal["manual", "light-load"]
    seed: int
    min_samples: int
    max_samples: int
    max_rows: int
    reference_time: datetime
    generator_version: str = "2"


def resolve_config(*, dataset: str, profile: str = "manual", seed: int | None = None,
                   min_samples: int | None = None, max_samples: int | None = None,
                   max_rows: int | None = None, reference_time: datetime | None = None) -> SeedConfig:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,39}", dataset):
        raise ValueError("dataset must match [a-z0-9][a-z0-9-]{0,39}")
    profiles = {"manual": (5, 15, 25_000), "light-load": (10, 30, 100_000)}
    if profile not in profiles:
        raise ValueError("profile must be manual or light-load")
    default_min, default_max, default_rows = profiles[profile]
    lower = default_min if min_samples is None else min_samples
    upper = default_max if max_samples is None else max_samples
    rows = default_rows if max_rows is None else max_rows
    if lower < 5 or upper < lower:
        raise ValueError("sample range must satisfy 5 <= min_samples <= max_samples")
    if rows < 1 or rows > 100_000:
        raise ValueError("max_rows must be between 1 and 100000")
    moment = reference_time or datetime(2026, 1, 1, tzinfo=timezone.utc)
    if moment.tzinfo is None:
        raise ValueError("reference_time must include a timezone")
    return SeedConfig(dataset, profile, secrets.randbits(64) if seed is None else seed,
                      lower, upper, rows, moment.astimezone(timezone.utc))
