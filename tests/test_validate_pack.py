from pathlib import Path
import textwrap

from engine.validate_pack import validate_pack


def _write_yaml(path: Path, content: str) -> None:
    path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")


def _build_minimal_pack(tmp_path: Path) -> Path:
    pack = tmp_path / "pack"
    pack.mkdir()

    _write_yaml(
        pack / "game.yaml",
        """
        id: demo
        title: Demo Pack
        version: 0.1.0
        engine_min_version: 0.1.0
        start_room_id: ship_bridge
        start_power_state: emergency
        """,
    )

    _write_yaml(
        pack / "rooms.yaml",
        """
        rooms:
          - room_id: ship_bridge
            name: Ship Bridge
            description: Fully operational bridge.
        """,
    )

    _write_yaml(
        pack / "objects.yaml",
        """
        objects:
          - id: torch
            name: Torch
            location: ship_bridge
        """,
    )

    _write_yaml(pack / "rules.yaml", "[]")
    _write_yaml(pack / "responses.yaml", "{}")
    _write_yaml(pack / "lexicon.yaml", "{}")

    return pack


def test_validate_pack_success(tmp_path):
    pack = _build_minimal_pack(tmp_path)
    errors, warnings = validate_pack(pack, return_warnings=True)
    assert errors == []
    assert warnings == []


def test_validate_pack_missing_start_room(tmp_path):
    pack = _build_minimal_pack(tmp_path)
    _write_yaml(
        pack / "game.yaml",
        """
        id: broken
        title: Broken Pack
        version: 0.1.0
        engine_min_version: 0.1.0
        start_power_state: emergency
        """,
    )

    errors = validate_pack(pack)
    assert any("start_room_id" in err for err in errors)
