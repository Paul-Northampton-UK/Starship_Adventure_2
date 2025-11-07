"""Pack validation helpers."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger
from pydantic import ValidationError
from ruamel.yaml import YAML

from .content_root import get_content_root
from .schemas.pack import GamePackSchema, ObjectSchema, RoomSchema

REQUIRED_FILES = [
    "game.yaml",
    "rooms.yaml",
    "objects.yaml",
    "rules.yaml",
    "lexicon.yaml",
    "responses.yaml",
]


def _load_yaml(path: Path) -> Any:
    yaml = YAML()
    try:
        with path.open("r", encoding="utf-8") as f:
            return yaml.load(f)
    except Exception as e:
        return {"__load_error__": str(e)}


def _is_iso_utc_z(ts: Any) -> bool:
    if not isinstance(ts, str) or not ts.endswith("Z"):
        return False
    try:
        # Strict second precision: 2025-08-14T12:34:56Z
        datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
        return True
    except Exception:
        return False


def _append_validation_errors(scope: str, exc: ValidationError, bucket: list[str]) -> None:
    """Convert Pydantic validation errors into human friendly strings."""

    for err in exc.errors():
        loc = " -> ".join(str(part) for part in err.get("loc", ()))
        bucket.append(f"{scope}: {loc}: {err.get('msg')}")


def _extract_entries(source: Any, key: str, filename: str, errors: list[str]) -> list[Any]:
    """Return list entries from YAML that may be under a key or be a root list."""

    if isinstance(source, dict) and isinstance(source.get(key), list):
        return source.get(key, [])
    if isinstance(source, list):
        return source
    errors.append(f"{filename}: expected a list or a mapping with '{key}' list")
    return []


def validate_pack(content_root: Path, return_warnings: bool = False) -> list[str] | tuple[list[str], list[str]]:
    """Validate presence and minimal structure of a game pack.

    Returns a list of error strings. Empty list means OK.
    """
    errors: list[str] = []
    warnings: list[str] = []

    # 1) Required files exist
    for fname in REQUIRED_FILES:
        fpath = content_root / fname
        if not fpath.is_file():
            errors.append(f"missing file: {fname}")

    # Stop early if core files are absent
    if errors:
        return errors

    # 2) game.yaml: id, title (str)
    game = _load_yaml(content_root / "game.yaml") or {}
    try:
        GamePackSchema.model_validate(game)
    except ValidationError as exc:
        _append_validation_errors("game.yaml", exc, errors)

    # 3) rooms.yaml: each has id, description
    rooms_src = _load_yaml(content_root / "rooms.yaml")
    rooms_list = _extract_entries(rooms_src, "rooms", "rooms.yaml", errors)
    for i, room in enumerate(rooms_list):
        if not isinstance(room, dict):
            errors.append(f"rooms.yaml[{i}]: expected mapping for room entry")
            continue
        try:
            room_model = RoomSchema.model_validate(room)
        except ValidationError as exc:
            _append_validation_errors(f"rooms.yaml[{i}]", exc, errors)
            continue
        if not room_model.has_any_description():
            room_id_txt = room_model.room_id or f"index {i}"
            warnings.append(
                f"rooms.yaml[{i}] ({room_id_txt}): no description/desc/long_description found"
            )

    # 4) objects.yaml: each has id, name, location
    objects_src = _load_yaml(content_root / "objects.yaml")
    obj_list = _extract_entries(objects_src, "objects", "objects.yaml", errors)
    object_numbers: list[int] = []
    for i, obj in enumerate(obj_list):
        if not isinstance(obj, dict):
            errors.append(f"objects.yaml[{i}]: expected mapping for object entry")
            continue
        try:
            obj_model = ObjectSchema.model_validate(obj)
        except ValidationError as exc:
            _append_validation_errors(f"objects.yaml[{i}]", exc, errors)
            continue
        if not obj_model.location and not obj_model.is_hidden():
            errors.append(
                f"objects.yaml[{i}] ({obj_model.id}): object needs a location or must be invisible"
            )
        # object_number
        onum = obj.get("object_number")
        if onum is not None:
            if not isinstance(onum, int) or onum < 1:
                errors.append(f"objects.yaml[{i}]: object_number must be int>=1 if present")
            else:
                object_numbers.append(onum)
        # timestamps
        for key in ("created_at", "updated_at"):
            if key in obj:
                if not _is_iso_utc_z(obj.get(key)):
                    warnings.append(f"objects.yaml[{i}]: {key} is not ISO-8601 UTC with 'Z'")

    # Duplicate object_number warnings
    if object_numbers:
        seen: dict[int, int] = {}
        for n in object_numbers:
            seen[n] = seen.get(n, 0) + 1
        dups = [n for n, cnt in seen.items() if cnt > 1]
        for n in sorted(dups):
            warnings.append(f"objects.yaml: duplicate object_number {n}")

    # 5) rules.yaml: list; each rule has id
    rules_src = _load_yaml(content_root / "rules.yaml")
    if isinstance(rules_src, list):
        for i, rule in enumerate(rules_src):
            if not isinstance(rule, dict):
                errors.append(f"rules.yaml[{i}]: expected mapping for rule entry")
                continue
            rid = rule.get("id")
            if not isinstance(rid, str) or not rid.strip():
                errors.append(f"rules.yaml[{i}]: missing 'id'")
    else:
        errors.append("rules.yaml: expected a list of rules")

    # 6) lexicon.yaml: allow dict or list (don’t fail on shape)
    _ = _load_yaml(content_root / "lexicon.yaml")
    # no structural enforcement here

    # 7) responses.yaml: dict
    responses_src = _load_yaml(content_root / "responses.yaml")
    if not isinstance(responses_src, dict):
        errors.append("responses.yaml: expected a mapping (YAML object)")

    if return_warnings:
        return errors, warnings
    return errors


def _cli_main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Starship Adventure game pack")
    parser.add_argument(
        "content_root",
        nargs="?",
        help="Path to the pack directory (defaults to active pack from game_config.yaml)",
    )
    args = parser.parse_args()

    if args.content_root:
        content_root = Path(args.content_root).expanduser().resolve()
    else:
        project_root = Path.cwd()
        cfg_path = project_root / "game_config.yaml"
        active_pack = None
        if cfg_path.is_file():
            try:
                y = YAML()
                with cfg_path.open("r", encoding="utf-8") as f:
                    cfg = y.load(f) or {}
                    if isinstance(cfg, dict):
                        active_pack = cfg.get("active_pack")
            except Exception as e:
                logger.warning(f"Could not read game_config.yaml: {e}")

        content_root = get_content_root(active_pack)

    if not content_root.exists():
        print(f"Pack path does not exist: {content_root}")
        return 1

    print(f"Validating pack at: {content_root}")
    errs, warns = validate_pack(content_root, return_warnings=True)
    if warns:
        print("Warnings:")
        for w in warns:
            print(f"- {w}")
    if errs:
        print("Errors:")
        for e in errs:
            print(f"- {e}")
        return 1
    print("All checks passed." if not warns else "Validation completed with warnings.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli_main())

