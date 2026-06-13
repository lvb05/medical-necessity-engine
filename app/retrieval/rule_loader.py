from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Final

logger = logging.getLogger(__name__)

AUTHORITY_AMA: Final[str] = "AMA_2021"
AUTHORITY_CMS: Final[str] = "CMS_1997"
AUTHORITY_HAAD: Final[str] = "HAAD"
AUTHORITY_JAWDA: Final[str] = "JAWDA_2026"
AUTHORITY_CLINICAL: Final[str] = "CLINICAL_CODING_PROCESS"

_AUTHORITY_FILES: Final[dict[str, str]] = {
    AUTHORITY_AMA: "ama_2021.json",
    AUTHORITY_CMS: "cms_1997.json",
    AUTHORITY_HAAD: "haad_process.json",
    AUTHORITY_JAWDA: "jawda_part_ix.json",
    AUTHORITY_CLINICAL: "clinical_coding_process.json",
}

_REQUIRED_KEYS: Final[frozenset[str]] = frozenset(
    {
        "authority",
        "authority_rank",
        "authority_scope",
        "document_name",
    }
)

AMA_CPT_CODES: Final[frozenset[str]] = frozenset(
    {
        "99202", "99203", "99204", "99205",
        "99212", "99213", "99214", "99215",
    }
)

_registry: dict[str, dict[str, Any]] = {}
_loaded: bool = False


def _validate_authority(key: str, data: dict[str, Any]) -> None:
    """Validate the minimum shape of each loaded authority JSON."""
    missing = _REQUIRED_KEYS - set(data.keys())
    if missing:
        raise ValueError(
            f"Authority '{key}' is missing required keys: {sorted(missing)}"
        )
    if "source_file" not in data and "source_files" not in data:
        raise ValueError(
            f"Authority '{key}' must contain source_file or source_files"
        )

    if not isinstance(data.get("authority_rank"), int):
        raise ValueError(
            f"Authority '{key}' has invalid authority_rank. Expected int."
        )

    authority_scope = data.get("authority_scope", [])
    if authority_scope is not None and not isinstance(authority_scope, list):
        raise ValueError(
            f"Authority '{key}' has invalid authority_scope. Expected list."
        )

    data.setdefault("authority_scope", [])
    data.setdefault("rank_context", "")
    data.setdefault("rank_note", "")
    data["_canonical_key"] = key


def _load_all(rules_dir: Path) -> dict[str, dict[str, Any]]:
    """
    Read every authority file from rules_dir, validate, and return the registry.
    """
    registry: dict[str, dict[str, Any]] = {}

    for canonical_key, filename in _AUTHORITY_FILES.items():
        path = rules_dir / filename
        if not path.exists():
            raise FileNotFoundError(
                f"Authority file not found: {path}. "
                f"Expected '{filename}' inside the rules/ directory."
            )

        with path.open(encoding="utf-8") as fh:
            try:
                data: dict[str, Any] = json.load(fh)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Authority file '{filename}' contains invalid JSON: {exc}"
                ) from exc

        _validate_authority(canonical_key, data)

        registry[canonical_key] = data
        logger.info(
            "Loaded authority %s (rank=%s) from %s",
            canonical_key,
            data["authority_rank"],
            filename,
        )

    logger.info("Loaded %d authority files.", len(registry))
    return registry


def load_rules(
    rules_dir: str | Path | None = None,
    force_reload: bool = False,
) -> dict[str, dict[str, Any]]:
    """
    Load and cache all rules.
    Call once at startup. In tests you can pass force_reload=True.
    """
    global _registry, _loaded

    if _loaded and not force_reload:
        return _registry

    if rules_dir is None:
        # app/retrieval/rule_loader.py -> project_root/rules/
        rules_dir = Path(__file__).resolve().parents[2] / "rules"

    rules_dir = Path(rules_dir)
    if not rules_dir.is_dir():
        raise FileNotFoundError(
            f"rules/ directory not found at '{rules_dir}'. "
            "Run from the project root or pass rules_dir explicitly."
        )

    _registry = _load_all(rules_dir)
    _loaded = True
    return _registry


def get_rules() -> dict[str, dict[str, Any]]:
    """Return the loaded registry."""
    if not _loaded:
        raise RuntimeError("Rules have not been loaded. Call load_rules() first.")
    return _registry


def get_rule(key: str) -> dict[str, Any]:
    """Return one canonical rule document by canonical key."""
    registry = get_rules()
    if key not in registry:
        raise KeyError(f"Unknown authority key '{key}'. Valid: {sorted(registry)}")
    return registry[key]


def get_documents_by_authority(authority: str) -> list[dict[str, Any]]:
    """
    Return all documents whose JSON authority field matches the requested authority.
    This is important because HAAD appears in both:
    - haad_process.json
    - clinical_coding_process.json
    """
    registry = get_rules()
    return [
        data
        for key, data in registry.items()
        if key == authority or data.get("authority") == authority
    ]


def get_loaded_authorities() -> list[str]:
    """Return canonical keys in load order."""
    return list(get_rules().keys())

def is_loaded() -> bool:
    return _loaded

def reset() -> None:
    """Test helper only."""
    global _registry, _loaded
    _registry = {}
    _loaded = False