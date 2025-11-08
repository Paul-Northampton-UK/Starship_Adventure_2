# Authoring Packs

## Rooms (`rooms.yaml`)
- `room_id`, `name`
- `first_visit_description` + `short_description` per power state
- `exits` list with `direction`, `destination`, `dynamic_description`
- `areas` optional; include `objects_present` for placement

## Objects (`objects.yaml`)
- `id`, `name`, `category`
- `location` (room) and optional `area_location`
- `properties` flags (storage, wearable, etc.)
- `commands` map to allowed actions

## Editor Workflow
1. Launch `python tools/main_design_hub.py`
2. Use **Game Library** to select a pack and validate it
3. Open the Object Editor to create/update items
4. Save writes atomically to `packs/<active_pack>/objects.yaml` & `rooms.yaml`

## Placeholders
Rooms missing prose are auto-filled with `TBD -- auto-filled placeholder (remove before release)` and should be replaced.

## Validation
Always run `python -m engine.validate_pack packs/<game>` before committing.

