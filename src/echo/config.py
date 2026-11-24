# SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
"""Typed simulation configuration with explicit validation and a stable hash.

Units: angles in radians; cosine quantities are unitless in [-1, 1];
``tau`` and ``skip_utility`` are in cosine units (the logit of a slate item
is cos / tau, the logit of skipping is skip_utility / tau).

Values marked "implementation default" are not fixed by the draft protocol
(research/protocol.md v0.1). They are proposed to the owner in progress.md
and must be confirmed or replaced at freeze.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass, fields
from typing import Any

POLICIES = ("RAND", "POP", "SIM", "MMR", "EXPLORE")
PERSONALISED_POLICIES = ("SIM", "MMR", "EXPLORE")
PREFERENCE_MODELS = ("fixed", "adaptive")
UPDATE_RULES = ("consumed", "exposure", "bounded")
PROFILES = ("estimated", "oracle")
CATALOGUES = ("synthetic", "fma")

SMOKE_SEED_BASE = 900000
CONFIRMATORY_SEEDS = tuple(range(20261124, 20261134))


class ConfigError(ValueError):
    """Raised when a configuration is invalid."""


@dataclass(frozen=True)
class SimConfig:
    """One simulation run. Defaults are the draft protocol section 3 values."""

    seed: int
    policy: str = "RAND"
    preference_model: str = "adaptive"
    update_rule: str = "consumed"
    profile: str = "estimated"
    n_tracks: int = 1000
    dim: int = 16
    n_clusters: int = 10
    zipf_s: float = 1.0
    n_users: int = 200
    n_steps: int = 100
    slate_size: int = 10
    tau: float = 0.1
    eta: float = 0.05
    warmup_steps: int = 5
    mmr_lambda: float = 0.5
    explore_epsilon: float = 0.2
    bounded_threshold: float = 0.5
    # Implementation defaults (not fixed by the draft protocol):
    skip_utility: float = 0.0
    track_spread: float = 0.1
    listener_spread: float = 0.1
    # Real-data amendment (protocol section 10.1, owner-approved 2026-11-24):
    # catalogue "synthetic" (default) or "fma" (EXP-004 second test).
    catalogue: str = "synthetic"
    # Synthetic catalogue only: cluster probabilities fitted on FMA; None = uniform.
    cluster_weights: tuple[float, ...] | None = None
    # FMA catalogue only: SHA-256 of data/processed/fma_catalogue_v1.npz.
    fma_catalogue_sha256: str | None = None

    def validate(self) -> "SimConfig":
        errors: list[str] = []

        def need_int(name: str, lo: int) -> None:
            v = getattr(self, name)
            if isinstance(v, bool) or not isinstance(v, int):
                errors.append(f"{name} must be an int, got {type(v).__name__}")
            elif v < lo:
                errors.append(f"{name} must be >= {lo}, got {v}")

        def need_float(name: str, lo: float, hi: float, lo_open: bool = False, hi_open: bool = False) -> None:
            v = getattr(self, name)
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                errors.append(f"{name} must be a number, got {type(v).__name__}")
                return
            if not math.isfinite(v):
                errors.append(f"{name} must be finite, got {v}")
                return
            if (v <= lo if lo_open else v < lo) or (v >= hi if hi_open else v > hi):
                errors.append(f"{name}={v} outside {'(' if lo_open else '['}{lo}, {hi}{')' if hi_open else ']'}")

        need_int("seed", 0)
        need_int("n_tracks", 2)
        need_int("dim", 2)
        need_int("n_clusters", 1)
        need_int("n_users", 2)
        need_int("n_steps", 1)
        need_int("slate_size", 2)
        need_int("warmup_steps", 0)
        need_float("zipf_s", 0.0, 10.0)
        need_float("tau", 0.0, 1e6, lo_open=True)
        need_float("eta", 0.0, 1.0)
        need_float("mmr_lambda", 0.0, 1.0, lo_open=True)
        need_float("explore_epsilon", 0.0, 1.0)
        need_float("bounded_threshold", -1.0, 1.0)
        need_float("skip_utility", -1e6, 1e6)
        need_float("track_spread", 0.0, 1e6)
        need_float("listener_spread", 0.0, 1e6)
        if self.policy not in POLICIES:
            errors.append(f"policy must be one of {POLICIES}, got {self.policy!r}")
        if self.preference_model not in PREFERENCE_MODELS:
            errors.append(f"preference_model must be one of {PREFERENCE_MODELS}, got {self.preference_model!r}")
        if self.update_rule not in UPDATE_RULES:
            errors.append(f"update_rule must be one of {UPDATE_RULES}, got {self.update_rule!r}")
        if self.profile not in PROFILES:
            errors.append(f"profile must be one of {PROFILES}, got {self.profile!r}")
        if self.catalogue not in CATALOGUES:
            errors.append(f"catalogue must be one of {CATALOGUES}, got {self.catalogue!r}")
        if self.cluster_weights is not None:
            w = self.cluster_weights
            if not isinstance(w, tuple) or not all(
                isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) and x >= 0 for x in w
            ):
                errors.append("cluster_weights must be a list of finite non-negative numbers")
            elif len(w) != self.n_clusters:
                errors.append(f"cluster_weights has {len(w)} entries, n_clusters is {self.n_clusters}")
            elif abs(sum(w) - 1.0) > 1e-4:
                errors.append(f"cluster_weights must sum to 1 within 1e-4, got {sum(w)}")
            if self.catalogue == "fma":
                errors.append("cluster_weights apply to the synthetic catalogue only")
        sha = self.fma_catalogue_sha256
        if self.catalogue == "fma":
            if not isinstance(sha, str) or len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
                errors.append("catalogue 'fma' needs fma_catalogue_sha256 (64 lowercase hex characters)")
        elif sha is not None:
            errors.append("fma_catalogue_sha256 applies to catalogue 'fma' only")
        if not errors:
            if self.preference_model == "fixed" and self.eta != 0.0:
                errors.append("preference_model 'fixed' requires eta == 0.0")
            if self.preference_model == "adaptive" and self.eta == 0.0:
                errors.append("preference_model 'adaptive' requires eta > 0")
            if self.slate_size > self.n_tracks:
                errors.append("slate_size must not exceed n_tracks")
            # Candidate exclusion: at most one track is consumed per step, so the
            # pool never drops below slate_size if n_steps <= n_tracks - slate_size.
            if self.n_steps > self.n_tracks - self.slate_size:
                errors.append(
                    f"design check failed: n_steps ({self.n_steps}) > n_tracks - slate_size "
                    f"({self.n_tracks - self.slate_size}); the candidate pool could be exhausted"
                )
        if errors:
            raise ConfigError("; ".join(errors))
        return self

    def to_dict(self) -> dict[str, Any]:
        """JSON-ready dict. The three real-data fields are omitted at their
        defaults, so configs and hashes from before the amendment are unchanged."""
        d = asdict(self)
        if d["cluster_weights"] is not None:
            d["cluster_weights"] = list(d["cluster_weights"])
        for key, default in (("catalogue", "synthetic"), ("cluster_weights", None), ("fma_catalogue_sha256", None)):
            if d[key] == default:
                del d[key]
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SimConfig":
        if not isinstance(data, dict):
            raise ConfigError("configuration must be a JSON object")
        known = {f.name for f in fields(cls)}
        unknown = sorted(set(data) - known)
        if unknown:
            raise ConfigError(f"unknown configuration keys: {unknown}")
        if "seed" not in data:
            raise ConfigError("configuration needs a seed")
        data = dict(data)
        if isinstance(data.get("cluster_weights"), list):
            data["cluster_weights"] = tuple(data["cluster_weights"])
        cfg = cls(**data)
        # Normalise ints given for float fields so hashes are stable.
        floats = {f.name for f in fields(cls) if f.type in ("float", float)}
        norm = {k: (float(v) if k in floats and isinstance(v, int) and not isinstance(v, bool) else v) for k, v in asdict(cfg).items()}
        if norm["cluster_weights"] is not None and all(
            isinstance(x, (int, float)) and not isinstance(x, bool) for x in norm["cluster_weights"]
        ):
            norm["cluster_weights"] = tuple(float(x) for x in norm["cluster_weights"])
        return cls(**norm).validate()

    def hash(self) -> str:
        return config_hash(self.to_dict())


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False)


def config_hash(obj: Any) -> str:
    """SHA-256 of the canonical JSON encoding (sorted keys, no whitespace)."""
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()
