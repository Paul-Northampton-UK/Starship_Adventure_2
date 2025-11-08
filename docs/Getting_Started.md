# Getting Started (Windows)

## 1. Environment
```
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Select a Pack
```
python -m engine.active_pack --show
python -m engine.active_pack --set starship_adventure
```

## 3. Validate Content
```
python -m engine.validate_pack packs/starship_adventure
```

## 4. Run the Engine & Hub
```
python -m engine.game_loop
python tools/main_design_hub.py
```

## 5. Useful Scripts
- `python tools/doc_audit.py`
- `python tools/doc_fix.py`
- `python tools/repo_report.py`

