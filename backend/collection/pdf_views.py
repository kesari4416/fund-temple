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

# Reuse the HMAC helpers + pending-dues logic from public_views so tokens
# stay compatible with the HTML public statement.
from collection.public_views import (
    _unsign_member_id,
    _unsign_interest_id,
    _serialize_pending,
    _build_ledger,
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
    ledger, ledger_totals = _build_ledger(member, since)
    pending = _serialize_pending(member) or {}

    full_name = " ".join(x for x in [member.member_name, getattr(member, "last_name", "")] if x)
    title = f"Statement_{member.member_no or member.id}_{timezone.now().date().isoformat()}.pdf"
    doc, buf, styles = _styled_doc(title)
    story = []

    story.append(Paragraph("Temple Statement", styles["TitleG"]))
    story.append(Paragraph(f"1-Year Balance Sheet · {since.strftime('%d-%b-%Y')} to {timezone.now().date().strftime('%d-%b-%Y')}", styles["Muted"]))
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

    # Balance sheet ledger
    story.append(Paragraph("1-Year Balance Sheet", styles["H2"]))
    if not ledger:
        story.append(Paragraph("No entries in the last 12 months.", styles["Muted"]))
    else:
        headers = ["Sl", "Date", "Particulars", "Name", "Credit", "Debit", "Balance", "Pen"]
        data = [headers]
        for r in ledger:
            data.append([
                str(r.get("sl_no", "")),
                str(r.get("date", "")),
                str(r.get("particulars", ""))[:32],
                str(r.get("name", ""))[:22],
                f"{float(r.get('credit', 0)):,.2f}",
                f"{float(r.get('debit', 0)):,.2f}",
                f"{float(r.get('balance', 0)):,.2f}",
                str(r.get("penalty", "")),
            ])
        if ledger_totals:
            data.append([
                "", "", "", "Total",
                f"{float(ledger_totals.get('credit', 0)):,.2f}",
                f"{float(ledger_totals.get('debit', 0)):,.2f}",
                f"{float(ledger_totals.get('balance', 0)):,.2f}",
                "",
            ])
        tbl = Table(data, colWidths=[9 * mm, 22 * mm, 42 * mm, 30 * mm, 20 * mm, 18 * mm, 22 * mm, 12 * mm])
        style = _table_style_header()
        # right-align numeric columns
        for col in (4, 5, 6):
            style.add("ALIGN", (col, 0), (col, -1), "RIGHT")
        if ledger_totals:
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
