# Documentation

This directory contains the methodology and frozen protocols needed to inspect
the final implementation and evaluation.

- `code_structure.md` describes package responsibilities and dependency rules.
- `deployment_guide.md` records the React and FastAPI deployment configuration.
- `skill_map_methodology.md` explains how pathway requirements were constructed.
- `graded_relevance_protocol.md` defines the blinded 3/2/1 grading procedure.
- `relevance_label_audit_protocol.md` defines the author consistency audit.
- `relevance_audit_disagreement_resolution.md` records the resolved audit cases.
- `hard_prerequisite_experiment_protocol.md` freezes the eligibility experiment.
- `graded_refinement_experiments.md` records the bounded weak-case refinements.
- `final_robustness_protocol.md` freezes the final sensitivity checks.

The final generated evidence referenced by these documents is stored under
`outputs/`. The `labels_revision_run` archive preserves the binary-label result
used for comparison with the final graded evaluation. Preliminary reports,
revision trackers and historical duplicate runs are deliberately absent from
this release repository.
