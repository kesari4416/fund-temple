# Temple Management System — Penalty Logic Fix

## Original Problem Statement
> "Need to correct all Logic and Penalty I have added the frontend and backend. Please verify and need to work all logic correctly"

Business rule clarified with the user:
- **Penalty = ₹25 per missed full calendar month** after the due date.
- **No grace period.**
- Applies across all modules where members can owe payment
  (Subscription Tariff, Festival, Death Tariff, Marriage, plus Interest).

## Architecture
- **Backend**: Django 4.2 + DRF (33 apps) on uvicorn :8001
- **Frontend**: React 18 + Vite (built bundle served via http-server on :3000)
- **DB**: MySQL/MariaDB `temple` (imported from `/app/temple_db.sql`, 71 tables)
- **Auth**: JWT (PyJWT) — `Authorization: <token>` header

## Setup steps performed in this session
1. Installed MariaDB server + client; created DB `temple` and user `appadmin:appadmin`.
2. Imported `/app/temple_db.sql` (replaced unsupported `utf8mb4_0900_ai_ci` with
   `utf8mb4_general_ci`).
3. Installed Python deps (Django 4.2.7, DRF, mysqlclient, etc.) into `/root/.venv`.
4. Created `/app/backend/server.py` (ASGI shim) so supervisor's
   `uvicorn server:app` command runs the Django ASGI app.
5. Added `/api/` URL prefix in `temple_proj/urls.py` so the K8s ingress
   `/api → :8001` rule works (legacy root-level routes preserved for
   internal callers).
6. Frontend baseURL changed to read `VITE_BACKEND_URL` from `.env` and
   append `/api/`.
7. `frontend/package.json` `start` script: `http-server dist -p 3000 -a 0.0.0.0
   -P http://localhost:3000?` (SPA fallback).

## Bugs found and fixed
1. **`interest/views.py` line 178** — penalty was only applied if interest_date
   was in the **same calendar year** as today and previous month. So any
   interest record from a prior year never got a penalty.  Replaced with
   `if interest_date + 1 month <= today` (works across years).
2. **No unified penalty engine** — each module set a one-time static penalty;
   nothing accumulated ₹25 per missed month. Created
   `amount/penalty_engine.py` with idempotent `recompute_all()` that:
   - Resolves due-date per row (sub_tariff.to_date, festival.penalty_start_date,
     death.penalty_apply_date, marriage.marriage_date).
   - Computes `missed_months = relativedelta(today, due).years*12 + .months`.
   - Sets `penalty_amount = 25 * months` and `penalty_balance = total -
     already_paid_penalty`.
   - Skips fully-paid rows. Multiple calls are safe (idempotent).
3. **`PendingPenaltyList.jsx`** — was a hardcoded mock. Wired to the new
   `/api/penalty/pending/` endpoint with category filter, search,
   "Recompute" button and live total.

## New API endpoints
- `GET  /api/penalty/pending/`   → list members with pending penalty
- `POST /api/penalty/recompute/` → force idempotent recompute, returns summary
- `GET  /api/penalty/summary/`   → numbers only

## Test results
- Engine unit tests: 9/9 passing (see `amount/penalty_engine.py` cases).
- Live data: 884 unpaid rows scanned → 778 have penalty → ₹3,40,225 total.
  Sample: M95 "L. Suresh", due 2024-04-08, today 2026-06-30 ⇒
  26 months × ₹25 = ₹650 (₹625 balance after one already-paid).

## What's been implemented (2026-06-30)
- [x] MySQL + Django app running in preview pod
- [x] Penalty engine with ₹25/missed-month rule
- [x] API endpoints for pending/recompute/summary
- [x] PendingPenaltyList page wired to real API
- [x] Interest year-condition bug fixed
- [x] App-wide visual refresh: emerald + saffron-gold theme (replaces red/maroon)
- [x] Plus Jakarta Sans body font, Fraunces for headings
- [x] Table styling refresh: green-tinted headers, zebra striping, hover row, larger row padding
- [x] Sign-in page: soft mint-cream background with green/gold radial gradients, emerald button

## Backlog / Future
- P1: Add a daily scheduled job (django-apscheduler is already installed)
  that calls `recompute_all()` automatically at midnight, so penalties
  appear without anyone visiting the list page.
- P1: Apply the same ₹25/missed-month rule inside Collection accept-payment
  flow so the penalty charged at payment time is always the engine value.
- P2: Per-tariff configurable penalty rate (instead of constant ₹25), if
  needed later.
- P2: WhatsApp / Print integrations on the Pending Penalty page (buttons
  exist but not wired yet).

## Test credentials
See `/app/memory/test_credentials.md`.
