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
4. **Layout overlap** — `SideMenuLayout` was `position: fixed` but the
   right-side `<Layout>` had no offset → header text and home image
   rendered under the sidebar.  Added `ContentLayout` styled component
   with `margin-left: 280px` (or 80 when collapsed), sticky TopHeader
   with z-index, `BodyContent` switched from `height: 80vh` to
   `min-height: calc(100vh - 70px)`, home image bounded by
   `objectFit: contain` and `maxHeight: calc(100vh - 180px)`,
   NavHeader temple-name uses flex + ellipsis.
5. **Chit-Fund EMI double-counting** (`collection/views.py` lines 624-632)
   — for Installment-Interest payments, `cash_inhand_amount` was
   adding both `temp_family.amount` (full EMI, already contains the
   interest portion) AND `temp_family.interst_amount` again, inflating
   cash-in-hand by the interest amount on every EMI payment.  Fixed to
   only add `amount + penalty_amount`.
6. **Chit-Fund loan edit not re-applied** (`interest/views.py` line 413-419)
   — when editing an existing chit-fund interest (loan), the old principal
   was reversed from `cash_inhand_amount` and `principal_given_amount`
   but the new principal was never re-applied.  Editing left chit-fund
   accounting out of sync.  Now reverses old AND applies new.

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

## What's been implemented (2026-02-10)
- [x] **Collection "Choose Member" dropdown bug fixed** — paid members no longer appear
  - Backend `collection/views.py` `get_select_member_collection`: fallback to newest active tariff when `type` is empty
  - Frontend `Collection.jsx` `handleCollectionType`: async, awaits `HandleSelectType` and uses fresh tariff id
- [x] **Chit Fund settlement redistribution** — exiting shares now split between Management + remaining investors
  - `chit_fund/views.py` `add_chit_fund_settlement_application_details`: largest-remainder proportional redistribution across mgmt + remaining active investors; `total_share_count = mgmt + investors` invariant preserved
  - Removed the double share_count/outer_invest_amount reduction previously done again in `add_chit_fund_settlement`
- [x] **Home Balance Sheet renamed** to "Temple Balance Sheet" (sidebar + page title + print header)
- [x] **Expense Subcategory** — Add Expense form now has a required "Subcategory" select with two options: `Chit Fund Expense`, `Temple Expense`
  - Backend: new `expense_subcategory` CharField on `ADDExpenseDetails` (migration 0002 applied)
  - Frontend: field added to Add Expense form, column added to Expense List (screen + print), row added to View Expense
  - CustomSelect now forwards `...rest` (data-testid, aria-*) to underlying AntdSelectStyle
- [x] **Balance sheet routing by subcategory** — expenses now split by subcategory
  - Temple Balance Sheet (`balancesheet_view`): all expense queries chained with `.exclude(expense_subcategory="Chit Fund Expense")` (legacy NULL rows preserved via ORM join semantics)
  - Chit Fund Balance Sheet (`balancesheet_chitfundview`): new `Chit_Fund_Expense` aggregation block on both `custom_date_range` and `custom_date` branches; adds to `total_debit_amount`
- [x] **Income Subcategory** — Add Income form now has a required "Subcategory" select with two options: `Chit Fund Income`, `Temple Income`
  - Backend: new `income_subcategory` CharField on `ADDIncomeDetails` (migration `income/0002` applied)
  - Frontend: field added to Add Income form, column added to Income List (screen + print), row added to Income View
- [x] **Balance sheet routing for income** — matches the expense pattern
  - Temple Balance Sheet: `ADDIncomeDetails.objects.filter(...).exclude(income_subcategory="Chit Fund Income")` (6 places); `Report...exclude(incomes=None).exclude(incomes__income_subcategory="Chit Fund Income")` (8 places)
  - Chit Fund Balance Sheet: new `Chit_Fund_Income` aggregation on both date branches. Filters by `date` field (aligned with expense) for consistency; adds to `total_credit_amount` and net balance.
- [x] Regression pytest suite `/app/backend/tests/` — 32+ tests across expense/income/collection/penalty/chit-fund settlement, all passing individually
- [x] **Chit Fund Details view** — new "Demand Share Amount" row (auto-computes as (Management Invested + Outer Invest + Profit) / Investers Share Count) plus adjusted "Investers Share Count" display to include Management (investers + management = displayed total). Both auto-update via `useMemo` when any dependency changes.
- [x] **Festival penalty cap** — Add / Edit Festival now enforces `penalty_amt <= 100` when `choice="Percentage"`. Server-side validation in `festival/serializers.py::validate` (falls back to `self.instance` for partial updates); frontend `antd Form.rule.validator` blocks submit inline. Removed the previous silent auto-swap to Amount when >100. 9 pytest cases + frontend E2E all green (iteration 7).

## What's been implemented (2026-07-23)
- [x] **Global 100% percentage cap** — strict server + client enforcement across every % input:
  - Chit Fund `set_profit_percent`, `set_intrest_percent` (`chit_fund/serializers.py::ChitFundsDetailsSerializer.validate`)
  - Interest `fix_interest_rate_percent` (when `interest_type_new='percentage'`) and `penalty_amount` (when `penalty_type='percentage'`) — `interest/serializers.py::validate`
  - Sub-Tariff `exp_amount` and `penalty_amt` when their type flag is `Percentage` — `sub_tariff/serializers.py::validate`
  - Death `tariff_peanalty` when `pen_amt_type='Percentage'` — `death/serializers.py::validate`
  - Set Tax `penalty_percentage` (frontend), plus AddChitFund UI validators for Set Profit / Set Fund Interest.
  - Removed the previous silent "flip to Amount at >100" behaviour in DeathForm and SetSubscriptionTariff — now the form blocks submission with an inline error message.
  - 11-case pytest suite `/app/backend/tests/test_percentage_caps.py` all green (JUnit `/app/test_reports/pytest/percentage_caps.xml`).
- [x] **Income / Expense Category fields removed** from Add Income / Add Expense forms. Categorisation now happens exclusively via the (already-existing) `income_subcategory` / `expense_subcategory` selectors (Chit Fund vs Temple). Backend accepts payloads with `category=null` (both FK columns were already nullable). Frontend still submits hidden `category` inputs for backwards compatibility. Verified with 2 backend pytest cases (POSTs without category → 201) and Playwright screenshots confirming labels are absent.
- [x] **Chit Fund List View — "Member 0" (Management share) card** rendered before the investor list with data-testids `member-0-card`, `member-0-name`, `member-0-invested-amt`, `member-0-share-count`, `member-0-application-date`, `member-0-settlement-date`.
- [x] **Application Date + Settlement Date (Application Date + 60 days)** now shown on every member card in ChitFundListView (`data-testid=member-{n}-application-date` / `member-{n}-settlement-date`), on the View Settlement Application modal (`settlement-view-application-date` / `settlement-view-settlement-date`), and as two separate columns in the Settlement Application list & print table. Business rule implemented via shared `computeSettlementDate` helper (`dayjs(applicationDate).add(60, 'day').format('YYYY-MM-DD')`).

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
