# Code Structure

## Purpose

The project separates the active React/FastAPI product, framework-independent
recommender, and reproducible scientific pipeline. Maintained `.py`, `.js`,
`.jsx`, and `.css` files normally stay at or
below 300 physical lines and must never exceed 350. Comments and docstrings count.

`tests/test_code_structure.py` enforces the ceiling, checks that every 301–350
line exception is listed here and verifies package re-exports and dependency
boundaries.

## Dependency Rules

1. `frontend/src` calls FastAPI through `frontend/src/lib/api.js`; it does not
   import Python code.
2. `src/api` may use `edu_recommender` data, models, learning paths, and
   presentation helpers. Authentication stays inside `src/api/auth`.
3. `src/pipeline` orchestrates phase packages. Scientific calculations and
   figures remain owned by their corresponding `edu_recommender` packages.
4. `src/edu_recommender` is framework-independent.
5. Generated artifacts, datasets, dependency folders, lockfiles, and
   documentation are not source-size candidates.

## Package Responsibilities

- `src/api/auth/`: routes, SQLite storage, password/token security, session
  dependencies, cookies, validation, and throttling.
- `src/pipeline/`: immutable configuration, orchestration, recommendation CSV
  rows, HTML reporting, and reproducibility manifest generation.
- `src/edu_recommender/validation/`: contracts, parsing, schemas, dataset value
  checks, reference checks, and the public validation service.
- `src/edu_recommender/eda/`: tables, findings, deterministic drawing
  primitives, figures, Markdown reporting, and orchestration.
- `src/edu_recommender/evaluation/`: ranking metrics, aggregation, bootstrap
  uncertainty, diagnostics, findings, figures, and reporting.
- `src/edu_recommender/robustness/`: ablation, sensitivity, seeded
  configurations, contributions, failure cases, figures, and reporting.
- `src/edu_recommender/statistical_comparison/`: paired differences, exact
  tests, Wilcoxon sensitivity checks, Holm correction, effects, blinded audit
  sampling, figures, and findings.
- `src/edu_recommender/prerequisite_experiment/`: eligibility, paired
  comparison, replacement traces, targeted audit, diagnostics, figures, and
  frozen experiment orchestration.
- `src/edu_recommender/models/`: public result contracts, recommender suite,
  deterministic text features, and hybrid signal calculations.
- `src/edu_recommender/learning_path/`: readiness/progression rules, verified
  module selection, and staged path construction.

## Third-Party Dependency Scope

The ranking path uses only the Python standard library. That covers
`data.py`, `text.py`, `presentation.py`, `models/`, `learning_path/`, and
`validation/`. `text.py` implements TF-IDF and cosine similarity directly
rather than importing scikit-learn, which removes a source of
version-dependent numerical drift and is a precondition for byte-identical
reproducibility.

Matplotlib and Pillow are confined to figure-generating modules: `eda/figures.py`
and the figure and drawing modules under `evaluation/`. A rendering difference
there cannot alter a reported number.

Do not describe the whole package as standard-library only. That was an
overstatement corrected on 1 August 2026 in both the report and the
architecture diagram.

## Documented 301–350 Line Exceptions

| File | Lines at verification | Why it remains cohesive |
| --- | ---: | --- |
| `src/edu_recommender/prerequisite_experiment/service.py` | 331 | The frozen experiment orchestration preserves one audited sequence of table writes and result construction; splitting the function would add mutable hand-off state and increase output-parity risk. |
| `src/pipeline/html_components.py` | 306 | Small deterministic HTML table/grid helpers share escaping and report markup conventions; an additional package layer would not isolate a distinct calculation. |
| `tests/test_reproducibility.py` | 347 | One end-to-end fixture deliberately checks the full artifact family, manifest contract, and two-run byte reproducibility in a single lifecycle. |

If any listed file changes line count, the ceiling test still applies. Prefer
extracting a genuine responsibility before adding another exception.
