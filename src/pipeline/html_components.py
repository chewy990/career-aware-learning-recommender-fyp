"""Render deterministic HTML fragments for the pipeline report.

These helpers format verified results only; they must not calculate metrics.
"""

from __future__ import annotations

from html import escape

from edu_recommender.eda import EdaResult
from edu_recommender.evaluation import EvaluationResult
from edu_recommender.models import Recommendation
from edu_recommender.prerequisite_experiment import PrerequisiteExperimentResult
from edu_recommender.robustness import RobustnessResult
from edu_recommender.statistical_comparison import StatisticalComparisonResult
from pipeline.config import TOP_K


def _metrics_table(metric_rows: list[dict[str, object]]) -> str:
    rows = "\n".join(
        "<tr>"
        f"<td>{row['model']}</td>"
        f"<td>{row['precision_at_k']}</td>"
        f"<td>{row['recall_at_k']}</td>"
        f"<td>{row['ndcg_at_k']}</td>"
        "</tr>"
        for row in metric_rows
    )
    return (
        "<table><thead><tr><th>Model</th><th>Precision@K</th><th>Recall@K</th><th>NDCG@K</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
    )


def _detailed_metrics_table(
    metric_rows: tuple[dict[str, object], ...],
) -> str:
    rows = "\n".join(
        "<tr>"
        f"<td>{row['model']}</td>"
        f"<td>{row['k']}</td>"
        f"<td>{row['profile_count']}</td>"
        f"<td>{row['precision_at_k']}</td>"
        f"<td>{row['recall_at_k']}</td>"
        f"<td>{row['ndcg_at_k']}</td>"
        "</tr>"
        for row in metric_rows
    )
    return (
        "<table><thead><tr><th>Model</th><th>K</th><th>Profiles</th>"
        "<th>Precision@K</th><th>Recall@K</th><th>NDCG@K</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
    )


def _svg_bar_chart(metric_rows: list[dict[str, object]]) -> str:
    width = 620
    height = 240
    baseline_y = 190
    bar_width = 110
    gap = 60
    max_bar_height = 150
    bars = []
    for index, row in enumerate(metric_rows):
        value = float(row["ndcg_at_k"])
        bar_height = value * max_bar_height
        x = 70 + index * (bar_width + gap)
        y = baseline_y - bar_height
        bars.append(
            f'<rect x="{x}" y="{y:.1f}" width="{bar_width}" height="{bar_height:.1f}" fill="#2f80ed" />'
            f'<text class="bar-label" x="{x}" y="{baseline_y + 18}">{row["model"]}</text>'
            f'<text class="bar-label" x="{x}" y="{y - 8:.1f}">{value:.3f}</text>'
        )
    return (
        f'<svg class="chart" width="{width}" height="{height}" role="img" '
        'aria-label="NDCG comparison chart">'
        f'<line x1="50" y1="{baseline_y}" x2="560" y2="{baseline_y}" stroke="#566573" />'
        + "".join(bars)
        + "</svg>"
    )


def _hybrid_examples(recommendations_by_profile: dict[str, list[Recommendation]]) -> str:
    blocks = []
    for profile_id, recommendations in recommendations_by_profile.items():
        rows = "\n".join(
            "<tr>"
            f"<td>{recommendation.rank}</td>"
            f"<td>{recommendation.title}</td>"
            f"<td>{recommendation.provider}</td>"
            f"<td>{recommendation.score}</td>"
            f"<td>{recommendation.explanation}</td>"
            "</tr>"
            for recommendation in recommendations[:TOP_K]
        )
        blocks.append(
            f"<h3>{profile_id}</h3>"
            "<table><thead><tr><th>Rank</th><th>Resource</th><th>Provider</th><th>Score</th><th>Explanation</th></tr></thead>"
            f"<tbody>{rows}</tbody></table>"
        )
    return "\n".join(blocks)


def _eda_findings_table(eda_result: EdaResult) -> str:
    rows = "\n".join(
        "<tr>"
        f"<td>{escape(finding['title'])}</td>"
        f"<td>{escape(finding['finding'])}</td>"
        f"<td>{escape(finding['implication'])}</td>"
        "</tr>"
        for finding in eda_result.findings
    )
    return (
        "<table><thead><tr><th>Analysis</th><th>Finding</th>"
        f"<th>Implication</th></tr></thead><tbody>{rows}</tbody></table>"
    )


def _eda_figure_grid(eda_result: EdaResult) -> str:
    selected = {
        "figures/resources_by_pathway.png",
        "figures/resources_by_provider.png",
        "figures/skill_frequency.png",
        "figures/relevance_by_profile.png",
    }
    figures = "\n".join(
        "<figure>"
        f'<img src="{escape(finding["figure"])}" '
        f'alt="{escape(finding["title"])}">'
        f"<figcaption>{escape(finding['title'])}</figcaption>"
        "</figure>"
        for finding in eda_result.findings
        if finding["figure"] in selected
    )
    return f'<div class="figure-grid">{figures}</div>'


def _evaluation_findings_table(
    evaluation_result: EvaluationResult,
) -> str:
    rows = "\n".join(
        "<tr>"
        f"<td>{escape(finding['title'])}</td>"
        f"<td>{escape(finding['finding'])}</td>"
        f"<td>{escape(finding['implication'])}</td>"
        "</tr>"
        for finding in evaluation_result.findings
    )
    return (
        "<table><thead><tr><th>Analysis</th><th>Finding</th>"
        f"<th>Implication</th></tr></thead><tbody>{rows}</tbody></table>"
    )


def _evaluation_figure_grid(
    evaluation_result: EvaluationResult,
) -> str:
    selected = (
        "figures/phase3_metrics_by_k.png",
        "figures/phase3_pathway_ndcg_at_5.png",
        "figures/phase3_uncertainty_ndcg_at_5.png",
        "figures/phase3_diagnostics_at_5.png",
    )
    captions = {
        "figures/phase3_metrics_by_k.png": "Model performance across K",
        "figures/phase3_pathway_ndcg_at_5.png": "Pathway NDCG@5",
        "figures/phase3_uncertainty_ndcg_at_5.png": "Profile-bootstrap NDCG@5 intervals",
        "figures/phase3_diagnostics_at_5.png": "Recommendation-quality diagnostics at K=5",
    }
    figures = "\n".join(
        "<figure>"
        f'<img src="{escape(filename)}" alt="{escape(captions[filename])}">'
        f"<figcaption>{escape(captions[filename])}</figcaption>"
        "</figure>"
        for filename in selected
        if filename in evaluation_result.output_files
    )
    return f'<div class="figure-grid">{figures}</div>'


def _robustness_findings_table(
    robustness_result: RobustnessResult,
) -> str:
    rows = "\n".join(
        "<tr>"
        f"<td>{escape(finding['title'])}</td>"
        f"<td>{escape(finding['finding'])}</td>"
        f"<td>{escape(finding['implication'])}</td>"
        "</tr>"
        for finding in robustness_result.findings
    )
    return (
        "<table><thead><tr><th>Analysis</th><th>Finding</th>"
        f"<th>Implication</th></tr></thead><tbody>{rows}</tbody></table>"
    )


def _robustness_figure_grid(
    robustness_result: RobustnessResult,
) -> str:
    selected = (
        "figures/phase4_ablation_ndcg_at_5.png",
        "figures/phase4_weight_sensitivity_ndcg_at_5.png",
        "figures/phase4_seeded_configurations_ndcg_at_5.png",
        "figures/phase4_failure_cases.png",
    )
    captions = {
        "figures/phase4_ablation_ndcg_at_5.png": "Hybrid component ablation at K=5",
        "figures/phase4_weight_sensitivity_ndcg_at_5.png": "One-at-a-time weight sensitivity",
        "figures/phase4_seeded_configurations_ndcg_at_5.png": "Seeded bounded weight configurations",
        "figures/phase4_failure_cases.png": "Flagged hybrid failure cases",
    }
    figures = "\n".join(
        "<figure>"
        f'<img src="{escape(filename)}" alt="{escape(captions[filename])}">'
        f"<figcaption>{escape(captions[filename])}</figcaption>"
        "</figure>"
        for filename in selected
        if filename in robustness_result.output_files
    )
    return f'<div class="figure-grid">{figures}</div>'


def _statistical_findings_table(
    statistical_result: StatisticalComparisonResult,
) -> str:
    rows = "\n".join(
        "<tr>"
        f"<td>{escape(finding['title'])}</td>"
        f"<td>{escape(finding['finding'])}</td>"
        f"<td>{escape(finding['implication'])}</td>"
        "</tr>"
        for finding in statistical_result.findings
    )
    return (
        "<table><thead><tr><th>Analysis</th><th>Finding</th>"
        f"<th>Implication</th></tr></thead><tbody>{rows}</tbody></table>"
    )


def _statistical_figure_grid(
    statistical_result: StatisticalComparisonResult,
) -> str:
    selected = (
        "figures/phase5_paired_ndcg_at_5.png",
        "figures/phase5_mean_differences.png",
        "figures/phase5_holm_adjusted_p_values.png",
        "figures/phase5_win_tie_loss_at_5.png",
    )
    captions = {
        "figures/phase5_paired_ndcg_at_5.png": "Paired profile-level NDCG@5",
        "figures/phase5_mean_differences.png": "Paired mean differences and intervals",
        "figures/phase5_holm_adjusted_p_values.png": "Holm-adjusted exact permutation p-values",
        "figures/phase5_win_tie_loss_at_5.png": "Profile-level wins, ties, and losses",
    }
    figures = "\n".join(
        "<figure>"
        f'<img src="{escape(filename)}" alt="{escape(captions[filename])}">'
        f"<figcaption>{escape(captions[filename])}</figcaption>"
        "</figure>"
        for filename in selected
        if filename in statistical_result.output_files
    )
    return f'<div class="figure-grid">{figures}</div>'


def _prerequisite_findings_table(
    prerequisite_result: PrerequisiteExperimentResult,
) -> str:
    rows = "\n".join(
        "<tr>"
        f"<td>{escape(finding['title'])}</td>"
        f"<td>{escape(finding['finding'])}</td>"
        f"<td>{escape(finding['implication'])}</td>"
        "</tr>"
        for finding in prerequisite_result.findings
    )
    return (
        "<table><thead><tr><th>Analysis</th><th>Finding</th>"
        f"<th>Implication</th></tr></thead><tbody>{rows}</tbody></table>"
    )


def _prerequisite_figure_grid(
    prerequisite_result: PrerequisiteExperimentResult,
) -> str:
    selected = (
        "figures/prerequisite_experiment_metrics_at_5.png",
        "figures/prerequisite_experiment_paired_ndcg_at_5.png",
        "figures/prerequisite_experiment_diagnostics_at_5.png",
    )
    captions = {
        "figures/prerequisite_experiment_metrics_at_5.png": "Ranking metrics at K=5",
        "figures/prerequisite_experiment_paired_ndcg_at_5.png": "Paired profile-level NDCG@5",
        "figures/prerequisite_experiment_diagnostics_at_5.png": "Recommendation-quality diagnostics at K=5",
    }
    figures = "\n".join(
        "<figure>"
        f'<img src="{escape(filename)}" alt="{escape(captions[filename])}">'
        f"<figcaption>{escape(captions[filename])}</figcaption>"
        "</figure>"
        for filename in selected
        if filename in prerequisite_result.output_files
    )
    return f'<div class="figure-grid">{figures}</div>'

