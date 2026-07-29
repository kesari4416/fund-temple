"""
Direct-PDF endpoints for the WhatsApp share flow.

The operator shares a link like:
    https://<host>/api/collection/public/member_statement.pdf/<token>/?receipt_no=...

When the customer taps the link on their phone, the browser opens/downloads
the PDF directly — no admin portal, no login, no HTML render, no JS.

Uses reportlab (already installed in the pod) for zero-dependency PDF
generation. Layout:
    1. Temple / statement header
    2. Payment Receipt block  (from ?receipt_* query params)
    3. Borrower / Member details + statement period
    4. Totals + Pending / Outstanding summary
    5. 1-year Balance Sheet table
"""

from datetime import timedelta
from io import BytesIO

from django.http import FileResponse, HttpResponseNotFound
from django.utils import timezone
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from family.models import Member_Details
from collection.models import CollectionDetails
from interest.models import PeopleInterestDetails
from balancesheet.models import PeopleInterestBalanceSheet
from reports.models import TempleMemberReport

# Reuse the HMAC helpers + pending-dues logic from public_views so tokens
# stay compatible with the HTML public statement.
from collection.public_views import (
    _unsign_member_id,
    _unsign_interest_id,
    _serialize_pending,
)


TEMPLE_GREEN = colors.HexColor("#0F5132")
BORDER_GREY = colors.HexColor("#e2e8f0")
MUTED_GREY = colors.HexColor("#64748b")


def _rupee(n) -> str:
    return f"Rs. {float(n or 0):,.2f}"


def _receipt_from_query(request):
    """Extract the payment-receipt fields the operator embedded in the URL."""
    q = request.GET
    return {
        "no": (q.get("receipt_no") or "").strip(),
        "amt": (q.get("receipt_amt") or "").strip(),
        "date": (q.get("receipt_date") or "").strip(),
        "purpose": (q.get("receipt_purpose") or "").strip(),
        "mode": (q.get("receipt_mode") or "").strip(),
    }


def _has_receipt(r):
    return bool(r.get("no") or r.get("amt"))


def _styled_doc(title):
    """Create a reportlab doc + a fresh set of paragraph styles."""
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        title=title,
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="TitleG",
        parent=styles["Title"],
        fontSize=18,
        textColor=TEMPLE_GREEN,
        alignment=0,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="H2",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=TEMPLE_GREEN,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="Muted",
        parent=styles["Normal"],
        fontSize=9,
        textColor=MUTED_GREY,
    ))
    return doc, buf, styles


def _receipt_flowables(styles, r):
    """Render the Payment Receipt card as reportlab flowables."""
    if not _has_receipt(r):
        return []
    data = [["Payment Receipt", ""]]
    if r["no"]:
        data.append(["Receipt No", r["no"]])
    if r["date"]:
        data.append(["Date", r["date"]])
    if r["purpose"]:
        data.append(["Purpose", r["purpose"]])
    if r["mode"]:
        data.append(["Payment Mode", r["mode"]])
    if r["amt"]:
        data.append(["Amount Paid", _rupee(r["amt"])])
    t = Table(data, colWidths=[55 * mm, None])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TEMPLE_GREEN),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 12),
        ("SPAN", (0, 0), (-1, 0)),
        ("ALIGN", (0, 0), (-1, 0), "LEFT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica"),
        ("FONTNAME", (1, 1), (1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER_GREY),
        ("INNERGRID", (0, 1), (-1, -1), 0.25, BORDER_GREY),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return [t, Spacer(1, 8 * mm)]


def _table_style_header():
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER_GREY),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, BORDER_GREY),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafafa")]),
    ])


# ---------------------------------------------------------------------------
# MEMBER PDF
# ---------------------------------------------------------------------------
@api_view(["GET"])
@permission_classes([AllowAny])
def public_member_statement_pdf(request, token: str):
    member_id = _unsign_member_id(token)
    if member_id is None:
        return HttpResponseNotFound("invalid or expired link")
    try:
        member = Member_Details.objects.get(pk=member_id, action=True)
    except Member_Details.DoesNotExist:
        return HttpResponseNotFound("member not found")

    since = timezone.now().date() - timedelta(days=365)

    # QA Bug — the operator asked that every WhatsApp share be scoped to the
    # SPECIFIC category of the payment that just happened (Sub Tariff /
    # Festival / Death / Marriage). Recipients should not see unrelated
    # ledger rows. The frontend passes the CollectionRecord.collection_category
    # as `?category=` and we map that to the TempleMemberReport `type_choice`
    # enum values below.
    category = (request.GET.get("category") or "").strip()
    CATEGORY_MAP = {
        "Subscription Tariff": ["subscription Tariff", "subscription Tariff Penalty"],
        "subscription Tariff": ["subscription Tariff", "subscription Tariff Penalty"],
        "Festival": ["Festival", "Festival Penalty"],
        "Death": ["Death Tariff", "Death Tariff Penalty"],
        "Death Tariff": ["Death Tariff", "Death Tariff Penalty"],
        "Marriage": ["Marriage Amount"],
        "Marriage Amount": ["Marriage Amount"],
    }
    type_choices = CATEGORY_MAP.get(category)

    reports_qs = (
        TempleMemberReport.objects
        .filter(members=member, reportdate__gte=since)
        .select_related("sub_tariff", "festivals", "marriage", "death_tariff", "collection")
    )
    if type_choices:
        reports_qs = reports_qs.filter(type_choice__in=type_choices)

    reports = reports_qs.order_by("reportdate", "created_at", "id")
    bs_rows = []
    total_credit = 0.0
    total_debit = 0.0
    prev_balance = 0.0
    for idx, r in enumerate(reports, start=1):
        credit = float(r.credit_amt or 0)
        debit = float(r.debit_amt or 0)
        balance = float(r.balance_amt or 0)
        # Compute "particulars" — the report's type_choice enum, e.g.
        # "Sub Tariff" / "Death" / "Festival" / "Marriage" / "Joining"
        particulars = r.type_choice or "-"
        # "Name" — human-readable sub-identifier for the bill (matches
        # frontend `name_type` field, e.g. "Jun-2026" or "Ganesh Chaturthi").
        name = None
        if r.death_tariff_id and r.death_tariff:
            name = r.death_tariff.member_name
        elif r.festivals_id and r.festivals:
            name = r.festivals.festival_name
        elif r.marriage_id and r.marriage:
            name = r.marriage.marriage_no
        elif r.sub_tariff_id and r.sub_tariff:
            if r.sub_tariff.from_date:
                name = r.sub_tariff.from_date.strftime("%b-%Y")
            else:
                name = r.sub_tariff.subscription_no or "-"
        bs_rows.append({
            "sl": idx,
            "date": r.reportdate.isoformat() if r.reportdate else "-",
            "particulars": particulars,
            "name": name or "-",
            "pre_balance": prev_balance,
            "credit": credit,
            "debit": debit,
            "balance": balance,
        })
        total_credit += credit
        total_debit += debit
        prev_balance = balance
    # Scope pending dues to the category when a category filter is active
    full_pending = _serialize_pending(member) or {}
    if type_choices:
        # PeoplesAmountDetails uses these `name` values as bucket keys:
        # "Subscription Tariff", "Festival", "Marriage", "Death"
        # (no " Tariff"/" Amount" suffix). Map from incoming category → bucket keys.
        CATEGORY_TO_PENDING_KEYS = {
            "Subscription Tariff": ["Subscription Tariff", "subscription Tariff"],
            "subscription Tariff": ["Subscription Tariff", "subscription Tariff"],
            "Festival": ["Festival"],
            "Death": ["Death", "Death Tariff"],
            "Death Tariff": ["Death", "Death Tariff"],
            "Marriage": ["Marriage", "Marriage Amount"],
            "Marriage Amount": ["Marriage", "Marriage Amount"],
        }
        wanted = set(CATEGORY_TO_PENDING_KEYS.get(category, [category]))
        pending = {k: v for k, v in full_pending.items() if k != "Total" and k in wanted}
        pending["Total"] = round(sum(v for v in pending.values() if isinstance(v, (int, float))), 2)
    else:
        pending = full_pending

    full_name = " ".join(x for x in [member.member_name, getattr(member, "last_name", "")] if x)
    category_label = category if type_choices else ""
    title_prefix = f"{category_label}_" if category_label else ""
    title = f"{title_prefix}Statement_{member.member_no or member.id}_{timezone.now().date().isoformat()}.pdf".replace(" ", "_")
    doc, buf, styles = _styled_doc(title)
    story = []

    header_line = "Temple Statement"
    if category_label:
        header_line = f"{category_label} Statement"
    story.append(Paragraph(header_line, styles["TitleG"]))
    period_line = f"1-Year Balance Sheet · {since.strftime('%d-%b-%Y')} to {timezone.now().date().strftime('%d-%b-%Y')}"
    if category_label:
        period_line = f"{category_label} · {period_line}"
    story.append(Paragraph(period_line, styles["Muted"]))
    story.append(Spacer(1, 6 * mm))

    story.extend(_receipt_flowables(styles, _receipt_from_query(request)))

    # Member card
    m_data = [
        ["Member details", ""],
        ["Name", full_name or "-"],
        ["Member No", member.member_no or "-"],
        ["Mobile", getattr(member, "member_mobile_number", "") or "-"],
    ]
    m_tbl = Table(m_data, colWidths=[55 * mm, None])
    m_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TEMPLE_GREEN),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 12),
        ("SPAN", (0, 0), (-1, 0)),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica"),
        ("FONTNAME", (1, 1), (1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER_GREY),
        ("INNERGRID", (0, 1), (-1, -1), 0.25, BORDER_GREY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(m_tbl)
    story.append(Spacer(1, 6 * mm))

    # Pending dues card
    if pending:
        p_data = [["Pending Dues", ""]]
        for k, v in pending.items():
            if k == "Total":
                continue
            if float(v or 0) != 0:
                p_data.append([k, _rupee(v)])
        p_data.append(["Total Pending", _rupee(pending.get("Total", 0))])
        p_tbl = Table(p_data, colWidths=[80 * mm, None])
        p_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), TEMPLE_GREEN),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("SPAN", (0, 0), (-1, 0)),
            ("FONTSIZE", (0, 0), (-1, 0), 12),
            ("FONTNAME", (0, 1), (0, -2), "Helvetica"),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#fef3c7")),
            ("FONTSIZE", (0, 1), (-1, -1), 10),
            ("BOX", (0, 0), (-1, -1), 0.5, BORDER_GREY),
            ("INNERGRID", (0, 1), (-1, -1), 0.25, BORDER_GREY),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(p_tbl)
        story.append(Spacer(1, 6 * mm))

    # Balance sheet ledger — mirrors Family Details → Member List → Balance Sheet
    story.append(Paragraph("1-Year Balance Sheet", styles["H2"]))
    if not bs_rows:
        story.append(Paragraph("No entries in the last 12 months.", styles["Muted"]))
    else:
        headers = ["Sl", "Date", "Particulars", "Name", "Pre Balance", "Credit", "Debit", "Balance"]
        data = [headers]
        for r in bs_rows:
            data.append([
                str(r["sl"]),
                str(r["date"]),
                str(r["particulars"])[:22],
                str(r["name"])[:20],
                f"{r['pre_balance']:,.2f}",
                f"{r['credit']:,.2f}",
                f"{r['debit']:,.2f}",
                f"{r['balance']:,.2f}",
            ])
        # Totals row: Total Credit · Total Debit · Closing Balance
        closing = bs_rows[-1]["balance"] if bs_rows else 0.0
        data.append([
            "", "", "", "Total",
            "",
            f"{total_credit:,.2f}",
            f"{total_debit:,.2f}",
            f"{closing:,.2f}",
        ])
        tbl = Table(
            data,
            colWidths=[8 * mm, 22 * mm, 34 * mm, 30 * mm, 22 * mm, 22 * mm, 20 * mm, 22 * mm],
        )
        style = _table_style_header()
        for col in (4, 5, 6, 7):
            style.add("ALIGN", (col, 0), (col, -1), "RIGHT")
        style.add("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f1f5f9"))
        style.add("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold")
        tbl.setStyle(style)
        story.append(tbl)

    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph(f"Generated on {timezone.now().strftime('%d-%b-%Y %H:%M')}", styles["Muted"]))

    doc.build(story)
    buf.seek(0)
    resp = FileResponse(buf, content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="{title}"'
    return resp


# ---------------------------------------------------------------------------
# INTEREST-LOAN PDF
# ---------------------------------------------------------------------------
@api_view(["GET"])
@permission_classes([AllowAny])
def public_interest_statement_pdf(request, token: str):
    interest_id = _unsign_interest_id(token)
    if interest_id is None:
        return HttpResponseNotFound("invalid or expired link")
    try:
        interest = PeopleInterestDetails.objects.get(pk=interest_id, action=True)
    except PeopleInterestDetails.DoesNotExist:
        return HttpResponseNotFound("interest not found")

    since = timezone.now().date() - timedelta(days=365)
    collections = (
        CollectionDetails.objects
        .filter(interest=interest, pay_date__gte=since, action=True)
        .order_by("-pay_date", "-id")
    )

    running = 0.0
    tot_pri = tot_int = tot_pen = 0.0
    rows = []
    for c in reversed(list(collections)):
        pri = float(c.amount or 0)
        intr = float(c.interst_amount or 0)
        pen = float(c.penalty_amount or 0)
        total_paid = pri + intr + pen
        running += total_paid
        tot_pri += pri
        tot_int += intr
        tot_pen += pen
        rows.append({
            "date": c.pay_date.isoformat() if c.pay_date else "-",
            "category": c.collection_category or "-",
            "amount": total_paid,
            "penalty": pen,
            "running": running,
        })
    rows.reverse()

    bal = PeopleInterestBalanceSheet.objects.filter(interest=interest).first()

    title = f"Loan_Statement_{interest.id}_{timezone.now().date().isoformat()}.pdf"
    doc, buf, styles = _styled_doc(title)
    story = []
    story.append(Paragraph("Loan Statement", styles["TitleG"]))
    story.append(Paragraph(
        f"{interest.interest_type or 'Interest'} · {since.strftime('%d-%b-%Y')} to {timezone.now().date().strftime('%d-%b-%Y')}",
        styles["Muted"],
    ))
    story.append(Spacer(1, 6 * mm))

    story.extend(_receipt_flowables(styles, _receipt_from_query(request)))

    # Borrower details
    b_data = [
        ["Borrower details", ""],
        ["Name", interest.people_name or "-"],
        ["Mobile", interest.people_mobile or "-"],
        ["Interest type", interest.interest_type or "-"],
    ]
    if interest.chit_name:
        b_data.append(["Chit / Management fund", interest.chit_name])
    b_tbl = Table(b_data, colWidths=[55 * mm, None])
    b_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TEMPLE_GREEN),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("SPAN", (0, 0), (-1, 0)),
        ("FONTSIZE", (0, 0), (-1, 0), 12),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica"),
        ("FONTNAME", (1, 1), (1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER_GREY),
        ("INNERGRID", (0, 1), (-1, -1), 0.25, BORDER_GREY),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(b_tbl)
    story.append(Spacer(1, 6 * mm))

    # Outstanding card
    if bal:
        outs = [
            ["Outstanding balance", ""],
            ["Principal issued", _rupee(bal.principal_amt)],
            ["Principal paid", _rupee(bal.principal_paid)],
            ["Principal balance", _rupee(bal.principal_balance)],
            ["Penalty balance", _rupee(bal.penalty_balance_amt)],
            ["Total outstanding", _rupee(float(bal.balance_amt or 0) + float(bal.penalty_balance_amt or 0))],
        ]
        o_tbl = Table(outs, colWidths=[80 * mm, None])
        o_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), TEMPLE_GREEN),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("SPAN", (0, 0), (-1, 0)),
            ("FONTSIZE", (0, 0), (-1, 0), 12),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#fef3c7")),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 1), (-1, -1), 10),
            ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f8fafc")]),
            ("BOX", (0, 0), (-1, -1), 0.5, BORDER_GREY),
            ("INNERGRID", (0, 1), (-1, -1), 0.25, BORDER_GREY),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(o_tbl)
        story.append(Spacer(1, 6 * mm))

    # 1-year balance sheet
    story.append(Paragraph("1-Year Balance Sheet", styles["H2"]))
    if not rows:
        story.append(Paragraph("No payments in the last 12 months.", styles["Muted"]))
    else:
        headers = ["Date", "Category", "Amount", "Penalty", "Running Total"]
        data = [headers]
        for r in rows:
            data.append([
                r["date"],
                str(r["category"])[:30],
                f"{r['amount']:,.2f}",
                f"{r['penalty']:,.2f}",
                f"{r['running']:,.2f}",
            ])
        data.append([
            "", "TOTAL",
            f"{running:,.2f}",
            f"{tot_pen:,.2f}",
            "",
        ])
        tbl = Table(data, colWidths=[28 * mm, 55 * mm, 32 * mm, 28 * mm, 35 * mm])
        style = _table_style_header()
        for col in (2, 3, 4):
            style.add("ALIGN", (col, 0), (col, -1), "RIGHT")
        style.add("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f1f5f9"))
        style.add("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold")
        tbl.setStyle(style)
        story.append(tbl)

    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph(f"Generated on {timezone.now().strftime('%d-%b-%Y %H:%M')}", styles["Muted"]))

    doc.build(story)
    buf.seek(0)
    resp = FileResponse(buf, content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="{title}"'
    return resp
