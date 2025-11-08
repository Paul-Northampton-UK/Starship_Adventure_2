# Packs

A pack lives under `packs/<name>/` and contains:

```
packs/<name>/
+- game.yaml
+- rooms.yaml
+- objects.yaml
+- responses.yaml
+- rules.yaml
+- lexicon.yaml (optional)
```

## Pack Metadata (`game.yaml`)
- `id`, `title`, `version`, `engine_min_version`
- `start_room_id`, `start_power_state`
- validated by `engine.active_pack` helpers

## CLI Helpers
```
python -m engine.active_pack --show
python -m engine.active_pack --set starship_adventure
python -m engine.validate_pack packs/starship_adventure
```

## YAML Tips
- Keep IDs lowercase with underscores
- Use lists for `rooms`/`objects`
- Keep everything under `packs/` (no legacy data directories)

## Validation Pipeline
1. Select pack via `engine.active_pack`
2. Run `engine.validate_pack`
3. Fix schema errors before editing further

