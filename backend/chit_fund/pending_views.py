"""
Pending-borrowers breakdown for the Chit Fund view.

The chit fund's "Pending Amount to Collect" is the aggregate of all
Chit-Fund-Interest loans that were given out from the pool and are not yet
repaid. It is NOT the investors' contribution.

This endpoint returns the per-borrower breakdown backing that total so
the UI can expand it into an actionable list.
"""

from datetime import date

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from token_app.views import token_checking
from management.models import ManagementDetails
from chit_fund.models import ChitFundsDetails
from balancesheet.models import PeopleInterestBalanceSheet


def _days_between(a, b):
    if not a or not b:
        return None
    try:
        return (b - a).days
    except Exception:
        return None


def _weeks_between(a, b):
    """Full weeks between two dates (integer, floor). Returns None if
    either date is missing. Post-due-date week counter — used on the
    Pending sheet per TC_CHITFUND_005 so operators see how many *weeks*
    a borrower is behind rather than raw days."""
    d = _days_between(a, b)
    if d is None or d < 0:
        return None
    return d // 7


@api_view(["GET"])
def chit_fund_pending_borrowers(request, chit_id: int):
    """Return active Chit-Fund-Interest borrowers with outstanding principal.

    Response shape (used by ChitFundListView.jsx):
    {
      "chit_id": <int>,
      "total_pending_principal": <float>,
      "total_pending_balance": <float>,     # principal + penalty
      "count": <int>,
      "borrowers": [
        {
          "id": <int>,                       # PeopleInterestBalanceSheet id
          "interest_id": <int>,
          "name": <str>, "mobile": <str>,
          "interest_type": <str>,
          "start_date": <YYYY-MM-DD | null>, # interest_apply_date
          "end_date": <YYYY-MM-DD | null>,   # apply_date + period (if set)
          "days_from_start": <int | null>,
          "days_from_last_payment": <int | null>,
          "principal_amt": <float>,
          "principal_paid": <float>,
          "principal_balance": <float>,
          "penalty_balance_amt": <float>,
          "balance_amt": <float>,
        }, ...
      ]
    }
    """
    rejin = token_checking(request)
    if not rejin:
        return Response({"message": "No User Found"}, status=status.HTTP_401_UNAUTHORIZED)
    if not rejin.is_active:
        return Response({"message": "Not Authorized Please Contact Admin"}, status=status.HTTP_401_UNAUTHORIZED)

    management = ManagementDetails.objects.first()
    if not management:
        return Response({"message": "First Add Management Profile details"}, status=status.HTTP_406_NOT_ACCEPTABLE)

    try:
        chit = ChitFundsDetails.objects.get(pk=chit_id, management_profile=management)
    except ChitFundsDetails.DoesNotExist:
        return Response({"detail": "chit fund not found"}, status=status.HTTP_404_NOT_FOUND)

    rows = (
        PeopleInterestBalanceSheet.objects
        .filter(
            interest__chitt_fund=chit,
            interest__interest_type="Chit fund Interest",
            interest__action=True,
            paid=False,
        )
        .exclude(principal_balance=0, balance_amt=0, penalty_balance_amt=0)
        .select_related("interest")
        .order_by("-updated_at", "-id")
    )

    today = date.today()
    borrowers = []
    total_principal = 0.0
    total_interest = 0.0
    total_balance = 0.0
    for b in rows:
        interest = b.interest
        # ------------------------------------------------------------------
        # Owner-locked column-to-source map (Feb 2026) for the "Pending
        # borrowers — <chit_name>" table on the "View details" screen:
        #
        #   Col 3  Start        <- balancesheet.interest_apply_date  (STRICT — no fallback)
        #   Col 4  End          <- start + interest.interest_period      periods of
        #                          interest.interest_period_type          {days|week|month}
        #   Col 7  Principal    <- interest.principal_amt + interest.interest_amt
        #   Col 8  Final amt    <- interest.final_amt_given          (renamed column)
        #   Col 9  Interest     <- interest.interest_amt             (from master, NOT balance sheet)
        #   Col 10 Interest paid<- balancesheet.intrest_paid_amt
        #   Col 11 Penalty bal  <- per-cycle penalty amount, i.e.
        #                          installment_amt × penalty_amount%  (or flat penalty_amount)
        #                          (single cycle, NOT the accumulated balance)
        # ------------------------------------------------------------------

        # Start: STRICT — read only from balance sheet, no fallback to
        # interest_date. If the balance sheet has no apply-date the cell
        # renders '-' in the UI (owner directive).
        start = b.interest_apply_date

        # End: interest_apply_date + interest_period (of the given
        # period type). Falls back to null when either is missing.
        end = None
        if start and interest and interest.interest_period:
            try:
                from dateutil.relativedelta import relativedelta
                p = int(interest.interest_period)
                t = (interest.interest_period_type or "").lower()
                if t == "days":
                    end = start + relativedelta(days=p)
                elif t == "week":
                    end = start + relativedelta(weeks=p)
                elif t == "month":
                    end = start + relativedelta(months=p)
            except Exception:
                end = None

        last_payment = b.updated_at.date() if b.updated_at else None
        # Column-mapped values from the interest master record:
        principal_master = float(interest.principal_amt or 0) if interest else 0.0
        interest_master = float(interest.interest_amt or 0) if interest else 0.0
        # Col 7 "Principal+Interest" = principal_amt + interest_amt (owner rule).
        principal_col_value = principal_master + interest_master
        # Col 8 "Final amount given" (rename of legacy "Principal paid").
        final_amt_given = float(interest.final_amt_given or 0) if interest else 0.0
        # Col 9 "Interest" comes strictly from the interest master row.
        interest_col_value = interest_master

        # Col 10 "Interest Paid" = installment_amt × paid_counts (owner rule).
        installment_amt_master = float(interest.installment_amt or 0) if interest else 0.0
        paid_counts_master = int(interest.paid_counts or 0) if interest else 0
        interest_paid = installment_amt_master * paid_counts_master

        # Derived Balance column per owner spec:
        #   if Interest Paid == 0  -> balance = 0
        #   else                   -> balance = (Principal+Interest) - Interest Paid
        if interest_paid == 0:
            balance_derived = 0.0
        else:
            balance_derived = principal_col_value - interest_paid

        # Col 11 "Penalty bal" — accumulated:
        #   cycles_elapsed = floor((today - start).days / period_days)
        #   missed_cycles  = max(0, cycles_elapsed - paid_counts)
        #   penalty_bal    = missed_cycles × 3 % × interest_amt
        #                    (0 when penalty_enabled=False OR missed_cycles=0)
        penalty_bal_accum = 0.0
        if interest and start and interest.interest_period and interest.interest_period_type:
            pen_on = True if interest.penalty_enabled is None else bool(interest.penalty_enabled)
            if pen_on:
                _period_days_by_unit = {"days": 1, "week": 7, "month": 30}
                unit_days = _period_days_by_unit.get(
                    (interest.interest_period_type or "").lower(), 30
                )
                period_days = unit_days * max(1, int(interest.interest_period or 1))
                days_elapsed = (today - start).days
                if days_elapsed > 0 and period_days > 0:
                    cycles_elapsed = days_elapsed // period_days
                    missed_cycles = max(0, cycles_elapsed - paid_counts_master)
                    penalty_bal_accum = missed_cycles * 0.03 * interest_master

        # Other ledger figures kept for downstream reports (unchanged).
        principal_paid = float(b.principal_paid or 0)
        principal_balance = float(b.principal_balance or 0)
        interest_balance = float(b.intrest_balance_amt or 0)
        penalty_balance_acc = float(b.penalty_balance_amt or 0)  # ledger accumulated
        ledger_balance_amt = float(b.balance_amt or 0)

        total_principal += principal_col_value
        total_interest += interest_col_value
        total_balance += ledger_balance_amt + penalty_balance_acc

        borrowers.append({
            "id": b.id,
            "interest_id": interest.id if interest else None,
            "name": interest.people_name if interest else None,
            "mobile": interest.people_mobile if interest else None,
            "interest_type": interest.interest_type if interest else None,
            "start_date": start.isoformat() if start else None,
            "end_date": end.isoformat() if end else None,
            "days_from_start": _days_between(start, today),
            "days_from_last_payment": _days_between(last_payment, today),
            # TC_CHITFUND_005 — weeks (floor).
            "weeks_from_start": _weeks_between(start, today),
            "weeks_from_last_payment": _weeks_between(last_payment, today),
            # Col-7 "Principal+Interest" per owner map.
            "principal_amt": round(principal_col_value, 2),
            "principal_paid": round(principal_paid, 2),
            "principal_balance": round(principal_balance, 2),
            # Col-8 "Final amount given" — from interest master.
            "final_amt_given": round(final_amt_given, 2),
            # Col-9 "Interest" — from interest master, NOT ledger.
            "interest_amt": round(interest_col_value, 2),
            # Col-10 "Interest paid" — installment_amt × paid_counts (owner rule).
            "interest_paid": round(interest_paid, 2),
            "interest_balance": round(interest_balance, 2),
            # Balance — derived per owner rule (0 when nothing paid yet).
            "balance_amt": round(balance_derived, 2),
            # Col-11 "Penalty bal" — accumulated (missed_cycles × 3 % × interest_amt).
            "penalty_balance_amt": round(penalty_bal_accum, 2),
            "penalty_balance_accumulated": round(penalty_balance_acc, 2),
            # Raw fields still exposed for any downstream report.
            "principal_only": principal_master,
            "interest_charged": interest_master,
        })

    return Response({
        "chit_id": chit.id,
        "chit_name": chit.chit_name,
        "principal_given_amount": float(chit.principal_given_amount or 0),
        "collected_principal_amount": float(chit.collected_principal_amount or 0),
        "count": len(borrowers),
        "total_pending_principal": round(total_principal, 2),
        "total_pending_interest": round(total_interest, 2),
        "total_pending_balance": round(total_balance, 2),
        "borrowers": borrowers,
    })
