# Career-Aware Learning Recommender

A React and FastAPI prototype that recommends staged computing learning paths
from a learner's target role, current skills, skill gaps, completed topics and
resource metadata.

The project tests three ranking approaches: a popularity baseline, a
content-based recommender and an explainable weighted hybrid. Recommendations
are organised around a short progression: learn the immediate foundations,
start practical work and deepen the relevant skills later.

## Demonstration

- Web application: https://chewy990-career-recommender.onrender.com
- API health check: https://chewy990-career-recommender-api-sg.onrender.com/api/health

The free API service may take a short time to wake after inactivity.

## Current Evaluation

The fixed offline evaluation uses 11 constructed learner profiles, 96 curated
resources and completed 3/2/1 graded relevance judgements. Precision and Recall
remain binary; NDCG uses the grades.

| Model | Precision@5 | Recall@5 | NDCG@5 |
|---|---:|---:|---:|
| Popularity | 0.3091 | 0.0646 | 0.2283 |
| Content-based | 0.8364 | 0.1835 | 0.7504 |
| Hybrid | 0.9455 | 0.2077 | 0.8078 |

The hybrid clearly improves on popularity within this test set. Its mean
advantage over content-based ranking is positive but not statistically
significant after correction, so the project does not claim general
superiority. The profiles and relevance labels are author-created prototype
evidence rather than observations of learning outcomes.

## Repository Structure

```text
data/       Validated catalogue, skill map, profiles and relevance labels
frontend/   React learner interface
src/api/    FastAPI application and authentication
src/edu_recommender/  Ranking, evaluation and robustness packages
src/pipeline/          Reproducible pipeline orchestration
tests/      Python tests for application and scientific behaviour
outputs/    Final verified results and bounded robustness experiments
docs/       Methodology, audit and experiment protocols
```

Historical development exports, preliminary reports, editor trackers and
retired interfaces are intentionally excluded from this examiner-facing
repository.

## Local Setup

Python 3.12 and Node.js are required.

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install --require-hashes -r requirements.txt
cd frontend
npm ci
```

Start the API from the repository root:

```powershell
.venv\Scripts\python.exe -m uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8001
```

Start React in another terminal:

```powershell
cd frontend
npm run dev
```

Open `http://127.0.0.1:5173`.

## Reproduce The Evaluation

```powershell
.venv\Scripts\python.exe src\run_pipeline.py --output-dir <scratch-directory>
```

The pipeline validates all source CSV files before model construction and
writes a manifest containing input, source and output hashes. Two unchanged
runs produce byte-identical non-manifest artifacts.

## Verification

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m ruff check src tests
cd frontend
npm run build
```

The committed final evidence is under `outputs/graded_relevance_run/`. The
smaller experiment directories record the final label-sensitivity,
leave-one-profile-out, counterfactual and weak-case checks.

## Scope

This is a recommender prototype rather than a learning management system. It
does not host courses, issue qualifications or establish that the recommended
paths improve learning outcomes.
