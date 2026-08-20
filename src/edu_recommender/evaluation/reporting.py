"""Own evaluation reporting responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from pathlib import Path
from statistics import mean

from .contracts import MODEL_ORDER


def _write_evaluation_summary(
    findings: tuple[dict[str, str], ...],
    figure_files: tuple[str, ...],
    output_dir: Path,
) -> None:
    figure_lookup = {
        "The hybrid remains the strongest model at K=5": figure_files[0],
        "The overall estimate still has profile-level uncertainty": figure_files[3],
        "Pathway performance is not uniform": figure_files[1],
        "The hybrid covers only part of the full catalogue": figure_files[4],
        "Suitability diagnostics provide a second evaluation layer": figure_files[4],
    }
    sections = []
    for finding in findings:
        figure = figure_lookup[finding["title"]]
        sections.append(
            f"## {finding['title']}\n\n"
            f"![{finding['title']}]({figure})\n\n"
            f"**Finding:** {finding['finding']}\n\n"
            f"**Implication:** {finding['implication']}\n"
        )
    text = (
        "# Phase 3 Broader Offline Evaluation\n\n"
        "All metrics are generated from the fixed validated catalogue, 11 curated "
        "profiles, and their relevance judgements. Bootstrap intervals resample "
        "profile-level metric rows with a recorded seed; they do not represent "
        "uncertainty for the real learner population.\n\n"
        + "\n".join(sections)
    )
    (output_dir / "phase3_summary.md").write_text(text, encoding="utf-8")

def _validate_k_values(k_values: tuple[int, ...]) -> None:
    if not k_values or any(k <= 0 for k in k_values):
        raise ValueError("k_values must contain positive integers")
    if len(set(k_values)) != len(k_values):
        raise ValueError("k_values must not contain duplicates")

def _ordered_models(
    recommendations_by_model: dict[str, object],
) -> list[str]:
    return [
        model
        for model in MODEL_ORDER
        if model in recommendations_by_model
    ] + sorted(set(recommendations_by_model) - set(MODEL_ORDER))

def _models_from_rows(rows: list[dict[str, object]]) -> list[str]:
    return _ordered_models({str(row["model"]): None for row in rows})

def _rounded_mean(values: list[float]) -> float:
    return round(mean(values), 4) if values else 0.0

def _humanise(value: str) -> str:
    acronyms = {"ml": "ML", "sql": "SQL", "api": "API", "apis": "APIs"}
    return " ".join(
        acronyms.get(part, part.capitalize())
        for part in value.split("_")
    )
