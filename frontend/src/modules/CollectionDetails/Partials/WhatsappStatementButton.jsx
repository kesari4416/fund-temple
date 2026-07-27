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

// Build a fixed-width text table (rendered as ```code block``` in WhatsApp so
// columns stay aligned on the recipient's phone).
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
  statement,
  isInterest,
}) => {
  const greeting = `Dear ${name}, thanks for your payment of \u20B9${paidAmt} on ${payDate}.`;
  const table = buildTable(statement?.collections || [], isInterest);
  const t = statement?.totals || {};
  const totalsLine = t.amount !== undefined
    ? `Total received (1 yr): \u20B9${fmtAmt(t.amount)} · ${t.count} payments`
    : "";
  const breakdownParts = [];
  if ((t.interest ?? 0) > 0) breakdownParts.push(`Interest \u20B9${fmtAmt(t.interest)}`);
  if ((t.penalty ?? 0) > 0) breakdownParts.push(`Penalty \u20B9${fmtAmt(t.penalty)}`);
  const breakdownLine = breakdownParts.length ? `(of which ${breakdownParts.join(" · ")})` : "";

  let outstanding = "";
  if (isInterest && statement?.outstanding) {
    const o = statement.outstanding;
    outstanding = `Outstanding: Principal \u20B9${fmtAmt(o.principal_balance)} · Penalty \u20B9${fmtAmt(o.penalty_balance_amt)} = \u20B9${fmtAmt(Number(o.balance_amt || 0) + Number(o.penalty_balance_amt || 0))}`;
  } else if (!isInterest && statement?.pending_dues && statement.pending_dues.Total !== undefined) {
    const tot = Number(statement.pending_dues.Total || 0);
    if (tot > 0) outstanding = `Pending dues: \u20B9${fmtAmt(tot)}`;
  }
  return [
    greeting,
    "",
    `*1-year statement*`,
    table,
    totalsLine,
    breakdownLine,
    outstanding,
    "",
    `Full details: ${link}`,
    `— ${templeName || "our Temple"}`,
  ]
    .filter(Boolean)
    .join("\n");
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
 */
const WhatsappStatementButton = ({ CollectionRecord, templeName, autoTrigger = false }) => {
  const [loading, setLoading] = useState(false);
  const firedRef = useRef(false);

  const category = CollectionRecord?.collection_category;
  const memberId = CollectionRecord?.member;
  const interestId = CollectionRecord?.interest;
  const isInterest = INTEREST_CATEGORIES.has(category);

  const canSend =
    category !== "Chit-fund" &&
    ((isInterest && interestId) || (!isInterest && memberId));

  const rawMobile =
    CollectionRecord?.mobile_number || CollectionRecord?.mobile_no || "";

  const amount = parseFloat(CollectionRecord?.amount) || 0;
  const interestAmount = parseFloat(CollectionRecord?.interst_amount) || 0;
  const penaltyAmount = parseFloat(CollectionRecord?.penalty_amount) || 0;
  const paidAmt = isInterest ? amount + interestAmount + penaltyAmount : amount;

  const send = useCallback(async () => {
    if (loading || !canSend) return;
    setLoading(true);
    try {
      let link;
      let fallbackName;
      let fallbackMobile;
      let statement;
      if (isInterest) {
        const { data: tokenResp } = await axios.get(
          `${API_BASE}/api/collection/interest_statement/token/${interestId}/`
        );
        link = buildInterestStatementLink(tokenResp.token);
        fallbackName = tokenResp.name;
        fallbackMobile = tokenResp.mobile;
        const { data: stmt } = await axios.get(
          `${API_BASE}/api/collection/public/interest_statement/${tokenResp.token}/`
        );
        statement = stmt;
      } else {
        const { data: tokenResp } = await axios.get(
          `${API_BASE}/api/collection/member_statement/token/${memberId}/`
        );
        link = buildMemberStatementLink(tokenResp.token);
        fallbackName = tokenResp.name;
        fallbackMobile = tokenResp.mobile;
        const { data: stmt } = await axios.get(
          `${API_BASE}/api/collection/public/member_statement/${tokenResp.token}/`
        );
        statement = stmt;
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
        statement,
        isInterest,
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
    isInterest,
    interestId,
    memberId,
    rawMobile,
    CollectionRecord?.member_name,
    CollectionRecord?.pay_date,
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
            Share Statement
          </span>
        )
      }
      onClick={send}
      data-testid="collection-whatsapp-btn"
    />
  );
};

export default WhatsappStatementButton;
