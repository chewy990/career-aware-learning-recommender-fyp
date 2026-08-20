"""Own eda findings responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

import statistics

from edu_recommender.data import Resource

from .tables import _dimension_rows, _label, _percentage


def _build_findings(
    tables: dict[str, list[dict[str, object]]],
    resources: list[Resource],
) -> tuple[dict[str, str], ...]:
    distributions = tables["resource_distribution.csv"]
    resource_count = len(resources)

    provider_rows = _dimension_rows(distributions, "provider")
    top_provider = provider_rows[0]
    top_three_count = sum(int(row["count"]) for row in provider_rows[:3])
    format_rows = _dimension_rows(distributions, "format")
    top_format = format_rows[0]
    difficulty = {
        str(row["category"]): row
        for row in _dimension_rows(distributions, "difficulty")
    }
    duration_rows = _dimension_rows(distributions, "duration_band")
    largest_duration_band = max(
        duration_rows, key=lambda row: int(row["count"])
    )
    cost_rows = {
        str(row["category"]): row
        for row in _dimension_rows(distributions, "cost")
    }
    pathway_positive = _dimension_rows(
        distributions, "pathway_positive_relevance"
    )
    highest_pathway = max(pathway_positive, key=lambda row: int(row["count"]))
    lowest_pathway = min(pathway_positive, key=lambda row: int(row["count"]))
    skill_rows = tables["skill_frequency.csv"]
    top_skill = skill_rows[0]
    least_skill_count = min(int(row["resource_count"]) for row in skill_rows)
    least_skills = [
        _label(str(row["skill"]))
        for row in skill_rows
        if int(row["resource_count"]) == least_skill_count
    ]
    pair = tables["skill_cooccurrence.csv"][0]
    coverage_rows = tables["pathway_skill_coverage.csv"]
    limited_coverage = [
        row for row in coverage_rows if row["coverage_status"] != "available"
    ]
    limited_cell_text = (
        "1 cell has"
        if len(limited_coverage) == 1
        else f"{len(limited_coverage)} cells have"
    )
    relevance_counts = [
        int(row["relevant_count"]) for row in tables["relevance_summary.csv"]
    ]

    findings = (
        {
            "figure": "figures/resources_by_pathway.png",
            "title": "Pathway relevance coverage overlaps substantially",
            "finding": (
                f"{_label(str(highest_pathway['category']))} has "
                f"{highest_pathway['count']} resources with positive relevance, while "
                f"{_label(str(lowest_pathway['category']))} has "
                f"{lowest_pathway['count']}. Counts overlap because one resource may "
                "support several pathways."
            ),
            "implication": (
                "Pathway-level model results should be interpreted alongside catalogue "
                "coverage rather than assuming equal candidate pools."
            ),
        },
        {
            "figure": "figures/resources_by_provider.png",
            "title": "The catalogue is concentrated in three providers",
            "finding": (
                f"{top_provider['category']} contributes {top_provider['count']} of "
                f"{resource_count} resources ({top_provider['percentage']}%). The top "
                f"three providers contribute {top_three_count} "
                f"({_percentage(top_three_count, resource_count)}%)."
            ),
            "implication": (
                "Later diversity analysis should check whether recommendations amplify "
                "this source concentration."
            ),
        },
        {
            "figure": "figures/resources_by_format.png",
            "title": "Courses dominate the available formats",
            "finding": (
                f"{_label(str(top_format['category']))} is the largest format with "
                f"{top_format['count']} resources ({top_format['percentage']}%)."
            ),
            "implication": (
                "Format-diversity results will partly reflect catalogue composition, "
                "not only recommender preference."
            ),
        },
        {
            "figure": "figures/resources_by_difficulty.png",
            "title": "Advanced resources are the smallest difficulty group",
            "finding": (
                f"The catalogue contains {difficulty['Beginner']['count']} beginner, "
                f"{difficulty['Intermediate']['count']} intermediate, and "
                f"{difficulty['Advanced']['count']} advanced resources."
            ),
            "implication": (
                "Advanced learners have a smaller candidate pool, which may constrain "
                "difficulty matching."
            ),
        },
        {
            "figure": "figures/resource_duration_distribution.png",
            "title": "Most resources are short or medium length",
            "finding": (
                f"The largest duration band is {largest_duration_band['category']} "
                f"with {largest_duration_band['count']} resources "
                f"({largest_duration_band['percentage']}%)."
            ),
            "implication": (
                "The catalogue broadly supports the project's targeted next-step "
                "approach, while long tracks remain a minority."
            ),
        },
        {
            "figure": "figures/resources_by_cost.png",
            "title": "Free and paid resources are nearly balanced",
            "finding": (
                f"The catalogue contains {cost_rows['free']['count']} free and "
                f"{cost_rows['paid']['count']} paid resources."
            ),
            "implication": (
                "Cost availability is balanced at catalogue level, although cost is "
                "not yet a learner preference in the ranking model."
            ),
        },
        {
            "figure": "figures/skill_frequency.png",
            "title": "Skill representation is uneven",
            "finding": (
                f"{_label(str(top_skill['skill']))} appears in "
                f"{top_skill['resource_count']} resources, while the least represented "
                f"skill group ({', '.join(least_skills)}) appears in "
                f"{least_skill_count}."
            ),
            "implication": (
                "Low-frequency skills may receive fewer suitable recommendations and "
                "need explicit coverage checks."
            ),
        },
        {
            "figure": "figures/skill_cooccurrence.png",
            "title": "Some skills are commonly taught together",
            "finding": (
                f"The most frequent pair is {_label(str(pair['skill_a']))} with "
                f"{_label(str(pair['skill_b']))}, appearing in "
                f"{pair['resource_count']} resources."
            ),
            "implication": (
                "Co-occurrence can help explain multi-skill recommendations but may "
                "also make rare standalone skills harder to retrieve."
            ),
        },
        {
            "figure": "figures/pathway_skill_coverage.png",
            "title": "Every required pathway skill has catalogue coverage",
            "finding": (
                "No required pathway-skill cell has zero matching resources. "
                f"{limited_cell_text} fewer than three resources."
            ),
            "implication": (
                "The skill map is usable for recommendation, but thin cells should be "
                "reviewed during pathway-level error analysis."
            ),
        },
        {
            "figure": "figures/profiles_by_pathway.png",
            "title": "Evaluation profiles are almost balanced by pathway",
            "finding": (
                "Data Analyst has three profiles; each of the other four pathways has "
                "two."
            ),
            "implication": (
                "Macro results are not dominated by a large profile group, but 11 "
                "profiles remain too few for strong generalisation."
            ),
        },
        {
            "figure": "figures/relevance_by_profile.png",
            "title": "Relevant-set sizes vary across profiles",
            "finding": (
                f"Relevant sets range from {min(relevance_counts)} to "
                f"{max(relevance_counts)} resources, with a mean of "
                f"{statistics.mean(relevance_counts):.1f}."
            ),
            "implication": (
                "Recall@K should be interpreted with relevant-set size, and later "
                "evaluation should retain profile-level results."
            ),
        },
    )
    return findings
