"""Documentation fixer for simple replacements."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
REPLACEMENTS = [
    ("python main.py", "python -m engine.game_loop"),
    ("python ./main.py", "python -m engine.game_loop"),
    ("run the editor", "python tools/main_design_hub.py"),
    ("data/", "packs/"),
]
INCLUDE_EXTS = {".md", ".txt", ".rst", ".yaml", ".yml"}
EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "logs",
}
EXCLUDE_FILES = {"repo_report.md"}


def iter_files() -> Iterable[Path]:
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        if path.name in EXCLUDE_FILES:
            continue
        if path.suffix.lower() in INCLUDE_EXTS:
            yield path


def apply_replacements(path: Path) -> tuple[bool, str]:
    original = path.read_text(encoding="utf-8")
    updated = original
    for old, new in REPLACEMENTS:
        updated = updated.replace(old, new)
    changed = updated != original
    return changed, updated


def ensure_backup(path: Path) -> None:
    backup_path = path.with_suffix(path.suffix + ".bak")
    if backup_path.exists():
        return
    shutil.copy2(path, backup_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply simple documentation fixes.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes instead of running in dry-run mode.",
    )
    args = parser.parse_args()

    changed_files = []
    for path in iter_files():
        try:
            changed, updated = apply_replacements(path)
        except UnicodeDecodeError:
            continue
        if not changed:
            continue
        if args.apply:
            ensure_backup(path)
            path.write_text(updated, encoding="utf-8")
        changed_files.append(str(path.relative_to(REPO_ROOT)))

    if not changed_files:
        print("No changes required.")
        return

    mode = "APPLIED" if args.apply else "DRY-RUN"
    print(f"{mode}: {len(changed_files)} file(s) would be updated:")
    for file in changed_files:
        print(f" - {file}")


if __name__ == "__main__":
    main()
