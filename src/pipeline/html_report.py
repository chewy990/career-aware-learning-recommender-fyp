"""Write the deterministic human-readable pipeline report.

Report presentation is separate from scientific CSV/figure generation. It must
not mutate evaluation results or alter output ordering.
"""

from __future__ import annotations

from pathlib import Path

from edu_recommender.eda import EdaResult
from edu_recommender.evaluation import EvaluationResult
from edu_recommender.models import Recommendation
from edu_recommender.prerequisite_experiment import PrerequisiteExperimentResult
from edu_recommender.robustness import RobustnessResult
from edu_recommender.statistical_comparison import StatisticalComparisonResult
from pipeline.config import TOP_K
from pipeline.html_components import (
    _detailed_metrics_table,
    _eda_figure_grid,
    _eda_findings_table,
    _evaluation_figure_grid,
    _evaluation_findings_table,
    _hybrid_examples,
    _metrics_table,
    _prerequisite_figure_grid,
    _prerequisite_findings_table,
    _robustness_figure_grid,
    _robustness_findings_table,
    _statistical_figure_grid,
    _statistical_findings_table,
    _svg_bar_chart,
)


def _write_html_report(
    evaluation_result: EvaluationResult,
    robustness_result: RobustnessResult,
    statistical_result: StatisticalComparisonResult,
    prerequisite_result: PrerequisiteExperimentResult,
    recommendations_by_model: dict[str, dict[str, list[Recommendation]]],
    eda_result: EdaResult,
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    k5_rows = [
        row
        for row in evaluation_result.summary_rows
        if int(row["k"]) == TOP_K
    ]
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Educational Recommender Evaluation Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; line-height: 1.45; color: #17202a; }}
    h1, h2 {{ color: #12355b; }}
    table {{ border-collapse: collapse; margin: 16px 0 28px; width: 100%; }}
    th, td {{ border: 1px solid #d5dde5; padding: 8px; text-align: left; vertical-align: top; }}
    th {{ background: #edf3f8; }}
    .chart {{ margin: 16px 0 28px; }}
    .bar-label {{ font-size: 12px; fill: #17202a; }}
    .figure-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 20px; }}
    .figure-grid figure {{ margin: 0; }}
    .figure-grid img {{ display: block; width: 100%; height: auto; border: 1px solid #d5dde5; }}
    .figure-grid figcaption {{ margin: 6px 0 20px; font-size: 13px; color: #425466; }}
  </style>
</head>
<body>
  <h1>Career-Aware Educational Content Recommender</h1>
  <p>This report compares the popularity baseline, content-based recommender, and hybrid career-aware recommender using the sample learner profiles and prototype relevance judgements.</p>
  <h2>Phase 2 Exploratory Data Analysis</h2>
  <p>These findings are generated from the validated source CSVs. Pathway relevance counts overlap because one resource can support multiple pathways.</p>
  {_eda_findings_table(eda_result)}
  {_eda_figure_grid(eda_result)}
  <h2>Evaluation Metrics at K={TOP_K}</h2>
  {_metrics_table(k5_rows)}
  <h2>NDCG@{TOP_K} Comparison</h2>
  {_svg_bar_chart(k5_rows)}
  <h2>Phase 3 Broader Offline Evaluation</h2>
  <p>Metrics are traced to profile and pathway rows at K=3, 5, and 10. Seeded bootstrap intervals describe variation across the 11 curated profiles, not the real learner population.</p>
  {_evaluation_findings_table(evaluation_result)}
  {_evaluation_figure_grid(evaluation_result)}
  <h2>Detailed Metrics Across K</h2>
  {_detailed_metrics_table(evaluation_result.summary_rows)}
  <h2>Phase 4 Hybrid Robustness And Explainability</h2>
  <p>The ablations and weight variants below are diagnostic experiments against the unchanged baseline. No variant is selected or written back into the recommender.</p>
  {_robustness_findings_table(robustness_result)}
  {_robustness_figure_grid(robustness_result)}
  <h2>Phase 5 Paired Statistical Comparison</h2>
  <p>Differences are paired within the same 11 curated profiles. Exact sign-flip tests are primary, signed-rank tests are a sensitivity check, and Holm correction covers all 18 planned comparisons. These results do not establish population-wide superiority.</p>
  {_statistical_findings_table(statistical_result)}
  {_statistical_figure_grid(statistical_result)}
  <h2>Hard-Prerequisite Eligibility Experiment</h2>
  <p>This diagnostic variant changes only candidate eligibility. Source data, relevance labels, hybrid weights, and the baseline remain unchanged, and the result does not automatically replace the production model.</p>
  {_prerequisite_findings_table(prerequisite_result)}
  {_prerequisite_figure_grid(prerequisite_result)}
  <h2>Hybrid Recommendation Examples</h2>
  {_hybrid_examples(recommendations_by_model["hybrid"])}
</body>
</html>
"""
    (output_dir / "report.html").write_text(html, encoding="utf-8")

