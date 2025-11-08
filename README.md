# Starship Adventure 2

Pack-first text adventure engine with a friendly hub for non-coders.

## Quick Start
1. `python -m venv .venv`
2. `.\.venv\Scripts\activate`
3. `pip install -r requirements.txt`
4. `python -m engine.active_pack --show`
5. `python -m engine.active_pack --set starship_adventure`
6. `python -m engine.validate_pack packs/starship_adventure`
7. `python -m engine.game_loop`
8. `python tools/main_design_hub.py`

## Docs
- [Overview](docs/Overview.md)
- [Getting Started](docs/Getting_Started.md)
- [Authoring](docs/Authoring.md)
- [Packs](docs/Packs.md)
- [Contributing](docs/Contributing.md)
- [Roadmap](docs/Roadmap.md)
- [Legacy Index](docs/Legacy.md)

## Tools
- `python tools/doc_audit.py` – audit docs
- `python tools/doc_fix.py` – apply replacements
- `python tools/repo_report.py` – snapshot repo

## Tests
Run targeted smoke tests:
```
python -m pytest tests/test_pack_discovery.py tests/test_active_pack.py tests/test_pack_schema.py tests/test_validate_pack.py -q
```

