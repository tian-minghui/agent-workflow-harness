from __future__ import annotations

import os
import uuid
from pathlib import Path


def atomic_write_text(path: Path, content: str) -> None:
    """Replace a file through a unique temporary file so readers see one complete value."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, path)
