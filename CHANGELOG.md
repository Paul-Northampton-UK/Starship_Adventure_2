# Changelog

## M1 – Active Pack Handshake
- Added `engine.active_pack` helpers and CLI (`--show`, `--set`)
- Hub Game Library now manages packs, validation, and engine console
- Engine resolves content root via the active pack and logs selection
- Shared theme + zoom controls applied across the hub

## M0 – Pack Hygiene & Safety
- Validated `game.yaml`, `rooms.yaml`, `objects.yaml` via Pydantic schemas
- Added placeholder descriptions for empty rooms
- Object Editor saves atomically into the active pack paths
- Introduced `python tools/doc_audit.py` and `python tools/doc_fix.py`
