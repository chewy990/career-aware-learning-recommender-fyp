"""Own prerequisite experiment reporting responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

import hashlib
from pathlib import Path


def _write_summary(
    findings: tuple[dict[str, str], ...],
    figures: tuple[str, ...],
    output_dir: Path,
) -> None:
    figure_lookup = {
        findings[0]["title"]: figures[2],
        findings[1]["title"]: figures[1],
        findings[2]["title"]: figures[1],
        findings[3]["title"]: figures[0],
        findings[4]["title"]: figures[2],
        findings[5]["title"]: figures[2],
    }
    sections = []
    for finding in findings:
        sections.append(
            f"## {finding['title']}\n\n"
            f"![{finding['title']}]({figure_lookup[finding['title']]})\n\n"
            f"**Finding:** {finding['finding']}\n\n"
            f"**Implication:** {finding['implication']}\n"
        )
    text = (
        "# Hard-Prerequisite Eligibility Experiment\n\n"
        "The experimental variant changes only candidate eligibility: a resource "
        "is ranked only when every prerequisite is completed or recorded at skill "
        "level 1 or above. Hybrid weights, scores, source data, relevance labels, "
        "and the baseline are unchanged. NDCG@5 is primary; Precision@5 and "
        "Recall@5 complete the three-test Holm family. Results remain limited to "
        "11 curated profiles.\n\n"
        + "\n".join(sections)
    )
    (output_dir / "prerequisite_experiment_summary.md").write_text(
        text,
        encoding="utf-8",
    )

def _derived_seed(base_seed: int, metric: str) -> int:
    payload = f"{base_seed}:hard_prerequisite:{metric}:5".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")
