from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from edu_recommender.label_audit import (
    AUTHOR_AUDIT_VERSION,
    analyse_author_audit,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BLINDED = ROOT / "outputs" / "phase5_run" / "relevance_audit_blinded.csv"
DEFAULT_KEY = ROOT / "outputs" / "phase5_run" / "relevance_audit_key.csv"
DEFAULT_OUTPUT = ROOT / "outputs" / "author_audit_run"
AUDIT_CODE_FILES = tuple(
    path.relative_to(ROOT).as_posix()
    for path in sorted((ROOT / "src" / "edu_recommender" / "label_audit").glob("*.py"))
) + ("src/run_author_audit.py",)


def main() -> int:
    """Run this module's supported command-line or application entry point."""

    parser = argparse.ArgumentParser(
        description="Validate and analyse the completed blinded author audit."
    )
    parser.add_argument("completed_csv", type=Path)
    parser.add_argument("--blinded", type=Path, default=DEFAULT_BLINDED)
    parser.add_argument("--key", type=Path, default=DEFAULT_KEY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    try:
        run_author_audit(
            completed_path=args.completed_csv.resolve(),
            blinded_path=args.blinded.resolve(),
            key_path=args.key.resolve(),
            output_dir=args.output_dir.resolve(),
        )
    except ValueError as error:
        print(f"Author audit validation failed: {error}", file=sys.stderr)
        return 1
    return 0


def run_author_audit(
    completed_path: Path,
    blinded_path: Path,
    key_path: Path,
    output_dir: Path,
) -> None:
    """Run run author audit using the maintained project contracts."""

    if not completed_path.is_file():
        raise ValueError(f"Missing completed audit: {completed_path}")
    input_dir = output_dir / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    archived_completed = input_dir / "relevance_audit_completed.csv"
    if completed_path != archived_completed:
        shutil.copyfile(completed_path, archived_completed)

    result = analyse_author_audit(
        archived_completed,
        blinded_path,
        key_path,
        output_dir,
    )
    input_files = {
        "completed_author_export": {
            "path": _display_path(archived_completed),
            "sha256": _sha256(archived_completed),
        },
        "generated_blinded_sheet": {
            "path": _display_path(blinded_path),
            "sha256": _sha256(blinded_path),
        },
        "generated_hidden_key": {
            "path": _display_path(key_path),
            "sha256": _sha256(key_path),
        },
    }
    code_files = {
        path: {"sha256": _sha256(ROOT / path)}
        for path in AUDIT_CODE_FILES
    }
    reproducibility_payload = {
        "author_audit_version": AUTHOR_AUDIT_VERSION,
        "audit_type": "blinded_author_consistency_audit",
        "input_files": input_files,
        "code_files": code_files,
    }
    fingerprint = hashlib.sha256(
        json.dumps(
            reproducibility_payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    manifest = {
        "schema_version": 1,
        "run_id": fingerprint[:16],
        "generated_at_utc": datetime.now(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
        "configuration_fingerprint_sha256": fingerprint,
        **reproducibility_payload,
        "result": {
            "item_count": result.item_count,
            "definite_count": result.definite_count,
            "uncertain_count": result.uncertain_count,
            "agreement_count": result.agreement_count,
            "disagreement_count": result.disagreement_count,
            "agreement_rate": round(result.agreement_rate, 4),
        },
        "output_files": {
            filename: {"sha256": _sha256(output_dir / filename)}
            for filename in result.output_files
        },
        "manifest_filename": "run_manifest.json",
        "python_version": sys.version.split()[0],
    }
    (output_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"Author audit verified: {result.agreement_count}/"
        f"{result.definite_count} agreements "
        f"({result.agreement_rate:.1%}); "
        f"{result.disagreement_count} disagreements."
    )
    print(f"Run manifest: {output_dir / 'run_manifest.json'}")


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
