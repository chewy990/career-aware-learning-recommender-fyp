# Free Deployment Guide

This deployment keeps the React frontend awake as a free static site and runs
FastAPI as a free Render web service. The frontend retries its initial catalogue
request and explains the cold start instead of showing a failed login screen.
Authentication data uses Neon Postgres because Render's free filesystem is
temporary and would erase a local SQLite database whenever the service sleeps.
The API is deployed in Singapore, matching the Neon database region to reduce
database round-trip latency.

## Public URLs

- App: `https://chewy990-career-recommender.onrender.com`
- API health check: `https://chewy990-career-recommender-api-sg.onrender.com/api/health`

The URLs above follow the unique service names declared in `render.yaml`. If
Render changes either URL during creation, update `AUTH_ALLOWED_ORIGINS` and
`VITE_API_BASE` to the actual HTTPS URLs and redeploy both services.

## 1. Create The Database

1. Create a free Neon project.
2. Open **Connect** and copy the pooled Postgres connection string.
3. Keep the string private. It contains the database password and must not be
   added to a file or committed to GitHub.

The API creates its three authentication tables on first startup. Local
development continues to use `data/auth.sqlite3` when `DATABASE_URL` is absent.

## 2. Create The Render Blueprint

1. Sign in to Render with GitHub.
2. Select **New > Blueprint**.
3. Connect `chewy990/career-aware-learning-recommender-fyp` and select `main`.
4. Render reads the repository-root `render.yaml`.
5. Paste the Neon connection string into the requested `DATABASE_URL` field.
6. Confirm that the API uses the **Free** instance type before applying.

Render builds the static site and API from the same commit only after the
repository's security-and-quality workflow passes. Do not create a free Render
Postgres database for this project: that database expires after 30 days, while
the examiner link needs to remain usable for longer.

## 3. Verify The Live Application

1. Open the API health-check URL. It must return `{"status":"ok"}`.
2. Open the app URL in a private browser window.
3. Register a temporary test account and sign in.
4. Select a pathway, generate a learning path, complete one item, and sign out.
5. Sign in again and confirm the account remains valid.
6. Check the dashboard and Research View on desktop and mobile widths.
7. Delete any temporary account directly from Neon if it should not remain.

After 15 minutes without traffic, Render's free API sleeps. The static frontend
still opens and retries the catalogue request while displaying the startup
message. Render states that a free-service wake-up can take about one minute.

## Deployment Environment Variables

| Service | Variable | Value |
|---|---|---|
| API | `DATABASE_URL` | Secret Neon pooled connection string |
| API | `APP_ENV` | `production` |
| API | `AUTH_ALLOWED_ORIGINS` | Public static-site URL |
| API | `AUTH_COOKIE_SECURE` | `true` |
| API | `AUTH_COOKIE_SAMESITE` | `none` |
| API | `AUTH_REQUIRE_ORIGIN` | `true` |
| Frontend | `VITE_API_BASE` | Public API URL, without a trailing slash |

`DATABASE_URL` is the only value intentionally omitted from source control.

## Local Verification

Without deployment environment variables, the existing local commands and
SQLite account database continue to work:

```powershell
.venv\Scripts\python.exe -m uvicorn src.api.main:app --host 127.0.0.1 --port 8001
cd frontend
npm run dev
```

## Temporarily Close The Site

Render supports suspending and resuming both web services and static sites.
From the workspace service list, select the frontend and API together and use
**Suspend**. Resume both shortly before a planned test and verify the health
check and login before sharing the link. Suspending Render does not delete the
Neon database.

After the examination period, suspend both Render services first. When the
project no longer needs to be demonstrated, delete the two Render services,
remove the Neon project, and revoke the Render GitHub App installation. Those
final deletions are permanent and should only be performed after graduation and
after preserving any evidence required for submission.
