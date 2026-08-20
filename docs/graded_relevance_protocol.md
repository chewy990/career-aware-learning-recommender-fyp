# Graded Relevance Protocol

Version: 1  
Frozen: 12 August 2026  
Primary purpose: increase ranking-evaluation resolution before user UX testing

## Scope

Grade every existing positive profile-resource judgement. Existing negatives
remain grade `0` and are not shown to the reviewer. The review must use the
blinded pack: it hides profile/resource IDs, model names, recommendation scores,
and ranking positions. Do not inspect model outputs while grading.

This is a relevance assessment from the documented learner profile and resource
metadata. It is not a judgement of teaching quality, learning effectiveness, or
value for money. Paid resources may be graded from their recorded title,
description, skills, level, format, prerequisites, duration, and pathway fit.

## Grade Rubric

| Grade | Label | Decision rule |
|---:|---|---|
| 3 | Essential | Directly addresses a priority weak skill or an immediate prerequisite at an appropriate level; it belongs near the top of this learner's next-step list. |
| 2 | Useful | Clearly supports the pathway and learner needs, but is less urgent, broader, partially overlapping, or better after a more immediate resource. |
| 1 | Tangential | Has a defensible connection to the pathway, but weakly matches this learner's present gaps, level, sequence, or preferred learning need. |
| 0 | Not relevant | Reserved for existing negative judgements and therefore absent from this positive-only grading pack. |

Use the learner's current skills, completed topics, weak skills, target pathway,
and preferred difficulty together. Do not award a higher grade because a
provider is popular or because a model ranked the resource highly.

## Review Procedure

1. Work only from the offline `graded_relevance_review.html`, the optional
   `graded_relevance_review.xlsx`, or the blinded CSV equivalent.
2. Enter exactly one grade (`1`, `2`, or `3`) for every row.
3. Enter confidence `1`, `2`, or `3`, where `1` is low and `3` is high.
4. Add a note whenever confidence is `1`; notes are optional otherwise.
5. Do not reorder, delete, add, or edit metadata cells.
6. Download the completed CSV from the browser reviewer, or export the completed
   workbook's `Grading` sheet as CSV, before applying it.

The browser reviewer automatically stores progress locally and also provides an
explicit **Save progress** button. Use **Download backup** periodically if the
browser may be cleared or the review will continue on another computer. The
backup can be restored into the same review pack. **Download completed CSV** is
enabled only when every row has a valid grade and confidence.

If a current positive appears completely irrelevant, record grade `1`, confidence
`1`, and explain why. Resolve possible binary-label removal separately rather
than silently changing the frozen scope during grading.

## Metric Contract

- Precision@K and Recall@K continue treating grades `1`, `2`, and `3` as
  relevant and grade `0` as not relevant.
- NDCG@K uses exponential gain: `gain = 2^grade - 1`, producing gains of
  `0`, `1`, `3`, and `7` for grades `0` through `3`.
- Rank discount remains `1 / log2(rank + 1)`.
- The existing binary results remain the historical baseline.

## Validity Limitations

A self-review measures consistency, not independent validity or inter-rater
reliability. A second knowledgeable reviewer is preferred. Any adjudication
must be documented and must not use model identity or scores as evidence.
