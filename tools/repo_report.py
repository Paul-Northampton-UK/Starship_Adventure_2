import os, time, ast, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".venv", "__pycache__", "node_modules", ".mypy_cache", ".pytest_cache", "dist", "build", ".idea", ".vscode"}
EXTS = {".py", ".yaml", ".yml", ".md", ".json"}

def is_skipped(p: pathlib.Path) -> bool:
    return any(part in SKIP_DIRS for part in p.parts)

def list_defs(pyfile: pathlib.Path):
    items = []
    try:
        src = pyfile.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(src)
        for n in tree.body:
            if isinstance(n, ast.ClassDef):
                items.append(f"class {n.name}")
            elif isinstance(n, ast.FunctionDef):
                items.append(f"def {n.name}()")
    except Exception:
        pass
    return items[:40]

lines = []
lines.append(f"# Repo snapshot — {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
lines.append("## Tree (selected files)\n")

for dirpath, dirnames, filenames in os.walk(ROOT):
    d = pathlib.Path(dirpath)
    dirnames[:] = [n for n in dirnames if n not in SKIP_DIRS]
    for fn in sorted(filenames):
        p = d / fn
        if is_skipped(p) or p.suffix.lower() not in EXTS:
            continue
        try:
            size = sum(1 for _ in open(p, "r", encoding="utf-8", errors="ignore"))
        except Exception:
            size = 0
        mtime = time.strftime("%Y-%m-%d %H:%M", time.localtime(p.stat().st_mtime))
        relp = p.relative_to(ROOT)
        lines.append(f"- `{relp}`  · {size} lines · {mtime}")

lines.append("\n## Python modules — top-level classes/functions\n")
for dirpath, _, filenames in os.walk(ROOT):
    d = pathlib.Path(dirpath)
    if is_skipped(d):
        continue
    for fn in sorted(filenames):
        p = pathlib.Path(dirpath) / fn
        if p.suffix != ".py" or is_skipped(p):
            continue
        defs = list_defs(p)
        if defs:
            relp = p.relative_to(ROOT)
            lines.append(f"### `{relp}`")
            for item in defs:
                lines.append(f"- {item}")
            lines.append("")

out = ROOT / "repo_report.md"
out.write_text("\n".join(lines), encoding="utf-8")
print(f"Wrote {out}")


