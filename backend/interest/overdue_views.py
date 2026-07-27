"""
On-demand backfill of missed overdue Interest + Penalty rows.

Business rule
-------------
For a Management/Chit Fund interest record, the app applies:

    * On day 5 of every month after `interest_date` → an *Interest* charge
      (either flat amount or a % of the current principal, depending on
      `interest_type_new`).
    * On day 20 of the same month, if the interest is still unpaid →
      a *Penalty* charge (either flat amount or a % of the outstanding
      interest, depending on `penalty_type`).

Historically these rows were only appended once — at record creation
(see `add_interest_given_details`). When time passes without payment,
neither the interest for the newer months nor the penalty is re-applied
to the balance sheet, leading to under-reporting of dues.

This module walks each month from the last-applied month up to today,
appends the missing Interest / Penalty rows to `PeopleInterestBalanceSheet`
and `InterestPeopleReport`, and updates `interest_apply_date` accordingly.
Idempotent — running it twice does nothing the second time.
"""
from __future__ import annotations

import datetime

from dateutil.relativedelta import relativedelta
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from interest.models import PeopleInterestDetails
from balancesheet.models import PeopleInterestBalanceSheet
from reports.models import InterestPeopleReport
from token_app.views import token_checking


def _month_key(dt: datetime.date) -> tuple[int, int]:
    return dt.year, dt.month


def _first_pending_month(interest_date: datetime.date, apply_date: datetime.date | None):
    """
    Return (year, month) for the first month whose interest has NOT been
    applied yet. Interest for month M is applied on day 5 of month (M+1).
    """
    reference = apply_date or interest_date
    nxt = reference + relativedelta(months=1)
    return nxt.year, nxt.month


def _apply_for_record(record: PeopleInterestDetails) -> dict:
    """Append missing Interest + Penalty rows for a single record."""
    try:
        bal = PeopleInterestBalanceSheet.objects.get(interest_id=record.id)
    except PeopleInterestBalanceSheet.DoesNotExist:
        return {"interest_id": record.id, "applied_months": [], "skipped": "no balance sheet"}

    today = datetime.date.today()
    applied = []
    y, m = _first_pending_month(record.interest_date, bal.interest_apply_date)

    while True:
        checking_day = datetime.date(y, m, 5)
        penalty_day = datetime.date(y, m, 20)

        # Nothing to do until we've reached the 5th of the target month.
        if checking_day > today:
            break

        # ---- 1) Interest for that month --------------------------------
        already_charged = InterestPeopleReport.objects.filter(
            interest=record,
            reportdate=checking_day,
            type_choice="Interest",
        ).exists()
        if not already_charged:
            if (record.interest_type_new or "").lower() == "amount":
                inc = float(record.fix_interest_rate_percent or 0)
            else:  # percentage (default)
                inc = (float(bal.principal_balance or 0) * float(record.fix_interest_rate_percent or 0)) / 100.0
            if inc > 0:
                bal.intrest_amt = float(bal.intrest_amt or 0) + inc
                bal.intrest_balance_amt = float(bal.intrest_balance_amt or 0) + inc
                bal.credit_amt = float(bal.credit_amt or 0) + inc
                bal.balance_amt = float(bal.balance_amt or 0) + inc
                bal.save()
                InterestPeopleReport.objects.create(
                    management_profile=record.management_profile,
                    interest=record,
                    reportdate=checking_day,
                    credit_amt=inc,
                    balance_amt=bal.balance_amt,
                    type_choice="Interest",
                    created_by=record.created_by,
                )
                applied.append({"month": checking_day.isoformat(), "interest": inc})

        # ---- 2) Penalty on day 20 if still unpaid ----------------------
        if penalty_day <= today and float(bal.intrest_balance_amt or 0) > 0:
            already_penalised = InterestPeopleReport.objects.filter(
                interest=record,
                reportdate=penalty_day,
                type_choice="Penalty",
            ).exists()
            if not already_penalised:
                if (record.penalty_type or "").lower() == "amount":
                    pen = float(record.penalty_amount or 0)
                else:  # percentage
                    pen = (float(bal.intrest_balance_amt or 0) * float(record.penalty_amount or 0)) / 100.0
                if pen > 0:
                    bal.penalty_amt = float(bal.penalty_amt or 0) + pen
                    bal.penalty_balance_amt = float(bal.penalty_balance_amt or 0) + pen
                    bal.credit_amt = float(bal.credit_amt or 0) + pen
                    bal.balance_amt = float(bal.balance_amt or 0) + pen
                    bal.save()
                    InterestPeopleReport.objects.create(
                        management_profile=record.management_profile,
                        interest=record,
                        reportdate=penalty_day,
                        credit_amt=pen,
                        balance_amt=bal.balance_amt,
                        type_choice="Penalty",
                        created_by=record.created_by,
                    )
                    applied.append({"month": penalty_day.isoformat(), "penalty": pen})

        # Advance to next month.
        bal.interest_apply_date = checking_day
        bal.save()
        nxt = checking_day + relativedelta(months=1)
        y, m = nxt.year, nxt.month
        # Safety: don't loop past today's month.
        if datetime.date(y, m, 5) > today:
            break

    return {"interest_id": record.id, "applied_months": applied}


@api_view(["POST"])
def apply_overdue_interest_and_penalty(request):
    """
    Backfill Interest + Penalty rows for every active interest record.

    Query / body params:
      * ``id``      – limit run to a single interest record (int).
      * ``dry_run`` – 1/true → compute totals without touching the DB.
    """
    rejin = token_checking(request)
    if not rejin:
        return Response({"message": "No User Found"}, status=status.HTTP_401_UNAUTHORIZED)
    if not rejin.is_active:
        return Response({"message": "Not Authorized"}, status=status.HTTP_401_UNAUTHORIZED)

    single_id = request.query_params.get("id") or (
        request.data.get("id") if isinstance(request.data, dict) else None
    )
    dry_raw = request.query_params.get("dry_run") or (
        request.data.get("dry_run") if isinstance(request.data, dict) else None
    )
    dry_run = str(dry_raw).lower() in ("1", "true", "yes")

    qs = PeopleInterestDetails.objects.filter(action=True)
    if single_id:
        qs = qs.filter(id=single_id)

    summary = []
    if dry_run:
        from django.db import transaction
        with transaction.atomic():
            sp = transaction.savepoint()
            try:
                for rec in qs:
                    summary.append(_apply_for_record(rec))
            finally:
                transaction.savepoint_rollback(sp)
    else:
        for rec in qs:
            summary.append(_apply_for_record(rec))

    total_penalty = sum(
        item.get("penalty", 0)
        for r in summary
        for item in r.get("applied_months", [])
    )
    total_interest = sum(
        item.get("interest", 0)
        for r in summary
        for item in r.get("applied_months", [])
    )
    return Response({
        "dry_run": dry_run,
        "records_processed": len(summary),
        "added_interest_total": round(total_interest, 2),
        "added_penalty_total": round(total_penalty, 2),
        "details": summary,
    })


# ---------------------------------------------------------------------------
# Recompute the balance sheet totals from the InterestPeopleReport audit
# trail. Used to heal drift from rounding / edited collections / historical
# manual edits reported by operators (e.g. TC_TEMPLE_INTEREST_001).
# ---------------------------------------------------------------------------
@api_view(["POST"])
def recompute_interest_balance(request):
    """
    For each active interest record, re-derive:
      * balance_amt         = Σ credits − Σ debits
      * credit_amt          = Σ credits
      * debit_amt           = Σ debits
    from every ``InterestPeopleReport`` row belonging to it.

    Pass ``?id=<pk>`` for a single record, ``?dry_run=1`` for a preview.
    """
    rejin = token_checking(request)
    if not rejin:
        return Response({"message": "No User Found"}, status=status.HTTP_401_UNAUTHORIZED)
    if not rejin.is_active:
        return Response({"message": "Not Authorized"}, status=status.HTTP_401_UNAUTHORIZED)

    single_id = request.query_params.get("id") or (
        request.data.get("id") if isinstance(request.data, dict) else None
    )
    dry_run = str(
        request.query_params.get("dry_run") or
        (request.data.get("dry_run") if isinstance(request.data, dict) else "")
    ).lower() in ("1", "true", "yes")

    qs = PeopleInterestDetails.objects.filter(action=True)
    if single_id:
        qs = qs.filter(id=single_id)

    fixed = []
    for rec in qs:
        try:
            bal = PeopleInterestBalanceSheet.objects.get(interest_id=rec.id)
        except PeopleInterestBalanceSheet.DoesNotExist:
            continue

        reports = InterestPeopleReport.objects.filter(interest=rec)
        credit = float(sum(float(r.credit_amt or 0) for r in reports))
        debit = float(sum(float(r.debit_amt or 0) for r in reports))
        new_balance = round(credit - debit, 2)
        drift = round(float(bal.balance_amt or 0) - new_balance, 2)

        if abs(drift) < 0.01:
            continue

        fixed.append({
            "interest_id": rec.id,
            "old_balance": float(bal.balance_amt or 0),
            "new_balance": new_balance,
            "drift": drift,
            "credit_sum": round(credit, 2),
            "debit_sum": round(debit, 2),
        })

        if not dry_run:
            bal.credit_amt = round(credit, 2)
            bal.debit_amt = round(debit, 2)
            bal.balance_amt = new_balance
            bal.save()

    return Response({
        "dry_run": dry_run,
        "records_scanned": qs.count(),
        "records_needing_fix": len(fixed),
        "total_drift_healed": round(sum(f["drift"] for f in fixed), 2),
        "details": fixed[:200],  # cap payload size
    })
