from pathlib import Path

from tools import pack_discovery


def test_has_game_yaml(tmp_path):
    pack_dir = tmp_path / "demo"
    pack_dir.mkdir()
    (pack_dir / "game.yaml").write_text("id: demo\n", encoding="utf-8")
    assert pack_discovery.has_game_yaml(pack_dir)


def test_list_packs(tmp_path, monkeypatch):
    packs_dir = tmp_path / "packs"
    packs_dir.mkdir()
    (packs_dir / "a").mkdir()
    (packs_dir / "a" / "game.yaml").write_text("id: a\n", encoding="utf-8")
    (packs_dir / "b").mkdir()
    (packs_dir / "b" / "game.yaml").write_text("id: b\n", encoding="utf-8")
    result = pack_discovery.list_packs(packs_dir)
    assert result == ["a", "b"]


def test_current_active_pack(monkeypatch, tmp_path):
    repo_root = tmp_path / "repo"
    packs_dir = repo_root / "packs"
    packs_dir.mkdir(parents=True)
    default_pack = packs_dir / "starship_adventure"
    default_pack.mkdir()
    (default_pack / "game.yaml").write_text("id: default\n", encoding="utf-8")
    monkeypatch.chdir(repo_root)
    monkeypatch.setattr(pack_discovery.active_pack, "REPO_ROOT", repo_root)
    assert pack_discovery.current_active_pack() == "starship_adventure"
