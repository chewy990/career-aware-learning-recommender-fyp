# Skill Map Methodology

## Purpose

The skill map converts career pathway requirements into numeric weights that the recommender can use. It supports the project proposal's aim of making recommendations based on learner skill gaps and target career pathway.

## Weight Scale

| Weight | Meaning |
|---|---|
| 0 | Not central to this pathway |
| 1 | Useful supporting skill |
| 2 | Important skill |
| 3 | Core high-priority skill |

## Evidence Approach

The current `data/skill_map.csv` is a prototype taxonomy derived from three evidence groups:

1. The FYP proposal and original project ideas brief.
2. Learning platform pathway descriptions from Coursera DataCamp and freeCodeCamp.
3. Career or skill-framework sources such as SkillsFuture and job-skill references.

The evidence table is stored in `data/skill_sources.csv`. The table records which sources support each pathway and which skills they mention.

## Pathway Rationale

### Data Analyst

High-priority skills are SQL Excel Python statistics data visualisation dashboards and data cleaning. These are repeatedly represented in data analyst learning pathways and in the project proposal. SQL and Excel support data extraction and analysis. Python and data cleaning support reproducible analysis. Statistics supports interpretation. Data visualisation and dashboards support communication of insights.

### Machine Learning Engineer

High-priority skills are Python machine learning model evaluation and deployment. ML engineering requires building models but also validating monitoring and deploying them. APIs and version control are included as important supporting skills because deployed models usually need integration into software systems.

### Software Developer

High-priority skills are programming OOP APIs databases testing and version control. These support building maintainable applications and match backend or full-stack developer learning pathways. SQL is medium priority because databases are central to many software systems but not every software role is data-focused.

## Limitations

The current weights are defensible for a prototype but should not be presented as final labour-market truth. For the final report the next improvement is to collect a small sample of job postings for each target role and count skill mentions. Those counts can be used to refine or validate the current 0-3 weights.

## Treatment Of Fixed Career Tracks

Broad career tracks are kept in the dataset as useful context and optional structured references, but they are not prioritised as first-step recommendations. This design choice is important because the project aims to improve on fixed learning paths. Instead of recommending an entire 40-60 hour track, the recommender prioritises shorter targeted modules and resources that address the learner's current skill gaps.

In the prototype, long resources and career tracks are penalised in the hybrid score and separated into an optional structured-track section in the demo app.
