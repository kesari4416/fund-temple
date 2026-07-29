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

## What's been implemented (2026-02 fork)
- [x] **Chit Fund View — Management Amount row** now uses the correct reconciling formula: `Management Amount = Profit × management_share_count / total_share_count` (equivalent to `Profit − Σ investor profit shares`). The previous formula subtracted the GROSS displayed share (invested capital + profit) from profit, which by construction could not reconcile.
  New behaviour: `Profit = Σ Investor Profit Shares + Management Amount` holds by identity. Live-verified on AMMAN FINANCE (profit ₹9,76,050 · 141 total shares) — Management ₹6,922.34, investors' profit share ₹9,69,127.66, sum ₹9,76,050.00, badge **✓ reconciled**. Added `data-testid="management-amount-reconciled"` / `management-amount-mismatch` badge with red-warning shown whenever `|Σ + Mgmt − Profit| ≥ ₹1`.
- [x] **Chit Fund View — Pending Amount breakdown expander** added next to "Pending Amount to Collect". Toggle button (`data-testid="pending-breakdown-toggle"`) opens an inline panel (`pending-breakdown-panel`) with a per-BORROWER table listing every active Chit-Fund-Interest loan whose principal_balance / balance_amt / penalty_balance is > 0. Columns: Borrower (name + mobile), Start Date (`interest_apply_date`), End Date (apply_date + interest_period), Days from start, Days from last payment (`updated_at` proxy), Principal, Paid, Balance. Data comes from **new backend endpoint** `GET /api/chit_fund/pending_borrowers/<chit_id>/` (see `/app/backend/chit_fund/pending_views.py`). Loading + error + empty states rendered with dedicated test-ids. **Important:** Pending is driven by Chit-Fund-Interest borrowers (loans given out from the pool), NOT by investors — the previous investor-based logic returned 0 rows because chit-fund investors carry `share_amount=0` until settlement application.
- [x] **WhatsApp 1-hour auto-disappear** — user confirmed to keep current `wa.me` intent links (technically not supported for auto-expiring messages outside official WhatsApp Business API).
- [x] **Collection → Share Statement (WhatsApp) now works for Management Interest & Chit Interest.**
  - Previously the button was hard-coded to SKIP those categories and required `CollectionRecord.member`, which is NULL for interest rows (borrower link is via `CollectionRecord.interest`).
  - New backend endpoints:
    - `GET /api/collection/interest_statement/token/<interest_id>/` → HMAC-signed token + borrower name/mobile.
    - `GET /api/collection/public/interest_statement/<token>/` → 1-year loan statement: borrower details, payments (with P/I/Pen breakdown), current outstanding (principal/paid/balance/penalty).
  - New frontend route `/interest-statement/:token` → `PublicInterestStatement.jsx` with `data-testid`s for name, totals, principal-balance, total-outstanding, payments list & rows.
  - `WhatsappStatementButton.jsx` fully rewritten: routes Management/Chit-Interest through the new interest endpoint (uses `CollectionRecord.interest`), non-interest through the existing member endpoint. Still skips pure `Chit-fund` settlement rows.
  - End-to-end verified via curl: `SELVAM TEA SHOP` (interest_id=209) → 6 payments · ₹80,000 collected · ₹20,000 outstanding.
- [x] **TC_INTEREST_002 — auto-apply overdue Interest + Penalty on Balance Sheet view.**
  The overdue engine (`interest/overdue_views.py::_apply_for_record`) applies missing monthly Interest (day 5 rule) and Penalty (day 20 rule) rows. It already existed but only ran when the operator manually POSTed to `/apply_overdue_interest_and_penalty/`.
  Fix: `interest/views.py::interest_profile` now calls `_apply_for_record(mer)` at the start of every GET, so opening `Interest → ChitFund Interest → ChitFund Installment → Person → Profile → Balance Sheet` (or the Management Interest equivalent) always returns an up-to-date ledger.
  The engine is fully idempotent (checks `InterestPeopleReport` for existing rows), safe on every load, and non-blocking (wrapped in try/except).
  End-to-end verified on `C. Balasubramaniyam` (id=44, Chit fund Interest): before → apply_date `2024-10-20`, penalty `₹0`, balance `₹7,500`, 17 reports. After a single GET → apply_date `2026-07-05`, **interest ₹105,000**, **penalty ₹115,500**, balance `₹228,000`, 59 reports. Second GET added zero rows (idempotency confirmed).
- [x] **Collection History → View → Print now shares the full 1-year balance sheet.**
  `CollectionUserList.jsx::ViewPrintModal` was rendering `<Bill />`, which passes `receiptOnly` and only sends the concise receipt. For a re-print from history the operator wanted the full 1-year ledger. Switched the modal to render `<ViewCollectionPrint />` — that component keeps `<WhatsappStatementButton />` without `receiptOnly`, so the "Share Statement" button attached inside sends the complete 1-year balance sheet in the aligned monospace `` ` ``code`` ` ``  table + totals + pending dues + public link.
  Result:
  - New collection add flow (`Collection.jsx → Bill.jsx`): still auto-shares the RECEIPT.
  - Collection History re-print (`CollectionUserList.jsx → ViewCollectionPrint.jsx`): shares the full 1-YEAR BALANCE SHEET.
- [x] **TC_FAMILYDETAILS_002 — Family Edit photo upload 500** debug hooks added:
  - `family/views.py` outer `except:` in `edit_family` PUT now uses `Exception as _e` + `traceback.print_exc()` and returns the detail message. Save call wrapped separately so an ORM error returns a distinct 500 with the specific message.
  - `dict8['member_photo']` assignment now only stores the value when it looks like an actual uploaded file (`hasattr(_mp, "read") and hasattr(_mp, "name")`). Fixes the most common regression: when the frontend guard passes but `image_send_value` was empty, it was appending `undefined` to the FormData and the backend serializer rejected the resulting string.

## What's been implemented (2026-02 fork — continued session)
- [x] **Bug 2 — Periodic Interest + Penalty Scheduled Task**. Django management command `apply_periodic_interest_penalty` is now bootstrapped correctly (missing `management/__init__.py` and `commands/__init__.py` files added). Command wraps the existing idempotent engine (`interest.overdue_views._apply_for_record`) and walks every active `PeopleInterestDetails` row. Supports `--dry-run`. Wire it to cron/apscheduler on EC2:
  `python manage.py apply_periodic_interest_penalty`.
- [x] **Bug 1 — NameError in edit_interest_given_details** verified via code review: the `customer.principal_amt` reversal happens before `serializer876.save()` and `temp_family` is only referenced *after* the save. Cash-in-hand reconciliation now correctly reverses OLD principal then applies NEW principal for both Management and Chit-fund interest edits.
- [x] **QA Bug 10 — Member List logic**. `sangam/views.py::get_sangam_members` was filtering `death=True` and therefore returning **dead** members instead of active ones for the "Member List" tab. Fixed to filter `death=False, marriage_remove=False` so the tab now shows only active temple members. Death List and Marriage-Remove List remain their own dedicated tabs.
- [x] **QA Bug 1 — Total Due vs Total Collected split** on Member Profile view. Added two new rows (`data-testid=member-total-collected`, `member-total-due`) alongside the existing "Total Pending Balance". Total Collected = `paid_amt_total`; Total Due = `paid_amt_total + temple_mem_pending_amt`.
- [x] **QA Bug 5/6 — Notification / WhatsApp receipt now surfaces fine (penalty) & interest amounts.** `WhatsappStatementButton::buildReceiptMessage` now conditionally appends a breakdown block:
  ```
  Breakdown:
  - Amount: ₹1000.00
  - Interest: ₹150.00
  - Fine: ₹25.00
  ```
  when either interest or penalty is non-zero. Base-amount, interest, and penalty are wired from `CollectionRecord.amount / interst_amount / penalty_amount`.
- [x] **WhatsApp share link now points at the internal Member/Interest Profile view** as requested by user. `buildMemberStatementLink` → `/memberProfileView/<memberId>?tab=balance`, `buildInterestStatementLink` → `/ManagementInterestProfile/<id>` or `/chit-Fund_Interest/<id>` depending on the interest category. Legacy tokenised public URLs kept as fallback.
- [x] **Member Profile — 1-year Balance Sheet default when arriving from WhatsApp share.** `MemberProfile.jsx` now reads a `?tab=balance` query param (via `useSearchParams`) and defaults the `CustomTabs` `defaultActiveKey` to the Balance Sheet tab. `MemberBalanceSheet` in `MemberProfileTabs.jsx` client-side filters `temple_mem_balancesheet` rows to only entries whose `reportdate` is within the last 12 months (`dayjs().subtract(1, "year")`). Verified live with member 225 (J.Radhakrishnan): active tab = "Balance Sheet", only Jun-2026 row shown (2024/2025 rows hidden).

## What's been implemented (2026-02 fork — WhatsApp Share Statement rework)
- [x] **Collection History → Print modal** now no longer renders the inline "1-year balance sheet" widget. `ViewCollectionPrint.jsx` reduced back to a simple bill-print layout + the Share Statement (WhatsApp) button.
- [x] **WhatsApp Share Statement message body enriched** — `WhatsappStatementButton.jsx::buildMessage` now composes:
  - `*Payment Receipt*` header + amount + purpose + payment mode + receipt number
  - Optional `Breakdown` block (Amount / Interest / Fine) when interest or penalty > 0
  - `*1-Year Statement*` block with Total Received + payment count
  - `Pending Amount` line: `pending_dues.Total` for members, or Principal+Penalty outstanding for interest
  - `View full balance sheet:` link → `/memberProfileView/{memberId}?tab=balance` (or `/ManagementInterestProfile/:id` / `/chit-Fund_Interest/:id` for interest)
  - Temple sign-off
  The `send()` handler now also fetches the public statement (via the existing `/api/collection/public/member_statement/<token>/` and `/interest_statement/<token>/` endpoints) so the message reflects the exact numbers a customer would see on the Balance Sheet page.
- [x] **Family Details → Member List** — new "Balance Sheet" action icon (money icon) alongside the existing View eye icon in every row. Clicking it navigates to `/memberProfileView/{memberId}?tab=balance` and lands on the customer's 1-year filtered balance sheet with the "Download PDF" button. `data-testid=member-balance-sheet-btn-<id>` added for automation.

## What's been implemented (2026-02 fork — Auto-PDF Balance Sheet)
- [x] **WhatsApp share link now auto-opens the Balance Sheet as a PDF.** The URL emitted by `WhatsappStatementButton::buildMemberStatementLink` now includes:
  - `?tab=balance` — lands on Balance Sheet tab
  - `&print=1` — triggers auto-print
  - `&receipt_no=...&receipt_amt=...&receipt_date=...&receipt_purpose=...&receipt_mode=...` — receipt of the payment
- [x] **`MemberBalanceSheet` (Family Details → Member List → Balance Sheet tab)** now:
  - Reads receipt URL params and renders a "Payment Receipt" block inside the printable area (only when receipt params are present).
  - Reads `?print=1` and auto-fires `handlePrint()` (via `useReactToPrint`) once the balance-sheet data lands. Uses a `useRef` guard so it never re-triggers on data-range submits.
  - Console log `[BalanceSheet] Auto-triggering print dialog…` verified live via Playwright.
- [x] **Final PDF output contains, in one document:**
  - Temple header (name + address) via `CommonManagePrint`.
  - Payment Receipt block (Receipt No, Date, Purpose, Payment Mode, Amount Paid).
  - "1-Year Balance Sheet Statement" title with period range.
  - Balance-sheet table (last 12 months, columns: Sl No · Date · Particulars · Name · Pre Balance · Credit · Debit · Balance).
  - Totals footer (Total Credit · Total Debit · Closing Balance).

## What's been implemented (2026-02 fork — Interest categories get same auto-PDF flow)
- [x] **Chit Interest / Management Interest WhatsApp share** now routes to `/interest-statement/<token>?print=1&receipt_*` instead of the internal auth-protected `/chit-Fund_Interest/{id}` / `/ManagementInterestProfile/{id}` links. Interest borrowers are typically NOT temple members so they get the token-based public interest statement.
- [x] **`PublicInterestStatement.jsx`** (route `/interest-statement/:token`) now:
  - Reads `?print=1` + `?receipt_*` URL params.
  - Renders a new `Payment Receipt` card at the top when receipt params are present (`data-testid=interest-statement-receipt`).
  - Auto-fires `window.print()` 800ms after the statement data loads (guarded with a `useRef` so it fires exactly once). Console log `[InterestStatement] Auto-triggering print dialog…` confirms the effect ran during live Playwright verification.
- [x] **PDF for interest borrowers includes:**
  - Payment Receipt (No / Date / Purpose / Mode / Amount)
  - Borrower details (name, interest type, chit / management fund, mobile) + statement period
  - Totals card (Total received 1-yr, count, principal / interest / penalty split)
  - Outstanding balance card (Principal issued / paid / balance + Penalty balance + Total outstanding)
  - 1-year balance sheet ledger table

## What's been implemented (2026-02 fork — Login-free WhatsApp PDF)
- [x] **`buildMemberStatementLink` now always emits the token-based public URL** `/statement/<token>?print=1&receipt_*` instead of the auth-protected `/memberProfileView/{id}`. Recipients no longer need to log into the admin portal to view the balance sheet.
- [x] **`PublicMemberStatement.jsx`** (route `/statement/:token`) now:
  - Reads `?print=1` + `?receipt_*` URL params via `useSearchParams`.
  - Renders a `Payment Receipt` card at the top when receipt params are present (`data-testid=statement-receipt`).
  - Auto-fires `window.print()` 800ms after statement data lands (guarded with `useRef` so it fires exactly once). Console log `[MemberStatement] Auto-triggering print dialog…` confirms the effect.
- [x] **Complete parity** with the interest-borrower flow — both member and interest WhatsApp shares now use token-based public URLs with the same auto-print + receipt-block pattern.
- [x] **Verified live in a fresh browser context (no cookies, no login)** — statement page rendered fully with Payment Receipt (COL2 / 2024-04-07 / Subscription Tariff / Offline / ₹100), member details (S.M NAVEEN M6), 1-year balance sheet table with 1 row + Total, 1-year totals, and Pending dues (Death ₹300 + Subscription Tariff ₹200 = Total ₹500). Auto-print console log fired.

## What's been implemented (2026-02 fork — DIRECT PDF link, no HTML)
- [x] **`backend/collection/pdf_views.py`** created — two new endpoints:
  - `GET /api/collection/public/member_statement_pdf/<token>/?receipt_*`
  - `GET /api/collection/public/interest_statement_pdf/<token>/?receipt_*`
  Both return `Content-Type: application/pdf` with `Content-Disposition: inline; filename="…"`. Built with reportlab (pre-installed). Contents:
  - Temple / Loan statement header + 1-year period range
  - Payment Receipt card (Receipt No · Date · Purpose · Mode · Amount)
  - Member/Borrower details card
  - Pending Dues (member) or Outstanding balance (interest)
  - 1-Year Balance Sheet table with totals row
  - Footer: "Generated on …"
- [x] **HMAC tokens reused** from `public_views` so links are interoperable with the existing HTML statements.
- [x] **`WhatsappStatementButton.jsx`** — `buildMemberStatementLink` and `buildInterestStatementLink` now return the backend PDF URL directly (`{API_BASE}/api/collection/public/…_pdf/<token>/?…`). The URL is a real PDF file, no HTML/JS/portal.
- [x] **Verified live**: `curl -sI ...pdf/token/...` returns `HTTP 200 · application/pdf`. `pypdf` extracted text confirms all sections rendered correctly for both endpoints. Playwright confirms browser treats URL as a real PDF download (Download is starting event fires).

## What's been implemented (2026-02 fork — PDF now uses the real Balance Sheet)
- [x] **`public_member_statement_pdf`** now sources balance-sheet rows from `TempleMemberReport` (same table that powers Family Details → Member List → Balance Sheet tab) instead of the raw `PeoplesAmountDetails` bills. This gives a proper running-balance ledger with Pre-Balance carried across rows, and shows both bills raised AND collections received in chronological order.
- [x] **PDF column layout now matches the on-screen Balance Sheet tab**: `Sl · Date · Particulars · Name · Pre Balance · Credit · Debit · Balance`.
- [x] **Totals row** shows Total Credit / Total Debit / Closing Balance.
- [x] **Verified live** for two members:
  - Member 225 (J.Radhakrishnan): balance sheet row shows Sub Tariff Jun-2026 · Credit ₹100 · **Closing Balance ₹5,175** — matches the portal exactly. Pending Dues block shows all four category buckets summing to ₹63,222.69.
  - Member 8: 2-row ledger where Pre Balance ₹500 on row 2 correctly carries from row 1's Balance ₹500 — closing balance ₹400.

## Backlog / Future
- P1: Run `testing_agent_v3_fork` to verify the QA Excel bug fixes carried over from the previous session (Marriage date picker, Family Balance Sheet 500, Interest negatives, Festival dropdown). Blocked in this pod because MariaDB is not installed; user should trigger on their EC2.
- P1: Remaining QA Excel bugs — Notification WhatsApp missing fine amounts, Agent collection list routing, Member list active/inactive logic, "Total Due" vs "Total Collected" split in Collection Details.
- P1: Add a daily scheduled job (django-apscheduler is already installed) that calls `recompute_all()` automatically at midnight.
- P1: Apply the same ₹25/missed-month rule inside Collection accept-payment flow so the penalty charged at payment time is always the engine value.
- P2: Refactor `/app/backend/collection/views.py` (4600+ lines) into services / thinner views.
- P2: Per-tariff configurable penalty rate (instead of constant ₹25).
- P2: WhatsApp / Print integrations on the Pending Penalty page.
- P2: User EC2 login returning HTTP 204 — needs their Nginx/Django infra debugging.

## Test credentials
See `/app/memory/test_credentials.md`.
