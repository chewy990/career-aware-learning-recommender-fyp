# Blinded Author Relevance-Label Audit Summary

This is an internal consistency audit by the project author. It is not independent validation or an inter-rater reliability study.

## Verified result

- Items: `40`
- Definite decisions: `40`
- Uncertain decisions: `0`
- Agreements: `34`
- Disagreements: `6`
- Raw author-to-current-label agreement: `85.0%`
- Current positive labels in the stratified sample: `21`
- Author positive decisions in the sample: `25`

The sample was deliberately balanced across pathways and case types, so its label proportions are not estimates of full-dataset prevalence.

## Agreement by pathway

| Pathway | Decisions | Agreements | Rate |
| --- | ---: | ---: | ---: |
| data_analyst | 8 | 5 | 62.5% |
| data_engineer | 8 | 7 | 87.5% |
| data_scientist | 8 | 8 | 100.0% |
| ml_engineer | 8 | 8 | 100.0% |
| software_developer | 8 | 6 | 75.0% |

## Disagreements requiring an explicit decision

| ID | Pathway | Resource | Current | Author | Confidence |
| --- | --- | --- | ---: | ---: | ---: |
| A003 | data_analyst | Excel Skills for Business | 0 | 1 | 1 |
| A004 | data_analyst | Excel Skills for Business | 0 | 1 | 3 |
| A008 | data_analyst | Git and GitHub Crash Course | 0 | 1 | 2 |
| A013 | data_engineer | MLOps Fundamentals | 1 | 0 | 2 |
| A035 | software_developer | Database Clients and ORM Basics | 0 | 1 | 1 |
| A039 | software_developer | Back End Development and APIs | 0 | 1 | 3 |

No source label is changed by this analysis. Each disagreement must be retained or accepted with a documented reason before a versioned label revision is created.
