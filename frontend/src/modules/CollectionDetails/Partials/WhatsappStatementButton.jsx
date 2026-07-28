import { useCallback, useEffect, useRef, useState } from "react";
import { FaWhatsapp } from "react-icons/fa";
import axios from "axios";
import { Button } from "@components/form";

// Collection categories that share a per-interest-loan statement instead of
// the per-Member one. These typically carry a NULL `member` FK but a valid
// `interest` FK, so we resolve them via the borrower's interest record.
const INTEREST_CATEGORIES = new Set(["Chit Interest", "Management Interest"]);

const API_BASE =
  import.meta.env?.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL || "";

// No row cap — the customer sees the full 1-year ledger. Very large tables
// may hit browser URL-length limits (~8 KB); if that ever happens the fetch
// will still open WhatsApp, just truncated by the OS/browser.

const buildMemberStatementLink = (token) => {
  const origin =
    typeof window !== "undefined" && window.location?.origin
      ? window.location.origin
      : "";
  return `${origin}/statement/${token}`;
};

const buildInterestStatementLink = (token) => {
  const origin =
    typeof window !== "undefined" && window.location?.origin
      ? window.location.origin
      : "";
  return `${origin}/interest-statement/${token}`;
};

const pad = (s, n) => {
  const t = String(s ?? "");
  return t.length >= n ? t.slice(0, n) : t + " ".repeat(n - t.length);
};

const padRight = (s, n) => {
  const t = String(s ?? "");
  return t.length >= n ? t.slice(0, n) : " ".repeat(n - t.length) + t;
};

const fmtAmt = (n) => Number(n || 0).toFixed(2);

// Build the accounting-style ledger table (Sl | Date | Particulars | Name |
// Credit | Debit | Balance | Penalty) for the WhatsApp message body. This
// matches the on-page table format the customer sees on the public page.
const buildLedgerTable = (ledger) => {
  if (!ledger || ledger.length === 0) {
    return "```\nNo bill entries in the last 12 months.\n```";
  }
  const header =
    `${pad("#", 3)}| ${pad("Date", 10)}| ${pad("Particulars", 14)}| ${pad("Name", 12)}| ${padRight("Credit", 8)}| ${padRight("Debit", 8)}| ${padRight("Balance", 9)}| ${pad("Pen", 3)}`;
  const sep = "-".repeat(header.length);
  const lines = ledger.map((r) => {
    const dateShort = (r.date || "-").split("-").reverse().join("/");
    return (
      `${pad(String(r.sl_no), 3)}| ${pad(dateShort, 10)}| ${pad((r.particulars || "-").slice(0, 14), 14)}| ` +
      `${pad((r.name || "-").slice(0, 12), 12)}| ${padRight(fmtAmt(r.credit), 8)}| ` +
      `${padRight(fmtAmt(r.debit), 8)}| ${padRight(fmtAmt(r.balance), 9)}| ${pad(r.penalty || "-", 3)}`
    );
  });
  return "```\n" + header + "\n" + sep + "\n" + lines.join("\n") + "\n```";
};

// Build a fixed-width text table (rendered as ```code block``` in WhatsApp so
// columns stay aligned on the recipient's phone). Used for INTEREST loans
// where the ledger isn't per-bill; falls back to the payment history table.
const buildTable = (rows, isInterest) => {
  if (!rows || rows.length === 0) {
    return "```\nNo payments recorded in the last 12 months.\n```";
  }
  const header = `${pad("Date", 10)} | ${pad("Category", 14)} | ${padRight("Amt", 9)} | ${padRight("Pen", 8)} | ${padRight("Running", 10)}`;
  const sep = "-".repeat(header.length);
  const lines = rows.map((c) => {
    const cat = isInterest
      ? c.category === "Management Interest"
        ? "Mgmt Interest"
        : "Chit Interest"
      : c.category || "-";
    return `${pad(c.date || "-", 10)} | ${pad(cat, 14)} | ${padRight(fmtAmt(c.amount), 9)} | ${padRight(fmtAmt(c.penalty_amount), 8)} | ${padRight(fmtAmt(c.running_total), 10)}`;
  });
  return "```\n" + header + "\n" + sep + "\n" + lines.join("\n") + "\n```";
};

const buildMessage = ({
  name,
  paidAmt,
  payDate,
  templeName,
  link,
}) => {
  // Minimal WhatsApp message — greeting + link + sign-off.
  // The full 1-year balance sheet lives on the public page at `link`.
  return [
    `Dear ${name}, thanks for your payment of \u20B9${paidAmt} on ${payDate}.`,
    ``,
    `Full details: ${link}`,
    `— ${templeName || "our Temple"}`,
  ].join("\n");
};

/**
 * Compose a concise payment-receipt WhatsApp message (TC_COLLECTION_001).
 * No balance sheet, no ledger totals, no public link — just:
 *   thank-you · amount · date · purpose · temple sign-off.
 */
const buildReceiptMessage = ({
  name,
  paidAmt,
  payDate,
  templeName,
  purpose,
  collectionNo,
  paymentMode,
}) => {
  const purposeLine = purpose ? ` for ${purpose}` : "";
  const modeLine = paymentMode ? ` (${paymentMode})` : "";
  const refLine = collectionNo ? `\nReceipt #: ${collectionNo}` : "";
  return [
    `*Payment Receipt*`,
    ``,
    `Dear ${name},`,
    `Thanks for your payment of \u20B9${paidAmt}${purposeLine} on ${payDate}${modeLine}.` +
      refLine,
    ``,
    `— ${templeName || "our Temple"}`,
  ].join("\n");
};

/**
 * "Share Statement" WhatsApp button.
 * - For regular collections: opens the per-Member 1-year statement.
 * - For Management/Chit Interest: opens the per-loan statement.
 * - Message body includes an aligned monospace ledger table (```code```
 *   block) so the recipient sees the balance-sheet directly in chat.
 *
 * Props:
 *   CollectionRecord – the just-saved collection row
 *   templeName        – for the sign-off
 *   autoTrigger       – when true, invokes send() automatically on mount
 *                       (used by Bill after a new collection is added)
 *   receiptOnly       – when true, sends a concise payment-receipt (no
 *                       ledger / no public link). Used from Bill after
 *                       adding a collection so the operator's WhatsApp
 *                       message is a clean receipt (TC_COLLECTION_001).
 *                       Balance-sheet share stays on the Family Details
 *                       → Balance Sheet page.
 */
const WhatsappStatementButton = ({
  CollectionRecord,
  templeName,
  autoTrigger = false,
  receiptOnly = false,
}) => {
  const [loading, setLoading] = useState(false);
  const firedRef = useRef(false);

  const category = CollectionRecord?.collection_category;
  const memberId = CollectionRecord?.member;
  const interestId = CollectionRecord?.interest;
  const isInterest = INTEREST_CATEGORIES.has(category);

  const rawMobile =
    CollectionRecord?.mobile_number || CollectionRecord?.mobile_no || "";

  const canSend = receiptOnly
    ? !!rawMobile && category !== "Chit-fund"
    : category !== "Chit-fund" &&
      ((isInterest && interestId) || (!isInterest && memberId));

  const amount = parseFloat(CollectionRecord?.amount) || 0;
  const interestAmount = parseFloat(CollectionRecord?.interst_amount) || 0;
  const penaltyAmount = parseFloat(CollectionRecord?.penalty_amount) || 0;
  const paidAmt = isInterest ? amount + interestAmount + penaltyAmount : amount;

  const send = useCallback(async () => {
    if (loading || !canSend) return;
    setLoading(true);
    try {
      // Receipt-only fast path (TC_COLLECTION_001): no server round-trip,
      // no ledger, no public link. Just a clean thank-you message with the
      // purpose (festival / subscription month / etc.).
      if (receiptOnly) {
        const phone = String(rawMobile || "").replace(/\D/g, "");
        const waNumber = phone.length === 10 ? `91${phone}` : phone;
        if (waNumber.length < 10) {
          alert(
            "No mobile number is saved for this record. Please update the profile and try again."
          );
          return;
        }
        const purpose =
          CollectionRecord?.festival_name ||
          CollectionRecord?.sub_tariff_name ||
          CollectionRecord?.marriage_name ||
          CollectionRecord?.death_name ||
          CollectionRecord?.collection_category ||
          "";
        const msg = buildReceiptMessage({
          name: CollectionRecord?.member_name || "Customer",
          paidAmt: fmtAmt(paidAmt),
          payDate: CollectionRecord?.pay_date,
          templeName,
          purpose,
          collectionNo: CollectionRecord?.collaction_no,
          paymentMode: CollectionRecord?.payment_mode,
        });
        const url = `https://wa.me/${waNumber}?text=${encodeURIComponent(msg)}`;
        window.open(url, "_blank", "noopener,noreferrer");
        return;
      }

      let link;
      let fallbackName;
      let fallbackMobile;
      if (isInterest) {
        const { data: tokenResp } = await axios.get(
          `${API_BASE}/api/collection/interest_statement/token/${interestId}/`
        );
        link = buildInterestStatementLink(tokenResp.token);
        fallbackName = tokenResp.name;
        fallbackMobile = tokenResp.mobile;
      } else {
        const { data: tokenResp } = await axios.get(
          `${API_BASE}/api/collection/member_statement/token/${memberId}/`
        );
        link = buildMemberStatementLink(tokenResp.token);
        fallbackName = tokenResp.name;
        fallbackMobile = tokenResp.mobile;
      }
      const phone = String(rawMobile || fallbackMobile || "").replace(/\D/g, "");
      const waNumber = phone.length === 10 ? `91${phone}` : phone;
      if (waNumber.length < 10) {
        alert(
          "No mobile number is saved for this record. Please update the profile and try again."
        );
        return;
      }
      const name =
        CollectionRecord?.member_name || fallbackName || "Customer";
      const msg = buildMessage({
        name,
        paidAmt: fmtAmt(paidAmt),
        payDate: CollectionRecord?.pay_date,
        templeName,
        link,
      });
      const url = `https://wa.me/${waNumber}?text=${encodeURIComponent(msg)}`;
      window.open(url, "_blank", "noopener,noreferrer");
    } catch (e) {
      alert("Could not generate the statement link. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [
    loading,
    canSend,
    receiptOnly,
    isInterest,
    interestId,
    memberId,
    rawMobile,
    CollectionRecord?.member_name,
    CollectionRecord?.pay_date,
    CollectionRecord?.festival_name,
    CollectionRecord?.sub_tariff_name,
    CollectionRecord?.marriage_name,
    CollectionRecord?.death_name,
    CollectionRecord?.collection_category,
    CollectionRecord?.collaction_no,
    CollectionRecord?.payment_mode,
    paidAmt,
    templeName,
  ]);

  // Auto-trigger once when Bill mounts after a new collection is added.
  useEffect(() => {
    if (!autoTrigger || firedRef.current || !canSend) return;
    firedRef.current = true;
    const t = setTimeout(() => {
      send();
    }, 1200);
    return () => clearTimeout(t);
  }, [autoTrigger, canSend]);

  if (!canSend) return null;

  return (
    <Button.Primary
      text={
        loading ? (
          "Sending..."
        ) : (
          <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
            <FaWhatsapp style={{ fontSize: "22px" }} />
            {receiptOnly ? "Share Receipt" : "Share Statement"}
          </span>
        )
      }
      onClick={send}
      data-testid={receiptOnly ? "collection-whatsapp-receipt-btn" : "collection-whatsapp-btn"}
    />
  );
};

export default WhatsappStatementButton;
