from pathlib import Path


def get_content_root(active_pack: str | None) -> Path:
    """Resolve the root directory for content files based on active_pack.

    - If active_pack is provided and packs/<active_pack> exists, return that path.
    - Otherwise, fall back to the legacy data/ directory.
    """
    root = Path.cwd()
    if active_pack:
        candidate = root / "packs" / active_pack
        if candidate.is_dir():
            return candidate
    return root / "data"



