from pathlib import Path
from engine.yaml_loader import YAMLLoader

PACK_DIR = Path(__file__).resolve().parents[1] / "packs" / "starship_adventure"

def test_engine_can_load_core_yaml():
    assert PACK_DIR.exists(), f"Missing pack dir: {PACK_DIR}"
    loader = YAMLLoader(PACK_DIR)

    must_have = ["rooms.yaml", "objects.yaml", "responses.yaml", "rules.yaml", "game.yaml", "lexicon.yaml"]
    loaded = {}
    for name in must_have:
        data = loader.load_file(name)   # <- updated API
        assert data is not None, f"{name} loaded as None"
        loaded[name] = data

    rooms = loaded["rooms.yaml"]
    assert isinstance(rooms, dict) and len(rooms) > 0, "rooms.yaml should contain rooms"
