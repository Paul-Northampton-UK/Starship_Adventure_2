"""Sanity checks for documentation."""

from __future__ import annotations

from pathlib import Path

from tools import doc_audit

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = REPO_ROOT / "docs"
LEGACY_DIR = DOCS_DIR / "legacy"


def _iter_doc_paths():
    for path in DOCS_DIR.rglob("*.md"):
        if LEGACY_DIR in path.parents:
            continue
        yield path
    # README at root
    yield REPO_ROOT / "README.md"


def test_no_legacy_data_paths_outside_legacy():
    for path in _iter_doc_paths():
        text = path.read_text(encoding="utf-8")
        assert "data/" not in text, f"Legacy data/ reference found in {path}"


def test_readme_lists_quick_start_commands():
    text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    required = [
        "python -m engine.active_pack --show",
        "python -m engine.active_pack --set",
        "python -m engine.validate_pack",
        "python -m engine.game_loop",
        "python tools/main_design_hub.py",
    ]
    for command in required:
        assert command in text, f"{command} missing from README quick start"


def test_packs_doc_mentions_helpers():
    text = (DOCS_DIR / "Packs.md").read_text(encoding="utf-8")
    assert "engine.active_pack" in text
    assert "engine.validate_pack" in text


def test_doc_audit_has_no_auto_fixable_items(tmp_path):
    md = tmp_path / "report.md"
    js = tmp_path / "report.json"
    stats = doc_audit.generate_reports(md, js)
    auto_issues = [
        issue
        for record in stats["files"]
        for issue in record["issues"]
        if issue["auto_fixable"]
    ]
    assert not auto_issues, "Doc audit reports auto-fixable issues"
