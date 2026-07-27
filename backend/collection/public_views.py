"""
Public (unauthenticated) member statement endpoint.

Used by the WhatsApp share flow: after each Collection print, the operator
opens `https://wa.me/<phone>?text=...&link=<url>` where the link points to
this endpoint. The URL contains a HMAC-signed token so only the intended
member's data can be retrieved – tampering with the token invalidates it.
"""

import base64
import hashlib
import hmac
import json
from datetime import timedelta

from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from family.models import Member_Details
from collection.models import CollectionDetails
from amount.models import PeoplesAmountDetails
from interest.models import PeopleInterestDetails
from balancesheet.models import PeopleInterestBalanceSheet


# ---------------------------------------------------------------------------
# HMAC token helpers (stateless, no DB migration required)
# ---------------------------------------------------------------------------
_TOKEN_SEPARATOR = "."
_STATEMENT_SALT = "temple.member_statement.v1"


def _sign_member_id(member_id: int) -> str:
    """Return an opaque URL-safe token that encodes and signs member_id."""
    payload = json.dumps({"m": int(member_id)}, separators=(",", ":")).encode("utf-8")
    payload_b64 = base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")
    key = (settings.SECRET_KEY + _STATEMENT_SALT).encode("utf-8")
    digest = hmac.new(key, payload_b64.encode("ascii"), hashlib.sha256).digest()
    sig = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return f"{payload_b64}{_TOKEN_SEPARATOR}{sig}"


def _unsign_member_id(token: str):
    """Return member_id if the token is valid, else None."""
    try:
        payload_b64, sig = token.split(_TOKEN_SEPARATOR)
    except ValueError:
        return None
    key = (settings.SECRET_KEY + _STATEMENT_SALT).encode("utf-8")
    expected = base64.urlsafe_b64encode(
        hmac.new(key, payload_b64.encode("ascii"), hashlib.sha256).digest()
    ).rstrip(b"=").decode("ascii")
    if not hmac.compare_digest(sig, expected):
        return None
    try:
        padded = payload_b64 + "=" * (-len(payload_b64) % 4)
        data = json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))
        return int(data.get("m"))
    except (ValueError, TypeError, json.JSONDecodeError):
        return None


@api_view(["GET"])
@permission_classes([AllowAny])
def get_member_statement_token(request, member_id: int):
    """Return a HMAC token + the member's saved mobile number.

    Frontend uses `mobile` to fall back when the Collection record itself
    doesn't carry a phone number (older records / anonymous collections).
    """
    try:
        member = Member_Details.objects.get(pk=member_id)
    except Member_Details.DoesNotExist:
        return Response({"detail": "member not found"}, status=status.HTTP_404_NOT_FOUND)
    return Response({
        "token": _sign_member_id(member_id),
        "mobile": member.member_mobile_number,
        "name": member.member_name,
    })


# ---------------------------------------------------------------------------
# Public statement endpoint
# ---------------------------------------------------------------------------
def _serialize_pending(member):
    """Aggregate pending dues per category.

    Combines:
    - `PeoplesAmountDetails` (unpaid Festival / Subscription Tariff / Marriage / Death rows)
    - `PeopleInterestBalanceSheet` (unpaid Management Interest & Chit fund Interest rows
      belonging to this member as the borrower — `interest.people_member`)
    """
    per_category = {}

    unpaid = PeoplesAmountDetails.objects.filter(member=member, paid=False)
    for row in unpaid:
        key = row.name or "Other"
        per_category[key] = round(
            per_category.get(key, 0.0) + float(row.total_bal_amt or row.amount_balance or 0), 2
        )

    # Interest dues for loans taken by this member. Both interest types
    # (Management Interest and Chit fund Interest) are surfaced separately
    # so the member sees each ledger they participate in.
    interest_rows = PeopleInterestBalanceSheet.objects.filter(
        interest__people_member=member,
        interest__action=True,
        paid=False,
    ).select_related("interest")
    for row in interest_rows:
        label = "Chit Interest" if (row.interest and row.interest.interest_type == "Chit fund Interest") else "Management Interest"
        balance = float(row.balance_amt or 0) + float(row.penalty_balance_amt or 0)
        if balance <= 0:
            continue
        per_category[label] = round(per_category.get(label, 0.0) + balance, 2)

    per_category["Total"] = round(sum(v for k, v in per_category.items() if k != "Total"), 2)
    return per_category


@api_view(["GET"])
@permission_classes([AllowAny])
def public_member_statement(request, token: str):
    """
    Public one-year statement for a single member. Anyone with the token
    can view but nothing else – tampering with the token yields 404.
    """
    member_id = _unsign_member_id(token)
    if member_id is None:
        return Response({"detail": "invalid or expired link"}, status=status.HTTP_404_NOT_FOUND)

    try:
        member = Member_Details.objects.get(pk=member_id, action=True)
    except Member_Details.DoesNotExist:
        return Response({"detail": "member not found"}, status=status.HTTP_404_NOT_FOUND)

    since = timezone.now().date() - timedelta(days=365)
    # Include:
    #  (a) collections where the member is DIRECTLY the payer (`member=member`)
    #  (b) collections for Management Interest / Chit Interest where the
    #      linked interest record's borrower is this member
    #      (`interest.people_member=member`). These rows historically leave
    #      `member` NULL, so we must OR them in explicitly.
    collections = (
        CollectionDetails.objects
        .filter(pay_date__gte=since, action=True)
        .filter(Q(member=member) | Q(interest__people_member=member))
        .distinct()
        .order_by("-pay_date", "-id")
    )

    running = 0.0
    rows = []
    for c in reversed(list(collections)):  # oldest → newest for running total
        # For Management Interest / Chit Interest the operator often stores
        # only the principal in `amount`; interest & penalty portions are in
        # separate columns. The customer statement must reflect the TOTAL
        # paid on that day.
        principal = float(c.amount or 0)
        interest_amt = float(c.interst_amount or 0)
        penalty_amt = float(c.penalty_amount or 0)
        is_interest_row = c.collection_category in ("Management Interest", "Chit Interest")
        total_paid = principal + interest_amt + penalty_amt if is_interest_row else principal
        running += total_paid
        rows.append({
            "id": c.id,
            "date": c.pay_date.isoformat() if c.pay_date else None,
            "category": c.collection_category,
            "amount": round(total_paid, 2),
            "principal_amount": principal,
            "interest_amount": interest_amt,
            "penalty_amount": penalty_amt,
            "payment_mode": c.payment_mode,
            "collection_no": c.collaction_no,
            "running_total": round(running, 2),
        })
    # reverse back so most-recent-first for display (running_total kept as-is)
    rows.reverse()

    return Response({
        "member": {
            "id": member.id,
            "name": member.member_name,
            "last_name": member.last_name,
            "mobile": member.member_mobile_number,
            "member_no": member.member_no,
        },
        "period": {"from": since.isoformat(), "to": timezone.now().date().isoformat()},
        "collections": rows,
        "totals": {
            "count": len(rows),
            "amount": round(running, 2),
        },
        "pending_dues": _serialize_pending(member),
    })
