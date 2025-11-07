# Starship Adventure 2 — Project Brief (Author: Paul)

## Vision
A **genre-free text adventure creation system** for non-coders: a GUI **Editor** that generates all data/files, and a **generic Engine** that plays any project created with the editor.

## Pillars (non-negotiables)
- Canonical content lives under `packs/<game_title>/` (not `data/`).
- Editor always writes **valid schema-checked YAML** the Engine can run without hand fixes.
- Works on Windows 10/11 + Python 3.12. Clean venv, reproducible installs.
- Smoke tests must pass; pack validation must be green (0 errors).

## Editor Scope (initial modules)
1) **Game Library**
   - Manage multiple projects (create/rename/delete, author, version, notes).
   - Store logos/art + intro/metadata.
   - Load/Save selected game for editing.
   - **Package**: build a distributable folder with engine + selected pack.

2) **Room Editor**
   - Forms/tabs for room data (id, name, descriptions, tags, exits, areas).
   - **Live 3D-ish map**: zoom/pan; show connections (N/E/S/W/U/D); simple layout, not CAD.
   - Writes `packs/<game>/rooms.yaml`.

3) **Object Editor** (existing, to refine)
   - Create objects with properties (visibility, portable/container/locked, states).
   - Place into rooms or libraries; conditionally reveal via puzzle logic.
   - Writes `packs/<game>/objects.yaml`.

4) **Puzzle Designer**
   - Define gating logic (room access, object manipulation, win/score conditions).
   - Writes `packs/<game>/rules.yaml` (or `puzzles.yaml` if split later).

5) **Dialogue & Responses Editor**
   - Extend/override generic engine responses and command phrasings.
   - Writes `packs/<game>/responses.yaml` (+ optional `lexicon.yaml`).

## Engine Scope
- Load a selected pack and run it in a **professional windowed UI** (terminal MVP acceptable).
- Show score, inventory, location, and allow **Save/Load** (safe, non-corrupting).
- Interpret editor-generated data (rooms/objects/rules/responses/lexicon).
- Keep **generic**: remove hardcoded game logic and use the pack data instead.

## Data & Structure (initial)
packs/
  <game_title>/
    game.yaml          # title, author, version, start_room, defaults
    rooms.yaml         # rooms, exits, areas (descriptions required)
    objects.yaml       # objects, states, containment
    rules.yaml         # gating/puzzles/conditions
    responses.yaml     # response templates and overrides
    lexicon.yaml       # synonyms, command words, nlp hints (optional)

### MVP Acceptance (first release)
- `python -m engine.game_loop` → walk 3 rooms, take an object, `inv` shows it.
- Editor: edit a room description → save → re-run game, change visible.
- `pytest -q` smoke tests green; `validate_pack` → 0 errors, ≤5 warnings (temp).
- Packaging: one click builds a runnable folder with engine + pack.

### Out of Scope (for now)
- Advanced AI/NPCs, combat, heavy story scripting, big GUI redesign.

### Known Gaps / Migration
- Some engine modules still assume a single, hardcoded game → must route through pack data.
- `data/` is legacy/staging; target is `packs/<game>/…`.

### Questions for the team (Codex must ask if unclear)
- Save format preference (JSON vs YAML for runtime saves)?
- Where should packaging output go (e.g., `dist/<game_title>-standalone/`)?
- Do we allow multiple packs installed and selectable at runtime?
