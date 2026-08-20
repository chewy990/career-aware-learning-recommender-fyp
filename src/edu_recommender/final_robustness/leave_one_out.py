"""Leave-one-profile-out stability analysis for the gated paired difference."""

from __future__ import annotations

import csv
from pathlib import Path
from statistics import mean

from edu_recommender.data import write_rows

from .common import write_json, write_manifest


def run_leave_one_out_experiment(
    profile_differences_path: Path,
    protocol_path: Path,
    output_dir: Path,
    runner_path: Path,
) -> None:
    """Recalculate the paired mean after omitting each profile exactly once."""

    with profile_differences_path.open(newline="", encoding="utf-8") as file:
        source_rows = list(csv.DictReader(file))
    if len(source_rows) != 11:
        raise ValueError("Expected exactly 11 paired profile differences")
    differences = {
        row["profile_id"]: float(row["difference"])
        for row in source_rows
    }
    full_mean = mean(differences.values())
    rows = []
    for omitted_profile in sorted(differences):
        retained = [
            value
            for profile_id, value in differences.items()
            if profile_id != omitted_profile
        ]
        rows.append(
            {
                "omitted_profile_id": omitted_profile,
                "omitted_pathway": next(
                    row["pathway"]
                    for row in source_rows
                    if row["profile_id"] == omitted_profile
                ),
                "omitted_difference": round(differences[omitted_profile], 6),
                "retained_profile_count": len(retained),
                "leave_one_out_mean_difference": round(mean(retained), 6),
                "change_from_full_mean": round(mean(retained) - full_mean, 6),
                "direction_positive": mean(retained) > 0,
            }
        )
    minimum = min(rows, key=lambda row: float(row["leave_one_out_mean_difference"]))
    maximum = max(rows, key=lambda row: float(row["leave_one_out_mean_difference"]))
    decision = {
        "criterion": "every leave-one-profile-out mean difference stays positive",
        "passed": all(bool(row["direction_positive"]) for row in rows),
        "full_mean_difference": round(full_mean, 6),
        "minimum_leave_one_out_mean": minimum["leave_one_out_mean_difference"],
        "minimum_when_omitting": minimum["omitted_profile_id"],
        "maximum_leave_one_out_mean": maximum["leave_one_out_mean_difference"],
        "maximum_when_omitting": maximum["omitted_profile_id"],
        "models_refit_or_reranked": False,
    }

    output_dir.mkdir(parents=True, exist_ok=False)
    write_rows(
        output_dir / "leave_one_profile_out.csv",
        list(rows[0]),
        rows,
    )
    write_json(output_dir / "decision.json", decision)
    write_json(
        output_dir / "protocol.json",
        {
            "version": "1",
            "frozen_protocol": "docs/final_robustness_protocol.md",
            "source": profile_differences_path.as_posix(),
            "stability_rule": "all eleven omitted-profile means remain positive",
        },
    )
    write_manifest(
        output_dir,
        "leave_one_profile_out_stability",
        [profile_differences_path, protocol_path],
        [Path(__file__).resolve(), Path(__file__).with_name("common.py"), runner_path.resolve()],
    )
