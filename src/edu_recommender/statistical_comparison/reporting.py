"""Own statistical comparison reporting responsibilities.

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
        findings[0]["title"]: figures[1],
        findings[1]["title"]: figures[1],
        findings[2]["title"]: figures[2],
        findings[3]["title"]: figures[3],
        findings[4]["title"]: figures[0],
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
        "# Phase 5 Paired Statistical Comparison\n\n"
        "The hybrid is compared with each baseline using differences calculated "
        "within the same 11 profiles. Exact sign-flip permutation tests are the "
        "primary tests; exact signed-rank tests are a sensitivity check. Holm "
        "correction covers all 18 planned model-metric-K comparisons. These "
        "results describe the curated evaluation set and do not establish "
        "population-wide performance.\n\n"
        + "\n".join(sections)
    )
    (output_dir / "phase5_summary.md").write_text(
        text,
        encoding="utf-8",
    )

def _derived_seed(
    base_seed: int,
    comparison: str,
    metric: str,
    k: int,
) -> int:
    payload = f"{base_seed}:{comparison}:{metric}:{k}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")

def _stable_sort_key(
    seed: int,
    *parts: str,
) -> str:
    payload = ":".join((str(seed), *parts)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()

def _metric_label(metric: str) -> str:
    return {
        "precision_at_k": "Precision difference",
        "recall_at_k": "Recall difference",
        "ndcg_at_k": "NDCG difference",
    }[metric]

def _metric_short(metric: str) -> str:
    return {
        "precision_at_k": "Precision",
        "recall_at_k": "Recall",
        "ndcg_at_k": "NDCG",
    }[metric]
