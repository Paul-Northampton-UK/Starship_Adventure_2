# Contributing

1. Create a feature branch: `git checkout -b feature/<topic>`
2. Keep commits focused; use prefixes (`feat`, `docs`, `chore`, `fix`)
3. Run targeted tests before pushing:
```
python -m pytest tests/test_pack_discovery.py tests/test_active_pack.py tests/test_pack_schema.py tests/test_validate_pack.py -q
```
4. Run `python tools/doc_audit.py` and resolve issues
5. Snapshot repo with `python tools/repo_report.py` when relevant

## Code Style
- Python 3.12, Ruff lint, Pydantic models for schemas
- Atomic file writes for any editor output

## Documentation
- Prefer `/docs/*.md` for canonical references
- Move outdated docs to `/docs/legacy/`
- Update `CHANGELOG.md` for notable changes

