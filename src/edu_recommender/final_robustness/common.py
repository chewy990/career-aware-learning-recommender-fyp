"""Shared deterministic artifact helpers for final robustness experiments."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    """Return one file's SHA-256 digest."""

    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    """Write stable formatted JSON."""

    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_manifest(
    output_dir: Path,
    experiment: str,
    input_paths: list[Path],
    code_paths: list[Path],
) -> None:
    """Hash exact experiment inputs, source files, and generated outputs."""

    project_root = Path(__file__).resolve().parents[3]
    manifest = {
        "experiment": experiment,
        "schema_version": "1",
        "input_sha256": {
            path.relative_to(project_root).as_posix(): sha256(path)
            for path in sorted(set(input_paths))
        },
        "code_sha256": {
            path.relative_to(project_root).as_posix(): sha256(path)
            for path in sorted(set(code_paths))
        },
        "output_sha256": {
            path.name: sha256(path)
            for path in sorted(output_dir.iterdir())
            if path.is_file() and path.name != "manifest.json"
        },
    }
    write_json(output_dir / "manifest.json", manifest)
