# Relevance-Audit Disagreement Resolution Tracker

## Purpose

The blinded author relevance audit produced 40 definite decisions, 34
agreements, and six disagreements (`85.0%` raw agreement). This tracker holds
the explicit retain-or-accept decision for each of those six cases.

Source: `outputs/author_audit_run/author_audit_disagreements.csv`
(verified run `708f8155d2753511`).

## Status - Resolved 31 July 2026

All six decisions are recorded. Five cases were resolved in favour of the audit
label and one retained the existing label.

| Case | Profile | Resource | Current | Decision | New label | Confidence |
|---|---|---|---|---|---|---|
| A003 | P001 | R003 Excel Skills for Business | `0` | Accept | `1` | medium |
| A004 | P007 | R003 Excel Skills for Business | `0` | Accept | `1` | full |
| A008 | P004 | R012 Git and GitHub Crash Course | `0` | Retain | `0` | full |
| A013 | P011 | R039 MLOps Fundamentals | `1` | Accept | `0` | medium |
| A035 | P006 | R055 Database Clients and ORM Basics | `0` | Accept | `1` | lowest |
| A039 | P003 | R048 Back End Development and APIs | `0` | Accept | `1` | medium |

Five labels in `data/relevance_judgements.csv` require revision: four move from
`0` to `1` and one moves from `1` to `0`. Affected profiles are P001, P003,
P006, P007, and P011.

### Interpretation Of The Outcome

Five of the six disagreements resolved against the original labels, so the
stratified 40-case sample contained five confirmed labelling errors. Report this
as five corrected labels out of 40 audited cases. Do **not** extrapolate it to a
dataset-wide error rate: the sample deliberately over-selected contested
recommended/not-relevant boundary cases rather than sampling by prevalence, so
the true full-dataset error rate is expected to be lower.

This also does not convert the exercise into independent validation. It remains
a blinded author consistency audit in which the author adjudicated their own
labels, and the absence of a second reviewer stays a stated limitation.

### Emergent Labelling Principle

The decisions are consistent under one rule, which should be recorded in the
report: **a relevance label records topical fit to the learner's declared skill
gaps; difficulty, unmet prerequisites, and course length are ranking and
eligibility concerns, not relevance concerns.** A003, A035, and A039 were all
accepted despite scope, prerequisite, or duration mismatches. A008 and A013 were
resolved as not relevant on genuine topical grounds - general professional
benefit and wrong subject orientation respectively.

## How To Use

- **Retain** keeps the existing label in `data/relevance_judgements.csv`.
- **Accept** adopts the author-audit label instead.
- Fill in **Final decision** and **Decision reason** for all six cases.
- Nothing in this file edits data. Label changes happen only after approval,
  as a separate, versioned dataset revision.

## Standing Interpretation Rules

- This is a blinded *author consistency* audit. It is not independent
  validation and not inter-rater reliability evidence.
- The sample was deliberately stratified, so `85.0%` agreement is **not** an
  estimate that 15% of the dataset is mislabelled.
- Relevance labels record **topical relevance to the profile's pathway and
  skill gaps**. Readiness concerns (difficulty fit, unmet prerequisites,
  duration limits) belong to ranking and eligibility, not to the label. Several
  cases below turn on exactly this distinction.

## Downstream Impact Warning

Profiles **P003** and **P008** are the two profiles whose top-five
recommendations change under the hard-prerequisite eligibility experiment. Case
**A039** concerns P003. Accepting it would change P003's relevance set and can
therefore alter the experiment's current result of 11 ties and adjusted exact
`p=1.000000` at K=5. Re-run the experiment after any accepted label change and
do not reuse the existing figures or claims.

---

## Case A003 - Excel Skills for Business

| Field | Value |
|---|---|
| Profile | `P001` Beginner Data Analyst |
| Resource | `R003` Excel Skills for Business |
| Current label | `0` not relevant |
| Author-audit label | `1` relevant |
| Reviewer confidence | `1` (lowest) |
| Selection reason | `recommended_not_relevant` |

**Reviewer note:** "this user already has more than basic excel and basic data
cleaning. doing the whole course just to learn dashboards is a waste."

**Pathway / skill evidence**

- `R003` skills: excel, dashboards, data_cleaning. `data_analyst_relevance = 3`.
- `P001` weak skills: sql, data_visualisation, statistics.
- None of the resource's three skills is a declared P001 gap.
- P001 already holds `excel:2` and lists `excel` under completed topics.

**Proposed recommendation:** **Retain `0`.** The reviewer's own written
reasoning argues *against* relevance while the recorded label says relevant, and
this case carries the lowest confidence score. The resource teaches skills P001
has already covered and misses all three declared gaps.

**Final decision:** **ACCEPT `1`** - change the label from `0` to `1`.
Recorded 31 July 2026. This overrides the proposed recommendation above.

**Decision reason:** P001 has `data_visualisation:0` as a declared gap, and the
dashboards content addresses it. The resource is therefore relevant on the
dashboards component even though the Excel component is redundant for a learner
already at `excel:2`. Decision confidence is medium, because the time cost of an
eight-hour Excel course to reach the dashboard material is disproportionate.
That is a ranking and scope concern, not grounds to call the resource
irrelevant.

---

## Case A004 - Excel Skills for Business

| Field | Value |
|---|---|
| Profile | `P007` Advanced Data Analyst |
| Resource | `R003` Excel Skills for Business |
| Current label | `0` not relevant |
| Author-audit label | `1` relevant |
| Reviewer confidence | `3` (highest) |
| Selection reason | `recommended_not_relevant` |

**Reviewer note:** none recorded.

**Pathway / skill evidence**

- `R003` skills: excel, dashboards, data_cleaning. `data_analyst_relevance = 3`.
- `P007` weak skills: statistics, data_cleaning, dashboards.
- The resource directly covers **two of three** declared gaps: data_cleaning and
  dashboards.
- Mismatch is readiness only: difficulty `1` versus preferred `2`, and course
  format versus preferred project.

**Proposed recommendation:** **Accept `1`.** Maximum pathway relevance, direct
coverage of two declared gaps, and the highest confidence rating. The difficulty
and format mismatch is a ranking concern, not a relevance concern.

**Final decision:** **ACCEPT `1`** - change the label from `0` to `1`.
Recorded 31 July 2026.

**Decision reason:** The resource delivers data visualisation and dashboarding,
which are declared P007 gaps. The beginner difficulty is appropriate rather than
mismatched: P007 has no recorded Excel skill, so an introductory Excel course is
the correct entry point for this content despite her otherwise advanced profile.
Decision confidence is full.

---

## Case A008 - Git and GitHub Crash Course

| Field | Value |
|---|---|
| Profile | `P004` Intermediate Data Analyst |
| Resource | `R012` Git and GitHub Crash Course |
| Current label | `0` not relevant |
| Author-audit label | `1` relevant |
| Reviewer confidence | `2` |
| Selection reason | `not_relevant_not_recommended` |

**Reviewer note:** "the pathway does not match given course, however every
technical professional generally benefits from version control and using
Github."

**Pathway / skill evidence**

- `R012` skills: version_control only. `data_analyst_relevance = 1` (lowest
  non-zero).
- `P004` weak skills: python, dashboards, data_cleaning.
- `version_control` does not appear in P004's current skills or declared gaps.

**Proposed recommendation:** **Retain `0`.** The reviewer explicitly concedes
the pathway does not match and justifies the `1` on general professional
benefit. General career utility is not the labelling criterion; the label is
profile- and gap-specific.

**Final decision:** **RETAIN `0`** - the existing label stands, no change.
Recorded 31 July 2026.

**Decision reason:** On reconsideration, a two-hour video dedicated purely to
GitHub does not advance P004 toward the analyst role within her six-hour budget,
and version control is neither a current skill nor a declared gap for her. The
original audit answer was based on general professional benefit rather than fit
to this profile. Decision confidence is full.

---

## Case A013 - MLOps Fundamentals

| Field | Value |
|---|---|
| Profile | `P011` Intermediate Data Engineer |
| Resource | `R039` MLOps Fundamentals |
| Current label | `1` relevant |
| Author-audit label | `0` not relevant |
| Reviewer confidence | `2` |
| Selection reason | `relevant_not_recommended` |

**Reviewer note:** "pathway does not match course given despite some overlapping
skills."

**Pathway / skill evidence**

- `R039` skills: python, deployment, machine_learning, model_evaluation,
  version_control.
- `data_engineer_relevance = 2`, but `ml_engineer_relevance = 3` - the resource
  is oriented toward ML engineering.
- `P011` weak skills: deployment, apis, version_control. The resource covers
  **two of three**: deployment and version_control.
- `R039` prerequisites are python and machine_learning. P011 holds `python:2`
  but has no recorded machine_learning skill, so the prerequisite is unmet.

**Proposed recommendation:** **Retain `1`.** Deployment is P011's primary
declared gap and the resource covers it alongside version_control, with a
non-trivial `data_engineer_relevance = 2`. The unmet machine_learning
prerequisite is precisely what the hard-prerequisite eligibility rule handles at
ranking time and is not a reason to remove the topical label. This is the
weakest retain of the six and is reasonable to overturn if the project decides
labels should encode pathway orientation rather than skill overlap.

**Final decision:** **ACCEPT `0`** - change the label from `1` to `0`.
Recorded 31 July 2026. This overrides the proposed recommendation above.

**Decision reason:** A data engineer does not require machine learning. P011's
declared gaps are deployment, APIs, and version control, and a course built
around the machine-learning lifecycle is the wrong vehicle for reaching them
even though deployment and version control appear in its skill list. The
resource is tagged `ml_engineer_relevance = 3` against `data_engineer_relevance
= 2`, which supports treating it as ML-oriented. Decision confidence is medium,
because the skill overlap is genuine.

---

## Case A035 - Database Clients and ORM Basics

| Field | Value |
|---|---|
| Profile | `P006` Beginner Software Developer |
| Resource | `R055` Database Clients and ORM Basics |
| Current label | `0` not relevant |
| Author-audit label | `1` relevant |
| Reviewer confidence | `1` (lowest) |
| Selection reason | `recommended_not_relevant` |

**Reviewer note:** "pathway does not match course given despite similar skills."

**Pathway / skill evidence**

- `R055` skills: databases, sql, apis, programming.
  `software_developer_relevance = 3` - the **maximum**, which contradicts the
  reviewer's "pathway does not match" note.
- `P006` weak skills: oop, apis, databases, testing, version_control. The
  resource covers **two**: apis and databases.
- `R055` prerequisites are sql and programming. P006 holds `programming:1` and
  has no recorded sql, so the prerequisite is unmet.
- Difficulty `2` versus P006's preferred `1`; P006 is the beginner profile.

**Proposed recommendation:** **Retain `0`** - but treat this as the most
contested case. The reviewer's note and lowest-confidence rating both point to
retain, and P006 is a beginner missing both stated prerequisites. The strong
counter-argument is that `software_developer_relevance = 3` and the resource
covers two declared gaps, which would normally support `1`. Decide this case
together with A013, since both turn on whether a label may encode readiness or
only topical fit. Applying the rule consistently means either retaining both or
accepting both.

**Final decision:** **ACCEPT `1`** - change the label from `0` to `1`.
Recorded 31 July 2026. This overrides the proposed recommendation above.

**Decision reason:** The pathway does match. On checking what ORM means, a
software developer does need to work with databases from application code, and
the catalogue agrees at `software_developer_relevance = 3`. The resource covers
two declared P006 gaps, databases and APIs. Decision confidence is lowest,
because P006 is a beginner without the stated SQL prerequisite and the course
sits above his preferred difficulty. That readiness gap is handled by
prerequisite eligibility at ranking time, not by the relevance label.

---

## Case A039 - Back End Development and APIs

| Field | Value |
|---|---|
| Profile | `P003` Intermediate Software Developer |
| Resource | `R048` Back End Development and APIs |
| Current label | `0` not relevant |
| Author-audit label | `1` relevant |
| Reviewer confidence | `3` (highest) |
| Selection reason | `not_relevant_not_recommended` |

**Reviewer note:** none recorded.

**Pathway / skill evidence**

- `R048` skills: programming, apis, testing, databases.
  `software_developer_relevance = 3` (maximum).
- `P003` weak skills: apis, testing, oop. The resource covers **two of three**:
  apis and testing.
- `R048` prerequisite is programming; P003 holds `programming:2`, so the
  prerequisite is **met**.
- Difficulty `2` exactly matches P003's preferred difficulty.
- Only mismatch is scope: 25 hours against P003's 10-hour maximum, in
  career_track rather than the preferred project format.

**Proposed recommendation:** **Accept `1`.** This is the strongest accept case:
maximum pathway relevance, two of three gaps covered, prerequisite satisfied,
difficulty matched, and highest reviewer confidence. The duration and format
mismatch is handled by the existing scope penalty in ranking, not by the label.

**Note:** P003 is one of the two profiles affected by the hard-prerequisite
experiment. Accepting this case requires re-running that experiment and
revalidating its tie result before any of its figures or claims are reused.

**Final decision:** **ACCEPT `1`** - change the label from `0` to `1`.
Recorded 31 July 2026.

**Decision reason:** The resource is genuinely relevant: it covers APIs and
testing, two of P003's three declared gaps, at his exact preferred difficulty
and with the programming prerequisite already met. The 25-hour length against a
10-hour stated maximum is accepted deliberately, because a learner does not have
to complete a career track for it to be useful; partial progress still delivers
the missing skills. Duration therefore acts as a soft scope penalty in ranking
rather than a relevance disqualifier. Decision confidence is medium.

---

## Approval

| Field | Value |
|---|---|
| Decisions approved by | Jaslyn Chan (project author) |
| Date approved | 31 July 2026 |
| Dataset revision required | Yes - five label changes |

## Applied - 31 July 2026

The five accepted changes were applied to `data/relevance_judgements.csv` and
the affected evidence was regenerated in a verified revision run
(`5a8bcd616d43cab5`; all 162 hashes verified, byte-identical across two
runs apart from the manifest). Steps 1 to 4 below are complete; step 5, the
report update, is outstanding.

### What Changed

Headline K=5 results, original labels then revised labels:

| Model | Precision@5 | Recall@5 | NDCG@5 |
|---|---|---|---|
| Popularity | 0.2727 -> 0.3091 | 0.0580 -> 0.0646 | 0.2878 -> 0.3116 |
| Content-based | 0.8182 -> 0.8364 | 0.1820 -> 0.1835 | 0.8398 -> 0.8531 |
| Hybrid | 0.9273 -> 0.9455 | 0.2067 -> 0.2077 | 0.9386 -> 0.9540 |

All three models improved, so the correction did not selectively favour the
hybrid. The hybrid's margin over content-based at NDCG@5 is essentially
unchanged, moving from `+0.0988` to `+0.1009`.

### What Did Not Change

- **Model behaviour.** Every recommendation file, the component contributions,
  and all recommendation diagnostics are byte-identical. Relevance labels are
  scoring inputs, not model inputs, so the recommender produced exactly the same
  lists before and after. Catalogue coverage `34.4%`, prerequisite validity
  `90.9%`, difficulty match `100.0%`, and the 17 Phase 4 failure flags all hold.
- **Phase 5 conclusions.** Nine of 18 comparisons remain significant after Holm
  correction, all against popularity, and no comparison changed significance
  status. Hybrid versus content-based at NDCG@5 moves from adjusted `p=0.609375`
  to `p=0.656250` and remains non-significant.
- **The hard-prerequisite result.** The paired K=5 test still returns 11 ties and
  adjusted exact `p=1.000000` on all three metrics, because baseline and variant
  shift identically under a label change. The earlier concern that A039 would
  invalidate this result did not materialise.

### What Did Change Beyond The Headline Numbers

- The `prerequisite_match` ablation flips sign at NDCG@5, from `+0.0013` to
  `-0.0141`. Removing that component now harms ranking instead of marginally
  helping it. Career relevance remains the strongest component at `-0.0295` and
  job-skill alignment still improves NDCG@5 by `+0.0173` when removed.
- Data Analyst pathway NDCG@5 rises from `0.9435` to `1.0000`, so four of five
  pathways now sit at the ceiling. Data Engineer is unchanged at `0.7469`.
- The hybrid NDCG@5 bootstrap interval narrows from `[0.8617, 1.0000]` to
  `[0.8885, 1.0000]`.
- Relevance-set sizes are now 16 to 29 with mean `23.45`, previously 16 to 30
  with mean `23.18`.

### Saturation Limitation

Four of five pathways at exactly `1.0000` means the 11-profile evaluation set no
longer discriminates well at K=5 for those pathways. Report this as a ceiling
effect: further ranking improvements cannot be detected on this set, and the
remaining measurable signal is concentrated in Data Engineer. This strengthens
the existing argument that the curated evaluation set is too small and too easy
to support strong generalisation claims.

## Remaining Work

Steps 1 to 4 are complete. Step 5 is outstanding.

1. Apply the five accepted changes to `data/relevance_judgements.csv` as an
   explicit, recorded **relevance-label revision**. Never edit historical
   phase-run directories or manifests, and keep the original labels recoverable
   for comparison.

   Scope note: this is a correction to relevance labels only. It is **not** the
   catalogue "dataset version 2" contemplated in the Phase 4 decision, which
   would add or change resources, modules, or profiles. No resource, module,
   skill-map, or profile row changes here. Keep the two revisions distinct in
   the report, because they rest on different justifications.
2. Re-run the full pipeline into a new output directory. Confirm validation
   passes and that two unchanged runs stay byte-identical.
3. Re-run the hard-prerequisite experiment. A039 changes P003, one of the two
   profiles whose top-five list the experiment alters, so its current result of
   11 ties and adjusted exact `p=1.000000` at K=5 is no longer valid evidence
   until regenerated.
4. Expect Phase 3, 4, and 5 results to move. Every metric is measured against
   these labels, so evaluation, robustness, and statistical-comparison outputs
   must be regenerated rather than reused.
5. Record the six decisions, corrected labels, regenerated results, and
   interpretation limits in the project report.
6. Only then evaluate the Phase 6 entry gate.

Until steps 1 to 5 are complete, the currently committed phase-run artifacts
remain the valid evidence for the original labels and must not be described as
reflecting the corrected dataset.
