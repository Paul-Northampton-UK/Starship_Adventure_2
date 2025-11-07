from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger
from ruamel.yaml import YAML

from .content_root import get_content_root

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
    game = _load_yaml(content_root / "game.yaml")
    if isinstance(game, dict):
        gid = game.get("id")
        title = game.get("title") or game.get("name")  # allow 'name' as fallback
        if not isinstance(gid, str) or not gid.strip():
            errors.append("game.yaml: 'id' must be a non-empty string")
        if not isinstance(title, str) or not title.strip():
            errors.append("game.yaml: 'title' (or 'name') must be a non-empty string")
    else:
        errors.append("game.yaml: expected a mapping (YAML object)")

    # 3) rooms.yaml: each has id, description
    rooms_src = _load_yaml(content_root / "rooms.yaml")
    rooms_list = []
    if isinstance(rooms_src, dict) and isinstance(rooms_src.get("rooms"), list):
        rooms_list = rooms_src.get("rooms", [])
    elif isinstance(rooms_src, list):
        rooms_list = rooms_src
    else:
        errors.append("rooms.yaml: expected a list or a mapping with 'rooms' list")
        rooms_list = []
    for i, room in enumerate(rooms_list):
        if not isinstance(room, dict):
            errors.append(f"rooms.yaml[{i}]: expected mapping for room entry")
            continue
        rid = room.get("room_id") or room.get("id")
        # Accept any of description|desc|long_description
        desc = room.get("description")
        if not isinstance(desc, str) or not desc.strip():
            desc = room.get("desc")
        if not isinstance(desc, str) or not desc.strip():
            desc = room.get("long_description")
        if not isinstance(rid, str) or not rid.strip():
            errors.append(f"rooms.yaml[{i}]: missing 'id' (room_id/id)")
        # Soften: warn if no description-like field
        if not isinstance(desc, str) or not desc.strip():
            room_id_txt = rid if isinstance(rid, str) and rid.strip() else f"index {i}"
            warnings.append(f"rooms.yaml[{i}] ({room_id_txt}): no description/desc/long_description found")

    # 4) objects.yaml: each has id, name, location
    objects_src = _load_yaml(content_root / "objects.yaml")
    obj_list = []
    if isinstance(objects_src, dict) and isinstance(objects_src.get("objects"), list):
        obj_list = objects_src.get("objects", [])
    elif isinstance(objects_src, list):
        obj_list = objects_src
    else:
        errors.append("objects.yaml: expected a list or a mapping with 'objects' list")
        obj_list = []
    object_numbers: list[int] = []
    for i, obj in enumerate(obj_list):
        if not isinstance(obj, dict):
            errors.append(f"objects.yaml[{i}]: expected mapping for object entry")
            continue
        oid = obj.get("id")
        name = obj.get("name")
        loc = obj.get("location")
        if not isinstance(oid, str) or not oid.strip():
            errors.append(f"objects.yaml[{i}]: missing 'id'")
        if not isinstance(name, str) or not name.strip():
            errors.append(f"objects.yaml[{i}]: missing 'name'")
        # Hidden/unplaced relaxation: accept missing location if explicitly invisible
        invisible = False
        props = obj.get("properties") if isinstance(obj.get("properties"), dict) else {}
        if props is not None and isinstance(props, dict):
            if props.get("is_visible") is False:
                invisible = True
        if obj.get("initial_state") is False:
            invisible = True
        if not isinstance(loc, str) or not loc.strip():
            if not invisible:
                errors.append(f"objects.yaml[{i}]: object needs a location or must be invisible")
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
    # Read active_pack from game_config.yaml and resolve content root
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
    if not errs and not warns:
        print("All checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli_main())


