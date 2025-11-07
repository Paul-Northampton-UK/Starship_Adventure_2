import argparse
from pathlib import Path

import pytest

from engine import active_pack


@pytest.fixture()
def temp_repo(tmp_path, monkeypatch):
    """Create an isolated fake repo root under tmp_path."""

    repo_root = tmp_path / "repo"
    packs_dir = repo_root / "packs"
    packs_dir.mkdir(parents=True)
    default_pack = packs_dir / "starship_adventure"
    default_pack.mkdir()
    (default_pack / "game.yaml").write_text("id: default\n", encoding="utf-8")

    monkeypatch.chdir(repo_root)
    monkeypatch.setattr(active_pack, "REPO_ROOT", repo_root)
    yield repo_root


def test_get_active_pack_defaults(temp_repo):
    assert active_pack.get_active_pack() == "starship_adventure"


def test_set_active_pack_writes_config(temp_repo):
    pack_dir = temp_repo / "packs" / "my_test_pack"
    pack_dir.mkdir()
    (pack_dir / "game.yaml").write_text("id: test\n", encoding="utf-8")

    active_pack.set_active_pack("my_test_pack")
    assert active_pack.get_active_pack() == "my_test_pack"

    config_path = temp_repo / "game_config.yaml"
    assert "my_test_pack" in config_path.read_text(encoding="utf-8")


def test_get_content_root_from_config(temp_repo):
    pack_dir = temp_repo / "packs" / "my_test_pack"
    pack_dir.mkdir()
    (pack_dir / "game.yaml").write_text("id: test\n", encoding="utf-8")
    active_pack.set_active_pack("my_test_pack")

    root = active_pack.get_content_root_from_config()
    assert root.samefile(pack_dir)


def test_cli_show_and_set(monkeypatch, temp_repo, capsys):
    pack_dir = temp_repo / "packs" / "cli_pack"
    pack_dir.mkdir()
    (pack_dir / "game.yaml").write_text("id: cli\n", encoding="utf-8")

    active_pack.main(["--show"])
    assert "starship_adventure" in capsys.readouterr().out

    active_pack.main(["--set", "cli_pack"])
    out = capsys.readouterr().out
    assert "cli_pack" in out
    assert active_pack.get_active_pack() == "cli_pack"
