"""
Unified penalty engine for the Temple Management System.

Rule
----
- Penalty = PENALTY_PER_MONTH * (number of fully-missed calendar months
  between the item's due-date and today, excluding the due month).
- No grace period.
- Applies to every UNPAID PeoplesAmountDetails row across:
    Subscription Tariff (due = sub_tariff.to_date)
    Festival            (due = festival.penalty_start_date or end_date)
    Death Tariff        (due = death.penalty_apply_date or date)
    Marriage            (due = marriage.marriage_date)
- For Interest module, the same per-month logic is applied on top of the
  existing balance fields (penalty_balance_amt).

This engine is idempotent: running it multiple times will NOT double-count
penalties.  It simply recomputes the correct value based on today's date.
"""

from __future__ import annotations

from decimal import Decimal
from datetime import date

from dateutil.relativedelta import relativedelta

from amount.models import PeoplesAmountDetails

# Fixed business rule provided by client
PENALTY_PER_MONTH = Decimal("25.00")


def missed_months(due_date: date, today: date | None = None) -> int:
    """Number of full calendar months passed AFTER the due date.

    Example: due=2024-04-10, today=2024-07-15 -> 3 missed months
             due=2024-04-10, today=2024-04-30 -> 0
             due=2024-04-10, today=2024-05-09 -> 0
             due=2024-04-10, today=2024-05-11 -> 1
    """
    if not due_date:
        return 0
    if today is None:
        today = date.today()
    if today <= due_date:
        return 0
    diff = relativedelta(today, due_date)
    return diff.years * 12 + diff.months


def _due_date_for_amount(p: PeoplesAmountDetails) -> date | None:
    """Resolve the due date from the linked entity for a PeoplesAmountDetails row."""
    if p.sub_tariff_id and p.sub_tariff:
        return p.sub_tariff.to_date
    if p.festival_id and p.festival:
        return p.festival.penalty_start_date or p.festival.end_date
    if p.death_id and p.death:
        return p.death.penalty_apply_date or p.death.date
    if p.marriage_id and p.marriage:
        return p.marriage.marriage_date
    return None


def recompute_for_amount(p: PeoplesAmountDetails, today: date | None = None) -> dict:
    """Recompute penalty for a single PeoplesAmountDetails row.

    Returns dict describing the result.  Does NOT touch fully-paid rows.
    """
    today = today or date.today()
    result = {
        "id": p.id,
        "member_id": p.member_id,
        "name": p.name,
        "due_date": None,
        "missed_months": 0,
        "penalty_amount": float(p.penalty_amount or 0),
        "penalty_balance": float(p.penalty_balance or 0),
        "paid": bool(p.paid),
        "updated": False,
    }
    if p.paid:
        return result

    due = _due_date_for_amount(p)
    result["due_date"] = due.isoformat() if due else None
    months = missed_months(due, today) if due else 0
    result["missed_months"] = months

    new_penalty = (PENALTY_PER_MONTH * months).quantize(Decimal("0.01"))
    already_paid_penalty = Decimal(p.penalty_amount or 0) - Decimal(p.penalty_balance or 0)
    if already_paid_penalty < 0:
        already_paid_penalty = Decimal("0")

    # Idempotent: total penalty = computed, balance = computed - paid-so-far
    new_balance = new_penalty - already_paid_penalty
    if new_balance < 0:
        new_balance = Decimal("0")

    changed = (
        Decimal(p.penalty_amount or 0) != new_penalty
        or Decimal(p.penalty_balance or 0) != new_balance
        or bool(p.penalty) != (new_penalty > 0)
    )

    if changed:
        p.penalty_amount = new_penalty
        p.penalty_balance = new_balance
        p.penalty = new_penalty > 0
        p.save(update_fields=["penalty_amount", "penalty_balance", "penalty", "updated_at"])

    result["penalty_amount"] = float(new_penalty)
    result["penalty_balance"] = float(new_balance)
    result["updated"] = changed
    return result


def recompute_all(management_profile=None, today: date | None = None) -> dict:
    """Recompute penalty for every UNPAID PeoplesAmountDetails row."""
    qs = PeoplesAmountDetails.objects.filter(paid=False)
    if management_profile is not None:
        qs = qs.filter(management_profile=management_profile)

    qs = qs.select_related("sub_tariff", "festival", "death", "marriage", "member")

    items = []
    updated_count = 0
    total_penalty = Decimal("0")
    for p in qs:
        r = recompute_for_amount(p, today=today)
        if r["updated"]:
            updated_count += 1
        if r["missed_months"] > 0:
            total_penalty += Decimal(str(r["penalty_amount"]))
            items.append(r)

    return {
        "rate_per_month": float(PENALTY_PER_MONTH),
        "scanned": qs.count(),
        "updated": updated_count,
        "with_penalty": len(items),
        "total_pending_penalty": float(total_penalty),
        "items": items,
    }
