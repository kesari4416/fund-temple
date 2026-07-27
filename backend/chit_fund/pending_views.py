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
    total_balance = 0.0
    for b in rows:
        interest = b.interest
        # End date: interest_apply_date + interest_period (of the given
        # period type). Falls back to null when either is missing.
        start = b.interest_apply_date or (interest.interest_date if interest else None)
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
        principal_balance = float(b.principal_balance or 0)
        penalty_balance = float(b.penalty_balance_amt or 0)
        balance_amt = float(b.balance_amt or 0)
        total_principal += principal_balance
        total_balance += balance_amt + penalty_balance

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
            "principal_amt": float(b.principal_amt or 0),
            "principal_paid": float(b.principal_paid or 0),
            "principal_balance": principal_balance,
            "penalty_balance_amt": penalty_balance,
            "balance_amt": balance_amt,
        })

    return Response({
        "chit_id": chit.id,
        "chit_name": chit.chit_name,
        "principal_given_amount": float(chit.principal_given_amount or 0),
        "collected_principal_amount": float(chit.collected_principal_amount or 0),
        "count": len(borrowers),
        "total_pending_principal": round(total_principal, 2),
        "total_pending_balance": round(total_balance, 2),
        "borrowers": borrowers,
    })
