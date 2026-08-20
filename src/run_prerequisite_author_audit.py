from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from edu_recommender.prerequisite_audit import (
    PREREQUISITE_AUTHOR_AUDIT_VERSION,
    analyse_prerequisite_author_audit,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BLINDED = (
    ROOT
    / "outputs"
    / "prerequisite_experiment_run"
    / "prerequisite_experiment_audit_blinded.csv"
)
DEFAULT_KEY = (
    ROOT
    / "outputs"
    / "prerequisite_experiment_run"
    / "prerequisite_experiment_audit_key.csv"
)
DEFAULT_OUTPUT = ROOT / "outputs" / "prerequisite_author_audit_run"


def main() -> int:
    """Run this module's supported command-line or application entry point."""

    parser = argparse.ArgumentParser(
        description="Validate and analyse the targeted prerequisite audit."
    )
    parser.add_argument("completed_csv", type=Path)
    parser.add_argument("--blinded", type=Path, default=DEFAULT_BLINDED)
    parser.add_argument("--key", type=Path, default=DEFAULT_KEY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    try:
        run_prerequisite_author_audit(
            args.completed_csv.resolve(),
            args.blinded.resolve(),
            args.key.resolve(),
            args.output_dir.resolve(),
        )
    except ValueError as error:
        print(
            f"Prerequisite author audit validation failed: {error}",
            file=sys.stderr,
        )
        return 1
    return 0


def run_prerequisite_author_audit(
    completed_path: Path,
    blinded_path: Path,
    key_path: Path,
    output_dir: Path,
) -> None:
    """Run run prerequisite author audit using the maintained project contracts."""

    if not completed_path.is_file():
        raise ValueError(f"Missing completed audit: {completed_path}")
    input_dir = output_dir / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    archived = input_dir / "prerequisite_audit_completed.csv"
    if completed_path != archived:
        shutil.copyfile(completed_path, archived)
    result = analyse_prerequisite_author_audit(
        archived,
        blinded_path,
        key_path,
        output_dir,
    )
    inputs = {
        "completed_author_export": _file_record(archived),
        "generated_blinded_sheet": _file_record(blinded_path),
        "generated_hidden_key": _file_record(key_path),
    }
    code_paths = (
        "src/edu_recommender/prerequisite_audit.py",
        "src/run_prerequisite_author_audit.py",
    )
    code = {
        path: {"sha256": _sha256(ROOT / path)}
        for path in code_paths
    }
    payload = {
        "prerequisite_author_audit_version": (
            PREREQUISITE_AUTHOR_AUDIT_VERSION
        ),
        "audit_type": "blinded_targeted_prerequisite_author_audit",
        "input_files": inputs,
        "code_files": code,
    }
    fingerprint = hashlib.sha256(
        json.dumps(
            payload,
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
        **payload,
        "result": {
            "item_count": result.item_count,
            "definite_count": result.definite_count,
            "uncertain_count": result.uncertain_count,
            "agreement_count": result.agreement_count,
            "removed_relevant_count": result.removed_relevant_count,
            "replacement_relevant_count": result.replacement_relevant_count,
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
        "Targeted prerequisite audit verified: "
        f"{result.removed_relevant_count}/5 removed and "
        f"{result.replacement_relevant_count}/5 replacements judged relevant."
    )
    print(f"Run manifest: {output_dir / 'run_manifest.json'}")


def _file_record(path: Path) -> dict[str, str]:
    try:
        displayed = path.relative_to(ROOT).as_posix()
    except ValueError:
        displayed = str(path)
    return {"path": displayed, "sha256": _sha256(path)}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
