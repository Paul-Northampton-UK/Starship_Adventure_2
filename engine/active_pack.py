"""Helpers for reading/writing the active pack selection."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

from loguru import logger
from ruamel.yaml import YAML

from .content_root import get_content_root

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACK = "starship_adventure"
_YAML = YAML()


def _config_path() -> Path:
    return REPO_ROOT / "game_config.yaml"


def _load_config() -> dict[str, Any]:
    config_file = _config_path()
    if not config_file.is_file():
        return {}
    try:
        with config_file.open("r", encoding="utf-8") as handle:
            data = _YAML.load(handle) or {}
            if isinstance(data, dict):
                return data
    except Exception as exc:  # pragma: no cover - log + fallback
        logger.warning(f"Unable to read {config_file}: {exc}")
    return {}


def get_active_pack() -> str:
    """Return the currently configured pack name."""

    config = _load_config()
    pack = config.get("active_pack")
    if isinstance(pack, str) and pack.strip():
        return pack.strip()
    return DEFAULT_PACK


def _write_config(data: dict[str, Any]) -> None:
    config_file = _config_path()
    config_file.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = config_file.with_suffix(config_file.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        _YAML.dump(data, handle)
        handle.flush()
        os.fsync(handle.fileno())
    tmp_path.replace(config_file)


def set_active_pack(pack: str) -> None:
    """Persist the new pack selection after validating the directory exists."""

    if not isinstance(pack, str) or not pack.strip():
        raise ValueError("Pack name must be a non-empty string")

    pack = pack.strip()
    pack_path = REPO_ROOT / "packs" / pack
    if not pack_path.is_dir():
        raise FileNotFoundError(f"Pack directory not found: {pack_path}")

    _write_config({"active_pack": pack})
    logger.info(f"Active pack set to '{pack}'")


def get_content_root_from_config() -> Path:
    """Resolve the content root directory for the current pack."""

    pack = get_active_pack()
    return get_content_root(pack)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manage the active Starship Adventure pack")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--show", action="store_true", help="Display the current active pack")
    group.add_argument("--set", dest="pack_name", metavar="PACK", help="Set the active pack")
    args = parser.parse_args(argv)

    if args.show:
        print(get_active_pack())
        return 0

    try:
        set_active_pack(args.pack_name)
    except FileNotFoundError as exc:
        parser.error(str(exc))
    except ValueError as exc:
        parser.error(str(exc))
    else:
        print(f"Active pack updated to '{args.pack_name}'")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
