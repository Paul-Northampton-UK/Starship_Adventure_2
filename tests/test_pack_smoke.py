from pathlib import Path
import yaml

PACK_DIR = Path(__file__).resolve().parents[1] / "packs" / "starship_adventure"

def yaml_files(base: Path):
    for p in base.rglob("*.yaml"):
        # Ignore obvious backups
        if p.name.endswith(".backup.yaml"):
            continue
        yield p

def test_all_pack_yaml_parse():
    assert PACK_DIR.exists(), f"Missing pack dir: {PACK_DIR}"
    bad = []
    for yf in yaml_files(PACK_DIR):
        try:
            with yf.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            assert data is not None, f"{yf} parsed to None"
        except Exception as e:
            bad.append((yf, repr(e)))
    assert not bad, "YAML parse errors:\n" + "\n".join(f"{p}: {err}" for p, err in bad)
