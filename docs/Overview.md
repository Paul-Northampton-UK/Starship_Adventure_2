# Overview

Starship Adventure 2 is a **pack-driven text adventure system**. Authors build packs (rooms, objects, rules, responses) and the engine + editor load them at runtime.

## Vision
- Let non-coders design adventures through a GUI.
- Keep content canonical under `packs/<game>/`.
- Ship a professional engine loop (`python -m engine.game_loop`) and a hub (`python tools/main_design_hub.py`).

## Pillars
1. **Active Pack awareness:** `engine.active_pack` selects the pack globally.
2. **Schema-first data:** rooms/objects/responses validated by Pydantic models and `engine.validate_pack`.
3. **Atomic authoring:** the Object Editor writes `.yaml` into the active pack using temp files.
4. **Reproducible installs:** Python 3.12 + `requirements.txt`.

## Editor Modules
- Game Library (pack selection, validation, engine console)
- Room Editor (WIP)
- Object Editor
- Puzzle Designer (WIP)
- Dialogue & Response editors (WIP)

## Engine Scope
- Load selected pack metadata from `packs/<game>/game.yaml`.
- Describe rooms/areas, manage inventory, handle commands.
- Provide save/load, logging, NLP command parsing.

## Data & Packs
See [Packs](Packs.md) for required files and validation helpers.

## Release Checklist
- `python -m engine.active_pack --show|--set`
- `python -m engine.validate_pack packs/<game>`
- `python -m engine.game_loop`
- `python tools/main_design_hub.py`

