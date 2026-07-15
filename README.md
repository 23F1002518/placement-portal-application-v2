# Placement Portal Application (V2)

A campus placement portal for an Admin (Institute), Companies, and Students — built as a
**Vue 3 SPA (Vite) + Flask REST API + SQLite + Redis (cache) + Celery (batch jobs)**, with JWT auth.

See `../V2-Migration-Plan.md` and `../New-requirements.txt` for the full spec and design.

## Architecture

```
backend/            Flask REST API (JSON), JWT auth, SQLAlchemy models, Celery tasks
frontend/           Vue 3 SPA built with Vite (.vue SFCs, Pinia) — Bootstrap 5 + Chart.js (npm)
```

The frontend is a **Vite project**: components are `.vue` Single-File Components, auth state
lives in a **Pinia** store, and Bootstrap 5 + Chart.js are bundled via npm. `npm run build`
emits `frontend/dist/`, which **Flask serves** at `/` (bundle under `/assets`); all data flows
through `/api/*` JSON endpoints. Vue Router (hash-based) handles client-side navigation. During
development, `npm run dev` runs the Vite dev server (with HMR) and proxies `/api` to Flask.

## Prerequisites

- Python 3.11+
- **Node.js 18+ and npm** (to build the Vue frontend)
- Redis server (cache + Celery broker/backend)
- A Gmail account with **2-Step Verification** enabled, for sending real email via SMTP

## 1. Backend setup

```bash
cd backend
python -m venv venv
source venv/Scripts/activate      # Windows Git Bash; use venv/bin/activate on Linux/macOS
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:
- `SECRET_KEY` / `JWT_SECRET_KEY` — set to random strings.
- `MAIL_USERNAME` / `MAIL_PASSWORD` / `MAIL_DEFAULT_SENDER` — your Gmail address + an
  **App Password** (generate one at https://myaccount.google.com/apppasswords — requires
  2-Step Verification). Do **not** use your normal Gmail password.
- Leave `REDIS_URL` / `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` as-is if running Redis
  locally on the default port.

`.env` is git-ignored — never commit real credentials.

## 1b. Frontend build (Vite)

The UI is a Vite-built Vue 3 SPA. Install its dependencies and build once so Flask can
serve it:

```bash
cd ../frontend
npm install
npm run build           # emits frontend/dist/ — Flask serves this at /
```

### Running frontend and backend as two separate servers

The frontend runs on its own server (Vite :5173) and the backend on its own (Flask
:5000); they talk **cross-origin** over `/api`. The backend URL the SPA calls is set by
`VITE_API_BASE_URL` (see `frontend/.env.example`):

- `frontend/.env.development` → used by `npm run dev` (defaults to `http://localhost:5000`)
- `frontend/.env.production`  → baked into `npm run build`; change it to the deployed
  backend URL before building.

If `VITE_API_BASE_URL` is left blank, the SPA uses relative `/api` paths instead — which
also works (Vite dev proxy, or Flask serving the built SPA same-origin).

Start the two servers in separate terminals:

```bash
# Terminal A — backend API (Flask)
cd backend && source venv/Scripts/activate && python app.py   # http://127.0.0.1:5000

# Terminal B — frontend dev server (Vite, hot reload)
cd frontend && npm run dev                                    # http://127.0.0.1:5173
```

Open **http://127.0.0.1:5173/** — the SPA there calls the Flask API on :5000. The backend
allows this via `CORS_ORIGINS` in `backend/.env` (default `*`; you can pin it to
`http://localhost:5173`).

> Flask still serves the built `frontend/dist/` at `http://127.0.0.1:5000/` as a fallback,
> so a same-origin single-server setup keeps working. If you open :5000 and get a
> "Frontend build not found" message, run `npm run build` first.

## 2. Install and start Redis

Redis is required for the cache and as the Celery broker/backend. It does **not**
ship with Windows, so install it with one of the options below, then start it.

### Option A — Native Windows build (simplest, matches `redis-server`)

1. Download the latest installer from
   **https://github.com/tporadowski/redis/releases** (grab `Redis-x64-*.msi`).
2. Run the MSI. Accept the default port **6379** and, when prompted, tick
   **"Add to PATH"** and **"Run as a Windows Service"** (so it starts on boot).
3. Verify it's up (from Git Bash or PowerShell):

   ```bash
   redis-cli ping      # → PONG
   ```

If you did not install it as a service, start it manually in its own terminal:

```bash
redis-server
```

### Option B — WSL2 (Ubuntu)

```bash
wsl --install                       # one-time, in PowerShell (admin); reboot if asked
# then, inside the Ubuntu shell:
sudo apt update && sudo apt install -y redis-server
sudo service redis-server start
redis-cli ping                      # → PONG
```

### Option C — Docker Desktop

```bash
docker run -d --name redis -p 6379:6379 redis:7
docker exec -it redis redis-cli ping   # → PONG
```

Whichever option you pick, the app connects to `redis://localhost:6379/0`
(the default in `.env`) — no code change needed. Confirm `redis-cli ping`
returns **PONG** before starting the Flask app or Celery.

> Troubleshooting: if Flask logs `ConnectionError: Error connecting to
> localhost:6379`, Redis isn't running — start it (Option A/B/C) and retry.
> Port already in use? Redis is already running; you're done.

## 3. Seed the database

The **single admin account is created automatically** the first time the database
is created (the app factory seeds it right after `db.create_all()`), so you can log
in as admin immediately after starting the app — no seed step required.

Run this script only when you also want **sample data** (companies, students,
drives, applications) so dashboards/reports/charts have something to show:

```bash
python create_initial_data.py --demo
```

(Running it without `--demo` just confirms the admin exists.)

Default admin login: `admin@placementportal.local` / `Admin@123`. Override the
credentials by setting `ADMIN_EMAIL` / `ADMIN_PASSWORD` in `.env` **before** the
database is first created.

## 4. Run the app (4 processes, each in its own terminal)

> Build the frontend first (`cd frontend && npm run build`, see step 1b) so Flask has
> `frontend/dist/` to serve. Alternatively run `npm run dev` as a 5th process for a live
> dev UI on :5173.

```bash
# Terminal 1 — Flask API + SPA
cd backend && source venv/Scripts/activate && python app.py

# Terminal 2 — Celery worker (executes tasks)
cd backend && source venv/Scripts/activate && celery -A celery_app.celery worker --loglevel=info

# Terminal 3 — Celery beat (fires the scheduled jobs)
cd backend && source venv/Scripts/activate && celery -A celery_app.celery beat --loglevel=info

# Terminal 4 — Redis (if not already running as a service)
redis-server
```

Open **http://127.0.0.1:5000/** in a browser.

## API surface

| Area | Prefix | Notes |
|------|--------|-------|
| Auth | `/api/register/student`, `/api/register/company`, `/api/login`, `/api/me` | JWT issued on login |
| Admin | `/api/admin/*` | dashboard, companies, students, drives, applications, reports — role=admin |
| Company | `/api/company/*` | dashboard, drive CRUD, applicants, application status, offer letters — role=company |
| Student | `/api/student/*` | dashboard, apply, applications, profile, resume, CSV export — role=student |
| Shared | `/api/drives`, `/api/offer-letter/<id>`, `/api/resume/<user_id>` | any authenticated role (with ownership checks) |

All write endpoints validate on the backend and return `422 {"errors": {...}}` on failure;
the frontend maps these to inline field messages.

## Caching (Redis, via Flask-Caching)

| Endpoint | TTL | Invalidated on |
|----------|-----|-----------------|
| `GET /api/admin/dashboard` | 300s | any company/drive/user status change |
| `GET /api/admin/reports` | 300s | any company/drive/user status change |
| `GET /api/drives` (approved+open list) | 120s | drive create/update/close/approve/reject |

## Batch jobs (Celery + Celery Beat)

| Job | Schedule | What it does |
|-----|----------|---------------|
| `tasks.daily_reminders` | Daily at `REMINDER_HOUR` (default 08:00) | Emails students about drives closing within `REMINDER_WINDOW_DAYS` (default 3) they're eligible for but haven't applied to, and their in-flight applications closing soon |
| `tasks.monthly_report` | 1st of each month, 06:00 | Emails the admin an HTML + PDF report of last month's drives/applications/selections |
| `tasks.export_applications_csv` | User-triggered (student dashboard) | Generates a CSV of the student's application history, emails a "ready" alert, frontend polls and downloads |

Email is sent via **Gmail SMTP**. If it fails (bad credentials, offline), the failure is
caught and logged — it never breaks the triggering request or task.

## Notes

- The database is created programmatically (`db.create_all()`) — never hand-created.
- Exactly one admin exists, created automatically by the app factory the first
  time the database is created (`ensure_admin()` in `app.py`, which
  `create_initial_data.py` also reuses); there is no admin registration endpoint.
- Duplicate applications are prevented at the DB level (unique constraint on
  `student_id` + `drive_id`) in addition to an API-level pre-check.
- Uploaded resumes, generated CSV exports, and offer letters are stored under
  `backend/static/uploads/` (git-ignored; `.gitkeep` files preserve the folder structure).
