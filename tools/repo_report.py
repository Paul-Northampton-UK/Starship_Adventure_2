from __future__ import annotations

import os
import pathlib
import sys
import time
from dataclasses import dataclass
from typing import Iterable

import yaml

# Ensure we can import engine.* when running from repo root
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.content_root import get_content_root  # type: ignore
from engine.validate_pack import validate_pack  # type: ignore


# Exclusion list (dirs) per requirements
SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".vscode",
    "logs",
}

# File types to include in counts
TEXT_EXTS = {".py", ".yaml", ".yml", ".md", ".json", ".toml"}

# Areas to summarize
AREAS = ["engine", "tools", "packs", "data", "docs", "tests"]


def is_skipped_path(p: pathlib.Path) -> bool:
    return any(part in SKIP_DIRS for part in p.parts)


def iter_files(base: pathlib.Path) -> Iterable[pathlib.Path]:
    for dirpath, dirnames, filenames in os.walk(base):
        d = pathlib.Path(dirpath)
        # prune directories in-place
        dirnames[:] = [n for n in dirnames if n not in SKIP_DIRS]
        if is_skipped_path(d):
            continue
        for fn in filenames:
            p = d / fn
            if is_skipped_path(p):
                continue
            yield p


def non_blank_loc(p: pathlib.Path) -> int:
    try:
        with p.open("r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for line in f if line.strip())
    except Exception:
        return 0


@dataclass
class FileInfo:
    rel: str
    size_bytes: int
    loc_nonblank: int
    mtime: str


def collect_file_infos(base: pathlib.Path) -> list[FileInfo]:
    infos: list[FileInfo] = []
    for p in iter_files(base):
        if p.is_dir():
            continue
        try:
            st = p.stat()
        except FileNotFoundError:
            continue
        rel = str(p.relative_to(base))
        loc = non_blank_loc(p) if p.suffix.lower() in TEXT_EXTS else 0
        mtime = time.strftime("%Y-%m-%d %H:%M", time.localtime(st.st_mtime))
        infos.append(FileInfo(rel=rel, size_bytes=st.st_size, loc_nonblank=loc, mtime=mtime))
    return infos


def summarize_by_area(infos: list[FileInfo]) -> dict[str, tuple[int, int]]:
    summary: dict[str, tuple[int, int]] = {}
    for area in AREAS:
        files = [fi for fi in infos if fi.rel.replace("\\", "/").startswith(area + "/")]
        file_count = len(files)
        loc = sum(fi.loc_nonblank for fi in files)
        summary[area] = (file_count, loc)
    return summary


def read_active_pack_path() -> pathlib.Path:
    cfg_path = ROOT / "game_config.yaml"
    active_pack = None
    if cfg_path.is_file():
        try:
            with cfg_path.open("r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
                if isinstance(cfg, dict):
                    active_pack = cfg.get("active_pack")
        except Exception:
            active_pack = None
    content_root = get_content_root(active_pack)
    return content_root.resolve()


def parse_previous_report(path: pathlib.Path) -> dict[str, int]:
    """Return mapping relpath -> loc_nonblank from previous report lines."""
    mapping: dict[str, int] = {}
    if not path.is_file():
        return mapping
    try:
        text = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return mapping
    for line in text:
        # Expect format: - `path` | <loc> loc | <mtime>
        s = line.strip()
        if not (s.startswith("- `") and " loc |" in s):
            continue
        try:
            b1 = s.index("`")
            b2 = s.index("`", b1 + 1)
            rel = s[b1 + 1 : b2]
            # extract integer before ' loc |'
            after = s[b2 + 1 :]
            parts = after.split("|")
            loc_str = "".join(ch for ch in parts[1] if ch.isdigit()) if len(parts) > 1 else "0"
            mapping[rel] = int(loc_str or 0)
        except Exception:
            continue
    return mapping


def build_report() -> str:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    infos = collect_file_infos(ROOT)

    # Separate very large files (> 50 KB)
    LARGE_THRESHOLD = 50 * 1024
    large_files = sorted(
        [fi for fi in infos if fi.size_bytes > LARGE_THRESHOLD], key=lambda x: (-x.size_bytes, x.rel)
    )
    # Files to list in tree (exclude very large ones), keep text-ish
    listable = [fi for fi in infos if fi.size_bytes <= LARGE_THRESHOLD]
    listable.sort(key=lambda x: x.rel.lower())

    # Summary by area
    summary = summarize_by_area(infos)

    # Active content root and validation
    active_root = read_active_pack_path()
    try:
        errs, warns = validate_pack(active_root, return_warnings=True)  # type: ignore[arg-type]
    except TypeError:
        res = validate_pack(active_root)  # type: ignore
        errs, warns = (res, []) if isinstance(res, list) else ([], [])

    # Delta versus previous snapshot
    report_path = ROOT / "repo_report.md"
    prev_map = parse_previous_report(report_path)
    curr_map = {fi.rel: fi.loc_nonblank for fi in listable}
    added = sorted(set(curr_map) - set(prev_map))
    removed = sorted(set(prev_map) - set(curr_map))
    loc_delta = sum(curr_map.values()) - sum(prev_map.values())

    out: list[str] = []
    out.append(f"# Repo snapshot — {timestamp}")

    # Summary
    out.append("")
    out.append("## Summary")
    for area in AREAS:
        cnt, loc = summary.get(area, (0, 0))
        out.append(f"- {area}/: {cnt} files | ~{loc} non-blank LOC")

    # Active pack
    out.append("")
    out.append("## Active Pack")
    out.append(f"- Resolved content root: `{active_root}`")
    if (ROOT / "data").is_dir():
        out.append("- Note: `data/` present (legacy/staging content; canonical pack is under `packs/`).")
    if errs or warns:
        out.append(f"- Pack validation: errors={len(errs)} warnings={len(warns)}")
        if errs:
            out.append("  - Errors:")
            for e in errs[:20]:
                out.append(f"    - {e}")
            if len(errs) > 20:
                out.append(f"    - ... and {len(errs)-20} more")
        if warns:
            out.append("  - Warnings:")
            for w in warns[:20]:
                out.append(f"    - {w}")
            if len(warns) > 20:
                out.append(f"    - ... and {len(warns)-20} more")
    else:
        out.append("- Pack validation: OK")

    # Delta
    out.append("")
    out.append("## Delta Since Last Snapshot")
    if prev_map:
        out.append(f"- Added files: {len(added)}")
        if added:
            for k in added[:20]:
                out.append(f"  - + {k}")
            if len(added) > 20:
                out.append(f"  - ... and {len(added)-20} more")
        out.append(f"- Removed files: {len(removed)}")
        if removed:
            for k in removed[:20]:
                out.append(f"  - - {k}")
            if len(removed) > 20:
                out.append(f"  - ... and {len(removed)-20} more")
        out.append(f"- Net LOC change (non-blank): {loc_delta:+}")
    else:
        out.append("- No previous snapshot detected.")

    # Very large files
    out.append("")
    out.append("## Very Large Files (>50 KB)")
    if large_files:
        for fi in large_files[:100]:
            out.append(f"- `{fi.rel}` | {fi.size_bytes // 1024} KB")
        if len(large_files) > 100:
            out.append(f"- ... and {len(large_files)-100} more")
    else:
        out.append("- None")

    # Selected files (exclude very large)
    out.append("")
    out.append("## Files (selected; excludes very large)")
    MAX_LIST = 300
    for fi in listable[:MAX_LIST]:
        out.append(f"- `{fi.rel}` | {fi.loc_nonblank} loc | {fi.mtime}")
    if len(listable) > MAX_LIST:
        out.append(f"- ... and {len(listable)-MAX_LIST} more")

    # Keep concise (<500 lines)
    return "\n".join(out[:500])


def main() -> None:
    report = build_report()
    out_path = ROOT / "repo_report.md"
    out_path.write_text(report, encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()

