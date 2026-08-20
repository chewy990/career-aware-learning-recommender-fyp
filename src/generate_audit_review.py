from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERAL_AUDIT = ROOT / "outputs" / "phase5_run" / "relevance_audit_blinded.csv"
TARGETED_AUDIT = (
    ROOT
    / "outputs"
    / "prerequisite_experiment_run"
    / "prerequisite_experiment_audit_blinded.csv"
)
OUTPUT_FILE = ROOT / "outputs" / "audit_review.html"
FORBIDDEN_FIELDS = {
    "current_label",
    "experiment_role",
    "profile_id",
    "resource_id",
    "model",
    "score",
    "rank",
}


def generate_audit_review_html(
    general_audit: Path = GENERAL_AUDIT,
    targeted_audit: Path = TARGETED_AUDIT,
    output_file: Path = OUTPUT_FILE,
) -> None:
    """Render the standalone author-audit interface from the maintained template."""

    review_sets = [
        {
            "id": "general",
            "label": "General review",
            "description": "40 pathway-balanced relevance cases",
            "rows": _read_blinded_rows(general_audit),
        },
        {
            "id": "targeted",
            "label": "Prerequisite changes",
            "description": "10 removed and replacement cases",
            "rows": _read_blinded_rows(targeted_audit),
        },
    ]
    payload = json.dumps(
        review_sets,
        ensure_ascii=False,
        separators=(",", ":"),
    ).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    template = (ROOT / "src" / "audit_review_template.html").read_text(
        encoding="utf-8"
    )
    html = template.replace("__AUDIT_DATA__", payload)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(html, encoding="utf-8")


def _read_blinded_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    if not rows:
        raise ValueError(f"Audit sheet is empty: {path}")
    exposed = FORBIDDEN_FIELDS & set(rows[0])
    if exposed:
        raise ValueError(
            f"Audit sheet exposes hidden fields: {', '.join(sorted(exposed))}"
        )
    return rows




if __name__ == "__main__":
    generate_audit_review_html()
