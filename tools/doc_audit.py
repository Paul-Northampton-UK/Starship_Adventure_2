"""Documentation audit helper."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = REPO_ROOT / "docs"
DEFAULT_MD = DOCS_DIR / "docs_audit_report.md"
DEFAULT_JSON = DOCS_DIR / "docs_audit_report.json"

INCLUDE_EXTS = {".md", ".txt", ".rst"}
YAML_EXTS = {".yaml", ".yml"}
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

PATTERNS = [
    {
        "name": "legacy_data_path",
        "regex": re.compile(r"\bdata/"),
        "issue": "Found reference to legacy `data/` paths.",
        "suggestion": "Use `packs/<active_pack>/...` paths instead of `data/`.",
        "auto_fixable": True,
    },
    {
        "name": "main_py_command",
        "regex": re.compile(r"python\s+\.?/main\.py", re.IGNORECASE),
        "issue": "Found `python main.py` command.",
        "suggestion": "Use `python -m engine.game_loop`.",
        "auto_fixable": True,
    },
    {
        "name": "run_editor_phrase",
        "regex": re.compile(r"run the editor", re.IGNORECASE),
        "issue": "Generic 'run the editor' phrasing.",
        "suggestion": "Reference `python tools/main_design_hub.py` explicitly.",
        "auto_fixable": True,
    },
    {
        "name": "content_root_without_context",
        "regex": re.compile(r"content root", re.IGNORECASE),
        "issue": "Mentions 'content root' without referencing `engine.active_pack`.",
        "suggestion": "Explain content root via `engine.active_pack` / `engine.validate_pack` helpers.",
        "auto_fixable": False,
        "requires_all": ["engine.active_pack", "engine.validate_pack"],
    },
    {
        "name": "todo_markers",
        "regex": re.compile(r"\b(?:TODO|FIXME)\b"),
        "issue": "Contains TODO / FIXME markers.",
        "suggestion": "Resolve or move TODO items to the tracker.",
        "auto_fixable": False,
    },
]


def iter_doc_files() -> Iterable[Path]:
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        if path.name in EXCLUDE_FILES:
            continue
        ext = path.suffix.lower()
        if ext in INCLUDE_EXTS:
            yield path
            continue
        if ext in YAML_EXTS and "packs" in path.parts:
            yield path


def analyze_file(path: Path) -> list[dict[str, str | bool]]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    lower_text = text.lower()
    issues: list[dict[str, str | bool]] = []
    for pattern in PATTERNS:
        regex: re.Pattern[str] = pattern["regex"]
        if not regex.search(text):
            continue
        requires = pattern.get("requires_all")
        if requires and any(req not in text for req in requires):
            # Issue triggered only when required markers missing
            pass
        elif requires:
            continue
        issues.append(
            {
                "issue": pattern["issue"],
                "suggestion": pattern["suggestion"],
                "auto_fixable": pattern["auto_fixable"],
            }
        )
    # Additional contextual checks
    if "content root" in lower_text and "engine.active_pack" not in text and "engine.validate_pack" not in text:
        issues.append(
            {
                "issue": "Mentions 'content root' without referencing helpers.",
                "suggestion": "Reference `engine.active_pack` / `engine.validate_pack` when discussing content roots.",
                "auto_fixable": False,
            }
        )
    return issues


def generate_reports(markdown_path: Path, json_path: Path) -> dict[str, Any]:
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = []
    total_files = 0
    files_with_issues = 0

    for path in sorted(iter_doc_files()):
        total_files += 1
        issues = analyze_file(path)
        if issues:
            files_with_issues += 1
            records.append(
                {
                    "file": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                    "issues": issues,
                }
            )

    markdown_lines = [
        "# Documentation Audit Report",
        "",
        f"- Generated: {datetime.now().isoformat(timespec='seconds')}",
        f"- Files scanned: {total_files}",
        f"- Files with issues: {files_with_issues}",
        "",
    ]

    if records:
        markdown_lines.append("| File | Issue | Suggested Change | Auto-fixable? |")
        markdown_lines.append("| --- | --- | --- | --- |")
        for record in records:
            for issue in record["issues"]:
                markdown_lines.append(
                    f"| `{record['file']}` | {issue['issue']} | {issue['suggestion']} | {'yes' if issue['auto_fixable'] else 'no'} |"
                )
    else:
        markdown_lines.append("No issues detected. ✅")

    markdown_path.write_text("\n".join(markdown_lines) + "\n", encoding="utf-8")
    json_path.write_text(json.dumps({"files": records}, indent=2), encoding="utf-8")
    return {"files": records, "total": total_files, "with_issues": files_with_issues}


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit documentation for stale references.")
    parser.add_argument("--md", type=Path, default=DEFAULT_MD, help="Path to write the Markdown report.")
    parser.add_argument("--json", type=Path, default=DEFAULT_JSON, help="Path to write the JSON report.")
    args = parser.parse_args()
    stats = generate_reports(args.md, args.json)
    print(
        f"Audit complete: {stats['total']} files scanned, {stats['with_issues']} file(s) with issues. Report saved to {args.md}."
    )


if __name__ == "__main__":
    main()
