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

## What's been implemented (2026-02 fork — Per-category scoped PDFs)
- [x] **Every WhatsApp share now generates a category-scoped Balance Sheet PDF.** When the operator hits Share Statement on a "Subscription Tariff" collection, the recipient's PDF shows ONLY Subscription-Tariff balance-sheet rows + Subscription-Tariff pending dues. Same isolation for Festival / Death / Marriage.
- [x] **`public_member_statement_pdf`** now reads `?category=` from the query string and:
  - Maps the category → matching `TempleMemberReport.type_choice` enum values (e.g. `Death` → `["Death Tariff", "Death Tariff Penalty"]`)
  - Filters the balance-sheet reports by that enum set
  - Filters `_serialize_pending()` output to only the matching pending bucket(s)
  - Rewrites the header ("Subscription Tariff Statement" instead of "Temple Statement") and the PDF filename (`Subscription_Tariff_Statement_M225_2026-07-29.pdf`)
- [x] **`WhatsappStatementButton::buildMemberStatementLink`** now accepts a `category` argument and appends `?category=` to the URL. The `send()` handler passes `CollectionRecord.collection_category`.
- [x] **Verified live** for member 225 (J.Radhakrishnan) across all 4 categories:
  - Sub Tariff → Pending ₹925 · 1 BS row
  - Festival → Pending ₹3,750 · 0 rows in window
  - Death → Pending ₹600 · 0 rows
  - Marriage → Pending ₹0 · 0 rows
- [x] Interest categories (Chit Interest / Management Interest) already generate per-loan PDFs via the interest endpoint — inherent isolation, no changes needed.

## What's been implemented (2026-02 fork — Prominent Pending Balance)
- [x] **PDF now shows a prominent Pending Balance chip** right below the Payment Receipt block, tagged with the specific category (e.g. `Pending Balance (Festival) · Rs. 3,750.00`). Yellow highlight so the recipient sees it at a glance.
- [x] **"Pending Dues" section renamed to "Pending Balance"** and "Total Pending" renamed to "Total Pending Balance" — matches the terminology used in the app (`temple_mem_pending_amt` / "Total Pending Balance" label on Member Profile).
- [x] **Verified live** for member 225 Festival share: PDF renders Payment Receipt (COL9 · ₹500) + yellow `Pending Balance (Festival) Rs. 3,750.00` chip + full Pending Balance breakdown card + empty balance sheet (no fest transactions in year window).

## What's been implemented (2026-02 fork — PDF closing balance matches portal)
- [x] **PDF's `Total Pending Balance` and Balance Sheet closing row now source from the same field the portal uses** — `TempleMemberReport.objects.filter(members=member).last().balance_amt` (aka `temple_mem_pending_amt` in `family/views.py::single_member_view`). This guarantees the number a recipient sees in the shared PDF matches the "Total Pending Amount" the operator sees on the Member List / single-member data.
- [x] **Balance Sheet ledger table reverted to un-filtered** (all categories) so its Total row's Closing Balance equals the portal's Total Pending Balance. Category filter now scopes ONLY the receipt block + the yellow `Pending Balance ({category})` chip beneath it.
- [x] **Verified live** for member 225 (portal: ₹5,175.00) across three test PDFs:
  - Sub Tariff category → Chip ₹925 · Total ₹5,175 · Ledger closing ₹5,175 ✓
  - Festival category   → Chip ₹3,750 · Total ₹5,175 · Ledger closing ₹5,175 ✓
  - No category filter  → Chip ₹5,175 · Total ₹5,175 · Ledger closing ₹5,175 ✓

## What's been implemented (2026-02 fork — Hotfix: EC2 login broken)
- [x] **Root cause identified**: `pdf_views.py` had a top-level `from reportlab...` import. EC2 didn't have reportlab installed → Django refused to boot → whole app inaccessible → frontend showed "Not able to connect server".
- [x] **Lazy-guarded the reportlab import** — the module now wraps every reportlab symbol in a `try/except ImportError` that flips a `_REPORTLAB_AVAILABLE` flag. If false, both PDF views return HTTP 501 with a plain-text install hint: `Install with: pip install reportlab`. Backend boots cleanly either way.
- [x] **Added `reportlab>=4.0` to `backend/requirements.txt`** (preserving the file's original UTF-16 LE encoding + CRLF line endings). Any fresh deploy picks it up automatically.
- [x] **Verified live**: backend restart → login returns JWT · PDF endpoint still returns 200/application/pdf (reportlab pre-installed in pod).

## What's been implemented (2026-02 fork — Absolute-URL fallback for WhatsApp share)
- [x] **WhatsApp share was emitting relative `/api/...` URLs on EC2** because `VITE_BACKEND_URL` was empty in the production build.
- [x] **Added `resolveApiBase()` helper** in `WhatsappStatementButton.jsx` — tries the explicit override / `VITE_BACKEND_URL` first, then falls back to `window.location.origin`. Guarantees the shared URL is always absolute (scheme + host + path).
- [x] Both `buildMemberStatementLink` and `buildInterestStatementLink` now use `resolveApiBase(apiBase)` before concatenating the path.
- [x] Recommended env var for EC2 (optional but future-proof): `VITE_BACKEND_URL=https://temple.sparkcurv.in`.

## What's been implemented (2026-02 fork — Feb-2026 continuation session)
- [x] **Issue 1 (P0) — Consolidate Penalty Accrual.** The daily
  scheduled task in `my_tasks/views.py::subscription_delete` no longer
  accrues Interest / Penalty rows for `PeopleInterestDetails`. The
  interest-module section (was lines 727-1264) is now short-circuited
  by an early `return` immediately after the `##################interest
  module##########` marker, with a docstring explaining that
  `interest/overdue_views.py::_apply_for_record` is the sole idempotent
  source of truth (already invoked on every `interest_profile` GET and
  via `manage.py apply_periodic_interest_penalty`). Sub-Tariff /
  Festival / Death / Marriage / Rental sections still run unchanged.
  Verified live: `subscription_delete()` call does not grow
  `InterestPeopleReport` row count.
- [x] **Issue 2 (P1) — "Choose Person" now respects the picked pay_date.**
  `Collection.jsx::handleIntCategory` now sends `selected_date:
  selectedDate` in the payload to `POST /api/collection/chitname_
  withfiltering_category/`. Backend reads `selected_date` from
  `request.data` (falls back to `date.today()` on missing / malformed
  input) and uses it as `checking_date` throughout the endpoint —
  including replacing the two `month = datetime.now().month` /
  `year = datetime.now().year` calls with `checking_date.month/.year`
  so the "current month" window matches the operator's picked date.
  Post-filter step at the end of both branches (Interest / Interest
  with capital AND Installment Interest) drops any borrower whose
  next expected due date (`installment_date` for installment loans,
  `interest_apply_date + 1 month` for others) is strictly greater
  than `checking_date` AND who owes zero penalty / interest — those
  with outstanding penalty / interest keep surfacing regardless of
  date (owner rule "no penalty should be missed"). Verified via
  end-to-end curl: loan 32 (installment_date 2030-04-09, penalty
  ₹1100) → visible on all dates; same loan artificially set to
  penalty=0 + inst_date=2099-06-15 → correctly hidden on 2020-01-01.
- [x] **Issue 3 (P1) — `balancesheet_peopleinterestbalancesheet.due_date`
  mirror column.** New nullable `DateField due_date` added to
  `PeopleInterestBalanceSheet`. Migration `balancesheet/0002_
  peopleinterestbalancesheet_due_date.py` includes a `RunPython`
  backfill step that copies each linked loan's `installment_date`
  onto the new column. New `mirror_due_date` signal in
  `interest/signals.py` runs on every `post_save` of
  `PeopleInterestDetails` and updates every linked balance-sheet row
  atomically via `QuerySet.update(due_date=…)` (no recursion,
  idempotent via `.exclude(due_date=new_due_date)`). Live-verified
  against 200 records (all matched) plus a mutating round-trip
  (change `installment_date` → refresh_from_db → `due_date` mirrors).
- [x] **Issue 5 (P2) — Member Profile tabs now show for every member.**
  Removed the `Memberprofile?.member_tax_eligible &&` gate in
  `MemberProfile.jsx`. Balance Sheet + Collection History tabs are
  now visible for non-Sangam / non-tax-eligible members as well.
- [x] **Regression test file** `/app/backend/tests/test_penalty_fork_
  feb2026.py` — 4 tests, all passing:
  - `test_due_date_backfill_and_signal` — 200 rows in sync
  - `test_signal_mirrors_on_installment_date_change` — post_save
    signal roundtrip works
  - `test_legacy_cron_interest_neutralized` — `subscription_delete()`
    leaves `InterestPeopleReport` count unchanged
  - `test_selected_date_filter_via_django_orm` — sanity check for
    candidate data

## What's been implemented (2026-02 fork — HOTFIX: installment_delta bug)
- [x] **Penalty was silently ₹0 on every Installment Interest loan.** The
  ``interest/overdue_views.py::_installment_delta`` helper was treating
  ``PeopleInterestDetails.interest_period`` as the delta multiplier
  (i.e. "20 weeks between two due dates" for a 20-week loan). In
  reality ``interest_period`` is the TOTAL COUNT of installments (a
  20-week loan means 20 weekly installments, each cycle = 1 week).
  Result: ``installment_date`` computed by the signal jumped years
  into the future (loan 102 = C.Subash: 2029-10-23 instead of
  2025-01-28), the penalty walker's ``while due_date <= today`` loop
  never fired, and the "Chit Fund → Pending Amount → View details"
  table always showed ``Penalty ₹0.00``.
- [x] **Fixed** ``_installment_delta`` to return a single-cycle
  ``relativedelta`` (1 day / 1 week / 1 month) regardless of
  ``interest_period``.
- [x] **Added a safety bound** in ``_apply_for_installment``: the
  penalty walker now stops once ``cycle > interest_period`` so the
  ledger never accrues past the loan's terminating date (when
  ``interest_period > 0``).
- [x] **Recomputed installment_date for 199 existing loans** using the
  corrected helper. Sample verifications:
  - Loan 32 (10-month term, paid_counts=6): 2030-04-09 → 2025-01-09 ✓
  - Loan 102 C.Subash (20-week term, paid_counts=12): 2029-10-23 →
    2025-01-28 ✓
- [x] **Backfilled missing penalty rows for 69 installment loans**
  totalling **₹50,973.36** of previously-missed penalty accrual.
  Sample: C.Subash id=102 → 8 missed weekly cycles × ₹15 (3 % of
  ₹500 installment) = ₹120 now shown in Penalty / Penalty bal.
- [x] **Verified end-to-end** via ``GET /api/chit_fund/pending_borrowers/1/``:
  AMMAN FINANCE totals now report ``penalty_amt = ₹1,62,455`` (was
  ₹0 before the fix) and C.Subash row correctly shows
  ``penalty_amt=₹120, penalty_balance_amt=₹120``.

## What's been implemented (2026-02 fork — Chit Fund Expense Deduction)
- [x] **Chit Fund Expense now atomically debits ``profit_amount`` and
  ``cash_inhand_amount`` on the linked chit fund** (owner rule Feb 2026).
- [x] **``ADDExpenseDetails`` gained a ``chitt_fund`` FK + ``chit_fund_name``**
  string mirror (migration ``expense/0003_addexpensedetails_chit_fund_
  name_and_more.py``). Every ``expense_subcategory == "Chit Fund
  Expense"`` row now points to the owning ``ChitFundsDetails`` record.
- [x] **``expense/chit_fund_hooks.py``** — three helpers:
  ``check_chit_fund_cash`` (guards against negative cash-in-hand),
  ``apply_chit_fund_expense`` (debit), ``reverse_chit_fund_expense``
  (credit-back). All operate on ``Decimal`` to avoid float drift.
- [x] **``expense/views.py``**
  - **POST** ``add_expen_details``: guard cash before save, debit chit
    fund after save.
  - **PUT** ``edit_expen_details``: reverse-then-reapply with
    ``refresh_from_db()`` on both objects so same-chit-fund amount
    tweaks don't stomp each other's writes.
  - **PATCH**: same reverse-then-reapply pattern.
  - **DELETE**: credit-back before ``customer.delete()``.
  - Cross-flow rejection ``HTTP 302`` with friendly message:
    ``"Insufficient chit-fund cash. Only Rs. 726000 available in
    AMMAN FINANCE"``.
- [x] **Frontend AddExpense form** (``AddExpense.jsx``): new **Chit
  Fund** dropdown, visible + required only when Subcategory =
  "Chit Fund Expense". Options fetched from
  ``/api/chit_fund/get_active_chitfunds/``. Included in POST + PUT
  payload as ``chitt_fund`` (id) + ``chit_fund_name`` (string).
  Update-mode pre-fills both fields on Edit.
- [x] **ExpenseList** — new "Chit Fund" column on main + print tables
  (renders "-" for Temple Expense rows).
- [x] **ViewExpensePage** — new "Chit Fund" row, shown only for Chit
  Fund Expense records.
- [x] **Balance Sheet payload** — ``dic1['Chit_Fund_Expense']['details']``
  now includes ``chit_fund_name`` + ``chit_fund_id`` per row so the
  eventual UI table can group by chit fund.
- [x] **End-to-end verified**:
  - START chit AMMAN FINANCE profit=₹9,75,550 cash=₹7,25,500
  - ADD ₹500 → 9,75,050 / 7,25,000 (both -500) ✓
  - EDIT 500→200 → 9,75,350 / 7,25,300 (net -200 from start) ✓
  - DELETE → back to 9,75,550 / 7,25,500 ✓
  - Overspend guard: rejected with "Insufficient chit-fund cash" ✓

## What's been implemented (2026-02 fork — Chit Fund Expense Row on Balance Sheet)
- [x] **Chit Fund Balance Sheet Debit column now surfaces the "Chit
  Fund Expense" total as an expandable line-item row.** Fixes the
  ₹100 mismatch where the Debit Total silently included Chit-Fund
  Expenses but no visible row explained the number.
- [x] **`SheetView.jsx`** — new ``ChitFundExpenseView`` component
  renders a 4-column table (``Sl No | Chit Fund | Expense Name |
  Amount``), matching the existing "Interest Given / Profit
  Distribution" styling.
- [x] **`SheetPage.jsx`** — new expand/collapse state
  (``chitFundExpenseModal``), toggle handler
  (``ChitFundExpenseToggle``), and a rendered row placed right after
  "Profit Distribution" in the Debit column. Uses the same
  ``MdOutlineKeyboardArrowDown / MdKeyboardArrowRight`` chevron
  affordance as the other rows.
- [x] **Backend verified**: ``POST /api/balancesheet/balancesheet_
  chitfundview/`` returns ``Debit.Chit_Fund_Expense.total_amount`` +
  ``details[]`` containing ``chit_fund_name``, ``expense_name``,
  ``amount`` per row. Confirmed with live curl on a fresh row
  (Rs 250 UI Sheet Test, AMMAN FINANCE) — payload contains matching
  entry and the ``total_debit_amount`` scales up accordingly.

## What's been implemented (2026-02 fork — Live Principal Amt Preview)
- [x] **Collection form now shows a live "remaining Principal Amt"
  as the operator increases "No of Count".** Formula:
  ``displayed principal_amt = _original_principal_amt −
  (installment_amt × no_count_install)``, clamped at 0.
- [x] **Purely UI arithmetic — DB never touched.** Verified against
  ``collection/views.py`` lines 418-420 / 467-469 / 571-573 —
  backend reads ``principal_balance`` straight from the DB and
  subtracts ``temp_family.amount`` (the paid instalment amount).
  The form's ``principal_amt`` is display-only and is disregarded
  when computing the actual debit.
- [x] **Frontend (only file touched)**:
  ``/app/frontend/src/modules/CollectionDetails/Partials/Collection.jsx``
  - Hidden ``_original_principal_amt`` mirror field added to the
    JSX under the "Principal Amt" input.
  - Seeded from ``PlaceFindMem?.principal_balance`` on borrower
    pick, and from ``record?.principal_amt`` on Edit.
  - Included in every ``form.resetFields([...])`` call (category
    switch, principal/interest checkbox toggles) so the mirror
    matches the visible field.
  - ``handlePricipalPay`` extended: for Installment Interest branch
    only, subtracts the computed ``PrincipalAmount`` from the hidden
    original and pushes the result into the visible
    ``principal_amt``.  When No of Count is cleared / 0, the field
    restores to the pristine original balance.
- [x] **Regression-safe**: Non-Installment branch, Edit / Delete /
  Insufficient-cash flows all untouched.

## What's been implemented (2026-02 fork — Add Chit Fund UX Polish)
- [x] **"Cash-In-Hand which is null" warn replaced with actionable
  guidance.** The old toast printed the raw string ``${GetCashInHandAmt}``
  which rendered as *"which is null"* whenever the treasury
  ``ManagementTreasure.cash_in_hand`` field was NULL or the row
  didn't exist. Now three distinct messages fire:
  - No treasure record / null cash → *"Cash-In-Hand is not yet set
    for this temple. Please add an Income entry (opening balance)
    before creating a chit fund."*
  - Cash exists but management amount exceeds it → *"Management
    Amount (Rs. X) exceeds current Cash-In-Hand (Rs. Y). Please
    reduce the Share Count or top up the treasury first."*
- [x] **Auto-refetch cash-in-hand** on every ``handleManagementCalculation``
  call so a stale ``useState({})`` initial value or a tab-side
  change never sneaks through.
- [x] **Live Cash-In-Hand hint under Management Amount field** —
  ``"Cash-In-Hand available: ₹ X"`` in grey, or the red *"not yet
  set — add an Income entry first"* when the value is missing.
- [x] **Add / Update buttons now disabled** while cash-in-hand is
  either not loaded or the entered Management Amount exceeds
  available cash — the operator can no longer submit an
  under-funded chit fund.
- [x] **File touched (only 1)**:
  ``/app/frontend/src/modules/ChitFund/Partials/AddChitFunds/Partials/AddChitFund.jsx``
- [x] **Bundle rebuilt + supervisor restarted.**

## Backlog / Future
- P1: Run `testing_agent_v3_fork` to verify the QA Excel bug fixes carried over from the previous session (Marriage date picker, Family Balance Sheet 500, Interest negatives, Festival dropdown). Blocked in this pod because MariaDB is not installed; user should trigger on their EC2.
- P1: Remaining QA Excel bugs — Notification WhatsApp missing fine amounts, Agent collection list routing, Member list active/inactive logic, "Total Due" vs "Total Collected" split in Collection Details.
- P1: Add a daily scheduled job (django-apscheduler is already installed) that calls `recompute_all()` automatically at midnight.
- P1: Apply the same ₹25/missed-month rule inside Collection accept-payment flow so the penalty charged at payment time is always the engine value.
- P2: Refactor `/app/backend/collection/views.py` (4600+ lines) into services / thinner views.
- P2: Per-tariff configurable penalty rate (instead of constant ₹25).
- P2: WhatsApp / Print integrations on the Pending Penalty page.
- P2: User EC2 login returning HTTP 204 — needs their Nginx/Django infra debugging.

## What's been implemented (2026-02 fork — EC2 subcategory column fix)
- [x] **Root cause of 500 error on Add Income/Expense with new categories**: Django migration `0002_addexpensedetails_expense_subcategory` and `0002_addincomedetails_income_subcategory` were applied on preview but NOT on the EC2 database. The frontend now sends `expense_subcategory` / `income_subcategory` in the payload; MySQL rejected the INSERT with "Unknown column" → 500. The user assumed a missing table.
- [x] **Delivered `/app/scripts/fix_income_expense_subcategory_ec2.sql`** — safe idempotent script that adds the two columns (guarded by `information_schema.COLUMNS` check) and records the migrations in `django_migrations` so `manage.py migrate` stays in sync.
- [x] **Hardened `AddExpense.jsx::onFinish`** — previously the payload was only built when `TransactionData` was strictly `"Online"` or `"Offline"`; if the payment_mode `onChange` state hadn't captured yet, `AddExpense(undefined)` was sent silently → "form not submitting" symptom. Now the payload is always constructed from `data` + captured dates.
- [x] Local preview verified: add_expen_categry, add_income_categry, add_expen_details (Chit Fund + Temple), add_income_details (Chit Fund + Temple with new categories `chitfund`/`temple`) all return HTTP 201.

## Test credentials
See `/app/memory/test_credentials.md`.
