import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SUPPORTED_SUFFIXES = {".md", ".markdown", ".txt"}


@dataclass(frozen=True)
class SourceDocument:
    id: str
    path: Path
    text: str
    metadata: dict[str, Any]


def load_documents(path: Path) -> list[SourceDocument]:
    files = _iter_supported_files(path)
    documents: list[SourceDocument] = []
    for file_path in files:
        text = file_path.read_text(encoding="utf-8")
        source_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        documents.append(
            SourceDocument(
                id=source_hash,
                path=file_path,
                text=text,
                metadata={
                    "source_path": str(file_path),
                    "source_name": file_path.name,
                    "source_hash": source_hash,
                    "suffix": file_path.suffix.lower(),
                },
            )
        )
    return documents


def _iter_supported_files(path: Path) -> list[Path]:
    if not path.exists():
        msg = f"Path does not exist: {path}"
        raise FileNotFoundError(msg)

    if path.is_file():
        return [path] if path.suffix.lower() in SUPPORTED_SUFFIXES else []

    return sorted(
        file_path
        for file_path in path.rglob("*")
        if file_path.is_file()
        and file_path.suffix.lower() in SUPPORTED_SUFFIXES
        and not any(part.startswith(".") for part in file_path.parts)
    )
