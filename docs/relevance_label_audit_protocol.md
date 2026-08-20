# Blinded Author Relevance-Label Audit Protocol

## Purpose

This audit checks whether the curated relevance labels are understandable and consistently defensible before any dataset revision or supervised experiment. The project author will perform the review without seeing the current labels or experiment roles. This makes it a blinded author consistency audit, not independent validation or an inter-rater reliability study. An independent second review is deferred and should be reported as a limitation and future improvement.

It is not a user-engagement study and does not measure learning outcomes.

## Files

For a no-spreadsheet review, regenerate the reviewer with `python src/generate_audit_review.py` and open the resulting `outputs/audit_review.html` in any modern browser. It contains both visible audit sheets, saves progress in browser storage, and exports the currently selected review as CSV. It contains no hidden key fields and makes no network requests.

The generated file is deliberately untracked and listed in `.gitignore` because it is fully regenerable from `src/audit_review_template.html` and the blinded CSVs. The completed audit inputs under `outputs/author_audit_run/input/` and `outputs/prerequisite_author_audit_run/input/` are the preserved evidence and must not be deleted.

- The author reviewer completes:
  - `outputs/phase5_run/relevance_audit_blinded.csv` for the 40-case pathway-balanced review
  - `outputs/prerequisite_experiment_run/prerequisite_experiment_audit_blinded.csv` for the 10-case hard-prerequisite replacement addendum
- Keep both keys hidden until the review is complete:
  - `outputs/phase5_run/relevance_audit_key.csv`
  - `outputs/prerequisite_experiment_run/prerequisite_experiment_audit_key.csv`
- Do not show model scores, ranks, current labels, profile IDs, or resource IDs during review.

The sheet contains 40 deterministic cases: eight per pathway. It spans resources that are currently recommended/relevant, recommended/not currently relevant, relevant/not recommended, and neither recommended nor relevant. Five balanced fallback cases were necessary because recommended-but-currently-non-relevant cases were scarce.

The addendum contains the five resources removed from P003/P008 top-five lists and their five replacements. Its shuffled visible sheet does not reveal which role each resource played. The hidden key stores `baseline_removed` or `variant_replacement`.

## Review Rule

Judge whether the resource is a reasonable learning recommendation for the described learner at the present stage.

Mark `reviewer_relevance` as:

- `1` when the resource addresses the target pathway or an identified skill gap and is reasonably suitable for the learner now
- `0` when it does not address the pathway/need, duplicates already completed learning, or is unsuitable because of difficulty or prerequisites
- `U` when the available metadata is insufficient or the decision is genuinely ambiguous

Mark `reviewer_confidence` from `1` (low) to `3` (high). Add a short `reviewer_notes` explanation for every `U`, every low-confidence decision, and any case where suitability depends on an unstated assumption.

## Procedure

1. The reviewer completes every row in both visible sheets without opening either key.
2. Save each completed sheet as a new dated file; do not overwrite the generated blank sheets.
3. Lock both completed files before revealing either key.
4. Join each completed sheet to its matching key using `audit_item_id`.
5. Report agreement separately for definite `0`/`1` decisions and the count of `U` decisions.
6. Review disagreements by pathway and selection reason. Do not silently change labels.
7. Record each accepted label change with the original label, proposed label, reason, reviewer, and date.

When using the browser form, complete and export both tabs separately:

- `General review` exports `relevance_audit_completed.csv`.
- `Prerequisite changes` exports `prerequisite_audit_completed.csv`.

Browser progress is device-local. Export before clearing browser data or moving to another device.

## Current Status

The general 40-case author audit was completed and validated on 31 July 2026. Run `708f8155d2753511` under `outputs/author_audit_run/` records:

- 40 definite decisions and no `U` decisions
- 34 agreements and six disagreements with the current labels (`85.0%` raw agreement)
- no changed blinded metadata
- a joined decision table and a separate six-case disagreement table
- three input hashes, two code hashes, and four output hashes, all verified

No source label has been changed. The six disagreements require explicit retain-or-accept decisions.

The targeted 10-case prerequisite-change addendum was also completed and validated on 31 July 2026. All five removed resources and all five replacements were judged relevant. The replacement group had higher mean confidence (`3.00` versus `2.40`), but there was no binary-relevance difference. Run `85e28d346151f8a0` under `outputs/prerequisite_author_audit_run/` verifies all eight recorded hashes.

## Decision Gate

- Do not create dataset version 2 merely because a changed label improves a model metric.
- Create a versioned label or catalogue revision only when disagreements reveal a documented labelling rule problem, missing coverage, or unsuitable resource metadata.
- Re-run the unchanged pipeline after any accepted revision and compare the new manifest with run `59b8164bc31d1c98`.
- Do not begin the Phase 6 supervised comparison until the audit is completed and each grouped validation fold still has usable positive and negative examples.

The report must distinguish the reproducible blank instruments from completed author-audit evidence. It must not describe either result as independent validation. Findings from both audits may now be reported from their verified packages, but no source label may change without an explicit recorded decision.
