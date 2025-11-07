import os
import hashlib
import yaml

def file_hash(path, algo="sha256"):
    """Return hash digest of file contents."""
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def summarize_file(path):
    """Summarize text files by showing first lines; skip binaries."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read(400)  # preview only
            return content.replace("\n", "\\n")
    except Exception:
        return "<binary or unreadable>"

def build_report(root_dir, max_preview=400):
    """Walk project tree and build YAML summary."""
    project_summary = []
    for dirpath, _, filenames in os.walk(root_dir):
        for fn in filenames:
            full_path = os.path.join(dirpath, fn)
            rel_path = os.path.relpath(full_path, root_dir)
            size = os.path.getsize(full_path)
            info = {
                "path": rel_path,
                "size_bytes": size,
                "sha256": file_hash(full_path),
            }
            # Only preview certain file types
            if fn.endswith((".py", ".yaml", ".yml", ".txt", ".md")):
                info["preview"] = summarize_file(full_path)[:max_preview]
            project_summary.append(info)
    return project_summary

if __name__ == "__main__":
    root = os.path.abspath(".")  # run from project root
    report = build_report(root)
    with open("project_report.yaml", "w", encoding="utf-8") as f:
        yaml.dump(report, f, sort_keys=False, allow_unicode=True)
    print("Report generated: project_report.yaml")
